py EpaWeatherTool.py -l -v default [1,37.9780,122.0311,4-4-2017,4-30-2017,0,0,US/Pacific,forecast_precip,concord_ca]
timeout /t 3

py EpaWeatherTool.py -l -v default [2,37,122,1-4-2016,1-6-2016,10,10,America/Chicago,historical_precip,dodge_city_ks]
timeout /t 3

py EpaWeatherTool.py -l -v default [2,40.7128,74.0059,1-4-2016,1-6-2016,10,10,America/New_York,historical_precip,New_York_ny]
timeout /t 3


