#!/bin/bash

if [ "$#" -eq 0 ]; then
    input_folder="."
    output_folder="./mp4_output"
elif [ "$#" -eq 1 ]; then
    input_folder="$1"
    output_folder="$1/mp4_output"
elif [ "$#" -eq 2 ]; then
    input_folder="$1"
    output_folder="$2"
else
    echo "Usage: $0 [input_folder] [output_folder]"
    exit 1
fi

if [ "$output_folder" == "$input_folder/mp4_output" ]; then
    mkdir -p "$output_folder"
fi

for file in "$input_folder"/*.avi; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        filename_no_ext="${filename%.*}"
        output_file="$output_folder/$filename_no_ext.mp4"
        ffmpeg -i "$file" -c:v libx264 -preset slow -crf 18 -vf "fps=20" "$output_file"
    fi
done


# ./convert_avi_to_mp4.sh               # Assumes current folder for both input and output, creates mp4_output here
# ./convert_avi_to_mp4.sh /path/to/input_folder               # Uses /path/to/input_folder for both input and output, creates mp4_output there
# ./convert_avi_to_mp4.sh /path/to/input_folder /path/to/output_folder  # Uses specified folders for input and output
