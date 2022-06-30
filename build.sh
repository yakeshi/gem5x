#!/bin/sh
cd gem5
scons EXTRAS=`pwd`/../cores build/riscv/libgem5_opt.so
scons EXTRAS=`pwd`/../cores build/riscv/gem5x.opt
scons EXTRAS=`pwd`/../cores  BUILD_EXTENSION=1 build/riscv/cores_opt.so
mv build/riscv/cores_opt.so build/riscv/cores.so
