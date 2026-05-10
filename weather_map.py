from cartopy import crs as ccrs
import cartopy.feature as cfeature
import contextily as ctx
from datetime import datetime
import geopandas as gpd
import json
import matplotlib.pyplot as plt
import requests
from shapely.geometry import box
import toml
from xyzservices import TileProvider
import xyzservices.providers as xyz
import math
import numpy as np
import os
import xarray as xr
from scipy.ndimage import gaussian_filter
import shutil
from time import perf_counter as pc

TIMINGS = False

if TIMINGS:
    print('Init')
    t0 = pc()

API_URL = 'https://api.rainviewer.com/public/weather-maps.json'
BLUR = 0
SNOW = 1
ZOOM = 'auto'

MAP_WIDTH = 22
MAP_HEIGHT = 8.2

PROJECTION = ccrs.Mercator()

with open('config.toml') as cin:
    config = toml.loads(cin.read())

point_lon = config['location']['longitude']
point_lat = config['location']['latitude']

min_lon = point_lon - (MAP_WIDTH / 2)
max_lon = point_lon + (MAP_WIDTH / 2)
min_lat = point_lat - (MAP_HEIGHT / 2)
max_lat = point_lat + (MAP_HEIGHT / 2)

radar_response = requests.get(API_URL)
radar_json = json.loads(radar_response.content)
tile_host = radar_json['host']
tile_path = radar_json['radar']['past'][-1]['path']

tile_base = f'{tile_host}{tile_path}/256/{{z}}/{{x}}/{{y}}/2/{BLUR}_{SNOW}.png'

# Define the XYZ Tile Provider
tile_provider = TileProvider({
    "url": tile_base,
    "name": "",
    "attribution": "",
    "cross_origin": "Anonymous"}
)

if TIMINGS:
    print(pc() - t0)
    print('Init figure')
    t0 = pc()


fig_ratio = 480 / 800
figsize_x = 10.26
figsize_y = figsize_x * fig_ratio

# Create a map with PlateCarree projection
fig, ax = plt.subplots(figsize=[figsize_x, figsize_y], subplot_kw={'projection': PROJECTION})
ax.set_extent([min_lon, max_lon, min_lat, max_lat], ccrs.PlateCarree())

if TIMINGS:
    print(pc() - t0)
    print('Rain radar')
    t0 = pc()

# Rain radar
ctx.add_basemap(ax, source=tile_provider, zoom=ZOOM, crs=PROJECTION, zorder=10)

if TIMINGS:
    print(pc() - t0)
    print('Land')
    t0 = pc()

# Countries and coasts
ax.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_0_countries',
    '10m', linewidth=0.5, ec='#000000', fc='#96ff96'))

if TIMINGS:
    print(pc() - t0)
    print('Pressure')
    t0 = pc()

# Pressure
pressure = xr.load_dataset('pressure.nc')['PRES_meansealevel'][0] / 100

if TIMINGS:
    print(pc() - t0)
    print('Smooth Pressure')
    t0 = pc()

smoothed_pressure = gaussian_filter(pressure.values, sigma=1)

if TIMINGS:
    print(pc() - t0)
    print('Draw Pressure')
    t0 = pc()

clevs = range(940, 1050, 4)
cs = ax.contour(pressure.longitude, pressure.latitude, smoothed_pressure, levels=clevs, 
                colors='#000000', linewidths=2, zorder=9, transform=ccrs.PlateCarree())
ax.clabel(cs, inline=True, fontsize=8)

if TIMINGS:
    print(pc() - t0)
    print('Locations')
    t0 = pc()

# Points of interest
ax.plot(point_lon, point_lat, 'ro', markersize=7, transform=ccrs.PlateCarree(), zorder=50)
ax.plot(1.484565, 52.544083, 'ro', markersize=5.5, transform=ccrs.PlateCarree(), zorder=50)
ax.plot(0.465837, 52.796555, 'ro', markersize=5.5, transform=ccrs.PlateCarree(), zorder=50)

if TIMINGS:
    print(pc() - t0)
    print('Save PNG')
    t0 = pc()

ax.text(0.992, 0.047, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), transform=ax.transAxes,
    ha='right', va='top', fontfamily='Noto Sans', fontweight='bold', fontsize=12, color='#323232',
    zorder=75, bbox=dict(facecolor='white', edgecolor='white', alpha=0.9))

# Save
plt.savefig('weather_map.new.png', bbox_inches='tight', pad_inches=0.02)
os.replace('weather_map.new.png', 'weather_map.png')

if os.path.isdir('output'):
    shutil.copy('weather_map.png', 'output/weather_map.png')

if TIMINGS:
    print(pc() - t0)

