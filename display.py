from astral import LocationInfo
from astral.sun import sun
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, date, timedelta
import drawsvg as draw
import io
import json
import math
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
import pytz
import sqlite3
import time
import toml

MIN_MAX_COLOR = 'black'
MAX_ARROW_ON = 'rgb(255, 0, 0)'
MAX_ARROW_OFF = 'rgb(255, 150, 150)'
MIN_ARROW_ON = 'rgb(0, 0, 255)'
MIN_ARROW_OFF = 'rgb(150, 150, 255)'

INDOOR_COLOR = '#00FF00'
MAIN_COLOR = '#FF0000'

SUNRISE = '#ff9900'
SUNSET = '#ff2200'

FONT = 'Roboto Mono'

HUMIDITY_SCALE = [
    {"value":   0, "color": [228,  78,  93]},
    {"value":  10, "color": [197, 106, 125]},
    {"value":  20, "color": [160, 138, 166]},
    {"value":  30, "color": [130, 173, 209]},
    {"value":  40, "color": [ 97, 183, 218]},
    {"value":  50, "color": [104, 206, 247]},
    {"value":  60, "color": [102, 203, 242]},
    {"value":  70, "color": [ 96, 178, 234]},
    {"value":  80, "color": [ 89, 154, 233]},
    {"value":  90, "color": [ 86, 131, 232]},
    {"value": 100, "color": [ 79, 105, 216]}
]

HUMIDITY_SCALE = [
    {"value":   0, "color": [255,   0,   0]},
    {"value":  25, "color": [255, 100, 100]},
    {"value":  50, "color": [100, 255, 255]},
    {"value":  75, "color": [ 50, 255, 255]},
    {"value": 100, "color": [  0,   0, 255]}
]


PRESSURE_SCALE = [
    {"value":  970.00, "color": [ 50, 255, 255]},
    {"value":  981.66, "color": [100, 255, 255]},
    {"value":  993.32, "color": [200, 255, 200]},
    {"value": 1004.98, "color": [253, 241,   8]},
    {"value": 1016.64, "color": [252, 177,   5]},
    {"value": 1028.30, "color": [255, 128,   3]},
    {"value": 1040.00, "color": [255,  50,  50]}
]


CO2_SCALE = [
    {"value":  400.0, "color": [0, 0, 255]},
    {"value":  550.0, "color": [0, 255, 0]},
    {"value":  700.0, "color": [255,  128,  50]},
    {"value":  850.0, "color": [255,  0,  0]},
    {"value": 1000.0, "color": [200,  0,  0]}
]


RAIN_SCALE = [
    {"value":  0.0, "color": [165, 218, 243]},
    {"value":  4.3, "color": [114, 198, 235]},
    {"value":  8.6, "color": [ 80, 167, 221]},
    {"value": 12.9, "color": [ 61, 123, 186]},
    {"value": 17.1, "color": [ 49,  90, 145]},
    {"value": 21.4, "color": [ 42,  71, 119]},
    {"value": 25.7, "color": [ 28,  44,  79]},
    {"value": 30.0, "color": [ 10,  12,  25]}
]


def _interpolate_color(color1, color2, proportion):
  return round(color1 + (color2 - color1) * proportion)

def to_hex(decimal):
    result = hex(decimal).split('x')[-1]
    return f'0{result}' if len(result) == 1 else result

def get_color(value, scale, type):
    if value <= scale[0]['value']:
        result = scale[0]['color']
    elif value >= scale[-1]['value']:
        result = scale[-1]['color']
    else:
        prev_entry = scale[0]
        next_entry = scale[1]

        for i in range(0, len(scale)):
            if scale[i]["value"] == value:
                prev_entry = scale[i]
                next_entry = scale[i]
            elif scale[i]["value"] < value and scale[i + 1]["value"] > value:
                prev_entry = scale[i]
                next_entry = scale[i + 1]

        if prev_entry['color'] == next_entry['color']:
            result = prev_entry['color']
        else:
            color_proportion = (value - prev_entry["value"]) / (next_entry["value"] - prev_entry["value"])
            red_value = _interpolate_color(prev_entry['color'][0], next_entry['color'][0], color_proportion)
            green_value = _interpolate_color(prev_entry['color'][1], next_entry['color'][1], color_proportion)
            blue_value = _interpolate_color(prev_entry['color'][2], next_entry['color'][2], color_proportion)

            result = [red_value, green_value, blue_value]

    if type == 'hex':
        return f'#{to_hex(result[0])}{to_hex(result[1])}{to_hex(result[2])}'
    elif type == 'rgb':
        return f'rgb({result[0]}, {result[1]}, {result[2]})'
    else:
        return result

