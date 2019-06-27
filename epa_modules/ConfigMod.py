#Filename:        ConfigMod.py
#Date:            5/25/2017
#Project:         EPA Weather Tool v1.0
#Prepared for:    US EPA Office of Research and Development
#                 National Homeland Security Research Center
#                 Decontamination and Consequences Management Division
#EPA Manager:     Timothy Boe
#Prepared by:     Tetra Tech, Inc. Lafayette, CA
#=======================================================================

import sys
import configparser
import argparse
import os.path
import datetime
import pytz

from epa_modules import ErrorHandler
from datetime import datetime
from epa_modules import Logger
from pytz import timezone
from extension_modules.dateutil.tz import tzlocal, tz


#Configuration class maintains user settings and variables
#reads config.ini file
class ConfigMod():
    forecast_datasource = None  
    historical_datasource = None
    
    outdir = None
    override_dir = False
    fname = None
    data_format = None
    precip_id = None
    precip_id_prompt = False
    precip_units = None
    date_restrict = False
    hour_restrict = False
    lat_lon_coord = ["",""]
    x_y_grid = ["",""]
    hours = [None,None]
    file_ext = None #TODO: Use array to include multiple output formats
    verbose = None
    logging = None
    illegal_chars = None
    mode = 'default'
    ver = 'v1.0, April 2018'
    data_type = None
    dates = ["",""]
    http_get = ""
    request_timeout = 0.001
    timezone = None
    auto_timezone = False
    tz_label = None
    valid = False
    spacer = '\t'
    parameter_str = None
    logger = Logger.Logger()

    #quick testing purposes
    bootstrap = False 
    bootstrap_file = None

    def __init__(self):
        
        try:
            self.run_arg_parse()
            
            # Based on sections defined in config.ini
            #  Sections => APIKey, IO_Dir, Options, Extensions
            ConfigParser = configparser.ConfigParser()
            ConfigParser.read('config.ini')
        
            map = self.get_fields(ConfigParser)

            self.forecast_datasource = map['forecast_datasource']
            self.historical_datasource = map ['historical_datasource']
            
            if(self.override_dir == False):
                if(os.path.isdir(map['out_dir'])):
                    self.outdir = map['out_dir']
                else:
                    raise ErrorHandler.Error("The output directory path '" + map['out_dir'] + "' is incorrect or does not exist.  Please ensure the default path has been configure in the config.ini file")
            
            self.file_ext = "." + map['file_ext']
            
            if self.fname != None:
                self.fname = self.fname + self.file_ext 
            
            self.data_format = map['data_format']
            
            if self.data_format != 'DSI-3240':
                raise ErrorHandler.Error("Unrecognized file format.  Please refer to the User's Manual for acceptable file formats")
            
            #Interactive settings for precip_id, batch settings set in run_arg_parse 
            if self.precip_id == None:
                self.precip_id = map['precip_id']
            
            if(self.precip_id.lower() == 'custom'):
                self.precip_id_prompt = True
                self.precip_id = None
            
            self.precip_units = map['precip_units'] 
            
            if self.precip_units != 'metric' and self.precip_units != 'standard':
                raise ErrorHandler.Error("Invalid precip units. Please specify either metric or standard units")

            self.illegal_chars = set('#%&{}\<>*?/$!'"@+`|=")

            if(self.timezone == None):
            #initialize timezone based on default option value
                try:
                    if(map['timezone'] == "auto"):
                        self.auto_timezone = True
                        self.logger.console_log(self,None,None,"Auto Detect Timezone: ON",False)
                    else:
                        if (map['timezone'] == "None"): #Trigger prompt during interactive mode
                            self.timezone = None
                            self.tz_label = None
                        elif (map['timezone'] != None or map['timezone'] != ""): 
                            self.timezone = timezone(str(map['timezone'])) #try given code
                            self.tz_label = self.timezone
                    
                except:
                    raise ErrorHandler.Error("Timezone code is incorrect.  Please see usage for timezone code list.")
            
            if(map['date_restrict'].lower() == 'on'):
                self.date_restrict = True
                self.logger.console_log(self,None,None,"Date Restrict Filter: ON", False)
            else:
                self.logger.console_log(self,None,None,"Date Restrict Filter: OFF", False)            
            
            if(map['hour_restrict'].lower() == 'on'):
                self.hour_restrict = True
                if(self.date_restrict == False):
                    self.hour_restrict = False
                    self.logger.console_log(self,None,None,"Hour Range: OFF", False)
                else:              
                    self.logger.console_log(self,None,None,"Hour Range: ON", False)           
            else:
                self.logger.console_log(self,None,None,"Hour Range: OFF", False)


        except ErrorHandler.Error as e:
            self.logger.console_log(self,None,"error","An unexpected error occurred while processing arguments. " + str(e),True)


    def get_fields(self, ConfigParser):
        dict1 = {}
        sections = ConfigParser.sections()
        for section in sections:
            options = ConfigParser.options(section)
            for option in options:
                try:
                    dict1[option] = ConfigParser.get(section, option)
                    if dict1[option] == -1:
                        DebugPrint("skip: %s" % option)
                except ValueError:
                    print("exception on %s!" % option)
                    dict1[option] = None
        return dict1


    def print_stats(self):
        print('\nOUTPUT >>>')     
        if(self.data_type == 1):
            self.logger.console_log(self,"","info",'Data Access Type: Forecast',False)
        elif(self.data_type == 2):
            self.logger.console_log(self,"","info",'Data Access Type: Historical',False)
        
        self.logger.console_log(self,"","info",'Output Time Series Format:' + self.data_format, False)
        self.logger.console_log(self,"","info",'output dir: ' + self.outdir, False)
        self.logger.console_log(self,"","info",'Filename: '+ str(self.fname), False)
        self.logger.console_log(self,"","info",'Timezone: ' +  str(self.tz_label),False)
        self.logger.console_log(self,"","info",'Precip Units: ' + self.precip_units,False)
        print('\n')


    def run_arg_parse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('dirpath', nargs='?', help='specify a new path to file output directory or default to load config defined path', default=self.outdir)    
        parser.add_argument('params', nargs='?', help='specify the input parameters in [] separated by commas. format: [lat,lon,startdate,enddate,data_access_type,timezone,output_filename]')
        parser.add_argument('-l','--logging',help='turn on logging', action='store_true')
        parser.add_argument('-v','--verbose',help='increase the output verbosity in logs', action='store_true')
        parser.add_argument('-tz', '--timezones', help='list all available timezones', action='store_true')
        parser.add_argument('-a', '--about', help='About information', action='store_true')
       
        args = parser.parse_args()
        
        if args.logging:
            self.logging = True
            self.logger.init_logging_file_writer() #Initialize file writing
            self.logger.console_log(self,None,None,"logging turned on\n",False)
            
        self.logger.console_log(self,None,None,"args received: " + str(args),False)

        if args.verbose:
            self.verbose = True
            if self.logging:
                self.logger.console_log(self,None,None,"verbosity turned on\n",False)
            else:
                print("verbosity turned on\n")

        if args.timezones:           
            if self.logging:
                self.logger.console_log(self,None,None,"Available Timezones" + str(pytz.all_timezones),False)
            else:
                print("Available Timezones" + str(pytz.all_timezones))
            sys.exit()
        
        if args.about:
            about_str = "About Information" +"\n\nEPA Weather Tool " + self.ver + "\n\nPrepared for:\t US EPA Office of Research and Development\n\t\t National Homeland Security Research Center\n\t\t Decontamination and Consequences Management Division"+ "\n\nManager:\t Timothy Boe" +"\n\nPrepared by:\t Tetra Tech, Inc. Lafayette, CA"
            if self.logging:
                self.logger.console_log(self,None,None, about_str,False)
            else:
                print(about_str)
            sys.exit()
            
        if args.dirpath:
            if args.dirpath != self.outdir:
                if(os.path.isdir(args.dirpath)):
                    self.outdir = args.dirpath
                    self.logger.console_log(self,None,None,'output dir: <OVERRIDE> ' + str(self.outdir), False)
                    self.override_dir = True
                elif str(args.dirpath) == 'default':
                    self.logger.console_log(self,None,None,'output dir: <DEFAULT> ' + str(self.outdir), False)
                else:
                    msg = "The output directory path '" + args.dirpath  + "' is incorrect or does not exist"
                    self.logger.console_log(self, "config", "error","The output directory path '" + args.dirpath  + "' is incorrect or does not exist", True)
                    
            
                # Check dataset arguments
                if args.params:
                    param_str = str(args.params).replace(" ","")
                    print("param_str: ",param_str)
                    if "[" in param_str and "]" in param_str:
                        temp1 = param_str.split("[")
                        temp2 = temp1[1].split("]")
                        if(temp2[1] != "" or temp1[0] != ""):
                            self.logger.console_log(self,"config","error","Invalid parameter entry.  Unexpected parameter outside of bracket.", True)
                        else:
                            params_str = str(temp2[0]).replace(" ","")
                            print("params_str: ", params_str)
                            params = params_str.split(',')                  
                            if(len(params) == 10): #(Latitude,Longitude,StartDate,EndDate,StartTime,EndTime,DataType,Timezone,precip_id,Output_Filename)
                                self.data_type = int(params[0])
                                self.lat_lon_coord = [params[1],params[2]]
                                self.dates = [params[3],params[4]]
                                #self.dates = [(datetime.strptime(params[3], '%m-%d-%Y').isoformat()),(datetime.strptime(params[4], '%m-%d-%Y').isoformat())]

                                start_hr = int(params[5])
                                end_hr = int(params[6])
                                
                                str_start = ""
                                str_end = ""

                                if(start_hr < 10):
                                    str_start = "0" + params[5]
                                else:
                                    str_start = str(start_hr)

                                if(end_hr < 10):
                                    str_end = "0" + params[6]
                                else:
                                    str_end = str(end_hr)

                                self.hours = [str_start,str_end]
                               
                               
                                try:
                                    if (params[7] == "auto"):
                                        self.auto_timezone = True
                                    else:    
                                        self.timezone = timezone(str(params[7])) #try given code
                                        self.tz_label = str(self.timezone)
                                except:
                                    self.logger.console_log(self,None,"error","Timezone code is incorrect.  Please see usage for timezone code list.",True)
                                
                                self.precip_id = params[8]
                                self.fname = params[9]
                                self.mode = "batch"
                        
                            else:
                                self.logger.console_log(self,"config","error","Supplied wrong number of parameters", True)
                    else:
                        self.logger.console_log(self,"config","error","Input parameters were entered incorrectly.  Please ensure parameters are in brackets.", True)
        else:
            print('Entering Interactive Mode - Using default output directory')

        
    def set_request_info_str(self):
        self.request_str = str(self.lat_lon_coord[0]) + "," + str(self.lat_lon_coord[1]) + "," + str(self.dates[1]) + "," + str(self.dates[0]) + "," + str(self.fname)
    
    def reset_attributes(self):
        self.lat_lon_coord = ["",""]
        self.x_y_grid = ["",""]
        self.dates = ["",""]
        self.http_get = ""
        self.timezone = None
        self.tzlabel = None
        self.valid = False
        
