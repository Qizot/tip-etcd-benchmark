#!/bin/bash

docker build -t etcd_benchmark -f Dockerfile.bench ./

docker build -t etcd_custom ./etcd_custom


sudo python3 containernet-environment/main.py