def interpolate_indexed_colors(scale, n=50):
    values = np.array([p["value"] for p in scale])
    colors = np.array([p["color"] for p in scale])

    target = np.linspace(values.min(), values.max(), n)

    r = np.interp(target, values, colors[:, 0])
    g = np.interp(target, values, colors[:, 1])
    b = np.interp(target, values, colors[:, 2])

    def rgb_to_hex(rgb):
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    return [
        (
            round(target[i], 2),
            round(target[i + 1], 2),
            rgb_to_hex((int(r[i]), int(g[i]), int(b[i])))
        )
        for i in range(n - 1)
    ]

def gauge_chart(data, unit, scale):
    zones = interpolate_indexed_colors(scale)
    min_val = zones[0][0]
    max_val = zones[-1][1]
    
    # Convert value to angular position (0° = max, 180° = min)
    def val_to_deg(v):
        return 180.0 * (1.0 - (v - min_val) / (max_val - min_val))

    plt.rc('font', family=FONT, weight='regular', size=10)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.set_aspect('equal')

    # Define geometry
    outer_r = 1.0
    thickness = 0.30
    inner_r = outer_r - thickness

    # Draw each zone as a wedge
    for a, b, color in zones:
        theta1 = val_to_deg(b)
        theta2 = val_to_deg(a)
        wedge = patches.Wedge(center=(0, 0), r=outer_r,
                              theta1=theta1, theta2=theta2,
                              width=thickness,
                              facecolor=color, edgecolor=color, linewidth=1)
        ax.add_patch(wedge)

    # Draw the needle
    for needle in data:
        # Clamp the input value
        value = max(min_val, min(max_val, needle[0]))
        
        angle_deg = val_to_deg(value)
        angle_rad = np.deg2rad(angle_deg)
        needle_len = inner_r * 0.9
        nx, ny = needle_len * np.cos(angle_rad), needle_len * np.sin(angle_rad)
        ax.plot([0, nx], [0, ny], lw=5, color=needle[1], zorder=5)
        ax.scatter([0], [0], s=120, color=needle[1], zorder=6)

    if len(data) == 1:
        label = '/'.join([str(n[0]) for n in data]) + unit
        ax.text(0, -0.20, label, ha='center', va='center',
                fontsize=32, fontweight='regular', color='black')
    else:
        # Unit
        ax.text(0, -0.20, unit, ha='center', va='center',
                fontsize=38, fontweight='regular', color='black')

        if data[0][0] < data[1][0]:
            label1_src = 0
            label2_src = 1
        else:
            label1_src = 1
            label2_src = 0

        ax.text(-1.03, -0.20, data[label1_src][0], ha='left', va='center',
                fontsize=38, fontweight='regular', color=data[label1_src][1])
        ax.text(1.04, -0.20, data[label2_src][0], ha='right', va='center',
                fontsize=38, fontweight='regular', color=data[label2_src][1])
        


    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.35, 1.15)
    ax.axis('off')
    plt.tight_layout()

    plot_bytes = io.BytesIO()
    # Save the figure as an SVG file
    plt.savefig(plot_bytes, format='svg', transparent=True)
    plt.close()

    return plot_bytes.getvalue()

def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def split_number(number):
    number_str = str(number)
    int_part = str(math.floor(abs(number)))
    if number < 0:
        int_part = f'-{int_part}'

    point_location = number_str.find('.')
    decimal_part = number_str[point_location + 1] if point_location > 0 else '0'

    return (int_part, decimal_part)

