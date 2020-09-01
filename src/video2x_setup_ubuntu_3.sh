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

# install anime4kcpp
apt-fast install -y --no-install-recommends build-essential libopencv-dev beignet-opencl-icd mesa-opencl-icd ocl-icd-opencl-dev opencl-headers
git clone --recurse-submodules --depth=1 --progress https://github.com/TianZerL/Anime4KCPP.git $TEMP/anime4kcpp
mkdir -v $TEMP/anime4kcpp//build
cd $TEMP/anime4kcpp/build
cmake -DBuild_GUI=OFF ..
make
mv -v $TEMP/anime4kcpp/CLI/build $INSTALLATION_PATH/video2x/src/dependencies/anime4kcpp
mv -v $TEMP/anime4kcpp/models_rgb $INSTALLATION_PATH/video2x/src/dependencies/anime4kcpp/models_rgb

# rewrite config file values
python3.8 - <<EOF
import yaml
import os


INSTALLATION_PATH = os.environ['INSTALLATION_PATH']

with open('{}/video2x/src/video2x.yaml'.format(INSTALLATION_PATH), 'r') as template:
    template_dict = yaml.load(template, Loader=yaml.FullLoader)
    template.close()

template_dict['ffmpeg']['ffmpeg_path'] = '/usr/bin'
template_dict['gifski']['gifski_path'] = '/root/.cargo/bin/gifski'
template_dict['waifu2x_caffe']['path'] = '{}/video2x/src/dependencies/waifu2x-caffe/waifu2x-caffe'.format(INSTALLATION_PATH)
template_dict['waifu2x_converter_cpp']['path'] = '{}/video2x/src/dependencies/waifu2x-converter-cpp/waifu2x-converter-cpp'.format(INSTALLATION_PATH)
template_dict['waifu2x_ncnn_vulkan']['path'] = '{}/video2x/src/dependencies/waifu2x-ncnn-vulkan/waifu2x-ncnn-vulkan'.format(INSTALLATION_PATH)
template_dict['srmd_ncnn_vulkan']['path'] = '{}/video2x/src/dependencies/srmd-ncnn-vulkan/srmd-ncnn-vulkan'.format(INSTALLATION_PATH)
template_dict['realsr_ncnn_vulkan']['path'] = '{}/video2x/src/dependencies/realsr-ncnn-vulkan/realsr-ncnn-vulkan'.format(INSTALLATION_PATH)
template_dict['anime4kcpp']['path'] = '{}/video2x/src/dependencies/anime4kcpp/anime4kcpp'.format(INSTALLATION_PATH)

# write configuration into file
with open('{}/video2x/src/video2x.yaml'.format(INSTALLATION_PATH), 'w') as config:
    yaml.dump(template_dict, config)
EOF

# clean up temp directory
# purge default utilities
# apt-get purge -y git-core curl wget ca-certificates gnupg2 python3-dev python3-pip python3-setuptools

# purge waifu2x-caffe build dependencies
# apt-get purge -y autoconf build-essential cmake gcc-8 libatlas-base-dev libboost-atomic-dev libboost-chrono-dev libboost-date-time-dev libboost-filesystem-dev libboost-iostreams-dev libboost-python-dev libboost-system-dev libboost-thread-dev libcudnn7 libcudnn7-dev libgflags-dev libgoogle-glog-dev libhdf5-dev libleveldb-dev liblmdb-dev libopencv-dev libprotobuf-dev libsnappy-dev protobuf-compiler python-numpy texinfo yasm zlib1g-dev

# purge waifu2x-converter-cpp build dependencies
# apt-get purge -y libopencv-dev ocl-icd-opencl-dev

# purge waifu2x/srmd/realsr-ncnn-vulkan build dependencies
# apt-get purge -y unzip jq

# run autoremove and purge all unused packages
# apt-get autoremove --purge -y

# remove temp directory
rm -vrf $TEMP
