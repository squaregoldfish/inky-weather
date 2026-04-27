import cartopy.crs as ccrs
import cartopy.feature as cfeature
from io import BytesIO
import json
import math
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
import toml
import contextily as ctx
from xyzservices import TileProvider
import xyzservices.providers as xyz


API_URL = 'https://api.rainviewer.com/public/weather-maps.json'
BLUR = 1
SNOW = 1
ZOOM = 7

MAP_WIDTH = 2
MAP_HEIGHT = 0.73
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

fig, ax = plt.subplots(figsize=[4, 2.75], subplot_kw={'projection': PROJECTION})
ax.set_extent([min_lon, max_lon, min_lat, max_lat], ccrs.PlateCarree())
ax.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_0_countries', '10m', ec='#000000', fc='#f3fff3'))
#ctx.add_basemap(ax, source=tile_provider, zoom=ZOOM, crs=PROJECTION, zorder=10)
ax.plot(point_lon, point_lat, 'ro', markersize=8, transform=ccrs.PlateCarree(), zorder=10)
ax.plot(2.939751, 51.23239, 'ro', markersize=5, transform=ccrs.PlateCarree(), zorder=10)

plt.tight_layout()
plt.savefig('rain_map.png', bbox_inches='tight', pad_inches=0.02)

