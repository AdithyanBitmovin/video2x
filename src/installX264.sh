#!/bin/bash

CPUS=$(grep -c ^processor /proc/cpuinfo)

# x264
git clone https://github.com/mirror/x264
cd x264/
git checkout ba24899b0bf23345921da022f7a51e0c57dbe73d
sed -i 's#) ytasm.*#)#' Makefile
./configure  --enable-static --disable-shared --enable-pic
make -j${CPUS}
sudo make -j${CPUS} install
ldconfig
cd ../
