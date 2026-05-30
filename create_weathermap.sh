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
        # Get ECMWF data and preprocess
        python get_ecmwf.py
        wgrib2 ecmwf.grib2 -netcdf ecmwf.nc
    fi

    last_hour=$current_hour

    # Draw main weather map
    python weather_map.py

    # Rain map (for dashboard display)
    python rain_map.py

    # Send images to display computer (script not in repository)
    ./scp_images.sh

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
