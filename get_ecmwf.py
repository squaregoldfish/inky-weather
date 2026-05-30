from ecmwf.opendata import Client
import glob
import os

[os.remove(f) for f in glob.glob('ecmwf*.idx')]

client = Client()

client.retrieve(
    step=0,
    type='fc',
    param=['msl', '10u', '10v'],
    target='ecmwf.grib2',
)