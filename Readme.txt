April 2018

Weather Data Tool
Version 1.0

Operating Systems Tested
------------------------
Microsoft Windows 7
Microsoft Windows 10

Platform Requirements
---------------------
python 3.4.4 or 3.5.2

Installation
------------
Unzip the distribution file at desired location. 
Using a command prompt from the application folder:

    py -m pip install .

Note: dependency packages are automatically installed (requests, pytz, timezonefinder)

Uninstallation
--------------
py -m pip uninstall requests
py -m pip uninstall pytz
py -m pip uninstall timezonefinder
Lastly, delete the application folder.

Running Interactive Mode
------------------------
From a command prompt:
    py EpaWeatherTool.py

Technical Support
-----------------
Ken Wilkinson, ken.wilkinson@tetratech.com
Sujoy Roy, sujoy.roy@tetratech.com
Timothy Boe, boe.timothy@epa.gov

Notes
-----
The specified location coordinates must be over an area of land, not ocean.
