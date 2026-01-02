import json
import toml
import sqlite3
import pandas as pd
import numpy as np
import drawsvg as draw
import math
from datetime import datetime, date, timedelta
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
import io
from astral import LocationInfo
from astral.sun import sun


MIN_MAX_COLOR = 'rgb(100, 100, 100)'
MAX_ARROW_ON = 'rgb(255, 0, 0)'
MAX_ARROW_OFF = 'rgb(255, 150, 150)'
MIN_ARROW_ON = 'rgb(0, 0, 255)'
MIN_ARROW_OFF = 'rgb(150, 150, 255)'

SUNRISE = '#ffc300'
SUNSET = '#ff8800'

TEMP_SCALE = [
    {"value":  -4.0, "color": [ 29,  70, 154]},
    {"value":  -2.0, "color": [ 20,  98, 169]},
    {"value":   0.0, "color": [ 22, 116, 182]},
    {"value":   2.0, "color": [ 54, 138, 199]},
    {"value":   4.0, "color": [ 63, 163, 218]},
    {"value":   6.0, "color": [ 78, 192, 238]},
    {"value":   8.0, "color": [174, 220, 216]},
    {"value":  10.0, "color": [168, 214, 173]},
    {"value":  12.0, "color": [158, 208, 127]},
    {"value":  14.0, "color": [174, 211,  82]},
    {"value":  16.0, "color": [208, 217,  62]},
    {"value":  18.0, "color": [252, 222,   4]},
    {"value":  20.0, "color": [251, 203,  12]},
    {"value":  22.0, "color": [252, 183,  22]},
    {"value":  24.0, "color": [250, 163,  26]},
    {"value":  26.0, "color": [246, 138,  31]},
    {"value":  28.0, "color": [242, 106,  47]},
    {"value":  30.0, "color": [236,  81,  57]},
    {"value":  32.0, "color": [237,  42,  42]},
    {"value":  34.0, "color": [195,  32,  39]},
    {"value":  36.0, "color": [155,  27,  29]}
]

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

PRESSURE_SCALE = [
    {"value":  950.0, "color": [  6,   4, 192]},
    {"value":  962.9, "color": [ 12,  68, 254]},
    {"value":  975.7, "color": [  6, 192, 255]},
    {"value":  988.6, "color": [ 63, 255, 192]},
    {"value": 1001.4, "color": [189, 249,  58]},
    {"value": 1014.3, "color": [252, 191,   2]},
    {"value": 1027.1, "color": [255,  64,   0]},
    {"value": 1040.0, "color": [189,   0,   0]}
]

