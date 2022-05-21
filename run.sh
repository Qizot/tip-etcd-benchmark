#!/bin/bash

docker build -t etcd_benchmark ./client-benchmark

python3 main.py
