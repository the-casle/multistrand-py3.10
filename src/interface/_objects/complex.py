# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)

from functools import reduce

from ..utils.thermo import Model, sample
import numpy as np

from .strand import Strand


class Complex:

    MAX_SAMPLES_AT_ONCE = 200
    """
    A representation of a single connected complex of strands.
    """
    unique_id = 0
    
    def __init__(self, structure, sequence=None, strands=None, name=None, boltzmann_sample=False):
        """
        Initialization:
        
        Keyword Arguments:
        sequence [type=str]          -- Flat sequence to use for this complex.
        structure [type=str]         -- Flat structure to use for this complex.
        name [type=str]              -- Name of the complex. If None (the default),
                                        it is automatically generated with the
                                        form 'automatic' + a unique integer.
        boltzmann_sample [type=bool] -- Whether we should boltzmann sample this
                                        complex.
        
        You must include both of the required keyword arguments to create a Complex with the new style init.
        """
        
        
        """  
            Set sampleSelect if you want to discard certain Boltzmann sampled secondary structures. 
            The function input is a string-concatenated secondary structure.
            The function should return True for accepted structures.
        """
        self.sampleSelect = None   

        if sequence and not strands:
            self.strand_list = [Strand(sequence=i) for i in sequence.split("+")]
            self._fixed_structure = str(structure)
        elif strands and not sequence:
            self.strand_list = strands
            self._init_parse_structure(str(structure))
        else:
            raise Exception("One of, and and not both of, 'sequence' or 'strands' must be provided")
        
        self.id = Complex.unique_id
        self.name = name or "automatic" + str(Complex.unique_id)
        # note: Boltzmann sampling is somewhat confusing if you pass a
        # structure that is anything other than all "."'s. So maybe we
        # should check for that.
        self.boltzmann_sample = boltzmann_sample
        self._last_boltzmann_structure = False
        self._boltzmann_sizehint = 1
        self._boltzmann_queue = []
        
        # Adjust here for default Boltzmann Parameters. 'None' in this case means to not pass that parameter and let the sample binary use its default. Substrate defaults to DNA.
        self._dangles = None
        self._substrate_type = None
        self._temperature = None
        self._sodium = None
        self._magnesium = None
        # Taken to be 1, unless it is EXPLICITLY stated otherwise!
        self.boltzmann_supersample = 1
        Complex.unique_id += 1

    def __eq__(self, other: "Complex") -> bool:
        """
        Compare complexes syntactically, ignoring names if they were generated
        automatically. Furthermore, if Boltzmann sampling is active, then the
        secondary structure is also ignored, while still ensuring that the
        strand positions are identical in the secondary structure
        representations.

        This method is currently used only to check whether the simulator
        configuration was generated deterministically. For a more semantically
        meaningful comparison of complexes that takes into account symmetries of
        the representation, see the object hierarchy in the `KinDA` package,
        which depends on `Multistrand`.
        """
        return (
            None if self.name.startswith("automatic") else self.name,
            self.sequence, self.strand_list,
            self.boltzmann_sample, self.boltzmann_supersample
        ) == (
            None if other.name.startswith("automatic") else other.name,
            other.sequence, other.strand_list,
            other.boltzmann_sample, other.boltzmann_supersample
        ) and (
            ((np.array(list(self.structure)) == '+') ==
             (np.array(list(other.structure)) == '+')).all()
            if self.boltzmann_sample else
            self.structure == other.structure
        )

    def __str__(self):
        return (
            "Complex:\n"
            "  {fieldnames[0]:>11}: '{0.name}'\n"
            "  {fieldnames[1]:>11}: {0.sequence}\n"
            "  {fieldnames[2]:>11}: {0.structure}\n"
            "  {fieldnames[3]:>11}: {1}\n"
            "  {fieldnames[4]:>11}: {0.boltzmann_sample}\n"
            "  {fieldnames[5]:>11}: {0.boltzmann_supersample}").format(
                self, [i.name for i in self.strand_list], fieldnames=(
                    'Name', 'Sequence', 'Structure', 'Strands', 'Boltzmann', 'Supersample'))

    def _init_parse_structure(self, structure):
        strand_count = len(self.strand_list)
        base_count = sum(len(s.sequence) for s in self.strand_list)
        total_flat_length = base_count + strand_count - 1
        
        if len(structure) == total_flat_length:
            self._fixed_structure = structure
        else:
            domain_count = sum(len(s.domain_list) for s in self.strand_list)
            if len(structure) != domain_count + strand_count - 1:
                error_msg = "ERROR: Could not interpret the passed structure [{0}];".format(structure)
                if domain_count > 0:
                    error_msg += "Expected a structure composed of characters from '.()+' \
                    and with either length [{0}] for a complete structure, or length [{1}] \
                    for a domain-level structure. If giving a domain-level structure, it \
                    should have the layout [{2}].".format(total_flat_length,
                        domain_count + strand_count - 1,
                        "+".join(''.join('x' for d in s.domain_list)\
                                 for s in self.strand_list))
                else:
                        error_msg += " Could not parse the dot-paren structure. Expected string composed of ()+."
                raise ValueError(error_msg)
            else:
                matched_list = list(zip(
                    structure,
                    # the reduce just composes the domain_lists into one big
                    # ordered list of domains
                    reduce(lambda x, y: x + [d.length for d in y.domain_list] + [1],
                           self.strand_list, [])))
                self._fixed_structure = "".join(i[0] * i[1] for i in matched_list)
    
    def get_unique_ids(self):
        """
        Produce the set of unique strands in this Complex
        
        Return Value:
          -- A `set` of the unique strand names.
        """
        return set([i.id for i in self.strand_list])
    
    def canonical_strand(self):
        """Return the name of the `canonical` strand for this complex.
        
        This is either the strand name which appears first alphabetically,
        or if no strands are named, this is just the name of the complex.
        
        Return Value:
          -- The string containing the canonical name.
        """
        return min(self.strand_list, key=lambda x: x.name).name
    
    def __len__(self):
        """ Length of a complex is the number of strands contained.
        
        Use the attribute :attr:`sequence_length` if you need the sequence length. """
        return len(self.strand_list)
    
    @property
    def sequence_length(self):
        """ The total length of all contained strands. """
        return len("".join([i.sequence for i in self.strand_list]))
    
    @property
    def structure(self):
        """ If this complex is set to use boltzmann sampling, this property returns a newly sampled structure. Otherwise it gets the fixed structure for the complex."""
        if self.boltzmann_sample:
            self.generate_boltzmann_structure()
            
            if not self.sampleSelect == None:
                while not self.sampleSelect(self._last_boltzmann_structure):
                    self.generate_boltzmann_structure()
            
            # puts the generated structure in self._last_boltzmann_structure
            # for use by other properties as well.
            return self._last_boltzmann_structure
        else:
            return self._fixed_structure
    
    @structure.setter
    def structure(self, value):
        # I include the following due to the 'normal' use cases of Complex
        # involve it immediately being deepcopy'd (e.g. in starting
        # states, etc). So allowing someone to set the fixed structure
        # member is probably not a good idea - we could remove this
        # completely so the structure component is pretty much immutable.
        #
        # In practice, I can see a case where it may be useful to modify it if you're using an interactive mode, but even in those cases it may not do what the user wants, if they're relying on that changing previous parts. For example:
        # c1 = Complex("c1","c1", "......((.......)).....")
        # o = Options()
        # o.start_state = [c1]
        # ... user runs a simulation and gets a syntax warning about mismatched parens...
        # c1.structure = "......((........))...."
        #
        # # This did NOT actually change o at all! So the warning used
        # # here mentions that, and just in case, returns a new object
        # # anyways!
        #
        import warnings
        warnings.warn("Setting a Complex's structure does not [usually] change existing uses of this Complex, so the object returned is a NEW object to avoid any confusion as to how it may affect previous usages.", SyntaxWarning)
        import copy
        retval = copy.deepcopy(self)
        retval._fixed_structure = value
        return retval
    
    @property
    def fixed_structure(self):
        """ The structure used to create this Complex. """
        return self._fixed_structure
    
    @property
    def current_boltzmann_structure(self):
        """ The structure that was the result of our last Boltzmann sampling, or the value False if no sampling has occurred."""
        return self._last_boltzmann_structure
    
    @property
    def boltzmann_count(self):
        """ The number of Boltzmann sampled structures we expect to be needed when using this Complex in a start structure. The default value is 1, which means every time a structure is requested it will need to call the sampling function; if you provide a better estimate, it may be a lot more efficient in how often it needs to call the sampling function. """
        return self._boltzmann_sizehint
    
    @boltzmann_count.setter
    def boltzmann_count(self, value):
        if value >= 1:
            self._boltzmann_sizehint = value
        else:
            self._boltzmann_sizehint = 1
    
    @property
    def sequence(self):
        """ The calculated 'flat' sequence for this complex. """
        return "+".join([strand.sequence for strand in self.strand_list])
    
    def set_boltzmann_parameters(self, dangles, substrate_type, temperature, sodium, magnesium):
        """
        Sets the parameters to be passed on to NUPACK for Boltzmann sampling of this complex.
        Uses the private properties which are then read by generate_boltzmann_structure.
        
        Called by the start_state setter in an Options object, and the setters for dangles, substrate_type and temperature properties in an Options object.
        """
        self._dangles = dangles
        self._substrate_type = substrate_type
        self._temperature = temperature
        self._sodium = sodium
        self._magnesium = magnesium


    def generate_boltzmann_structure(self):

        """
        Create a new boltzmann sampled structure for this complex.
        
        Mostly intended for internal use, but can access the generated structure
        via the `current_boltzmann_structure` property.
        
        Return Value:
          -- None
        """
        if len(self._boltzmann_queue) > 0:
            self._pop_boltzmann()
            return

        # set up the # of structures to grab from the file, max out at
        # ~100 so we don't use too much CPU on this step. JS's testing
        # timed a 100 count at ~ .1s and 10 and 1 counts were almost
        # always around .08s, so at least in this range there's a lot more
        # call overhead than generation time being used.
        # MAX_SAMPLES_AT_ONCE * supersample is the effective number of sample
        # we generate per round
        if self._boltzmann_sizehint > self.MAX_SAMPLES_AT_ONCE * self.boltzmann_supersample:
            count = self.MAX_SAMPLES_AT_ONCE
        elif self._boltzmann_sizehint >= 1:
            count = int(self._boltzmann_sizehint / self.MAX_SAMPLES_AT_ONCE) + 1
        else:
            count = 1

        sequence = []
        for strand in self.strand_list:
            sequence.append(strand.sequence)

        model = Model(material=self._substrate_type, ensemble=self._dangles, celsius=self._temperature, sodium=self._sodium, magnesium=self._magnesium)
        results = sample(sequence, model=model, num_sample=count)

        self._boltzmann_queue = results

        if len(self._boltzmann_queue) < 1:
            raise IOError("Did not get any results back from the Boltzmann sample function.")

        self._pop_boltzmann()
    
    def _pop_boltzmann(self):
        """ Pops a structure off our waiting queue, putting it in the correct internal.
        
        Does not check for the queue being empty: any caller must ensure
        there is something in the queue, or catch the exception raised by
        pop.
        
        Note also that this implicitly decrements the size hint, so if you
        use more requests than you noted in the size hint, the later ones
        get pulled in much smaller amounts. Theoretically the user should
        poke the complexes and reset the size hint back upwards if they
        need to use more, rather than making this pop smart about dynamic
        resizing of the requested amounts."""
        self._last_boltzmann_structure = str(self._boltzmann_queue.pop())
        self._boltzmann_sizehint -= 1
