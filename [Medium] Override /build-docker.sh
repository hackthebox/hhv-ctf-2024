#!/bin/bash
NAME="flash_mem"
docker rm -f hardware_$NAME
docker build --tag=hardware_$NAME . && \
docker run -p 1337:1337 -p 1338:1338 --rm --name=hardware_$NAME --detach hardware_$NAME
