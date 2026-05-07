#!/bin/bash

# Get data and create images for display

source .venv/bin/activate

# Retrieve Netatmo
python get_netatmo.py

# Get Open Meteo forecast
python get_open_meteo.py

# Get pressure data and preprocess
python get_pressure.py
wgrib2 pressure.grib2 -netcdf pressure.nc


# Draw main weather map
python weather_map.py

# Rain map (for dashboard display)
python rain_map.py

# Draw dashboards
python dashboard.py
