#!/bin/bash
echo $1
nc -u -l 5005 | tee "data/$1" | python3 robot-plot.py

