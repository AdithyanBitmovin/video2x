#!/bin/bash

CPUS=$(grep -c ^processor /proc/cpuinfo)

# x265
wget http://ftp.videolan.org/pub/videolan/x265/x265_2.6.tar.gz
tar -xvf x265_2.6.tar.gz
rm x265_2.6.tar.gz

# x265 itself
cd x265_v2.6/build
cmake ../source/
make -j${CPUS}
sudo make -j${CPUS} install
sudo ldconfig
cd ../../
