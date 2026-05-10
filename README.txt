Display Netatmo weather and open-meteo forecasts on an Inky Impression.

REQUIREMENTS

This installation assumes that a lot of required Python packages have been included in system libs
  python -m venv .venv --system-site-packages
  
The requirements.txt is probably exhaustive, but you should install as much as possible via
distribution packages, and then add the remainder using pip.

Requires wgrib2 v3.7.0. Newer versions won't work on a Pi Zero

If you create a folder named 'output', the output images will be copied to it.
Make it a symbolic link to send images to wherever you like.

CREDITS

Furniture icons by Yayat Dayat via The Noun Project https://thenounproject.com/creator/yayatdayat1974/

Sunrise/Sunset icons by Fajriah Robiatul Adawiah Avatar via The Noun Project https://thenounproject.com/creator/fajriahrobiatuladawiah21/

Gauge chart based on https://en.moonbooks.org/Articles/How-to-Create-a-Gauge-Chart-Using-Python-/
