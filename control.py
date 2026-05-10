from datetime import datetime
import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge, Value
from inky import auto
import os
import pandas as pd
from PIL import Image
import pytz
import sqlite3
from threading import Thread
from time import sleep

RAIN_LIMIT = 4
LAST_BUTTON_PUSH = None

LED_PIN = 13

def poll_buttons():
    global LAST_BUTTON_PUSH
    # All logic copied from Pimoroni buttons.py example

    # Button pins and labels
    pins = [5, 6, 16, 24]
    labels = ['AUTO', 'FORECAST', 'RAIN', 'MAP']
    button_settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
    chip = gpiodevice.find_chip_by_platform()
    offsets = [chip.line_offset_from_id(id) for id in pins]
    line_config = dict.fromkeys(offsets, button_settings)
    request = chip.request_lines(consumer="spectra6-buttons", config=line_config)

    while True:
        for event in request.read_edge_events():
            index = offsets.index(event.line_offset)
            LAST_BUTTON_PUSH = labels[index]

def rain_incoming():
    with sqlite3.connect('weather_display.sqlite') as db:
        hourly = pd.read_sql('SELECT * FROM open_meteo_hourly', db, parse_dates=['date'])

    cet = pytz.timezone('Europe/Brussels')
    current_hour = datetime.now(cet).replace(minute=0, second=0, microsecond=0)
    rain_search_limit = current_hour + pd.Timedelta(hours=RAIN_LIMIT)

    hourly = hourly[(hourly['date'] >= current_hour) & (hourly['date'] <= rain_search_limit)].copy()
    return hourly['precipitation'].sum() > 0.0


def get_draw_file(mode):
    real_draw_mode = mode

    if real_draw_mode == 'AUTO':
        real_draw_mode = 'RAIN' if rain_incoming() else 'FORECAST'

    if real_draw_mode == 'FORECAST':
        return 'dashboard_forecast.png'
    elif real_draw_mode == 'RAIN':
        return 'dashboard_rain.png'
    elif real_draw_mode == 'MAP':
        return 'weather_map.png'
    else:
        raise ValueError(f'Unrecognised mode {mode}')

# Start thread to capture button presses
Thread(target=poll_buttons).start()

# LED control setup
chip = gpiodevice.find_chip_by_platform()
led = chip.line_offset_from_id(LED_PIN)
led_gpio = chip.request_lines(consumer="inky", config={led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)})

inky = auto()

# Main control loop
button_mode = 'AUTO'
last_draw_file = None
last_draw_time = None

while True:

    draw_image = False

    if LAST_BUTTON_PUSH is not None and LAST_BUTTON_PUSH != button_mode:
        button_mode = LAST_BUTTON_PUSH


    draw_file = get_draw_file(button_mode)
    if draw_file != last_draw_file or last_draw_time is None or os.path.getmtime(draw_file) > last_draw_time:
        draw_image = True

    if draw_image:
        led_gpio.set_value(led, Value.ACTIVE)
        image = Image.open(draw_file)
        inky.set_image(image.resize(inky.resolution), saturation=0)
        inky.show()
        led_gpio.set_value(led, Value.INACTIVE)
        last_draw_file = draw_file
        last_draw_time = os.path.getmtime(draw_file)

    sleep(0.5)
