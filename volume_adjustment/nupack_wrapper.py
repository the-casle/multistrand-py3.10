# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)


import math
import numbers

import nupack
from nupack import utility
import os
from multistrand

class Model(object):
    intern_model = None

    def __init__(self, ensemble="stacking-nupack3", material="rna95-nupack3", celsius=37, sodium=1.0, magnesium=0.0):
        self.intern_model = nupack.Model(ensemble=ensemble,
                                         material=material,
                                         celsius=celsius,
                                         sodium=sodium,
                                         magnesium=magnesium)

    @property
    def ensemble(self):
        return self.intern_model.ensemble

    @property
    def material(self):
        return self.intern_model.material

    @property
    def celsius(self):
        return self.intern_model.celsius

    @property
    def sodium(self):
        return self.intern_model.sodium

    @property
    def magnesium(self):
        return self.intern_model.magnesium



def dGadjust(T, N):
    """Adjust NUPACK's native free energy (with reference to mole fraction units) to be appropriate for molar units, assuming N strands in the complex."""
    R = 0.0019872041  # Boltzmann's constant in kcal/mol/K
    water = 55.14  # molar concentration of water at 37 C, ignore temperature dependence, which is about 5%
    K = T + 273.15  # Kelvin
    adjust = R * K * math.log(water)  # converts from NUPACK mole fraction units to molar units, per association
    return adjust * (N - 1)

def pfunc(strands, model=Model()





def pfunc(sequences, ordering=None, material='dna',
          dangles='some', T=37.0, multi=True, pseudo=False,
          sodium=1.0, magnesium=0.0):
    """Calls NUPACK's pfunc on a complex consisting of the unique strands in sequences, returns dG.
         sequences is a list of the strand sequences
         See NUPACK User Manual for information on other arguments. """


    pfunc(strands=sequences, )

    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='pfunc', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)

    ## Perform call until it works (should we have a max # of tries before quitting?)
    output, error = call_with_pipe(args, cmd_input)
    while len(
            output) < 4:  # can't figure out why, but occasionally NUPACK returns empty-handed.  Subsequent tries seem to work...
        print(f"Retrying pfunc: NUPACK failed with output {output} and error {error}.")
        output, error = call_with_pipe(args, cmd_input)

    ## Parse and return output
    if output[-4] != "% Free energy (kcal/mol) and partition function:":
        raise NameError('NUPACK output parsing problem')

    if float(output[-3]) == float('inf'):
        return 0  # if these strands can't base-pair
    else:
        return float(output[-3]) + dGadjust(T, len(sequences))


def pairs(sequences, ordering=None, material='rna',
          dangles='some', T=37.0, multi=True, pseudo=False,
          sodium=1.0, magnesium=0.0, cutoff=0.001):
    """Calls NUPACK's pairs executable on a complex consisting of the unique strands in sequences.
       Returns the probabilities of pairs of bases being bound, only including those pairs
       with probability greater than cutoff.
         sequences is a list of the strand sequences
         See NUPACK User Manual for information on other arguments.
    """

    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='pairs', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)
    if multi:
        suffix = '.epairs'
    else:
        suffix = '.ppairs'

    ## Perform call
    output = call_with_file(args, cmd_input, suffix)

    ## Parse and return output
    pair_probs = []
    for l in (x for x in output if x[0].isdigit() and len(x.split()) > 1):
        i, j, p = l.split()
        pair_probs.append(tuple((int(i), int(j), float(p))))

    return pair_probs


def mfe(sequences, ordering=None, material='rna',
        dangles='some', T=37.0, multi=True, pseudo=False,
        sodium=1.0, magnesium=0.0, degenerate=False):
    """Calls NUPACK's mfe executable on a complex consisting of the strands in sequences.
       Returns the minimum free energy structure, or multiple mfe structures if the degenerate
       option is specified
         sequences is a list of the strand sequences
         degenerate is a boolean specifying whether to include degenerate mfe structures
         See NUPACK User Manual for information on other arguments.
    """

    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='mfe', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)
    if degenerate: args += ['-degenerate']

    ## Perform call
    output = call_with_file(args, cmd_input, '.mfe')

    ## Parse and return output
    structs = []
    for i, l in enumerate(output):
        if l[0] == '.' or l[0] == '(':
            s = l.strip()
            e = output[i - 1].strip()
            structs.append((s, e))
    return structs


def subopt(sequences, energy_gap, ordering=None, material='rna',
           dangles='some', T=37.0, multi=True, pseudo=False,
           sodium=1.0, magnesium=0.0, degenerate=False):
    """Calls NUPACK's subopt executable on a complex consisting of the strands in the given order.
       Returns the structures within the given free energy gap of the minimum free energy.
         sequences is a list of the strand sequences
         energy_gap is the maximum energy gap from the mfe of any returned structure.
         See NUPACK User Manual for information on other arguments.
    """
    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='subopt', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)
    cmd_input += '\n' + str(energy_gap)

    ## Perform call
    output = call_with_file(args, cmd_input, '.subopt')

    ## Parse and return output
    structs = []
    for i, l in enumerate(output):
        if l[0] == '.' or l[0] == '(':
            s = l.strip()
            e = output[i - 1].strip()
            structs.append((s, e))
    return structs


