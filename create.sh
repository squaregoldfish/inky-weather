#!/bin/bash

# Get data and create images for display
source .venv/bin/activate

MIN_TIME=600

last_hour=-1

while true
do

    # Record the start time of the iteration
    start=`date +%s`

    # Some things we only get once per hour
    current_hour=$(date +%H)

    if [[ "$current_hour" != "$last_hour" ]]; then
        # Get Open Meteo forecast
        python get_open_meteo.py

        # Get pressure data and preprocess
        python get_pressure.py
        wgrib2 pressure.grib2 -netcdf pressure.nc
    fi

    last_hour=$current_hour

    # Retrieve Netatmo
    python get_netatmo.py

    # Draw main weather map
    python weather_map.py

    # Rain map (for dashboard display)
    python rain_map.py

    # Draw dashboards
    python dashboard.py

    end=`date +%s`

    elapsed=$((end - start))
    if [ "$elapsed" -ge "$MIN_TIME" ]
    then
        continue
    else
        wait_time=$((MIN_TIME - elapsed))
        sleep "$wait_time"
    fi
done