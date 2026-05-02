#!/bin/bash

# Downloads the lates ECMWF mean sea level pressure
# and converts it to netCDF
#
source .venv/bin/activate
python get_pressure.py
wgrib2 pressure.grib2 -netcdf pressure.nc

