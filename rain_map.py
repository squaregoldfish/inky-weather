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

API_URL = 'https://api.rainviewer.com/public/weather-maps.json'
BLUR = 1
SNOW = 1
ZOOM = 7

MAP_WIDTH = 2
MAP_HEIGHT = 0.73

def lonlat_to_tile(lon, lat, z):
    n = 2.0 ** z
    xtile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def tile_bounds(x, y, z):
    n = 2.0 ** z
    lon_left = x / n * 360.0 - 180.0
    lon_right = (x + 1) / n * 360.0 - 180.0
    lat_top = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_bottom = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_left, lon_right, lat_bottom, lat_top


plt.show()

# Get the path to the latest radar tiles
radar_response = requests.get(API_URL)
radar_json = json.loads(radar_response.content)
tile_host = radar_json['host']
tile_path = radar_json['radar']['past'][12]['path']

tile_base = f'{tile_host}{tile_path}/512/{{z}}/{{x}}/{{y}}/2/{BLUR}_{SNOW}.png'

with open('config.toml') as cin:
    config = toml.loads(cin.read())

point_lon = config['location']['longitude']
point_lat = config['location']['latitude']

min_lon = point_lon - (MAP_WIDTH / 2)
max_lon = point_lon + (MAP_WIDTH / 2)
min_lat = point_lat - (MAP_HEIGHT / 2)
max_lat = point_lat + (MAP_HEIGHT / 2)


# compute tile range covering bbox
x0, y1 = lonlat_to_tile(min_lon, min_lat, ZOOM)
x1, y0 = lonlat_to_tile(max_lon, max_lat, ZOOM)
x_min, x_max = min(x0, x1), max(x0, x1)
y_min, y_max = min(y0, y1), max(y0, y1)

fig = plt.figure(figsize=[4, 2.75])
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mercator())

ax.set_extent([min_lon, max_lon, min_lat, max_lat], ccrs.PlateCarree())    
ax.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_0_countries', '10m', ec='#000000', fc='#f3fff3'))

# fetch and plot tiles
for x in range(x_min, x_max + 1):
    for y in range(y_min, y_max + 1):
        url = tile_base.format(z=ZOOM, x=x, y=y)
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            continue
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        arr = np.asarray(img) / 255.0  # normalized RGBA

        lon_left, lon_right, lat_bottom, lat_top = tile_bounds(x, y, ZOOM)
        # plot with PlateCarree extents (cartopy will reproject)
        ax.imshow(arr, origin='upper',
                  extent=(lon_left, lon_right, lat_bottom, lat_top),
                  transform=ccrs.PlateCarree(), zorder=5, interpolation='nearest')


ax.plot(point_lon, point_lat, 'ro', markersize=8, transform=ccrs.PlateCarree(), zorder=10)
ax.plot(2.939751, 51.23239, 'ro', markersize=5, transform=ccrs.PlateCarree(), zorder=10)

plt.tight_layout()
plt.savefig('rain_map.png', bbox_inches='tight', pad_inches=0.02)

