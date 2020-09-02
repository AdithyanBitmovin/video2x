#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for scale_factor in 2 4
do
    for filter_reference in scale
    do
      comparison_directory="$HOME/EN-8066/output/comparison"
      mkdir -p ${comparison_directory}

      reference_output_file_directory="$HOME/EN-8066/output/output/NARUTO/segments/${filter_reference}_${scale_factor}x"
      reference_concatenated_file_full_path="${reference_output_file_directory}/concatenate_${filter_reference}_${scale_factor}x.mkv"

      for filter_optimized in waifu2x_caffe
      do
          optimized_output_file_directory="$HOME/EN-8066/output/output/NARUTO/segments/${filter_optimized}_${scale_factor}x"
          optimized_concatenated_file_full_path="${optimized_output_file_directory}/concatenate_${filter_optimized}_${scale_factor}x.mkv"

          comparison_file_name="comparison_${filter_optimized}vs${filter_reference}_${scale_factor}x.mkv"
          comparison_file_full_path="${comparison_directory}/${comparison_file_name}"

          ffmpeg_command="ffmpeg -i ${reference_concatenated_file_full_path} -i ${optimized_concatenated_file_full_path} \
          -filter_complex \"[0:v]crop=1/2*in_w:in_h[v0];[1:v]crop=1/2*in_w:in_h[v1];[v0][v1]hstack\" -c:v libx264 -crf 17 -preset veryfast ${comparison_file_full_path}"
          echo ${ffmpeg_command}

      done
    done
done