from distutils.core import setup
from setuptools import find_packages

setup(name="EpaWeatherTool",
       version="1.0",
       packages=['','epa_modules','extension_modules', 'extension_modules.dateutil.tz'],
       install_requires=['requests>=2.12.4','pytz','timezonefinder'],
       data_files=['config.ini']
       )