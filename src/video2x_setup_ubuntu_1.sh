#!/usr/bin/bash -e
# Name: Video2X Setup Script (Ubuntu)
# Creator: K4YT3X
# Date Created: June 5, 2020
# Last Modified: July 25, 2020

# help message if input is incorrect of if -h/--help is specified
if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -gt 2 ]; then
    echo "usage: $0 INSTALLATION_PATH TEMP"
    exit 0
fi

# set intallation path if specified
if [ ! -z "$1" ]; then
    export INSTALLATION_PATH=$1
else
    export INSTALLATION_PATH="$HOME/.local/share"
fi

# set temp directory location if specified
if [ ! -z "$2" ]; then
    export TEMP=$2
else
    export TEMP="/tmp/video2x"
fi

# environment variables
export DEBIAN_FRONTEND="noninteractive"

# install basic utilities and add PPAs
apt-get update
apt-get install -y --no-install-recommends apt-utils software-properties-common

# add PPAs and sources
add-apt-repository -y ppa:apt-fast/stable
add-apt-repository -y ppa:graphics-drivers/ppa
apt-get install -y --no-install-recommends apt-fast
apt-fast update

# install runtime packages
apt-fast install -y --no-install-recommends libmagic1 nvidia-cuda-toolkit nvidia-driver-440 python3.8

# install compilation packages
apt-fast install -y --no-install-recommends git-core curl wget ca-certificates gnupg2 python3-dev python3-pip python3-setuptools python3-wheel

# add Nvidia sources
curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub | apt-key add -
echo "deb https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64 /" >/etc/apt/sources.list.d/nvidia-ml.list
apt-fast update

# install python3 packages
git clone --recurse-submodules --progress https://github.com/k4yt3x/video2x.git --depth=1 $INSTALLATION_PATH/video2x
python3.8 -m pip install -U pip
python3.8 -m pip install -U -r $INSTALLATION_PATH/video2x/src/requirements.txt
mkdir -v -p $INSTALLATION_PATH/video2x/src/dependencies

