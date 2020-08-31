#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for i in {0..346}
  do
    y=$(printf "%05d" $i)
    echo "file '/home/adithyan_ilangovan_bitmovin_com/EN-8066/output/output/NARUTO/segments/waifu2x_caffe_2x/video_${y}_scale=2_CRF=17_libx264_default_waifu2x_caffe.mkv'" >> /home/adithyanilangovan/Repos/video2x/input/linkNarutoConcatanate_waifu2x_caffe_2x.txt
done
