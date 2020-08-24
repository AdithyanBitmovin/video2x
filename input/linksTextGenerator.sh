#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..900}
  do
    y=$(printf "%04d" $i)
    echo "https://storage.googleapis.com/adi-hardware-testing/fubo/segments/TS_SEGMENTS/FUBO_MOVIESTAR_20200702-02.00.13/FUBO_MOVIESTAR_20200702-02.00.13_$y.mkv" >> /Users/iadithyan/PycharmProjects/interns-arm-eval/input/links.txt
done
