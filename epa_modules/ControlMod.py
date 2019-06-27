#Filename:        ControlMod.py
#Date:            5/25/2017
#Project:         EPA Weather Tool v1.0
#Prepared for:    US EPA Office of Research and Development
#                 National Homeland Security Research Center
#                 Decontamination and Consequences Management Division
#EPA Manager:     Timothy Boe
#Prepared by:     Tetra Tech, Inc. Lafayette, CA
#=======================================================================
import sys
import epa_modules
import os.path
import numbers
import argparse
import datetime
import pdb
import re

from epa_modules import ConfigMod
from epa_modules import ErrorHandler
from epa_modules import HistoricalMod
from epa_modules import ForecastMod
from datetime import datetime
from pytz import timezone
from timezonefinder import TimezoneFinder


class ControlMod():
    
    # mode = 'Default' #Interactive Default mode
    loop = None
   
    def __init__(self):
        self = self

#
# Description: Takes in user input.  Processes one request at a time to the output directory specified in config  
#
    def interactive_prompt(self,config):
        config.logger.console_log(config,"control","info","Interactive Mode",False)
        #Get coordinate input
        
        while True: 
            try:
                strIn = str(input("Please enter the coordinates (lat, long) for a location separated by a comma. \n(e.g. 33.9375,86.9375): \n")).replace(" ","")
                
                if(on_exit(config,strIn) == True):
                    break

                temp = strIn.split(",")            
                
                #check number of args
                if len(temp) < 2 or len(temp) > 2:
                    raise ErrorHandler.Error("\nExpected 2 coordinate paramaters, but received ", str(len(temp)))
                
                config.lat_lon_coord = ["",""]
            
                #set latitude
                config.lat_lon_coord[0] = float(temp[0])
            
                #set longitude
                if(float(temp[1]) > 0):
                    config.lat_lon_coord[1] = (-1)*float(temp[1])
                else:
                    config.lat_lon_coord[1] = float(temp[1])
                
                #Check range
                if(config.lat_lon_coord[0] > 90 or config.lat_lon_coord[0] < -90) or (config.lat_lon_coord[1] > 180 or config.lat_lon_coord[1] < -180):
                    raise ErrorHandler.Error(" Invalid coordinate values")

                print("\nLatitude: ",config.lat_lon_coord[0])
                print("Longitude: ",config.lat_lon_coord[1])
                config.valid = True
                break

            except TypeError:
                print("\nError: Incorrect number of arguments\n")
            except ErrorHandler.Error as e:
                print ("\nError: Invalid input." + e.value + "\n")
            except ValueError:
                print("\nError: Parameters were not valid numbers")

        #get timezone
        if(config.valid):
            config = get_timezone(config)     
            print("\nTimezone: ",config.tz_label)
        
        #Get date range
        if(config.valid):
            config = get_date_range(config)    
        
        #Get/check for hour range
        if(config.valid):
            config = get_hour_range(config)
        
        #Get/check for precip_id
        if(config.valid):
            config = get_precip_id(config)    
        
        #Get filename input
        if(config.valid):
            config = get_filename_input(config)   
        
        #Run routine
        if(config.valid):
            run_routine(config)
            config.lat_lon_coord = None
        else:
            printCancelMsg(config.valid)

#
# Automates processing in batch mode  
#   
    def batch_mode_processor(self,config):
        config.logger.console_log(config,"control","info","Process started, validating input and running routine...", False)
        
        batch_mode_validate_coord(config)
        batch_mode_validate_dates(config)

        if(config.valid):
            run_routine(config)
        else:
            config.logger.console_log(config,"","error","A problem with one of the input parameters was encountered, request has been aborted",False)
    def print_data_type(self, config):
        if(config.data_type == 1):  
            print("\nData Access Type: Forecast\n")
        else:
            print("\nData Access Type: Historical\n")

        
