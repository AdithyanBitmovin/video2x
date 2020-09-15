#!/bin/bash
echo "Bash version ${BASH_VERSION}..."

for scale_factor in 2 4
do
    for filter_reference in scale
    do
      comparison_directory="$HOME/EN-8066/comparison"
      mkdir -p ${comparison_directory}


        for crf in 20 23 26
        do
            reference_output_file_directory="$HOME/EN-8066/concatanate"
            reference_concatenated_file_full_path="${reference_output_file_directory}/concatenate_${filter_reference}_${scale_factor}x_crf={crf}.mkv"
              for filter_optimized in waifu2x_caffe
              do
                  optimized_output_file_directory="$HOME/EN-8066/concatanate"
                  optimized_concatenated_file_full_path="${optimized_output_file_directory}/concatenate_${filter_optimized}_${scale_factor}x.mkv"

                  comparison_file_name="comparison_${filter_optimized}_vs_${filter_reference}_${scale_factor}x_crf={crf}.mkv"
                  comparison_file_full_path="${comparison_directory}/${comparison_file_name}"


                  ffprobe_optimized="ffprobe -hide_banner -loglevel 0 -of default=nokey=1:noprint_wrappers=1 -i ${comparison_file_full_path} -select_streams v -show_entries 'format=bit_rate'"
                  optimized_file_bitrate=$(ffprobe -hide_banner -loglevel 0 -of default=nokey=1:noprint_wrappers=1 -i ${optimized_concatenated_file_full_path} -select_streams v -show_entries 'format=bit_rate')
            optimized_file_bitrate_kbps=$(( optimized_file_bitrate / 1000  ))

                  ffprobe_reference="ffprobe -hide_banner -loglevel 0 -of default=nokey=1:noprint_wrappers=1 -i ${reference_concatenated_file_full_path} -select_streams v -show_entries 'format=bit_rate'"
                  reference_file_bitrate=$(ffprobe -hide_banner -loglevel 0 -of default=nokey=1:noprint_wrappers=1 -i ${reference_concatenated_file_full_path} -select_streams v -show_entries 'format=bit_rate')
            reference_file_bitrate_kbps=$(( reference_file_bitrate / 1000  ))


                  filter_text_optimized="|${scale_factor}x|${filter_optimized}|x264_crf_17|${optimized_file_bitrate_kbps}kbps|"
                  filter_text_reference="|${scale_factor}x|bicubic|x264_crf_20|${reference_file_bitrate_kbps}kbps|"

                  echo ${filter_text_optimized}
                  echo ${filter_text_reference}

                  font_size=0
                  if [ "${scale_factor}" -eq "2" ];
                  then
                  font_size=25
                  else
                  font_size=50
                  fi

                  draw_text_filter_reference="[v00]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text=${filter_text_reference}:x=(w-text_w)/2:y=(h-text_h)*9/10:fontcolor=white:fontsize=${font_size}[v0]"
                  draw_text_filter_optimized="[v11]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text=${filter_text_optimized}:x=(w-text_w)/2:y=(h-text_h)*9/10:fontcolor=white:fontsize=${font_size}[v1]"

                  ffmpeg_command="ffmpeg -y -i ${reference_concatenated_file_full_path} -i ${optimized_concatenated_file_full_path} -filter_complex \"[0:v]crop=1/2*in_w:in_h[v00];${draw_text_filter_reference};[1:v]crop=1/2*in_w:in_h[v11];${draw_text_filter_optimized};[v0][v1]hstack\" -c:v libx264 -crf 17 -preset veryfast ${comparison_file_full_path}"
            eval $ffmpeg_command
                  sudo gsutil cp ${comparison_file_full_path} gs://adi-innovation-superresolution/output/NARUTO/comparison/

              done
        done
    done
done
