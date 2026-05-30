#!/bin/bash

# Downloads the latest ECMWF data
# and converts it to netCDF
#
source .venv/bin/activate
python get_ecmwf.py
wgrib2 ecmwf.grib2 -netcdf ecmwf.nc

