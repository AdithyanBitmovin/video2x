#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for filter in waifu2x_caffe
do
  echo ${filter}
    for scale_factor in 2
    do
        for segment_number in {0..346}
          do
            formatted_segment_number=$(printf "%05d" $segment_number)
            output_file_directory="/home/adithyan_ilangovan_bitmovin_com/EN-8066/output/output/NARUTO/segments/${filter}_${scale_factor}x"
            output_file_name="video_${formatted_segment_number}_scale=${scale_factor}_CRF=17_libx264_default_${filter}.mkv"

            sudo mkdir -p ${output_file_directory}

            directory_to_store="/home/adithyanilangovan/Repos/video${scale_factor}x/input/"
            concatante_file_to_store="concatante_${filter}_${scale_factor}.txt"

            echo "file '${output_file_directory}/${output_file_name}'" >> ${directory_to_store}${concatante_file_to_store}

        done
    done
done