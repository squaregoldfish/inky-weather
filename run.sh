#!/bin/bash

nohup ./create.sh > create.nohup &
nohup ./control.sh > control.nohup &