def outdoor_temperature(d, module):
    temp = module['Temperature']
    int_part, decimal_part = split_number(temp)    

    d.append(draw.Text(int_part, 122, 148, 115, font_weight='Bold', fill='black', stroke='black', text_anchor='end'))
    d.append(draw.Text('.', 55, 143, 115, font_weight='Bold', fill='black', stroke='black'))
    d.append(draw.Text(decimal_part, 43, 168, 115, font_weight='Bold', fill='black', stroke='black'))
    d.append(draw.Text('°C', 30, 154, 47, font_weight='Bold', fill='black', stroke='black'))

    # Max/Min and trend
    trend = module['temp_trend']

    # Max Temp
    max = f'{module["max_temp"]:.1f}'
    max_arrow_color = MAX_ARROW_ON if trend == 'up' else MAX_ARROW_OFF

    d.append(draw.Lines(198, 38, 208, 23, 218, 38, fill=max_arrow_color, stroke=None, close='true'))
    d.append(draw.Text(max, 20, 198, 57, font_weight='Regular', fill=MIN_MAX_COLOR, stroke_width=0))

    min = f'{module["min_temp"]:.1f}'
    min_arrow_color = MIN_ARROW_ON if trend == 'down' else MIN_ARROW_OFF

    d.append(draw.Lines(198, 103, 208, 117, 218, 103, fill=min_arrow_color, stroke=None, close='true'))
    d.append(draw.Text(min, 20, 198, 98, font_weight='Regular', fill=MIN_MAX_COLOR, stroke_width=0))

def pressure(d, module):
    pressure = module['Pressure']
    int_part, decimal_part = split_number(pressure)  

    pressure_color = get_color(pressure, PRESSURE_SCALE, 'rgb')

    d.append(draw.Text(int_part, 50, 408, 60, font_weight='Bold', fill=pressure_color, stroke_width=0, text_anchor='end'))
    d.append(draw.Text('.', 30, 406, 60, font_weight='Bold', fill=pressure_color, stroke_width=0))
    d.append(draw.Text(decimal_part, 20, 421, 60, font_weight='Bold', fill=pressure_color, stroke_width=0))
    d.append(draw.Text("mb", 18, 433, 38, font_weight='Regular', fill=pressure_color, stroke_width=0, text_anchor='end'))

    # Trend
    trend = module['pressure_trend']

    max_arrow_color = MAX_ARROW_ON if trend == 'up' else MAX_ARROW_OFF
    d.append(draw.Lines(440, 42, 450, 32, 460, 42, fill=max_arrow_color, stroke=None, close='true'))

    min_arrow_color = MIN_ARROW_ON if trend == 'down' else MIN_ARROW_OFF
    d.append(draw.Lines(440, 50, 450, 60, 460, 50, fill=min_arrow_color, stroke=None, close='true'))

def pressure_trend(d, module):

    MAX_ARROW_X = 375
    MIN_ARROW_X = 270
    ARROW_Y = 100

    trend = module['pressure_trend']

    if trend == 'up':
        d.append(draw.Lines(MAX_ARROW_X, ARROW_Y, MAX_ARROW_X + 10, ARROW_Y + 5, MAX_ARROW_X, ARROW_Y + 10, fill=MAX_ARROW_ON, stroke=None, close='true'))

    if trend == 'down':
        d.append(draw.Lines(MIN_ARROW_X, ARROW_Y, MIN_ARROW_X - 10, ARROW_Y + 5, MIN_ARROW_X, ARROW_Y + 10, fill=MIN_ARROW_ON, stroke=None, close='true'))

def humidity(d, module):
    humidity = module['Humidity']
    humidity_color = get_color(humidity, HUMIDITY_SCALE, 'rgb')

    d.append(draw.Text(str(humidity), 50, 408, 110, font_weight='Bold', fill=humidity_color, stroke_width=0, text_anchor="end"))
    d.append(draw.Text('%', 30, 413, 111, font_weight='Bold', fill=humidity_color, stroke_width=0))

