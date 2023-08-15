# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)


import math
import numbers

import nupack
import os
from multistrand import *

NUPACK3 = "-nupack3"
RNA_NUPACK = "rna06" + NUPACK3
DNA_NUPACK = "dna04" + NUPACK3

class Model(nupack.Model):
    def __init__(self, ensemble="some", material="DNA", kelvin=None, celsius=37, sodium=1.0, magnesium=0.0):
        kwargs = {
            "kelvin": kelvin,
            "celsius": celsius,
            "sodium": sodium,
            "magnesium": magnesium,
        }

        if material == "RNA":
            kwargs["material"] = RNA_NUPACK
        else:
            kwargs["material"] = DNA_NUPACK

        kwargs["ensemble"] = ensemble.lower() + NUPACK3

        super(Model, self).__init__(**kwargs)

    @nupack.Model.ensemble.setter
    def ensemble(self, value):
        self._ensemble = value.lower() + NUPACK3

    @nupack.Model.material.setter
    def material(self, value):
        if value == "RNA":
            self._material = RNA_NUPACK
        else:
            self._material = DNA_NUPACK



def dGadjust(K, N):
    """Adjust NUPACK's native free energy (with reference to mole fraction units) to be appropriate for molar units, assuming N strands in the complex."""
    R = 0.0019872041  # Boltzmann's constant in kcal/mol/K
    water = 55.14  # molar concentration of water at 37 C, ignore temperature dependence, which is about 5%
    adjust = R * K * math.log(water)  # converts from NUPACK mole fraction units to molar units, per association
    return adjust * (N - 1)


def pfunc(strands, model=None):
    if model is None:
        model = Model()
    return nupack.pfunc(strands=strands, model=model)[1] + dGadjust(model.temperature, len(strands))


for name, attr in vars(nupack).items():
    if callable(attr) and name not in globals():
        globals()[name] = attr