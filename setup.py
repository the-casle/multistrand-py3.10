# Copyright (c) 2010-2017 Caltech. All rights reserved.
# Joseph Schaeffer (schaeffer@dna.caltech.edu)
# Frits Dannenberg (fdann@dna.caltech.edu)

from setuptools import Extension, setup
from distutils.command.build_ext import build_ext as _build_ext
import distutils.errors
import sys

sources = ["src/system/utility.cc",
           "src/system/sequtil.cc",
           "src/system/simtimer.cc",
           "src/interface/multistrand_module.cc",
           "src/interface/optionlists.cc",
           "src/interface/options.cc",
           "src/loop/move.cc",
           "src/loop/moveutil.cc",
           "src/loop/loop.cc",
           "src/system/energyoptions.cc",
           "src/energymodel/nupackenergymodel.cc",
           "src/energymodel/energymodel.cc",
           "src/state/scomplex.cc",
           "src/state/scomplexlist.cc",
           "src/system/statespace.cc",
           "src/system/simoptions.cc",
           "src/system/ssystem.cc",
           "src/state/strandordering.cc"
           ]

setup(
    ext_modules=[
        Extension("multistrand.system",
                  sources=sources,
                  include_dirs=["./src/include"],
                  language="c++",
                  undef_macros=["NDEBUG"],
                  extra_compile_args=['-O3', '-w', "-std=c++11", "-g", "-Wall", "-fno-inline"],
                  ),
    ]
)
# ['-O3', '-w', "-std=c++11", "-DNDEBUG"]
# ['-O0', '-w', "-std=c++11", "-g", "-Wall", "-fno-inline"]