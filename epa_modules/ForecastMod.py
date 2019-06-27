#Filename:        ForecastMod.py
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
import xml
import os
import collections

from epa_modules import ErrorHandler
from extension_modules import dateconvert
from collections import OrderedDict
from xml.etree import ElementTree as ET

def build_request_obj(config):
#convert local dates to UTC 
    utc_start_date_str = dateconvert.convert_local_to_utc(config,config.dates[0],1)
    utc_end_date_str = dateconvert.convert_local_to_utc(config,config.dates[1],1) 

    url = config.forecast_datasource
    url = url.replace("@LATITUDE", str(config.lat_lon_coord[0]))
    url = url.replace("@LONGITUDE", str(config.lat_lon_coord[1]))
    url = url.replace("@STARTDATE", utc_start_date_str)
    url = url.replace("@ENDDATE", utc_end_date_str)
   
    config.http_get = url

    print("\nHttp_get url: ", config.http_get)
    return config

def get_forecast_weather_data(config):
    try:
        timeout = config.request_timeout
        response = requests.get(config.http_get, timeout)
        data = ""
        config.logger.console_log(config,"forecast","info","Response code: " + str(response.status_code), False)
        
        if(str(response.status_code) == "202" or str(response.status_code) == "200"):
            data = format_process_data(config, str(response.text))
        else:
            data = None
        return data

    except requests.exceptions.Timeout:
        config.logger.console_log(config,"forecast","error","Request Timed Out after " + timeout,False)
    

def format_process_data(config, responseData):
    # print("response data: ", responseData)
    try:    
        precip_key = ""
        dates_node = None
        precip_node = None
        start_dates_list = []
        precip_dates_dict = OrderedDict()

        root = None

        if (config.bootstrap_file != None):
            #read from file
            fpath = os.path.abspath(os.getcwd() + config.bootstrap_file)
            config.logger.console_log(config,"forecast","info","fpath: " + fpath, False)
            tree = ET.parse(fpath)
            root = tree.getroot()
        else:
        # read from stream
            root = ET.fromstring(responseData) #parse from string
            if root == None or root == "error":
                raise ErrorHandler.Error("root error")
        
        config.logger.console_log(config,None,None,"root " + root.tag,False)
        
        tl_list = root.findall("./data/time-layout")
        param_list = root.findall("./data/parameters")
        
        for param in param_list:
            for el in param:
                attr = el.get('type')
                if(attr == 'liquid'):
                    precip_node = el
                    precip_key = str(el.get('time-layout'))
                    config.logger.console_log(config,"forecast","info","precip node attrib: " + str(precip_node.attrib), False)
                    config.logger.console_log(config,"forecast","info",("precip_key: " + precip_key), False)
                    break
            if(precip_node != None):
                break
        
        for tl in tl_list:
            curr_key = str(tl[0].text) #Get first element -> time-layout key
            # print("current key: ", curr_key)
            if(curr_key == precip_key):
                dates_node = tl
                config.logger.console_log(config,"forecast","info","found key match: " + curr_key, False)
                break

        # print("\nstart dates:")
        if dates_node == None:
            raise ErrorHandler.Error("An error occurred with the given parameters. The server returned no data for the values supplied.")

        for el in dates_node:
            tag = str(el.tag)
            if(tag == 'start-valid-time'): #Retrieve only start dates for the current period
                date = str(el.text)
                start_dates_list.append(date)
                # print(date)
        
        del precip_node[0]

        # print("start dates len: ",len(start_dates_list))
        # print("precip_node len:",len(precip_node))
        if(len(start_dates_list) == len(precip_node)):
        # Precip data
            
            for i in range(len(precip_node)): #precip n is 1/2 of dates_list
                # print("precip node val: ", precip_node[i].text)
                val = float(precip_node[i].text) #in/6hr
                if(val > 0):
                    precip_dates_dict[start_dates_list[i]] = val    
                # else:
                #     print("rejected: " +  start_dates_list[i] + " , " + str(val) + "\n")
        else:
            raise ErrorHandler.Error("Critical Error, List mismatch")
    
    except ErrorHandler.Error as e:
        config.logger.console_log(config,"forecast","error", str(e), False)
        return None  
    # except: #catch all anonymous exceptions
    #     config.logger.console_log(config,"forecast","error","Unexpected error, " + str(sys.exc_info()[0]), True) 
    
    #return generate_output_data_QPF(config,precip_dates_dict)
    return generate_output_data_next6Hrs(config,precip_dates_dict)


def generate_output_data_QPF(config,dates_dict):
    # Output data of a Quantitative Precipitation Forecast period, e.g. inches/6 hrs
    # This is provided for testing purposes.
    # date_time is LOCAL start of QPF duration, from XML tag <start-valid-time> 
    data = ""
    
    # print("\nDictionary Vals:")
    for k, v in dates_dict.items(): #k is datetime, v is precip val
        tokens = k.split(':')
        date_time = tokens[0].split("T")
        local_date_str = dateconvert.convert_datestr_timestr_to_datetimestr(config,date_time[0],date_time[1])
        #print (local_date_str) 
        # config.logger.console_log(config,"forecast","info","Local date: " + local_date_str, False)
        if(config.precip_units == 'metric'): #default response data is standard units
            val = round(v*25.4,4)
            buffer = config.precip_id + config.spacer + local_date_str + config.spacer + str(val) + "\n"
        else:    
            buffer = config.precip_id + config.spacer + local_date_str + config.spacer + str(v) + "\n"
        data += buffer 
        # print(k,v)
    return data
    

def generate_output_data_next6Hrs(config,dates_dict):
    # Output data of a Quantitative Precipitation Forecast period, e.g. inches/6 hrs
    # is converted to in/hr or mm/hr for the next six hours
    # date_time is LOCAL start of QPF duration, from XML tag <start-valid-time>
    data = ""
    HR_PER_QPF = 6.0; # hours per QPF duration
    MM_PER_IN = 25.4; # millimeters per inch

    # print("\nDictionary Vals:")
    for k, v in dates_dict.items(): #k is datetime, v is precip val, in/6 hr
        tokens = k.split(':')
        date_time = tokens[0].split("T")
        
        #utc aware datetime obj
        datetimeObj0 = dateconvert.convert_datestr_timestr_to_DateTime(config, date_time[0], date_time[1])

        for hr in range(0, 6):
            datetimeObj1 = dateconvert.add_hours( datetimeObj0, hr )
            date_str1 = dateconvert.convert_datetime_to_datestr( datetimeObj1 )
            time_str1 = dateconvert.convert_datetime_to_hourstr( datetimeObj1 )

            local_date_str = dateconvert.convert_datestr_timestr_to_datetimestr(config, date_str1, time_str1)
            # config.logger.console_log(config,"forecast","info","Local date: " + local_date_str, False)

            if (config.precip_units == 'metric'): #default response data is standard units
                depthPerHr = round(v * MM_PER_IN / HR_PER_QPF, 4)
            else:    
                depthPerHr = round(v * 1.0 / HR_PER_QPF, 4)

            buffer = config.precip_id + config.spacer + local_date_str + config.spacer + str(depthPerHr) + "\n"
            data += buffer 
        # print(k,v)
    return data
