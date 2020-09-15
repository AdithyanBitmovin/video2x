#!/bin/bash

sudo apt install -y ninja-build
sudo apt install -y cython
pip3 install meson
git clone https://github.com/Netflix/vmaf.git
cd vmaf
sudo make
sudo make install
