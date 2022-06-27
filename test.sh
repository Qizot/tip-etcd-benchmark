#!/bin/bash

if [ $# -ne 2 ]
  then
    echo "Incorrect number of arguments passed"
    echo "Usage: ./test.sh [config_filepath] [output_filename]"
    echo "config_filepath - path to the config file"
    echo "output_filename - name of the output file"
    exit 1;
fi

if ! [[ $1 == *.json ]]
  then
    echo "Incorrect config file format, please pass .json file"
    exit 1;
fi

if ! [[ $2 == *.csv ]]
  then
    echo "Incorrect target format of output file - only csv files are allowed"
    exit 1;
fi

if ! [ -f "$1" ]
  then
    echo "Incorrect file path: $1"
    exit 1;
fi

./build.sh

python3 test.py $1 $2 http://localhost:8080/benchmark
