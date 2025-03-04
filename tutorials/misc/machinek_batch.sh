# Multistrand nucleic acid kinetic simulator
# Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
# The Multistrand Team (help@multistrand.org)

python machinek.py metropolis 2 2 80 DUMMY		> machinek_metropolis-dummy.txt;
python machinek.py arrhenius 2 2 80 DUMMY		> machinek_arrhenius-dummy.txt;
python machinek.py jsdefault  2 2 80 DUMMY 		> machinek_jsdefault-dummy.txt;

#python machinek.py metropolis 8 32 1600		> machinek_metropolis.txt;
#python machinek.py arrhenius 8 32 1600		> machinek_arrhenius.txt;
#python machinek.py jsdefault  8 32 1600		> machinek_jsdefault.txt;