def count(sequences, ordering=None, material='rna',
          dangles='some', T=37.0, multi=True, pseudo=False,
          sodium=1.0, magnesium=0.0):
    """Calls NUPACK's count executable on a complex consisting of the strands in the given order.
       Returns the number of secondary structures, overcounting rotationally symmetric structures.
         sequences is a list of the strand sequences
         See NUPACK User Manual for information on other arguments. """

    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='count', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)

    ## Perform call
    output, error = call_with_pipe(args, cmd_input)

    ## Parse and return output
    if output[-3] != "% Total number of secondary structures:":
        raise NameError('NUPACK output parsing problem')
    return float(output[-2])  # the number of structures can be very large


def energy(sequences, structure, ordering=None, material='rna',
           dangles='some', T=37.0, multi=True, pseudo=False,
           sodium=1.0, magnesium=0.0):
    """Calls NUPACK's energy executable. Returns the microstate dG.
         sequences is a list of the strand sequences
         structure is a string with the dot-paren structure notation
           (pair-list notation for structures is not currently supported)
         See NUPACK User Manual for information on the other arguments.
    """
    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='energy', sequences=sequences, ordering=ordering,
                           structure=structure, material=material,
                           sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)

    ## Perform call
    output, error = call_with_pipe(args, cmd_input)

    ## Parse and return output
    if output[-3] != "% Energy (kcal/mol):":
        raise ValueError('NUPACK output parsing problem')
    return float(output[-2])


def prob(sequences, structure, ordering=None, material='rna',
         dangles='some', T=37.0, multi=True, pseudo=False,
         sodium=1.0, magnesium=0.0):
    """Calls NUPACK's prob executable. Returns the probability of the given structure.
         sequences is a list of the strand sequences
         structure is a string with the dot-paren structure notation
           (pair-list notation for structures is not currently supported)
         See NUPACK User Manual for information on the other arguments.
    """
    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='prob', sequences=sequences, ordering=ordering,
                           structure=structure, material=material,
                           sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)

    ## Perform call
    output, error = call_with_pipe(args, cmd_input)

    ## Parse and return output
    if output[-3] != "% Probability:":
        raise ValueError('NUPACK output parsing problem')
    return float(output[-2])


def defect(sequences, structure, ordering=None, material='rna',
           dangles='some', T=37.0, multi=True, pseudo=False,
           sodium=1.0, magnesium=0.0, mfe=False):
    """Calls NUPACK's defect executable. Returns the ensemble defect (default) or the mfe defect.
         sequences is a list of the strand sequences
         structure is a string with the dot-paren structure notation
           (pair-list notation for structures is not currently supported)
         See NUPACK User Manual for information on the other arguments.
    """
    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='tubedefect', sequences=sequences, ordering=ordering,
                           structure=structure, material=material,
                           sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)
    if mfe: args += ['-mfe']

    ## Perform call
    output, error = call_with_pipe(args, cmd_input)

    ## Parse and return output
    if "% Ensemble defect" not in output[-4] and \
            "% Fraction of correct nucleotides vs. MFE" not in output[-4]:
        raise ValueError('NUPACK output parsing problem')
    # We don't return the normalized ensemble defect, because that is easily calculable on your own
    return float(output[-3])


def sample(sequences, samples, ordering=None, material='rna',
           dangles='some', T=37.0, multi=True,
           pseudo=False, sodium=1.0, magnesium=0.0):
    """ Calls the NUPACK sample executable.
          sequences is a list of the strand sequences
          samples is the number of Boltzmann samples to produce.
          See NUPACK User Manual for information on the other arguments.
        This only works with NUPACK 3.0.2+

        Note that if using OS X and sample is not in your $PATH, this will try
        to run the standard BSD tool 'sample'.
    """
    assert isinstance(samples, int), "Argument 'samples' is not an integer"
    ## Set up command-line arguments and input
    args, cmd_input = \
        setup_nupack_input(exec_name='sample', sequences=sequences, ordering=ordering,
                           material=material, sodium=sodium, magnesium=magnesium,
                           dangles=dangles, T=T, multi=multi, pseudo=pseudo)
    args += ['-samples', samples]

    # Call executable
    output = call_with_file(args, cmd_input, '.sample')

    # Check NUPACK version
    if not ("NUPACK 3.0" in output[0] or "NUPACK 3.2" in output[0]):
        raise OSError("Boltzmann sample function is not up to date. NUPACK 3.0.2 or greater needed.")

    # Parse and return output
    sampled = [l.strip() for l in output[14:]]
    return sampled