#
#Private/Local Module Functions
#
def batch_mode_validate_coord(config):
    try:
        config.logger.console_log(config,"control","info","Validating Latitude and Longitude...", False)

        config.lat_lon_coord[0] = float(config.lat_lon_coord[0])
        if(float(config.lat_lon_coord[1]) > 0):
            config.lat_lon_coord[1] = (-1)*float(config.lat_lon_coord[1])
        else:
            config.lat_lon_coord[1] = float(config.lat_lon_coord[1])
                    
        coord_length = len(config.lat_lon_coord)
                    
        if(config.lat_lon_coord[0] > 90 or config.lat_lon_coord[0] < -90) or (config.lat_lon_coord[1] > 180 or config.lat_lon_coord[1] < -180):
            raise ErrorHandler.Error(" Invalid coordinate values")

        #check number of args
        if coord_length < 2 or coord_length > 2:
            raise ErrorHandler.Error(" Expected 2 paramaters, but received " + str(coord_length))
        else:
            
            config.logger.console_log(config,"control","info","Latitude: " + str(config.lat_lon_coord[0]), False)
            config.logger.console_log(config,"control","info","Longitude: " + str(config.lat_lon_coord[1]), False)
            config = detect_timezone(config)
                    
    except ErrorHandler.Error as e:
        config.logger.console_log(config,"control","error","Invalid input." + e.value, True)
    except ValueError:
        config.logger.console_log(config,"control","error","Coordinate parameters were invalid",True)
       

def batch_mode_validate_dates(config):
   
    try:    
        start_date = (datetime.strptime(config.dates[0], '%m-%d-%Y')).isoformat()
        end_date = (datetime.strptime(config.dates[1], '%m-%d-%Y')).isoformat()
       
        now = (datetime.now()).isoformat()
                                
        #Validate dates
        config.logger.console_log(config,"control","info", "Validating Start and End Dates...", False)
        config.logger.console_log(config,None,None,"Now: " + now, False)

        if(config.data_type == 1):
            if start_date < now or end_date < now:              
                raise ErrorHandler.Error("dates must be after the current date")
            
            if start_date > end_date:
                raise ErrorHandler.Error("start date must before End Date")
            else:
                #config.dates = [str(config.dates[0])+"T00",str(config.dates[1])+"T00"]
                config.dates = [str(config.dates[0])+"T"+ config.hours[0],str(config.dates[1])+"T"+config.hours[1]]
                config.logger.console_log(config, "control", "info", "Start Date: " + config.dates[0], False)
                config.logger.console_log(config, "control", "info", "End Date: " +  config.dates[1], False)
                                
        elif(config.data_type == 2):
            if start_date > now or end_date > now:
                raise ErrorHandler.Error("dates must be before current date")
            
            if start_date > end_date:
                raise ErrorHandler.Error("start date must be before End Date")
            else:               
                #config.dates = [str(config.dates[0])+"T00",str(config.dates[1])+"T00"]
                config.dates = [str(config.dates[0])+"T"+config.hours[0],str(config.dates[1])+"T"+config.hours[1]]
                config.logger.console_log(config, "control", "info", "Start Date: " + config.dates[0], False)
                config.logger.console_log(config, "control", "info", "End Date: " +  config.dates[1], False)
                
                                                            
    except ErrorHandler.Error as e:
        config.logger.console_log(config,"control","error","Invalid Input, " + e.value, True)
    #except ValueError: 
     #   config.logger.console_log(config,"control","error","Date parameters were not valid", True)
   
#
# Interactive function for reading in date ranges
#     
'''def get_date_range(config):
        
    while (True):
        try:
            if(config.data_type == 1):
                dateinput = str(input("\nPlease enter a valid Future Start and End date of format MM-DD-YYYY separated by a comma: ")).replace(" ","")
            elif(config.data_type == 2):
                dateinput = str(input("\nPlease enter valid Historical Start and End date of format MM-DD-YYYY separated by a comma. \n e.g. 2010-1-1,2010-12-1: ")).replace(" ","")
            
            if dateinput == "exit":
                config.lat_lon_coord = None
                config.dates = ["",""]
                config.valid = False
                break
            
            dates_str = dateinput.split(",")
            
            if len(dates_str) < 2 or len(dates_str) > 2:
                raise ErrorHandler.Error("Expected 2 date parameters but received ", str(len(dates_str)))                
                
            #start_date = (datetime.strptime(dates_str[0], '%Y-%m-%d')).isoformat()
            #end_date = (datetime.strptime(dates_str[1], '%Y-%m-%d')).isoformat()

            start_date = (datetime.strptime(dates_str[0], '%m-%d-%Y')).isoformat()
            end_date = (datetime.strptime(dates_str[1], '%m-%d-%Y')).isoformat()
                        
            now = (datetime.now()).isoformat()
                            
            #Validate dates
            if(config.data_type == 1):
                if start_date < now or end_date < now:
                    raise ErrorHandler.Error("dates must be after the current date")
                if start_date > end_date:
                    raise ErrorHandler.Error("start date must before End Date")
                else:
                    config.dates[0] = str(start_date[:-6]) #Trim second and hour markers         
                    config.dates[1] = str(end_date[:-6])
                    print("\nStart Date: ", config.dates[0])
                    print("End Date: ", config.dates[1])
                    config.valid = True
                    break
            
            elif(config.data_type == 2):
                if start_date > now or end_date > now:
                    raise ErrorHandler.Error("dates must be before current date")
                if start_date > end_date:
                    raise ErrorHandler.Error("start date must be before End Date")
                else:
                    config.dates[0] = str(start_date[:-6]) #Trim second and hour markers         
                    config.dates[1] = str(end_date[:-6])
                    print("\nStart Date: ", config.dates[0])
                    print("End Date: ", config.dates[1])
                    config.valid = True
                    break
                                                        
        except ValueError:
            print ("\nError: Not a valid date. \n")
        except TypeError:
            print("\nError: Incorrect number of arguments were given\n")
        except ErrorHandler.Error as e:
            print("\nError: Invalid Input, " + e.value + " \n")
            config.dates = ["",""]
    
    return config'''

