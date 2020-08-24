#!/bin/bash

# nv-codec-headers
ls -lhtr

git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git nv-codec-headers
cd nv-codec-headers
sudo make -j${CPUS}
sudo make -j${CPUS} install
cd ../

# ffmpeg
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
cd ffmpeg
./configure --enable-cuda-sdk --enable-cuda-nvcc --enable-cuvid --enable-nvenc --enable-nonfree --enable-libx265 \
--enable-libx264 --enable-libnpp --enable-libvmaf --enable-gpl --extra-cflags=-I/usr/local/cuda/include --disable-debug --disable-ffplay\
 --extra-ldflags=-L/usr/local/cuda/lib64
make -j${CPUS}
sudo make -j${CPUS} install
sudo ldconfig
