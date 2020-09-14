#!/bin/bash

# ffmpeg
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
cd ffmpeg
./configure --enable-gpl --enable-nonfree --enable-libx265 --enable-libx264 --enable-libvmaf --disable-debug --disable-ffplay --enable-pic --enable-shared
make -j${CPUS}
sudo make -j${CPUS} install
sudo ldconfig
