#!/bin/bash

# ffmpeg
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
cd ffmpeg
./configure --enable-gpl --enable-nonfree --enable-libx265 --enable-libx264 --enable-libvmaf --disable-debug --disable-ffplay
make -j${CPUS}
make -j${CPUS} install
ldconfig