def get_date_range(config):
    
    start_date = None
    end_date = None
    now = datetime.now().isoformat()

    while (True):
        try:
            if(config.data_type == 1):
                date1 = str(input("\nPlease enter a valid Future Start Date of format MM-DD-YYYY: ")).replace(" ","")
                if(on_exit(config,date1) == True):
                    break
                start_date = (datetime.strptime(date1, '%m-%d-%Y')).isoformat()

                date2 = str(input("Please ender a valid Future End Date of the format MM-DD-YYYY:")).replace(" ","")
                if(on_exit(config,date2) == True):
                    break
                end_date = (datetime.strptime(date2, '%m-%d-%Y')).isoformat()

            elif(config.data_type == 2):
                date1 = str(input("\nPlease enter a valid Historical Start Date of format MM-DD-YYYY. \n e.g. 01-01-2010: ")).replace(" ","")
                if(on_exit(config,date1) == True):
                    break
                start_date = (datetime.strptime(date1, '%m-%d-%Y')).isoformat()

                date2 = str(input("Please ender a valid Historical End Date of the format MM-DD-YYYY:")).replace(" ","")
                if(on_exit(config,date2) == True):
                    break
                end_date = (datetime.strptime(date2, '%m-%d-%Y')).isoformat()
                            
            #start_date = (datetime.strptime(config.dates[0], '%m-%d-%Y')).isoformat()
            #end_date = (datetime.strptime(config.dates[1], '%m-%d-%Y')).isoformat()
            
            #config.logger.console_log(config,None,None,"start_date datetime: " + str(start_date), False)
            #config.logger.console_log(config,None,None,"end_date datetime: " + str(end_date), False)
            

            #Validate dates for Forecast
            if(config.data_type == 1):
                if start_date < now or end_date < now:
                    raise ErrorHandler.Error("Dates must be after the current date --> " + now)
                if start_date > end_date:
                    raise ErrorHandler.Error("Start date must before End Date --> " + end_date)
                else:
                   # config.dates[0] = str(start_date[:-6]) #Trim second and hour markers         
                   # config.dates[1] = str(end_date[:-6])
                    config.dates = [date1 + "T00", date2 + "T00"]
                    print("\nStart Date: ", config.dates[0])
                    print("End Date: ", config.dates[1])
                    config.valid = True
                    break

            #Validate dates for Historical
            elif(config.data_type == 2):
                if start_date > now or end_date > now:
                    raise ErrorHandler.Error("Dates must be before current date --> " + now)
                if start_date > end_date:
                    raise ErrorHandler.Error("Start date must be before End Date --> " + end_date)
                else:
                   # config.dates[0] = str(start_date[:-6]) #Trim second and hour markers         
                   # config.dates[1] = str(end_date[:-6])
                    config.dates = [date1 + "T00", date2 + "T00"]
                    print("\nStart Date: ", config.dates[0])
                    print("End Date: ", config.dates[1])
                    config.valid = True
                    break
                                                        
        except ValueError:
            print ("\nError: Not a valid date. \n")
        except TypeError:
            print("\nError: Incorrect number of arguments were given\n")
        except ErrorHandler.Error as e:
            print("\nError: Invalid Input, " + e.value + " \n")
            config.dates = ["",""]
    
    return config

   
#
#   Interactive function for reading in timezone
# 
def get_timezone(config):
    if(config.auto_timezone):
        config = detect_timezone(config)
        if(config.timezone == None):
            config.logger.console_log(config,None,None,"Auto detect could not determine timezone...",False)
            config = timezone_ask_loop(config)
    else:
        config = timezone_ask_loop(config)
    return config

