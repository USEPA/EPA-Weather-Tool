import epa_modules
import os.path
import argparse
import sys

from epa_modules import *

#init Config and Control module objects
Config = epa_modules.ConfigMod.ConfigMod()
Control = epa_modules.ControlMod.ControlMod()

print("mode: ", Config.mode)

if(Config.bootstrap): #Bootstrap for testing purposes, bypasses interactive prompts
    # Config.mode = "bootstrap forecast"
    # Config.data_type = 1
    # Config.dates = ["2016-12-8","2016-12-29"]
    # Config.lat_lon_coord = [33,-86]
    # Config.fname = "test_forecast"  
    # Config.bootstrap_file = '/forecast_sample.xml' #NOTE: Specify stream or file for XML data tree parse

    Config.mode = "bootstrap historical"
    Config.data_type = 2
    Config.dates = ["2010-12-01T00","2010-12-30T00"]
    Config.lat_lon_coord = [33,-86]
    Config.fname = "bootstrap_historical"  
   
    ControlMod.run_routine(Config)

#Mode check => Flow Control
if (Config.mode == 'default'):
    print("\n********************************************************************************\n" +
            "                               EPA Weather Tool \n\n"
            "                               " + Config.ver + "       \n" +
            "\n********************************************************************************\n")
    Control.loop = True

    while Control.loop == True:
        #Check Data Type Access
        
        if (Config.data_type == None):           
            while True:
                try:
                    ans = input("\nPlease select the type of Data to access, Forecast = 1, Historical = 2.  Type 'exit' to exit the application: ")               
                    if ans == "exit":
                        sys.exit()
                    else:
                        num = int(ans)
                        if num < 1 or num > 2:
                            raise ErrorHandler.Error("Unexpected number value, '" + str(num) +"'.  input must be either 1 or 2")
                        else:
                            Config.data_type = num
                            break
                except ErrorHandler.Error as e:
                    print ("\nError: " + e.value + "\n")
                except ValueError:
                    print("\nError: Unexpected string value, input must be an integer 1 or 2")
               
        Control.print_data_type(Config)       
        
        Config.reset_attributes() #clear stored config attributes for new request  
        Control.interactive_prompt(Config) 
        
        ans = input("\nWould you like to process another request? y/n or t (toggle data access type) : ").lower()
        if ans == 'n' or ans == "exit":
            break #exit program
        elif ans == "t":
            Config.data_type = None           
        else:
            while ans !='y' and ans !='n' and ans != 't' and ans != "exit":
                ans = input("\nSorry invalid command.\n\nWould you like to process another request? y/n or t (toggle data access type) : ").lower()
                if ans == 'n' or ans == "exit":
                    Control.loop = False 
                    break #exit program
                elif ans == "t":
                    Config.data_type = None
                    
        
elif (Config.mode == 'batch'):
    Control.batch_mode_processor(Config)

else:
    sys.exit("Program Exited, Ran Bootstrap")
