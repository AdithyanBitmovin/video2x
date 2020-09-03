#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for filter in waifu2x_caffe scale
do
    for scale_factor in 2 4
    do
        output_file_directory="$HOME/EN-8066/output/output/NARUTO/segments/${filter}_${scale_factor}x"
        #sudo mkdir -p ${output_file_directory}
        directory_to_store="$HOME/Repos/video2x/input"

        for crf in 20 23 26
        do
            concatenate_file_to_store="concatenate_${filter}_${scale_factor}x_${crf}.txt"
            concatenate_file_list=${directory_to_store}/${concatenate_file_to_store}
            sudo rm ${concatenate_file_list}

            for segment_number in {0..346}
              do
                formatted_segment_number=$(printf "%05d" $segment_number)
                output_file_name="video_${formatted_segment_number}_scale=${scale_factor}_CRF=${crf}_libx264_default_${filter}.mkv"

                echo "file '${output_file_directory}/${output_file_name}'" >> ${concatenate_file_list}
            done


            concatenated_file_full_path="${output_file_directory}/concatenate_${filter}_${scale_factor}x_crf=${crf}.mkv"
            echo ffmpeg -y -f concat -safe 0 -i ${concatenate_file_list} -c copy ${concatenated_file_full_path}
            echo gsutil cp ${concatenated_file_full_path} gs://adi-innovation-superresolution/output/NARUTO/segments/${filter}_${scale_factor}x/

        done
    done
done