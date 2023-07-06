from multistrand.objects import *
from multistrand.options import Options
from multistrand.system import *
import tracemalloc

if __name__ == "__main__":
    tracemalloc.start()
    TEMPERATURE=25
    o = Options(temperature=TEMPERATURE,dangles="Some", rate_method="Metropolis")
    o.DNA23Metropolis()
    initialize_energy_model(o)

    Loop_Energy = 0    # argument value to energy() function call, below, requesting no dG_assoc or dG_volume terms to be added.  So only loop energies remain.
    Volume_Energy = 1  # argument value to energy() function call, below, requesting dG_volume but not dG_assoc terms to be added.  No clear interpretation for this.
    Complex_Energy = 2 # argument value to energy() function call, below, requesting dG_assoc but not dG_volume terms to be added.  This is the NUPACK complex microstate energy.
    Tube_Energy = 3    # argument value to energy() function call, below, requesting both dG_assoc and dG_volume terms to be added.  Summed over complexes, this is the system state energy.


    SEQUENCE = "GTTCGGGCAAAAGCCCGAAC"
    STRUCTURE = '..((' + 12*'.' + '))..'
    c = Complex( strands=[Strand(name="hairpin", sequence=SEQUENCE)], structure= STRUCTURE )
    b = [c]
    em = energy( b, o, Complex_Energy)  # should be -1.1449...
    print(em)
    print(c)
    print(b)
    # Note that energy() takes a *list* of complexes, and returns a tuple of energies.  Don't give it just a complex as input, else all hell may break loose.
