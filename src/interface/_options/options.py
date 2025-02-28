# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)

"""
Options object.
"""

import copy
from enum import IntEnum
from typing import List, Optional

from .interface import Interface
from ..utils.thermo import C2K
from ..objects import Strand, Complex, StopCondition
from ..__init__ import __version__


""" Literals for Multistrand"""


class Literals:
    """
    Preset tags that are used in the MergeResult objects (FirstStepRate, FirstStepLeakRate, FirstPassageRate)
    and multistrand.experiment  
    """

    failure = "FAILURE"
    success = "SUCCESS"
    alt_success = "ALT_SUCCESS"

    """
     protected results may occupy the [x.tag in a x in options.interface.results]
    """
    time_out = "timeout"
    no_initial_moves = "noinitial"
    sim_error = "error"

    """ rate_method """
    metropolis = 1
    kawasaki = 2
    arrhenius = 3

    """ Nupack dangle options """
    dangles_none = 0
    dangles_some = 1
    dangles_all = 2

    """ Substrate type.    """
    substrateRNA = 1
    substrateDNA = 2

    """ Simulation modes """
    first_passage_time = 16  # 0x0010
    first_step = 48  # 0x0030
    transition = 256  # 0x0100
    trajectory = 128  # 0x0080
    
    """
        FD, May 8th, 2018:
        
        StopCondition and Macrostate definitions:
            Exact - match a secondary structure exactly (i.e. any system state that has a complex with this exact structure)
            Bound - match any system state in which the given strand is bound to another strand
            Ordered - match any system state in which there exists a complex with exactly the given strands, in that order (previous name: dissoc macrostate)
            Loose - match a secondary structure, allowing a certain number of disagreements, allowing domain state to be unspecified (* notation)
            Count - match a secondary structure, allowing a certain number of disagreements
            
            Compuational expense, low to high :           dissoc -- exact -- count -- loose     
    """
    exact_macrostate = 0  # 
    bound_macrostate = 1  # 
    dissoc_macrostate = 2  # 
    ordered_macrostate = 2 
    loose_macrostate = 3  # 
    count_macrostate = 4  # 


class Energy_Type(IntEnum):
    Loop_energy = 0     # [default]: no volume or association terms included. So only loop energies remain.
    Volume_energy = 1   # include dG_volume. No clear interpretation for this.
    Complex_energy = 2  # include dG_assoc. This is the NUPACK complex microstate energy, sans symmetry terms.
    Tube_energy = 3     # include dG_volume + dG_assoc. Summed over complexes, this is the system state energy.


