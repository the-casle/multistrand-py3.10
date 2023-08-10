# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional

import numpy as np
import pytest

from multistrand.options import Options, Energy_Type
from multistrand.system import initialize_energy_model, energy
from multistrand.objects import Complex, Strand
import nupack

import time


class Test_SingleStrandEnergy:
    """
    Compare the thermodynamic scores between Multistrand and Nupack, for a set
    of single-stranded complexes.
    """
    # subsampling of input file, defined per category
    examples_fraction: float = 1.0  # all examples when 1.0
    examples_min: int = 1000


    @pytest.mark.parametrize("rel_tol", [1e-6])
    @pytest.mark.parametrize("examples_file", [Path(__file__).parent / 'testSetSS.txt'])
    def test_energy(cls, examples_file: Path, rel_tol: float):
        complexes = cls.load_complexes(examples_file)
        opt = cls.create_config()
        for category, (seqs, structs) in complexes.items():
            print(f"{category}: {len(seqs)}")
            cls.compare_energies(opt, rel_tol, category, (seqs, structs))

    @classmethod
    def load_complexes(cls, path: Path) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        dataset = defaultdict(list)
        category: Optional[str] = None
        # read complexes from file
        with open(path) as f:
            for l in f:
                if l.startswith('>'):
                    category = l[1:].strip()
                else:
                    assert category is not None
                    dataset[category].append(l.strip())
            f.close()
        # parse and subsample
        complexes = {}
        for category, samples in dataset.items():
            seqs, structs = np.array(samples[0::2]), np.array(samples[1::2])
            N = len(seqs)
            n = N if N <= cls.examples_min else int(cls.examples_fraction * N)
            idx = np.arange(N)
            np.random.shuffle(idx)
            idx = idx[:n]
            complexes[category] = (seqs[idx], structs[idx])
        return complexes

    @staticmethod
    def create_config() -> Options:
        opt = Options(verbosity=0, reuse_energymodel=True)
        opt.DNA23Metropolis()
        return opt

    @staticmethod
    def compare_energies(opt: Options, rel_tol: float, category: str,
                         complexes: Tuple[Iterable[str], Iterable[str]]) -> None:
        model1 = nupack.Model(material='dna04-nupack3', ensemble="some-nupack3")
        for seq, struct in zip(*complexes):
            assert len(seq) == len(struct)
            start_nupack = time.time()
            e_nupack = nupack.structure_energy([seq], struct, model=model1)
            end_nupack = time.time()

            start_multistrand = time.time()
            c_multistrand = Complex(
                strands=[Strand(name="hairpin", sequence=seq)], structure=struct)
            e_multistrand = energy(
                [c_multistrand], opt, Energy_Type.Complex_energy)
            end_multistrand = time.time()
            #print(f"nupack elapsed: {end_nupack - start_nupack} multistrand elapsed: {end_multistrand - start_multistrand}")
            assert np.allclose(e_nupack, e_multistrand, rtol=rel_tol), \
                f"category = {category}, seq = {seq}, struct = {struct}"

if __name__ == "__main__":
    Test_SingleStrandEnergy.test_energy(Test_SingleStrandEnergy, examples_file= (Path(__file__).parent / 'testSetSS.txt'), rel_tol=1e-6)