#!/bin/bash
while true; do
    now=$(date +"%Y-%m-%d %H:%M:%S")
    echo "Running at $now"

    current_hour=$(date +%H)
    if [[ "$current_hour" != "$last_hour" ]]; then
        echo "  New hour; retrieving open-meteo forecast"
        python get_open_meteo.py
    fi

    last_hour=$current_hour

    echo "  Retrieving Netatmo observations"
    python get_netatmo.py

    echo "  Updating display"
    python display.py

    next_run=$(date -d "+15 minutes" +"%Y-%m-%d %H:%M:%S")
    echo "Next run: $next_run"
    echo ""
    sleep 900
done