def detect_timezone(config):
    try:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=config.lat_lon_coord[1],lat=config.lat_lon_coord[0])
        if(timezone_str == None):
            timezone_str = tf.certain_timezone_at(lng=config.lat_lon_coord[1],lat=config.lat_lon_coord[0])
        elif(timezone_str == None):
            timezone_str = tf.closest_timezone_at(lng=config.lat_lon_coord[1],lat=config.lat_lon_coord[0])     
            
        if(timezone_str != None):
            config.timezone = timezone(timezone_str)
            config.tz_label = config.timezone
            config.valid = True
            config.logger.console_log(config,"control","info","timezone detected >> " + timezone_str, False)
        else:
            if(config.mode == "batch"):
                config.logger.console_log(config,"control","error","timezone could not be auto-detected, given lat long may be offshore", True) #exit on auto detect failure
            else:
                config.logger.console_log(config,"control","error","timezone could not be auto-detected, given lat long may be offshore", False)
    except:
        config.logger.console_log(config,"control","error","Timezone detect encoutered an error",False)
    return config

def timezone_ask_loop(config):
    while True:
        try:
            timezone_str = str(input("\nPlease enter a valid timezone id: \n")).replace(" ","")
            if(on_exit(config,timezone_str) == True):
                break
            #if(timezone_str == 'exit'):
            #    config.valid = False
            #   break
            config.timezone = timezone(timezone_str)
            config.tz_label = config.timezone
            config.valid = True
            break
        
        except:
            print("\nTimezone entered id was invalid.")
    return config

#
#   Option Specified - Interactice function for checking for precip_id
#
def get_precip_id(config):
    if(config.precip_id_prompt):
        strinput = str(input("\nPlease enter a name for the Precip_id: ")).replace(" ","")
        config.precip_id = strinput
    return config

#
#   Option Specified - Interactive function for checking for hour range inclusion
#
def get_hour_range(config):
    if(config.hour_restrict == True):
        
        start_hr = ""
        end_hr = ""
        
        while True:
            try:
                strinput = str(input("\nPlease enter the Start and End Hours in 24 hour Format (range of 0-23), separated by a comma: ")).replace(" ","")
                
                if(on_exit(config,strinput) == True):
                    break
                
                temp = strinput.split(",")

                #check number of args
                if len(temp) < 2 or len(temp) > 2:
                    raise ErrorHandler.Error("\nExpected 2 paramaters, but received ", str(len(temp)))
                else:
                    config.hours[0] = int(temp[0])
                    config.hours[1] = int(temp[1])
                    
                    if(0 < config.hours[0] > 23) or (0 < config.hours[1] > 23):
                        raise ErrorHandler.Error("Hours must be between 0 and 23.")
                    
                    if(config.hours[0] < 10):
                        start_hr = "0" + str(config.hours[0])
                    else:
                        start_hr = str(config.hours[0])
                    
                    if(config.hours[1] < 10):
                        end_hr = "0" + str(config.hours[1])
                    else:
                        end_hr = str(config.hours[1])

                    config.logger.console_log(config,None,"info","\nStarting Hour: " + start_hr,False)
                    config.logger.console_log(config,None,"info","Ending Hour: " + end_hr,False)

                    config.dates[0] = (config.dates[0][:-2]) + start_hr
                    config.dates[1] = (config.dates[1][:-2]) + end_hr

                    config.logger.console_log(config,None,"info","\n** Updated DateTime **\nStart DateTime: " + config.dates[0],False)
                    config.logger.console_log(config,None,"info","End DateTime: " + config.dates[1],False)                    
                    break

            except ValueError:
                print ("\nError: Not a valid input, please enter an integer. \n")
            except TypeError:
                print("\nError: Incorrect number of arguments were given\n")
            except ErrorHandler.Error as e:
                print("\nError: Invalid Input, " + e.value + " \n") 
            
    return config
#
#   Interactive function for reading input filename
# 
def get_filename_input(config):
    while True:    
        try:
            fnameinput = str(input("\nPlease enter a name for the output file (e.g. WeatherData): \n")).replace(" ","") 
            if(on_exit(config,fnameinput) == True):
                break 
            
            config.fname = fnameinput + config.file_ext
            
            if any((c in config.illegal_chars) for c in config.fname):
                raise ErrorHandler.Error( "Illegal character in filename. Please avoid the following characters in the file name " + str(config.illegal_chars))
            else:
                print("Output filename: " + config.fname)
                config.valid = True
                break
        except ErrorHandler.Error as e:
            print ("\nError: " + e.value + "\n")
    return config     