def rain(d, module, forecast):
    hour = round(module['sum_rain_1'], 1)
    day = round(module['sum_rain_24'], 1)

    hour_color = '#6464ff'
    day_color = '#0000ff'
    forecast_color = '#c8c8ff'

    START = 590
    END = 784
    WIDTH = END - START
    TOP = 98
    HEIGHT = 12

    print(WIDTH)
    
    if day == 0 and hour == 0 and forecast == 0:
        d.append(draw.Text('Dry', 60, 635, 80, font_family='Noto Sans', font_weight='Bold', fill='#9696ff', stroke_width=0, text_anchor='center'))
    else:
        d.append(draw.Text('Rain', 20, START - 3, 50, font_family='Noto Sans', font_weight='Regular', fill=day_color, text_anchor='start'))

        rain_amount = ''
        if hour > 0:
            rain_amount += f'{hour}/'
        rain_amount += f'{day + hour}mm'

        d.append(draw.Text(rain_amount, 20, END, 50, font_weight='Regular', fill=day_color, text_anchor='end'))

        d.append(draw.Text('Forecast', 20, START - 3, 80, font_family='Noto Sans', font_weight='Regular', fill=day_color, text_anchor='start'))
        d.append(draw.Text(f'{forecast}mm', 20, END, 80, font_weight='Regular', fill=day_color, text_anchor='end'))

        total = day + forecast
        tenth_width = WIDTH / (total * 10)

        day_width = math.ceil((day - hour) * 10 * tenth_width)
        hour_width = math.ceil(hour * 10 * tenth_width)
        forecast_width = math.ceil(forecast * 10 * tenth_width)

        if day_width > 0:
            d.append(draw.Rectangle(START, TOP, day_width, HEIGHT, fill=day_color, stroke_width=0))       
        if hour_width > 0:
            d.append(draw.Rectangle(START + day_width, TOP, hour_width, HEIGHT, fill=hour_color, stroke_width=0))
        if forecast_width > 0:
            d.append(draw.Rectangle(START + day_width + hour_width, TOP, forecast_width, HEIGHT, fill=forecast_color, stroke_width=0))

def temperature_plot(ax, dates, temps, markers, color, linewidth):
    ax.plot(dates, temps, color=color, linewidth=linewidth, marker='o', markersize=6 if markers else 0)

def precip_plot(ax, dates, precip, bar_width, min_y):
    ax.bar(dates, precip, color='#9696ff', width=bar_width)
    if (precip < 0.1).all():
        ax.set_yticks([])
    elif (precip <= min_y).all():
        ax.set_ylim((0, min_y))

