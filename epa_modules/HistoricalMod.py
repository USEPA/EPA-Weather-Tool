#Filename:        HistoricalMod.py
#Date:            5/25/2017
#Project:         EPA Weather Tool v1.0
#Prepared for:    US EPA Office of Research and Development
#                 National Homeland Security Research Center
#                 Decontamination and Consequences Management Division
#EPA Manager:     Timothy Boe
#Prepared by:     Tetra Tech, Inc. Lafayette, CA
#=======================================================================

import os.path
import sys
import argparse
import itertools
import re
import requests
import itertools
import math

# from datetime import datetime
# from extension_modules.dateutil.tz import tzutc, tzlocal
from extension_modules import dateconvert

from itertools import islice

# class HistoricalMod():
   

#     def __init__(self):
#         self = self

# GES grid to coordinate conversion Definitions:
# X = (Longitude - WestMostGridCenter)/DegreesPerGridCell
# Y = (Latitude - SouthMostGridCenter)/DegreesPerGridCell
def convert_grid(config):
  
    lat = float(config.lat_lon_coord[0])
    lon = float(config.lat_lon_coord[1])

    x_res = math.floor(0.5 + (lon + 124.9375)/0.125)
    y_res = math.floor(0.5 + (lat - 25.0625)/0.125)

    if x_res <= 463 and y_res <= 223:
        config.logger.console_log(config,"historical","info","Grid Conversions:", False)

        if x_res < 100:
            config.x_y_grid[0] = "0" + str(int(x_res))
            config.logger.console_log(config,"historical","info",("X = " + config.x_y_grid[0]),False)
        else:
            config.x_y_grid[0] = str(int(x_res))
            config.logger.console_log(config,"historical","info",("X = " + config.x_y_grid[0]), False)

        if y_res < 100:
            config.x_y_grid[1] = "0" + str(int(y_res))
            config.logger.console_log(config,"historical","info",("Y = " + config.x_y_grid[1]), False)
        else:
            config.x_y_grid[1] = str(int(y_res))
            config.logger.console_log(config,"historical","info",("Y = " + config.x_y_grid[1]), False)
    else:
        if x_res > 463:
            config.logger.console_log(config,"historical","info",("X exceeds max: ", str(int(x_res))),False)
        if y_res > 223: 
            config.logger.console_log(config,"historical","info",("Y exceeds max: ", str(int(y_res))), False)
        
        config.logger.console_log(config,"historical","error","Given coordinates yielded bad results on conversion.", True)
    return config
    
    
def build_request_obj(config):
    # if timezone override
    #convert local dates to UTC 
    utc_start_date_str = dateconvert.convert_local_to_utc(config,config.dates[0],2)
    utc_end_date_str = dateconvert.convert_local_to_utc(config,config.dates[1],2) 

    url = config.historical_datasource
    url = url.replace("@XCOORD", config.x_y_grid[0])
    url = url.replace("@YCOORD", config.x_y_grid[1])
    url = url.replace("@STARTDATE", utc_start_date_str)
    url = url.replace("@ENDDATE", utc_end_date_str)
    # url = url.replace("@STARTDATE", config.dates[0])
    # url = url.replace("@ENDDATE", config.dates[1])
    config.http_get = url

    config.logger.console_log(config,"historical","info","\nHttp_get url: " + config.http_get, False)
    return config

def get_historical_weather_data(config):
    try:
        timeout = config.request_timeout
        response = requests.get(config.http_get, timeout)
        data = ""
        config.logger.console_log(config,None,None,"Response code: "+ str(response.status_code), False)
        if(str(response.status_code) == "202" or str(response.status_code) == "200"):
            data = format_process_data(config, str(response.text))
            # data = str(response.text)
        else:
            data = None
        return data
    except requests.exceptions.Timeout:
        config.logger.console_log(config,"historical","error","Request Timed Out after " + timeout,False)

#Parses out data removing header meta-data and extracts only non-zero precip data
def format_process_data_OLD(config, responseData):
    index = 1
    start = 100 #initialize at index much greater
    buffer = ""
    filteredData = ""
    for line in responseData.splitlines():
        tokens = line.split()
        if("Date&Time" in tokens):
            start = index
        if(index > start):
            if(len(tokens) > 2):
                if float(tokens[2]) > 0:
                    val = float(tokens[2]) #metric by default
                    if(config.precip_units != 'metric'): #convert to standard units
                        val = round((val/25.4),4)
                    if(val > 0.0): #conversion occasionally yields insignificant values
                        date_str = tokens[0]
                        #converts UTC response data to local time
                        local_date_str = dateconvert.convert_utc_to_local(config, date_str, tokens[1]) 
                        # config.logger.console_log(config,"historical","info", "utc_to_local_date: " + local_date_str,False)
                        buffer = config.precip_id + config.spacer + local_date_str + config.spacer + str(val) + "\n" #Formatted for EPASWMM (id yr mo day hr val)
                        filteredData += buffer

        index += 1
    
    # print(filteredData)
    return filteredData
     
#Parses out data removing header meta-data and extracts only non-zero precip data
def format_process_data(config, responseData):
    index = 1
    start = 100 #initialize at index much greater
    buffer = ""
    filteredData = ""
    MM_PER_IN = 25.4; # millimeters per inch
    for line in responseData.splitlines():
        tokens = line.split()
        if("Date&Time" in tokens):
            start = index
        if(index > start):
            if(len(tokens) > 2):
                if float(tokens[2]) > 0:
                    val = float(tokens[2]) #metric by default, kg/m2
                    #convert units from kg/m2 to mm, multiply by 1.0
                    #kg/m^2 ==> m*kg/m^3 ==> m*kg/(100cm)^3 ==> 1000*mm*kg/(1000*1000*cm^3)  ==> 1000mm/1000 ==> mm
                    if(config.precip_units != 'metric'): #convert to standard units, mm to inches
                        val = round((val/MM_PER_IN),4)
                    if(val > 0.0): #conversion occasionally yields insignificant values
                        date_str = tokens[0]
                        #NLDAS precip data is hourly backward-accumulated. 
                        #subtract one hour to provide SWMM data at top of the hour
                        datetimeObj0 = dateconvert.convert_datestr_timestr_to_DateTime(config, date_str, tokens[1])
                        datetimeObj1 = dateconvert.subtract_hours( datetimeObj0, 1 )
                        date_str1 = dateconvert.convert_datetime_to_datestr( datetimeObj1 )
                        time_str1 = dateconvert.convert_datetime_to_hourstr( datetimeObj1 )

                        #converts UTC response data to local time
                        local_date_str = dateconvert.convert_utc_to_local(config, date_str1, time_str1) 
                        # config.logger.console_log(config,"historical","info", "utc_to_local_date: " + local_date_str,False)
                        buffer = config.precip_id + config.spacer + local_date_str + config.spacer + str(val) + "\n" #Formatted for EPASWMM (id yr mo day hr val)
                        filteredData += buffer

        index += 1
    
    # print(filteredData)
    return filteredData
     