CO2_SCALE = [
    {"value":  400.0, "color": [136, 239, 237]},
    {"value":  514.3, "color": [ 97, 221, 174]},
    {"value":  628.6, "color": [124, 200, 108]},
    {"value":  742.9, "color": [149, 170,  44]},
    {"value":  857.1, "color": [157, 129,  31]},
    {"value":  971.4, "color": [153,  93,  50]},
    {"value": 1085.7, "color": [148,  61,  72]},
    {"value": 1200.0, "color": [144,  27,  99]}
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


def split_number(number):
    number_str = str(number)
    int_part = str(math.floor(number))
    decimal_part = number_str[number_str.find('.') + 1]

    return (int_part, decimal_part)

def outdoor_temperature(d, module):
    temp = module['Temperature']
    int_part, decimal_part = split_number(temp)    

    d.append(draw.Rectangle(10, 20, 180, 95, fill=get_color(temp, TEMP_SCALE, 'rgb')))

    d.append(draw.Text(int_part, 105, 140, 105, font_weight='Bold', fill='white', stroke='white', text_anchor='end'))
    d.append(draw.Text('.', 60, 132, 105, font_weight='Bold', fill="rgb(255, 255, 255)", stroke='white'))
    d.append(draw.Text(decimal_part, 40, 160, 105, font_weight='Bold', fill='white', stroke='white'))
    d.append(draw.Text('°C', 28, 150, 50, font_weight='Bold', fill='white', stroke='white'))

    # Max/Min and trend
    trend = module['temp_trend']

    # Max Temp
    max = f'{module["max_temp"]:.1f}'
    max_arrow_color = MAX_ARROW_ON if trend == 'up' else MAX_ARROW_OFF

    d.append(draw.Lines(195, 90, 205, 75, 215, 90, fill=max_arrow_color, stroke=None, close='true'))
    d.append(draw.Text(max, 17, 260, 90, font_weight='Regular', fill=MIN_MAX_COLOR, stroke_width=0, text_anchor='end'))

    min = f'{module["min_temp"]:.1f}'
    min_arrow_color = MIN_ARROW_ON if trend == 'down' else MIN_ARROW_OFF

    d.append(draw.Lines(195, 100, 205, 115, 215, 100, fill=min_arrow_color, stroke=None, close='true'))
    d.append(draw.Text(min, 17, 260, 113, font_weight='Regular', fill=MIN_MAX_COLOR, stroke_width=0, text_anchor='end'))

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

def humidity(d, module):
    humidity = module['Humidity']
    humidity_color = get_color(humidity, HUMIDITY_SCALE, 'rgb')

    d.append(draw.Text(str(humidity), 50, 408, 110, font_weight='Bold', fill=humidity_color, stroke_width=0, text_anchor="end"))
    d.append(draw.Text('%', 30, 413, 111, font_weight='Bold', fill=humidity_color, stroke_width=0))

def rain(d, module, forecast):
    hour = round(module['sum_rain_1'], 1)
    day = round(module['sum_rain_24'], 1)

    hour_color = get_color(hour, RAIN_SCALE, 'rgb')
    day_color = get_color(day, RAIN_SCALE, 'rgb')
    forecast_color = get_color(forecast, RAIN_SCALE, 'rgb')

    START = 550
    END = 780
    WIDTH = END - START
    
    if day == 0 and hour == 0 and forecast == 0:
        d.append(draw.Text('Dry', 60, 580, 75, font_weight='Bold', fill='rgb(220, 220, 255)', stroke_width=0, text_anchor='center'))
    else:
        if forecast <= day:
            tenth_width = WIDTH / (day * 10)
        else:
            # Forecast
            tenth_width = WIDTH / (forecast * 10)
            d.append(draw.Lines(START, 30, END, 30, END, 90, START, 90, fill='white',
                            stroke=forecast_color, stroke_dasharray='9,5', close='false'))

        day_width = (day - hour) * 10 * tenth_width
        hour_width = hour * 10 * tenth_width

        d.append(draw.Rectangle(START + day_width, 30, hour_width, 60, fill=hour_color, stroke=hour_color))       
        if day != hour:
            d.append(draw.Rectangle(START, 30, day_width, 60, fill=day_color, stroke=day_color))
        
        d.append(draw.Text(f'{day:.1f}mm', 26, 550, 113, font_weight='Bold', fill=day_color, stroke_width=0))
        d.append(draw.Text(f'{hour:.1f}', 18, 684, 110, font_weight='Regular', fill=hour_color, stroke_width=0, text_anchor='center'))
        d.append(draw.Text(f'{forecast:.1f}', 18, 780, 110, font_weight='Regular', font_style='Italic', fill=forecast_color, stroke_width=0, text_anchor='end'))

def temperature_plot(ax, dates, temps, points, markers):
    x = (dates - dates.min()).dt.total_seconds()  # Convert to seconds
    y = temps.values
    
    xnew = np.linspace(x.min(), x.max(), points)
    ynew = np.interp(xnew, x, y)
    timestamps_new = dates.min() + pd.to_timedelta(xnew, unit='s')
    spline_colors = [get_color(y, TEMP_SCALE, 'hex') for y in ynew]

    ax.scatter(timestamps_new, ynew, c=spline_colors, s=1 if markers else 8)

    if markers:
        ax.scatter(dates, temps, color=[get_color(y, TEMP_SCALE, 'hex') for y in temps])

def precip_plot(ax, dates, precip, bar_width, min_y):
    ax.bar(dates, precip, color='#ddddff', width=bar_width)
    if (precip < 0.1).all():
        ax.set_yticks([])
    elif (precip <= min_y).all():
        ax.set_ylim((0, min_y))

def forecast_plot(d, hourly, daily, sunrise, sunset):
    plt.rc('font', family='Noto Sans Mono', weight='regular', size=10)
    fig, axs = plt.subplots(1, 2, figsize=(8, 2.75))

    plot_hour = axs[0]
    temperature_plot(plot_hour, hourly['date'], hourly['temperature_2m'], 2000, False)

    precip_hour = plot_hour.twinx()
    plot_hour.set_zorder(precip_hour.get_zorder()+1)
    plot_hour.patch.set_visible(False)

    precip_plot(precip_hour, hourly['date'], hourly['precipitation'], 0.025, 0.5)

    precip_hour.axvline(sunrise, color=SUNRISE, linewidth=2).set_zorder(-100)
    precip_hour.axvline(sunset, color=SUNSET, linewidth=2).set_zorder(-100)

    plot_hour.xaxis.set_major_formatter(mdates.DateFormatter('%H', tz=cet))

    plot_day = axs[1]
    temperature_plot(plot_day, daily['date'], daily['temperature_2m_min'], 1000, True)
    temperature_plot(plot_day, daily['date'], daily['temperature_2m_max'], 1000, True)

    precip_day = plot_day.twinx()
    plot_day.set_zorder(precip_day.get_zorder()+1)
    plot_day.patch.set_visible(False)

    precip_plot(precip_day, daily['date'], daily['precipitation_sum'], 0.5, 5)
    plot_day.xaxis.set_major_formatter(mdates.DateFormatter('%a %-d', tz=cet))
    plot_day.xaxis.set_major_locator(MultipleLocator(1))

    plt.tight_layout()

    plot_bytes = io.BytesIO()
    # Save the figure as an SVG file
    plt.savefig(plot_bytes, format='svg', transparent=True)
    plt.close()

    d.append(draw.Image(0, 125, 800, 275, data=plot_bytes.getvalue(), mime_type='image/svg+xml', embed=True))

def indoor_data(y, icon, module):
    
    temperature = module['Temperature']
    humidity = module['Humidity']
    co2 = module['CO2']

    d.append(draw.Image(10, y - 30, 45, 45, icon, embed=True))

    int_part, decimal_part = split_number(temperature)

    temperature_color = get_color(temperature, TEMP_SCALE, 'rgb')
    
    d.append(draw.Text(int_part, 25, 105, y, font_weight='Bold', fill=temperature_color, stroke_width=0, text_anchor='end'))
    d.append(draw.Text('.', 25, 103, y, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text(decimal_part, 25, 115, y, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text('°', 25, 130, y, font_weight='Bold', fill=temperature_color, stroke_width=0))
    d.append(draw.Text('C', 25, 142, y, font_weight='Bold', fill=temperature_color, stroke_width=0))

    d.append(draw.Text(f'{module["Humidity"]}%', 25, 239, y, font_weight='Bold', fill=get_color(humidity, HUMIDITY_SCALE, 'rgb'), stroke_width=0, text_anchor='end'))

    co2_color = get_color(co2, CO2_SCALE, 'rgb')
    d.append(draw.Text(f'{co2}ppm', 25, 360, y, font_weight='Bold', fill=co2_color, stroke_width=0, text_anchor='end'))

def battery(y, name, value):
    d.append(draw.Text(name, 13, 772, y + 4, font_weight="Bold", fill="rgb(50, 50, 50)", stroke_width=0))
   
    if value <= 4000:
        color = 'red'
    elif value <= 4500:
        color = 'orange'
    else:
        color = 'green'

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
    d.append(draw.Image(500, 402, 45, 45, 'sunrise.svg', embed=True))
    d.append(draw.Text(sunrise.strftime("%H"), 25, 587, 432, font_weight='Bold', fill=SUNRISE, stroke_width=0, text_anchor='end'))
    d.append(draw.Text(':', 25, 585, 430, font_weight='Bold', fill=SUNRISE, stroke_width=0))
    d.append(draw.Text(sunrise.strftime("%M"), 25, 598, 432, font_weight='Bold', fill=SUNRISE, stroke_width=0))

    d.append(draw.Image(500, 442, 45, 45, 'sunset.svg', embed=True))
    d.append(draw.Text(sunset.strftime("%H"), 25, 587, 470, font_weight='Bold', fill=SUNSET, stroke_width=0, text_anchor='end'))
    d.append(draw.Text(':', 25, 585, 468, font_weight='Bold', fill=SUNSET, stroke_width=0))
    d.append(draw.Text(sunset.strftime("%M"), 25, 598, 470, font_weight='Bold', fill=SUNSET, stroke_width=0))


# Load Data
with open('netatmo_weather.json') as nin:
    netatmo = json.load(nin)

with open('config.toml') as cin:
    config = toml.loads(cin.read())

main_module = netatmo['devices'][0]['dashboard_data']
outdoor_module = None
indoor_module = None
rain_module = None

for module in netatmo['devices'][0]['modules']:
    module_name = module['module_name']

    if module_name == 'Outdoor Module':
        outdoor_module = module['dashboard_data']
        outdoor_module['battery'] = module['battery_vp']
    elif module_name == 'Indoor 1':
        indoor_module = module['dashboard_data']
        indoor_module['battery'] = module['battery_vp']
    elif module_name == 'Rain':
        rain_module = module['dashboard_data']
        rain_module['battery'] = module['battery_vp']

with sqlite3.connect('weather_display.sqlite') as db:
    hourly = pd.read_sql('SELECT * FROM open_meteo_hourly', db, parse_dates=['date'])
    daily = pd.read_sql('SELECT * FROM open_meteo_daily', db, parse_dates='date')

cet = pytz.timezone('Europe/Brussels')
current_hour = datetime.now(cet).replace(minute=0, second=0, microsecond=0)
plus_24_hours = current_hour + pd.Timedelta(hours=24)
hourly = hourly[(hourly['date'] >= current_hour) & (hourly['date'] <= plus_24_hours)].copy()

today_forecast = daily.iloc[0]
daily = daily[1:6].copy()

# Canvas
d = draw.Drawing(800, 480, origin=(0, 0), font_family='Noto Sans Mono')
r = draw.Rectangle(0, 0, 800, 480, fill="white", stroke=None)
d.append(r)

sunrise, sunset = get_sun(config['location'], cet)

outdoor_temperature(d, outdoor_module)
pressure(d, main_module)
humidity(d, outdoor_module)
rain(d, rain_module, today_forecast['precipitation_sum'])
forecast_plot(d, hourly, daily, sunrise, sunset)

indoor_data(433, config['display']['indoor_module_icon'], indoor_module)
indoor_data(468, config['display']['main_module_icon'], main_module)

sun_info(d, sunrise, sunset)

battery(436, 'O', outdoor_module['battery'])
battery(453, 'R', rain_module['battery'])
battery(470, 'L', indoor_module['battery'])


d.append(draw.Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 10, 800, 10, font_weight='Regular', fill='black', stroke_width=0, text_anchor='end'))

d.save_png("display.png")
