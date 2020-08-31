# Name: Video2X Dockerfile
# Creator: Danielle Douglas
# Date Created: Unknown
# Last Modified: January 14, 2020

# Editor: Lhanjian
# Last Modified: May 24, 2020

# Editor: K4YT3X
# Last Modified: June 13, 2020

# using Ubuntu LTS 19.10
# Ubuntu 20.x is incompatible with Nvidia libraries
FROM ubuntu:19.10

# file mainainter labels
LABEL maintainer="Danielle Douglas <ddouglas87@gmail.com>"
LABEL maintainer="Lhanjian <lhjay1@foxmail.com>"
LABEL maintainer="K4YT3X <k4yt3x@k4yt3x.com>"

RUN apt-get update

RUN apt install -y sudo software-properties-common git
RUN apt install -y wget git gcc g++ make cmake nasm pkg-config
RUN DEBIAN_FRONTEND=noninteractive apt install -y tzdata
RUN apt install -y python3

RUN sudo apt install -y python3-pip time
RUN pip3 install requests

ADD ./src/installYasm.sh installYasm.sh
RUN ./installYasm.sh

ADD ./src/installX264.sh installX264.sh
RUN ./installX264.sh

ADD ./src/installX265.sh installX265.sh
RUN ./installX265.sh

ADD ./src/installVMAF.sh installVMAF.sh
RUN ./installVMAF.sh

ADD ./src/installFfmpeg.sh installFfmpeg.sh
RUN ./installFfmpeg.sh

RUN pip3 install ffmpeg_quality_metrics
RUN pip3 install requests


RUN pwd

# run installation
RUN apt-get update
RUN apt-get install -y git-core
RUN git clone -b feature/EN-8066-InnovationSuperRes --recurse-submodules --progress https://github.com/AdithyanBitmovin/video2x.git /tmp/video2x/video2x
RUN bash -e /tmp/video2x/video2x/src/video2x_setup_ubuntu_1.sh
RUN bash -e /tmp/video2x/video2x/src/video2x_setup_ubuntu_2.sh

ADD ./src/RunTests.py RunTests.py
ADD ./input/links.txt links.txt
ADD ./input/linksTest.txt linksTest.txt
ADD ./input/linksNaruto.txt linksNaruto.txt
ADD ./input/linksConan.txt linksConan.txt

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES video,compute,utility

ENV INPUT=None
ENV TEST_TYPE=software

CMD ["RunTests.py"]
ENTRYPOINT ["python3.8"]