class Options:
    """ The main wrapper for controlling a Multistrand simulation. Has an interface for returning results. """
       
    RateMethodToString = ["None", "Metropolis", "Kawasaki", "Arrhenius"]
    dangleToString = ["None", "Some", "All"]

    # Parameter type. Vienna is depreciated.
    viennaModel = 0
    nupackModel = 1
    parameterTypeToString = ["Vienna", "Nupack" ]
    substrateToString = ["Invalid", "RNA", "DNA"]
    
    # translation
    simulationMode = {"Normal"    :         Literals.first_passage_time,
                      "First Step":         Literals.first_step,
                      "Transition":         Literals.transition,
                      "Trajectory":         Literals.trajectory,
                      "First Passage Time": Literals.first_passage_time}
    
    cotranscriptional_rate_default = 0.001  # 1 nt added every 1 ms

    activestatespace = False
    reuse_energymodel = False
    
    def __init__(self, *args, **kargs):
        """
        Initialization of an Options object:

        Keyword Arguments:
        dangles -- Specifies the dangle terms used in the energy model.
                   Can be the strings 'None', 'Some', or 'All'.
        start_state  [type=list]     -- A list of Complexes to use as the
                                        initial state of the system.
        simulation_time [type=float] -- Cap on the maximum simulation time.
        num_simulations [type=int]   -- Number of trajectories to run
        biscale         [type=float] -- Bimolecular scaling constant
        uniscale        [type=float] -- Unimolecular scaling constant
        parameter_type               -- Which set of energy parameters is
                                        used. Available options: 'Nupack',
                                        'Vienna'
        substrate_type               -- Whether we want 'DNA' or 'RNA' energy
                                        parameters.
        rate_method                  -- Whether we want 'Kawasaki' or 'Metropolis'
                                        or 'Arrhenius' rate method for unimolecular steps.
                                        
        If rate_method == Literals.Arrhenius, please set lnAEnd, lnALoop, lnAStack, 
                                lnAStackStack, lnALoopEnd, lnAStackEnd, lnAStackLoop, 
                                EEnd, ELoop, EStack, EStackStack, ELoopEnd, EStackEnd, 
                                EStackLoop and bimolecular_rate(double value).
        """

        ##################################################
        #                                                #
        # Data Members                                   #
        # ->Members new to the python implementation     #
        #                                                #
        ##################################################
        
        """ Pipe to let Multistrand know the version from ../__init__.py """
        self.ms_version = float(__version__)
        
        self.errorlog = []
        """ Keeps lines relating to possible errors or warnings that
        should be reported to the user. Usually issues relating to the
        input file or parameters with odd values.

        TODO: implement some functions to report the errors found here.
        """
        self.full_trajectory = []
        self.full_trajectory_times = []
        self.full_trajectory_arrType = []
        self.trajectory_complexes = []
        self.trajectory_state_count = 0
        self._current_end_state = []
        self._current_transition_list = []
        self.trajectory_current_time = 0.0
        self.current_graph = None

        self.verbosity = 1
        """ Indicates how much output will be generated for each trajectory run.
        Value = 0:  No end state reported, no warnings for timeout and nonitial steps
        Value = 1:  No end states reports, warnings active   
        Value = 2:  Warnings and end states reports to stdout
        Value = 3:  Print debugging information from SimulationSystem to stdout
        """
        
        self.print_initial_first_step = False
        """
        If True, this value will print the initial state in First Step Mode to the trajectory with a timestamp of -1.0
        """

        self.cotranscriptional = False
        """
        If True, enables the cotranscriptional simulation mode. The mode works only when a single strand is supplied.
        Starting with the initial 8 nucleotides, the simulation adds a nucleotide on the 3' end every 1 millisecond. 
        """
        
        self.cotranscriptional_rate = self.cotranscriptional_rate_default
        """
        By default, the cotranscriptional mode adds one nucleotide every 1 millisecond.
        """
        
        #############################################
        #                                           #
        # Data Members: Energy Model                #
        #                                           #
        #############################################
        # See accessors below
        self._start_state: List[Complex] = []
        
        self.gt_enable = True
        """ Allow GT base pairs? If not, penalize by 10000 kcal/mol.
            False (0) : Do not allow GT base pairs.
        """

        self.log_ml = False
        """ Use logarithm to compute multiloop energy contributions?
        int          False (0): Do not use the logarithm.

        If True, uses log to compute one component of the multiloop energy, for loops of length > 6. Otherwise, uses the usual
        linear approximation. Using the log formula is slightly more expensive as it makes computation time for a multiloop scale
        with the number of adjoining helices.
        """
        
        self._join_concentration: float = 1.0
        """ concentration for V calcs
        Units are in M (molar), and represent the concentration of a single unique strand in the system. The volume simulated is
        then chosen using this parameter.
        """

        self._temperature_celsius = 37.0
        self._temperature_kelvin = 310.15

        self.rate_scaling = None
        """FD: This is a legacy option that sets unimolecular and bimolecular scaling automatically if set"""

        self._unimolecular_scaling: float = -1.0
        """ Rate scaling factor for unimolecular reactions."""
        
        self._bimolecular_scaling: float = -1.0
        """ Rate scaling factor for bimolecular reactions."""

        self._rate_method: int = Literals.kawasaki
        """ Choice of methods for determining forward/reverse rates. """

        self._dangles: int = Literals.dangles_some
        """ Dangles options for the energy model.
        
        None [0]: Do not include any dangles terms in the energy model.
        Some [1]: Some dangles terms.  (Nupack Default)
        All  [2]: Include all dangles terms, including odd overlapping ones.
        """

        self._parameter_type: int = self.nupackModel
        """ Which type of energy model parameter file to use.

        Vienna [0]: No longer well tested. Recommend not using.
        Nupack [1]: Includes some multi-complex parameters, otherwise
                    nearly the same as mfold style files.
        """

        self._substrate_type: int = Literals.substrateDNA
        """ What substrate's parameter files to use. 

        Invalid [0]: Indicates we should not auto-search for a param file.
        RNA     [1]: RNA parameters are available for Vienna and Nupack, see also
                     the comment in parameter_file_version.
        DNA     [2]: DNA parameters are publicly available via the Nupack distribution,
                     and possibly by the Vienna group upon request.
        """
        
        self.parameter_file = None
        """ Shortcut for using a very specific parameter file. Usually shouldn't be used.
        
        Type         Default
        str          None

        Should only be set to a string if it's ok to actually search
        for that parameter file. None will pass an error back to
        Multistrand if it gets used.
        """

        ####################
        #
        # BEGIN simmode
        #
        ####################
        
        self._simulation_mode = Literals.first_passage_time
        """ The simulation mode: how we want the simulation system to
        perform the main loop.
        """
        
        self._simulation_time: float = 600.0
        """ Maximum time (in seconds) allowed for each trajectory.
        
        Type         Default
        double       600.0
        """
        
        self._num_simulations: int = 1
        """ Total number of trajectories to run. 
        """
        
        self._initial_seed: Optional[int] = None
        """ Initial random number seed to use.
        If None when simulation starts, a random seed will be chosen
        """
        
        self.name_dict = {}
        """ Dictionary from strand name to a list of unique strand objects
        having that name.
        
        Type         Default
        dict         {}
        
        Modified when start state is added. Used as a lookup when stop states 
        are added.
        """
        
        self.lnAEnd = -0.1
        self.lnALoop = -0.1
        self.lnAStack = -0.1
        self.lnAStackStack = -0.1
        self.lnALoopEnd = -0.1
        self.lnAStackEnd = -0.1
        self.lnAStackLoop = -0.1
        self.EEnd = -0.1
        self.ELoop = -0.1
        self.EStack = -0.1
        self.EStackStack = -0.1
        self.ELoopEnd = -0.1
        self.EStackEnd = -0.1
        self.EStackLoop = -0.1
         
        """ These are undocumented adjustments to the energy model """
        self.dSA = -0.0
        self.dHA = -0.0

        """ 
            Buffer conditions 
            Like substrate_type, temperature, and dangles,
            these follow a listener pattern to propagate settings to dangles.
            (as opposed to copying settings at the last possible moment)
        """
        self.sodium = 1.0
        self.magnesium = 0.0
        
        ####################
        #
        # BEGIN startstop
        #
        ####################
                
        # See accessors below
        self._stop_conditions = []
        self._use_stop_conditions = False
        
        self.stop_count = 0
        """ The number of stop states. Equivalent to 'len(self.stop_conditions)'.
        
        Type         Default
        int          0
        
        Incremented automatically when a stop state is added. Should not be 
        modified externally.
        """
        
        self.output_time = -1.0
        """ The amount of time (in seconds) to wait between outputs of 
        trajectory information.
        
        Type         Default
        float        -1.0
        
        A value of -1.0 corresponds to not basing outputs on output_time
        (but perhaps outputting based on some other condition). A value of 0 
        means output as often as possible.
        """
        
        self._output_interval: int = -1
        """ The number of states between outputs of trajectory information.
        
        Type         Default
        int          -1
        
        A value of -1 corresponds to not basing outputs on output_interval
        (but perhaps outputting based on some other condition). A value of 1 
        means output every state, 2 means every other state, and so on.
        """
        
        self.current_interval = 0
        """ Current value of output state counter.
        
        Type         Default
        int          0
        
        When current_interval is equal to output_interval, the output state is 
        True, and otherwise the output state is False. This is modified by 
        increment_output_state, and probably shouldn't be used externally."""
        
        self.output_state = False
        """ Indicates whether output should be reported.
        
        Type         Default
        boolean      False
        
        Value should be True if self.current_interval == self.output_interval 
        and False otherwise.        
        """
        
        self.interface = Interface()
        
        ##############################
        #
        # End of __init__: call the keyword hook fn. 
        #
        ##############################

        self.__init_keyword_args(self, *args, **kargs)

    def __eq__(self, other: "Options") -> bool:
        """
        Compare configurations syntactically, ignoring random seeds and
        simulator state.
        """
        return (
            self.ms_version,
            self.verbosity, self.print_initial_first_step,
            self.activestatespace, self.reuse_energymodel,
            self.substrate_type, self.parameter_type, self.parameter_file,
            self.gt_enable, self.log_ml, self.dangles,
            self.cotranscriptional, self.cotranscriptional_rate,
            self.join_concentration, self.temperature,
            self.rate_scaling,
            self.rate_method, self.unimolecular_scaling, self.bimolecular_scaling,
            self.simulation_mode, self.simulation_time, self.num_simulations,
            self.dSA, self.dHA, self.sodium, self.magnesium,
            self.start_state, self.stop_conditions,
            self.output_time, self.output_interval, self.output_state,
        ) == (
            other.ms_version,
            other.verbosity, other.print_initial_first_step,
            other.activestatespace, other.reuse_energymodel,
            other.substrate_type, other.parameter_type, other.parameter_file,
            other.gt_enable, other.log_ml, other.dangles,
            other.cotranscriptional, other.cotranscriptional_rate,
            other.join_concentration, other.temperature,
            other.rate_scaling,
            other.rate_method, other.unimolecular_scaling, other.bimolecular_scaling,
            other.simulation_mode, other.simulation_time, other.num_simulations,
            other.dSA, other.dHA, other.sodium, other.magnesium,
            other.start_state, other.stop_conditions,
            other.output_time, other.output_interval, other.output_state,
        ) and (
            True if self.rate_method != Literals.arrhenius else (
                self.lnAStack, self.EStack, self.lnALoop, self.ELoop,
                self.lnAEnd, self.EEnd, self.lnAStackLoop, self.EStackLoop,
                self.lnAStackEnd, self.EStackEnd, self.lnALoopEnd, self.ELoopEnd,
                self.lnAStackStack, self.EStackStack,
            ) == (
                other.lnAStack, other.EStack, other.lnALoop, other.ELoop,
                other.lnAEnd, other.EEnd, other.lnAStackLoop, other.EStackLoop,
                other.lnAStackEnd, other.EStackEnd, other.lnALoopEnd, other.ELoopEnd,
                other.lnAStackStack, other.EStackStack,
            ))

    def legacyRates(self):
                    
        warningmsg = "Warning! rate_scaling is set, enabling support for legacy code. Now setting rate defaults for "
                
        if self.temperature == 298.15 and self.rate_method == Literals.kawasaki:
            warningmsg += "Kawasaki 25 C"
            self.JSKawasaki25()
        elif self.temperature == 310.15 and self.rate_method == Literals.kawasaki:
            warningmsg += "Kawasaki 37 C"
            self.JSKawasaki37()
        elif self.temperature == 298.15 and self.rate_method == Literals.metropolis:
            warningmsg += "Metropolis 25 C"
            self.JSMetropolis25()
        elif self.temperature == 310.15 and self.rate_method == Literals.metropolis:
            warningmsg += "Metropolis 37 C"
            self.JSMetropolis37()
        else:
            warningmsg += "JS-Default"
            self.JSDefault()

        print(warningmsg)
        self.rate_scaling = None
        
    # FD, May 5th 2017
    # Supplying rate options for Metropolis and Kawasaki methods,
    # all using the dangles = some option. Also:  one general default,
    # and one setting for Metropolis rates derived for DNA23.
    
    def JSDefault(self):
        """ Default rates (Kawasaki at 37 degree Celcius) from Joseph Schaeffer's thesis  """
        self.JSKawasaki37()
    
    def JSMetropolis25(self):
        """ Default rates for Metropolis at 25 degree Celcius, from Joseph Schaeffer's thesis
        """
        self.rate_method = Literals.metropolis

        self.unimolecular_scaling = 4.4e8
        self.bimolecular_scaling = 1.26e6
    
    def JSKawasaki25(self):
        """ Default rates for Kawasaki at 25 degree Celcius, from Joseph Schaeffer's thesis
        """
        self.rate_method = Literals.kawasaki

        self.unimolecular_scaling = 6.1e7
        self.bimolecular_scaling = 1.29e6
    
    def JSKawasaki37(self):
        """ Default rates for Kawasaki at 37 degree Celcius, from Joseph Schaeffer's thesis
        """
        self.rate_method = Literals.kawasaki

        self.unimolecular_scaling = 1.5e8
        self.bimolecular_scaling = 1.38e6
    
    def JSMetropolis37(self):
        """ Default rates for Metropolis at 37 degree Celcius, from Joseph Schaeffer's thesis
        """
        self.rate_method = Literals.metropolis

        self.unimolecular_scaling = 7.3e8
        self.bimolecular_scaling = 1.40e6

    def DNA23Metropolis(self):
        """ 
        Parameters for Metropolis at 25 degree Celcius, from the DNA23 conference (55th walker)

        Reference:
        ----------
        Zolaktaf, Sedigheh, Frits Dannenberg, Xander Rudelis, Anne Condon,
        Joseph M. Schaeffer, Mark Schmidt, Chris Thachuk, and Erik Winfree.
        2017. ‘Inferring Parameters for an Elementary Step Model of DNA
        Structure Kinetics with Locally Context-Dependent Arrhenius Rates’. In
        DNA Computing and Molecular Programming, edited by Robert Brijder and
        Lulu Qian, 172–87. Lecture Notes in Computer Science. Cham: Springer
        International Publishing. https://doi.org/10.1007/978-3-319-66799-7_12.
        """
        self.rate_method = Literals.metropolis

        self.unimolecular_scaling = 2.41686715e+06
        self.bimolecular_scaling = 8.01171383e+05
    
    def DNA23Arrhenius(self):
        """
        Reference:
        ----------
        Zolaktaf, Sedigheh, Frits Dannenberg, Xander Rudelis, Anne Condon,
        Joseph M. Schaeffer, Mark Schmidt, Chris Thachuk, and Erik Winfree.
        2017. ‘Inferring Parameters for an Elementary Step Model of DNA
        Structure Kinetics with Locally Context-Dependent Arrhenius Rates’. In
        DNA Computing and Molecular Programming, edited by Robert Brijder and
        Lulu Qian, 172–87. Lecture Notes in Computer Science. Cham: Springer
        International Publishing. https://doi.org/10.1007/978-3-319-66799-7_12.
        """
        self.rate_method = Literals.arrhenius

        self.lnAStack = 1.41839430e+01
        self.EStack = 5.28692038e+00

        self.lnALoop = 1.64236969e+01
        self.ELoop = 4.46143369e+00

        self.lnAEnd = 1.29648159e+01
        self.EEnd = 3.49798154e+00

        self.lnAStackLoop = 5.81061725e+00
        self.EStackLoop = -1.12763854e+00

        self.lnAStackEnd = 1.75235569e+01
        self.EStackEnd = 2.65589869e+00
        
        self.lnALoopEnd = 2.42237267e+00
        self.ELoopEnd = 8.49339120e-02
        
        self.lnAStackStack = 8.04573830e+00
        self.EStackStack = -6.27121400e-01
        
        self.bimolecular_scaling = 1.60062641e-02
 
    # FD: After temperature, substrate (RNA/DNA) or danlges is updated, we
    # attempt to update boltzmann samples.
    def updateBoltzmannSamples(self):
        for c in self._start_state:
            c.set_boltzmann_parameters(
                self.dangleToString[self.dangles],
                self.substrateToString[self.substrate_type],
                self._temperature_celsius, self.sodium, self.magnesium)
            self.warn_Boltzmann_sample_wo_GT(c)

    def warn_Boltzmann_sample_wo_GT(self, c: Complex):
        if c.boltzmann_sample and not self.gt_enable:
            raise Warning(
                "Attempting to use Boltzmann sampling, but GT pairing is "
                "disabled. Energy model of Multistrand will not match that of "
                "the NUPACK sampling method.")

    @property
    def simulation_time(self):
        return self._simulation_time

    @simulation_time.setter
    def simulation_time(self, value):
        self._simulation_time = float(value)

    @property
    def num_simulations(self):
        return self._num_simulations

    @num_simulations.setter
    def num_simulations(self, value):
        self._num_simulations = int(value)

    @property
    def output_interval(self):
        return self._output_interval

    @output_interval.setter
    def output_interval(self, value):
        self._output_interval = int(value)

    @property
    def bimolecular_scaling(self):
        if self.rate_scaling != None :
            self.legacyRates()
        return self._bimolecular_scaling
 
    @bimolecular_scaling.setter
    def bimolecular_scaling(self, value):
        self._bimolecular_scaling = float(value)
 
    @property
    def unimolecular_scaling(self):
        if self.rate_scaling != None:
            self.legacyRates()
        return self._unimolecular_scaling
    
    @unimolecular_scaling.setter
    def unimolecular_scaling(self, value):
        self._unimolecular_scaling = float(value)

    @property
    def join_concentration(self):
        return self._join_concentration

    @join_concentration.setter
    def join_concentration(self, value):
        self._join_concentration = float(value)

    # FD: Shadow variables for danlges because we need to observe changes
    # (and update boltzmann samples accordingly)
    @property
    def dangles(self):
        return self._dangles
    
    @dangles.setter
    def dangles(self, value):
        if isinstance(value, str):
            value = self.dangleToString.index(value)
        self._dangles = int(value)
        assert self.dangles in range(3)
        self.updateBoltzmannSamples()
        
    # FD: Shadow parameter so that boltzmann samples can be updated when this
    # parameter is set. In a better control flow, complexes themselves might fetch the right
    # constants just before evaluating their boltzmann samples.
    @property
    def substrate_type(self):
        return self._substrate_type

    @substrate_type.setter
    def substrate_type(self, value):
        if isinstance(value, str):
            value = self.substrateToString.index(value)
        self._substrate_type = int(value)
        assert self.substrate_type in range(1, 3)
        self.updateBoltzmannSamples()

    @property
    def parameter_type(self):
        return self._parameter_type

    @parameter_type.setter
    def parameter_type(self, value):
        if isinstance(value, str):
            value = self.parameterTypeToString.index(value)
        self._parameter_type = int(value)
        assert self.parameter_type in range(2)

    @property
    def simulation_mode(self):
        return self._simulation_mode

    @simulation_mode.setter
    def simulation_mode(self, value):
        if isinstance(value, str):
            value = self.simulationMode[value]
        self._simulation_mode = int(value)
        assert self.simulation_mode in [16, 48, 256, 128]

    @property
    def rate_method(self):
        return self._rate_method

    @rate_method.setter
    def rate_method(self, value):
        if isinstance(value, str):
            value = self.RateMethodToString.index(value)
        self._rate_method = int(value)
        assert self.rate_method in range(1, 4)

    # FD: Following same listener pattern for sodium, magnesium, so that changes
    # are propagated to complexes.
    @property
    def sodium(self):
        return self._sodium

    @sodium.setter
    def sodium(self, value):
        self._sodium = float(value)
        self.updateBoltzmannSamples()
    
    @property
    def magnesium(self):
        return self._magnesium
    
    @magnesium.setter
    def magnesium(self, value):
        self._magnesium = float(value)
        self.updateBoltzmannSamples()
        
    """ FD: Setting boltzmann sample in options could be used to propagate this setting to all starting states. 
            But we do not support this, and sampling is a property of each individual complex instead. """

    @property
    def boltzmann_sample(self):
        raise ValueError('Options.boltzmann_sample is now depreciated. Use Complex.boltzmann_sample instead.')

    @boltzmann_sample.setter
    def boltzmann_sample(self, val):
        raise ValueError('Options.boltzmann_sample is now depreciated. Use Complex.boltzmann_sample instead.')

    @property
    def start_state(self):
        """ Get the start state, i.e. a list of Complex objects.
        
        Type         Default
        list         []
        
        This should be used by ssystem.cc to get the (potentially sampled) 
        start state.
        """
        return self._start_state

    @start_state.setter
    def start_state(self, *args):
        """ Set the start state, i.e. a list of Complex objects.
        
        Type         Default
        list         []
        
        The start state should be set (e.g. by the parser) so trajectories know 
        how to start.
        """
        # Error checking first
        if self._start_state != []:
            raise Exception("Start state should only be set once.")
        if len(args) == 0 or len(args[0]) == 0:
            raise ValueError("No start state given.")
        
        # deduce our input from the type of args[0].
        # Copy the input list because it's easy to do and it's safer
        
        if isinstance(args[0], Complex):
            # args is a list of complexes
            vals = copy.deepcopy(args) 
        elif len(args) == 1 and hasattr(args[0], "__iter__"):
            vals = copy.deepcopy(args[0])
        else:
            raise ValueError("Could not comprehend the start state you gave me.")

        # vals is now an iterable over our starting configuration
        for i in vals:
            if isinstance(i, Complex):
                self._add_start_complex(i)
            else:
                raise TypeError(f"Start states must be Complexes. "
                                f"Received something of type {type(i)}.")

    def _add_start_complex(self, c: Complex):
        self._start_state.append(c)
        c.set_boltzmann_parameters(
            self.dangleToString[self.dangles],
            self.substrateToString[self.substrate_type],
            self._temperature_celsius, self._sodium, self._magnesium)
        self.warn_Boltzmann_sample_wo_GT(c)

    @property
    def initial_seed(self):
        return self._initial_seed if self.initial_seed_flag else None

    @initial_seed.setter
    def initial_seed(self, seed):
        self._initial_seed = int(seed)

    @property
    def initial_seed_flag(self):
        return self._initial_seed != None
    
    @property
    def stop_conditions(self):
        """ The stop states, i.e. a list of StopCondition objects.
        
        Type         Default
        list         []
        
        Stop states should be added to this list (e.g. by the parser) so
        trajectories know when to end.
        """
        return self._stop_conditions
    
    @stop_conditions.setter
    def stop_conditions(self, stop_list):
        """ The stop states, i.e. a list of StopCondition objects.
        
        Type         Default
        list         []
        
        Stop states should be added to this list (e.g. by the parser) so
        trajectories know when to end.
        """
        # Error checking
        if self._stop_conditions != []:
            raise Exception("Stop conditions should be set only once.")

        # Type checking
        for item in stop_list:
            if not isinstance(item, StopCondition):
                raise TypeError(f"All items must be 'StopCondition', not '{type(item)}'.")
        
        # Copy the input list because it's easy to do and it's safer
        stop_list = copy.deepcopy(stop_list)
        
        # Set the internal data members
        self.stop_count = len(stop_list)
        self._stop_conditions = stop_list
        self._use_stop_conditions = True

    @property
    def use_stop_conditions(self):
        """ Indicates whether trajectories should end when stop states
        are reached.
        
        Type            Default
        boolean         False: End trajectory upon reaching max time only.
        
        Defaults to ending trajectories only on the max simulation
        time, but setting any stop conditions automatically changes
        this to True, and it will stop whenever it reaches a stop
        condition, or at max time [whichever comes first].
        """
        return self._use_stop_conditions

    @use_stop_conditions.setter
    def use_stop_conditions(self, val):
        
        if val == True and len(self._stop_conditions) == 0:
             raise Warning("Options.use_stop_conditions was set to True, but no stop conditions have been defined!")

        self._use_stop_conditions = val
    
    @property
    def increment_output_state(self):
        """ Modifies self.current_interval and self.output_state as 
        necessary based on self.output_interval.
        """
        if self.output_interval == None or self.output_interval < 0:
            raise ValueError("output_interval has invalid value: %s" % self.output_interval)
        
        elif self.current_interval > self.output_interval:
            raise ValueError("current_interval has invalid value: %s" % self.current_interval)
        
        elif self.current_interval == self.output_interval:
            self.current_interval == 0
        
        else:
            self.current_interval += 1
        
        self.output_state = (self.current_interval == self.output_interval)

        return None

    @property
    def temperature(self):
        """
        Temperature, in degrees Kelvin.
        
        Arguments:
        temperature [type=float,default=310.15] -- Standard units of Kelvin.
               Default value corresponds to 37(C).
        
        This is used mostly in scaling energy model terms, and those
        scaling factors always use Kelvin. Note that when set, the
        Options object will try to make sure it's actually a 'sane'
        value, as follows:
        
        Temperatures in the range [0,100] are assumed to be Celsius,
        and are converted to Kelvin.
        
        Temperatures in the range [273,373] are assumed to be in
        Kelvin.
        
        Any temperature outside these ranges is set as the temperature
        in Kelvin, and a warning is raised. If any conversion takes
        place, a message is added to the Options object's errorlog.
        """
        return self._temperature_kelvin

    @temperature.setter
    def temperature(self, val):
        """ performs some sanity checking and provides a log error if
        perhaps the user was confused.

        Assumptions: Input should be in Kelvin, if it's not in a
        'reasonable' range for Kelvin, convert to Celsius if it's in a
        reasonable range for C [sending an output to the error log
        warning that it did so], otherwise error.

        Reasonable ranges:
            [0,100]  : Celsius
            [273,373]: Kelvin
            Others:    If you want a Fahrenheit reasonable range, I think you
                       might be unreasonable. Also, it overlaps with Celsius a bit much.

        Yes, these ranges are quite generous.
        """
        if C2K < val < C2K + 100:
            self._temperature_kelvin = val
            self._temperature_celsius = val - C2K
            self.updateBoltzmannSamples()

        elif 0.0 < val < 100.0:
            self._temperature_celsius = val
            self._temperature_kelvin = val + C2K
            self.updateBoltzmannSamples()
            self.errorlog.append("Warning: Temperature was set at the value [{0}]. We expected a value in Kelvin, or with appropriate units.\n         Temperature was automatically converted to [{1}] degrees Kelvin.\n".format(val, self._temperature_kelvin))

        else:
            self._temperature_kelvin = val
            self._temperature_celsius = val - C2K
            self.updateBoltzmannSamples()
            self.errorlog.append("Warning: Temperature was set at the value [{0}]. This is outside the normal range of temperatures we expect, so it was assumed to be in Kelvin.\n".format(val))
            raise Warning("Temperature did not fall in the usual expected ranges. Temperatures should be in units Kelvin, though the range [0,100] is assumed to mean units of Celsius.")
    
    def make_unique(self, strand):
        """Returns a new Strand object with a unique identifier replacing the 
        old id. Also adds the new strand to self.name_dict[strand.name].
        """
        new_strand = Strand(self.unique_id, strand.name, strand.sequence, strand.domain_list)
        self.unique_id += 1
        
        try:
            self.name_dict[strand.name].append(new_strand)
        except KeyError:
            self.name_dict[strand.name] = [new_strand]

        return new_strand

    @property
    def add_result_status_line(self):
        return None

    @add_result_status_line.setter
    def add_result_status_line(self, val):
        """
        Accepts a 4-tuple with format:
            (random number seed, stop result flag, completion time,
             stop result tag)
        """
        assert isinstance(val, tuple) and len(val) == 4
        self.interface.add_result(val, res_type='status_line')
        if len(self._current_end_state) > 0:
            self.interface.end_states.append(self._current_end_state)
            self._current_end_state = []
    
    @property
    def add_result_status_line_firststep(self, val):
        return None

    @add_result_status_line_firststep.setter
    def add_result_status_line_firststep(self, val):
        """
        Accepts a 5-tuple with format:
            (random number seed, stop result flag, completion time,
             collision rate, stop result tag)
        """
        assert isinstance(val, tuple) and len(val) == 5
        self.interface.add_result(val, res_type='firststep')
        if len(self._current_end_state) > 0:
            self.interface.end_states.append(self._current_end_state)
            self._current_end_state = []
            
    @property
    def add_complex_state_line(self):
        return None

    @add_complex_state_line.setter
    def add_complex_state_line(self, val):
        """
        Accepts a 7-tuple with format:
            (random number seed, unique complex id, strand names, sequence,
             structure, energy, enthalpy)
        """
        assert isinstance(val, tuple) and len(val) == 7
        self._current_end_state.append(val)
        if self.verbosity > 1:
            print("{0[0]}: [{0[1]}] '{0[2]}': {0[5]} \n{0[3]}\n{0[4]}\n".format(val))

    @property
    def add_transition_info(self):
        return None

    @add_transition_info.setter
    def add_transition_info(self, val):
        """
        Accepts a 2-tuple with format:
            (current time, list of boolean values for stop conditions)
        """
        assert isinstance(val, tuple) and len(val) == 2
        # print( "Time: {0[0]} Membership: {0[1]}".format( val ))
        self._current_transition_list.append(val)

    @property
    def add_trajectory_complex(self):
        return None

    @add_trajectory_complex.setter
    def add_trajectory_complex(self, val):
        """ Takes a 6-tuple as only value, it should be:
            (random number seed, unique complex id, strand names, sequence, structure, energy )
            Adds this data to the interface's results object."""

        self.trajectory_complexes.append(val)
        # print "Number of complexes in current traj output:" + str(len(self.trajectory_complexes))

    @property
    def add_trajectory_current_time(self):
        return None

    @add_trajectory_current_time.setter
    def add_trajectory_current_time(self, val):
        self.trajectory_current_time = val
        self.trajectory_state_count += 1
        self.full_trajectory.append(self.trajectory_complexes)
        self.full_trajectory_times.append(self.trajectory_current_time)
        self.trajectory_complexes = []
        
    @property
    def add_trajectory_arrType(self):
        return None

    @add_trajectory_arrType.setter
    def add_trajectory_arrType(self, val):
        self.full_trajectory_arrType.append(val)
        
    @property
    def interface_current_seed(self) -> Optional[int]:
        """ This is the current random number seed for the trajectory currently being
        simulated by multistrand.

        This property and its setter exist mainly for use by the
        multistrand module to provide some feedback on what seed it's
        working on, in case that trajectory crashes before completion,
        and other similar cases."""
        return self.interface.current_seed

    @interface_current_seed.setter
    def interface_current_seed(self, val):
        self.interface.current_seed = int(val)
        get_structure = lambda s: (s._last_boltzmann_structure
                                   if s.boltzmann_sample else s._fixed_structure)
        self.interface.start_structures[val] = list(
            map(get_structure, self._start_state))

    @property
    def increment_trajectory_count(self):
        self.interface.increment_trajectory_count()
        if len(self._current_transition_list) > 0:
            self.interface.transition_lists.append(self._current_transition_list)
            self._current_transition_list = []

    def __init_keyword_args(self, *args, **kargs):
        """ Helper subfunction. """
        
        """ Create an options object [with default (presumably useful) values]

        Now with new and improved argument lists!

        Any default Options attribute can be set just by passing a
        keyword argument with the desired value, e.g.
        Options(simulation_time=100.0)

        Listed below are some shortcuts, for attributes that have a
        range of options, or shortened names for long attributes.
        

        Keyword Argument  |  Options
        dangles           |  'None', 'Some', 'All'
        parameter_type    |  'Nupack', 'Vienna'
        substrate_type    |  'DNA','RNA'
        
        sim_time          | [simulation_time] Max time to simulate
        num_sims          | [num_simulations] Number of trajectories to run
        biscale           | [bimolecular_scaling] Bimolecular scaling constant
        uniscale          | [unimolecular_scaling] Unimolecular scaling constant

        start_state       |  List of Complexes

        ...
        More to come!"""
        arg_lookup_table = {
            'biscale': lambda x: self.__setattr__('bimolecular_scaling', x),
            'uniscale': lambda x: self.__setattr__('unimolecular_scaling', x),
            'num_sims': lambda x: self.__setattr__('num_simulations', x),
            'sim_time': lambda x: self.__setattr__('simulation_time', x),
            'concentration': lambda x: self.__setattr__('join_concentration', x)
            }
        
        # FD: Start throwing errors if not in the right format
        for key, value in kargs.items():
            if key == "sim_time":
                if not isinstance(value, (float)):
                    raise Warning("Please provide sim_time as float")
            if key == "num_sims":
                if not isinstance(value, (int)):
                    raise Warning("Please provide num_sims as int")
            if key == "biscale":
                if not isinstance(value, (float)):
                    raise Warning("Please provide biscale as float")
            if key == "uniscale":
                if not isinstance(value, (float)):
                    raise Warning("Please provide uniscale as float")
            if key == "concentration":
                if not isinstance(value, (float)):
                    raise Warning("Please provide concentration as float")

        for key, value in kargs.items():
            if key in arg_lookup_table:
                arg_lookup_table[key](value)
            # FD: Do some additional parsing for legacy support
            else:
                self.__setattr__(key, value)
