from ecmwf.opendata import Client
import glob
import os

[os.remove(f) for f in glob.glob('pressure*.idx')]

client = Client()

client.retrieve(
    step=0,
    type='fc',
    param='msl',
    target='pressure.grib2',
)