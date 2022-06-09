#!/bin/bash

docker build -t etcd_benchmark -f Dockerfile.bench ./

docker build -t etcd_wrapper -f Dockerfile.etcd ./


sudo python3 containernet-environment/main.py