def run_routine(config):
    config.print_stats()
   
    data = ""
    if(config.data_type == 1): #Access Forecast data provider
        config = ForecastMod.build_request_obj(config)
        print("\nWorking, Please Wait...\n")
        data = ForecastMod.get_forecast_weather_data(config)
        
    elif(config.data_type == 2): #Access Historical data provider
        config = HistoricalMod.convert_grid(config)
        config = HistoricalMod.build_request_obj(config)
        print("\nWorking, Please Wait...\n")
        data = HistoricalMod.get_historical_weather_data(config)
    
   
           
    #Write data out to file
    if (data != None):
        #Check Additional Data Filters
        if (config.date_restrict):
            data = filter_dates(config,data)    
        if not data: #if data is empty string, add message to file
            data = "No precipitation data was available for the data range: " + config.dates[0] + " - " + config.dates[1] 
        config.set_request_info_str()
        write_data_to_output_dir(config,data)
    else:
        config.logger.console_log(config,None,None,"Response returned no data.  Data file write was cancelled.",False)

def filter_dates(config,data):
    buffer = ""
    date_filtered_data = ""
    config.logger.console_log(config,None,None,"\nRunning Strict Date and Time Filter...\n",False) 
    s_tokens = re.split(r'[-T]',config.dates[0])
    e_tokens = re.split(r'[-T]',config.dates[1])
    
    print("start date:" + config.dates[0])

#    start_date = datetime(int(s_tokens[0]),int(s_tokens[1]),int(s_tokens[2]),int(s_tokens[3])).isoformat() #year,month,day,hour
#    end_date = datetime(int(e_tokens[0]),int(e_tokens[1]),int(e_tokens[2]),int(e_tokens[3])).isoformat()
    if(config.hour_restrict == False):
        s_tokens[3] = "0"
        e_tokens[3] = "0"
        config.logger.console_log(config,None,None,"\nTime Constraint ignored...\n",False)

    start_date = datetime(int(s_tokens[2]),int(s_tokens[0]),int(s_tokens[1]),int(s_tokens[3])).isoformat() #year,month,day,hour
    end_date = datetime(int(e_tokens[2]),int(e_tokens[0]),int(e_tokens[1]),int(e_tokens[3])).isoformat()
    
       
    config.logger.console_log(config,None,None,"Strict Date Range: " + str(start_date) + " -- " + str(end_date),False )
    
    for line in data.splitlines():
        tokens = line.split(config.spacer) 
        item_date = datetime(int(tokens[1]),int(tokens[2]),int(tokens[3]),int(tokens[4])).isoformat()
        
        config.logger.console_log(config,None,None,'item_date: ' + str(item_date),False)
              
        #Add to buffer if dates are within strict range of start and end dates, hour is included
        if (start_date <= item_date <= end_date):
            buffer = line + "\n"
            date_filtered_data += buffer
            config.logger.console_log(config,None,None,"+ Date Accepted",False)
        else:
            config.logger.console_log(config,None,None,"-> Date Rejected",False)

    print("\nFiltered data: \n")    
    for f_line in date_filtered_data.splitlines():
        print(f_line)
    
    data = date_filtered_data
    return data


def write_data_to_output_dir(config, data):
    try:
        config.logger.console_log(config,"control","info","Writing data to output file...", False)
        
        completeName = os.path.join(config.outdir, config.fname)
        fileObj = open(completeName,"w")
        fileObj.write(data)
        fileObj.close()
        config.logger.console_log(config,None,None,"\nDATA: \n" + data + "\n",False) #print out to console
        config.logger.console_log(config,None,None,'SUCCESS! A new file has been created named: ' + config.fname + "\n", False)
        config.logger.console_log(config,None,None,"Path to File: " + config.outdir, False)
    
    except PermissionError:
        config.logger.console_log(config,"control","error", "Permission Denied. The Folder or Path has denied write access.  File write has been canceled.", True)

def printCancelMsg(valid):
    if(valid == False):
        print("\nUser canceled action, exiting loop...\n")
    else:
        print("\nAn issue with one of the input parameters caused the request to be aborted")

def on_exit(config,input):
    if input == "exit":
        config.lat_lon_coord = None
        config.dates = ["",""]
        config.hours = [None,None]
        config.valid = False
        return True