def indoor_temp(y, icon, module):
    
    temperature = module['Temperature']
    humidity = module['Humidity']
    co2 = module['CO2']

    d.append(draw.Image(10, y - 30, 45, 45, icon, embed=True))

    int_part, decimal_part = split_number(temperature)

    temperature_color='black'

    d.append(draw.Text(int_part, 28, 98, y + 2, font_weight='Bold', fill=temperature_color, stroke_width=0, text_anchor='end'))
    d.append(draw.Text('.', 23, 96, y + 2, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text(decimal_part, 23, 107, y + 2, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text('°', 23, 121, y + 2, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text('C', 23, 133, y + 2, font_weight='Bold', fill=temperature_color, stroke_width=0))

def battery(y, name, value):
    d.append(draw.Text(name, 14, 771, y + 5, font_weight="Regular", fill="rgb(50, 50, 50)", stroke_width=0))
   
    if value <= 12:
        color = 'rgb(255, 0, 0)'
    elif value <= 18:
        color = 'rgb(255, 128, 0)'
    else:
        color = 'rgb(0, 255, 0)'

    d.append(draw.Circle(790, y, 6, stroke_width=0, fill=color))

def get_sun(position, timezone):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    location = LocationInfo(name='Home', region='', timezone=timezone,
                        latitude=position['latitude'], longitude=position['longitude'])

    today_sun = sun(location.observer, date=today, tzinfo=location.timezone)
    tomorrow_sun = sun(location.observer, date=tomorrow, tzinfo=location.timezone)

    sunrise = today_sun['sunrise'] if today_sun['sunrise'] >= datetime.now(timezone) else tomorrow_sun['sunrise'] 
    sunset = today_sun['sunset'] if today_sun['sunset'] >= datetime.now(timezone) else tomorrow_sun['sunset'] 

    return(sunrise, sunset)

def sun_info(d, sunrise, sunset):
    d.append(draw.Image(540, 402, 45, 45, 'sunrise.svg', embed=True))
    d.append(draw.Text(sunrise.strftime("%H"), 35, 632, 433, font_weight='Bold', fill=SUNRISE, stroke_width=0, text_anchor='end'))
    d.append(draw.Text(':', 35, 629, 431, font_weight='Bold', fill=SUNRISE, stroke_width=0))
    d.append(draw.Text(sunrise.strftime("%M"), 35, 645, 433, font_weight='Bold', fill=SUNRISE, stroke_width=0))

    d.append(draw.Image(540, 442, 45, 45, 'sunset.svg', embed=True))
    d.append(draw.Text(sunset.strftime("%H"), 35, 632, 471, font_weight='Bold', fill=SUNSET, stroke_width=0, text_anchor='end'))
    d.append(draw.Text(':', 35, 629, 469, font_weight='Bold', fill=SUNSET, stroke_width=0))
    d.append(draw.Text(sunset.strftime("%M"), 35, 645, 471, font_weight='Bold', fill=SUNSET, stroke_width=0))


def draw_netatmo_outdoor(config, canvas, outdoor_module, bedroom_module):
    # Temperature
    outdoor_temperature(canvas, outdoor_module)

    # Pressure
    pressure = bedroom_module['Pressure']
    pressure_text = f'{pressure:.01f}'
    pressure_chart = gauge_chart([(pressure, '#2F4F4F')], 'mb', PRESSURE_SCALE)
    canvas.append(draw.Image(202, -85, 250, 250, data=pressure_chart, mime_type='image/svg+xml', embed=True))
    pressure_trend(d, bedroom_module)

    # Humidity
    humidity = outdoor_module['Humidity']
    humidity_text = f'{humidity}%'
    humidity_chart = gauge_chart([(humidity, '#2F4F4F')], '%', HUMIDITY_SCALE)
    canvas.append(draw.Image(360, -85, 250, 250, data=humidity_chart, mime_type='image/svg+xml', embed=True))

def draw_netatmo_indoor(config, canvas, living_room, bedroom):
    indoor_temp(433, 'sofa.svg', living_room)
    indoor_temp(468, 'bed.svg', bedroom)

    indoor_humidity = living_room['Humidity']
    main_humidity = bedroom['Humidity']

    humidity_data = [
        (indoor_humidity, INDOOR_COLOR),
        (main_humidity, MAIN_COLOR)
    ]

    indoor_humidity_chart = gauge_chart(humidity_data, '%', HUMIDITY_SCALE)
    d.append(draw.Image(133, 320, 200, 200, data=indoor_humidity_chart, mime_type='image/svg+xml', embed=True))

    indoor_co2 = living_room_module['CO2']
    main_co2 = bedroom_module['CO2']

    co2_data = [
        (indoor_co2, INDOOR_COLOR),
        (main_co2, MAIN_COLOR)
    ]

    co2_chart = gauge_chart(co2_data, 'ppm', CO2_SCALE)
    d.append(draw.Image(270, 320, 200, 200, data=co2_chart, mime_type='image/svg+xml', embed=True))

def hourly_forecast(canvas, forecast, sunrise, sunset):
    plt.rc('font', family=FONT, weight='regular', size=10)
    fig, ax = plt.subplots(figsize=(4, 2.75))

    temperature_plot(ax, forecast['date'], forecast['temperature_2m'], False, 'black', 3)

    range = max(forecast['temperature_2m']) - min(forecast['temperature_2m'])
    if range < 5:
        midpoint = min(forecast['temperature_2m']) + (range / 2)
        range_min = midpoint - 2.5
        range_max = midpoint + 2.5

        print(range_min)
        print(range_max)

        if range >= 4.75:
            range_min -= 0.2
            range_max += 0.2

        ax.set_ylim([range_min, range_max])

    precip_hour = ax.twinx()
    ax.set_zorder(precip_hour.get_zorder()+1)
    ax.patch.set_visible(False)

    precip_plot(precip_hour, forecast['date'], forecast['precipitation'], 0.025, 0.5)

    precip_hour.axvline(sunrise, color=SUNRISE, linewidth=2).set_zorder(-100)
    precip_hour.axvline(sunset, color=SUNSET, linewidth=2).set_zorder(-100)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H', tz=cet))

    plt.tight_layout()
    plot_bytes = io.BytesIO()
    # Save the figure as an SVG file
    plt.savefig(plot_bytes, format='svg', transparent=True)
    plt.close()

    canvas.append(draw.Image(0, 125, 400, 275, data=plot_bytes.getvalue(), mime_type='image/svg+xml', embed=True))

def daily_forecast(canvas, forecast):
    plt.rc('font', family=FONT, weight='regular', size=10)
    fig, ax = plt.subplots(figsize=(4, 2.75))

    temperature_plot(ax, forecast['date'], forecast['temperature_2m_min'], True, 'blue', 2)
    temperature_plot(ax, forecast['date'], forecast['temperature_2m_max'], True, 'red', 2)

    range = max(daily['temperature_2m_max']) - min(daily['temperature_2m_min'])
    if range < 5:
        midpoint = min(daily['temperature_2m_min']) + (range / 2)
        range_min = midpoint - 2.5
        range_max = midpoint + 2.5

        print(range_min)
        print(range_max)

        if range >= 4.75:
            range_min -= 0.2
            range_max += 0.2

        ax.set_ylim([range_min, range_max])

    precip_day = ax.twinx()
    ax.set_zorder(precip_day.get_zorder()+1)
    ax.patch.set_visible(False)

    precip_plot(precip_day, forecast['date'], forecast['precipitation_sum'], 0.5, 5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %-d', tz=cet))
    ax.xaxis.set_major_locator(MultipleLocator(1))

    plt.tight_layout()
    plot_bytes = io.BytesIO()
    # Save the figure as an SVG file
    plt.savefig(plot_bytes, format='svg', transparent=True)
    plt.close()

    canvas.append(draw.Image(400, 125, 400, 275, data=plot_bytes.getvalue(), mime_type='image/svg+xml', embed=True))

def get_remaining_precip(hourly):
    today = pd.Timestamp.now(tz=hourly['date'].iloc[0].tz).normalize()
    tomorrow = today + pd.Timedelta(days=1)
    precip_sum = hourly[hourly['date'] < tomorrow]['precipitation'].sum()
    return round(precip_sum, 1)


# Load Config
with open('config.toml') as cin:
    config = toml.loads(cin.read())

while True:
    # Load Netatmo Data
    with open('netatmo_weather.json') as nin:
        netatmo = json.load(nin)

    bedroom_module = netatmo['devices'][0]['dashboard_data']
    outdoor_module = None
    living_room_module = None
    rain_module = None

    for module in netatmo['devices'][0]['modules']:
        module_name = module['module_name']

        if module_name == 'Outdoor Module':
            outdoor_module = module['dashboard_data']
            outdoor_module['battery'] = module['battery_percent']
        elif module_name == 'Indoor 1':
            living_room_module = module['dashboard_data']
            living_room_module['battery'] = module['battery_percent']
        elif module_name == 'Rain':
            rain_module = module['dashboard_data']
            rain_module['battery'] = module['battery_percent']

    # Load and setup meteo forecast
    with sqlite3.connect('weather_display.sqlite') as db:
        hourly = pd.read_sql('SELECT * FROM open_meteo_hourly', db, parse_dates=['date'])
        daily = pd.read_sql('SELECT * FROM open_meteo_daily', db, parse_dates='date')

    cet = pytz.timezone('Europe/Brussels')
    current_hour = datetime.now(cet).replace(minute=0, second=0, microsecond=0)
    plus_24_hours = current_hour + pd.Timedelta(hours=24)
    hourly = hourly[(hourly['date'] >= current_hour) & (hourly['date'] <= plus_24_hours)].copy()

    today_forecast = daily.iloc[0]
    daily = daily[1:6].copy()

    # Sun info
    sunrise, sunset = get_sun(config['location'], cet)

    # Prepare canvas
    d = draw.Drawing(800, 480, origin=(0, 0), font_family=FONT)
    r = draw.Rectangle(0, 0, 800, 480, fill="white", stroke=None)
    d.append(r)

    # Timestamp
    d.append(draw.Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 15, 798, 12,
        font_family='Noto Sans', font_weight='Bold', fill='rgb(100, 100, 100)', stroke_width=0, text_anchor='end'))

    # Draw basic Netatmo stuff (no rain)
    draw_netatmo_outdoor(config, d, outdoor_module, bedroom_module)
    draw_netatmo_indoor(config, d, bedroom_module, living_room_module)

    # Netatmo Battery Status
    battery(436, 'O', outdoor_module['battery'])
    battery(453, 'R', rain_module['battery'])
    battery(470, 'I', living_room_module['battery'])


    # Hourly forecast plot
    hourly_forecast(d, hourly, sunrise, sunset)

    # Daily forecast plot
    daily_forecast(d, daily)

    # Rain map
    #d.append(draw.Image(415, 143, 374, 218, 'rain_map.png', embed=True))


    # Rain info
    forecast_rain = get_remaining_precip(hourly)
    rain(d, rain_module, forecast_rain)

    # Sun info
    sun_info(d, sunrise, sunset)

    # Save the final image
    d.save_png("display.png")

    exit()

    time.sleep(900)


