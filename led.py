#!/usr/bin/env python3

import argparse
import time

import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Value

LED_PIN = 13

# Find the gpiochip device we need, we'll use
# gpiodevice for this, since it knows the right device
# for its supported platforms.
chip = gpiodevice.find_chip_by_platform()

# Setup for the LED pin
led = chip.line_offset_from_id(LED_PIN)
gpio = chip.request_lines(consumer="inky", config={led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)})

parser = argparse.ArgumentParser(
    prog='led.py',
    description='Switch the inky LED on or off')

parser.add_argument('state', type=int)

args = parser.parse_args()
gpio.set_value(led, Value.INACTIVE if args.state == 0 else Value.ACTIVE)
