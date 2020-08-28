#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for i in {0..367}
  do
    y=$(printf "%05d" $i)
    echo "http://adi-innovation-superresolution.commondatastorage.googleapis.com/source/CONAN/chunk_4s_forced/video_$y.mkv" >> /home/adithyanilangovan/Repos/video2x/input/linksConan.txt
done
