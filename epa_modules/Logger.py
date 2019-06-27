#Filename:        Logger.py
#Date:            5/25/2017
#Project:         EPA Weather Tool v1.0
#Prepared for:    US EPA Office of Research and Development
#                 National Homeland Security Research Center
#                 Decontamination and Consequences Management Division
#EPA Manager:     Timothy Boe
#Prepared by:     Tetra Tech, Inc. Lafayette, CA
#=======================================================================

import logging
import os
import datetime
import sys


#Adapted from resource: https://docs.python.org/3/howto/logging-cookbook.html

#
#   Logger class handles both writing to log file and console print statements.  Depending on given parameters, output gets routed to correct I/O endpoints
#

class Logger():
    #defined app areas
    root = None
    control = None
    config = None
    historical = None
    forecast = None

    log_dir = './logs'
    system_filename = str(datetime.date.today()) + "T" + str(datetime.datetime.now().time().strftime('%H_%M_%S')) + '_applog.log'
    
    def __init__(self):
        self.root = logging.getLogger('app.root')
        self.control = logging.getLogger('app.control')
        self.config = logging.getLogger('app.config')
        self.historical = logging.getLogger('app.historical')
        self.forecast = logging.getLogger('app.forecast')

    def init_logging_file_writer(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        completeName = os.path.join(self.log_dir, self.system_filename)    
        logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=completeName,
                        filemode='w')

#
#   controls logging and print functions.
#   1. print takes no source or msg type parameters
#   2. Verbose prints all messages
#   3. Logging records all msg types with appropriate area label 
#
    def console_log(self,config,source,msg_type,msg,exit):
        if config.verbose or source == None or source == "": #print to console
            print(msg)
        if config.logging:
            if source == None or source == "":
                    config.logger.root.info(msg) #log the print message
            else:    
                if source == 'config':
                    if msg_type == 'info':
                        config.logger.config.info(msg)
                    elif msg_type == 'error':
                        config.logger.config.error(msg)
                elif source == 'control':
                    if msg_type == 'info':
                        config.logger.control.info(msg)
                    elif msg_type == 'error':
                        config.logger.control.error(msg)
                elif source == 'historical':
                    if msg_type == 'info':
                        config.logger.historical.info(msg)
                    elif msg_type == 'error':
                        config.logger.historical.error(msg)
                elif source == 'forecast':
                    if msg_type == 'info':
                        config.logger.forecast.info(msg)
                    elif msg_type == 'error':
                        config.logger.forecast.error(msg)
        if exit:
            sys.exit("\nERROR: " + msg)

class MyFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level
