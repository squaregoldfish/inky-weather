from ecmwf.opendata import Client

client = Client()

client.retrieve(
    step=0,
    type='fc',
    param='msl',
    target='pressure.grib2',
)