import pytz

from datetime import datetime
from datetime import timedelta
from pytz import timezone
from extension_modules.dateutil.tz import tzutc, tzlocal, tz

def dateAdd1Day( date_str ):
    # Add one day to date string using timedelta, return new date string
    tokens = date_str.split("-")
    date = datetime(int(tokens[0]),int(tokens[1]),int(tokens[2])) 
    delta = timedelta(days=1)
    nextDate = date + delta
    nextDateStr = str(nextDate.date())
    return nextDateStr

def subtract_hours( datetime, hr ):
    # subtract specified hours to datetime, return new datetime
    datetime1 = datetime - timedelta(hours=hr)
    return datetime1

def add_hours( datetime, hr ):
    # Add specified hours to datetime, return new datetime
    datetime1 = datetime + timedelta(hours=hr)
    return datetime1

def convert_datestr_timestr_to_DateTime(config, date_str, time_str):
    # Return a datetime object from date and time strings
    tokens = date_str.split("-")
    utc_date = datetime(int(tokens[0]),int(tokens[1]),int(tokens[2]),int(time_str.replace("Z","")),0,0,0) #create  datetime obj
    return utc_date

def convert_datetime_to_datestr( datetimeObj ):
    # Return extracted date string from datetime 
    date_str = datetimeObj.strftime('%Y')+'-'+ datetimeObj.strftime('%m')+'-'+ datetimeObj.strftime('%d')
    return date_str

def convert_datetime_to_hourstr( datetimeObj ):
    # Return extracted 24 hour string with leading zero from datetime 
    hour_str = datetimeObj.strftime('%H')
    return hour_str

def convert_datestr_timestr_to_datetimestr(config, date_str, time_str):
    # Using date and time strings, return date string
    tokens = date_str.split("-")
    #                      year            month           day            hr,min,sec
    local_date = datetime(int(tokens[0]),int(tokens[1]),int(tokens[2]),int(time_str.replace("Z","")),0,0) #create datetime obj
    local_date_str = str(local_date.year) + config.spacer + str(local_date.month) + config.spacer + str(local_date.day) + config.spacer + str(local_date.hour)  
    return local_date_str


def convert_utc_to_local(config, date_str, time_str):
    tokens = date_str.split("-")
    utc_date = datetime(int(tokens[0]),int(tokens[1]),int(tokens[2]),int(time_str.replace("Z","")),0,0,0,tzinfo=tz.tzutc()) #create utc aware datetime obj
    local_date = utc_date.astimezone(config.timezone)
    local_date_str = str(local_date.year) + config.spacer + str(local_date.month) + config.spacer + str(local_date.day) + config.spacer + str(local_date.hour)  
    return local_date_str

def convert_local_to_utc(config,date_str, datatype):
    utc_date = None
    utc_date_str = None

    if(datatype == 1):
        tokens = date_str.split(":")
        date_time = tokens[0].split("T")
        date_tokens = date_time[0].split("-")
        
        if(config.date_restrict == False or config.hour_restrict == False):
            date_time[1] = "0"
            config.logger.console_log(config,None,None,"Date Conversion - ignoring time constraint...", False)
        
        config.logger.console_log(config,None,None,"date tokens: " + date_tokens[0] + "/" + date_tokens[1] + "/" +date_tokens[2],False)
        config.logger.console_log(config,None,None,"hour: " + date_time[1],False)
        #local_date = datetime(int(date_tokens[0]),int(date_tokens[1]),int(date_tokens[2]),int(hr),0,0,0,tzinfo=tz.tzlocal()) #create local aware datetime obj
        #local_date = datetime(int(date_tokens[2]),int(date_tokens[0]),int(date_tokens[1]),int(date_time[1]),0,0,0,tzinfo=tz.tzlocal()) #create local aware datetime obj
        # create timezone aware datetime using timezone from config
        local_date = config.timezone.localize(datetime(int(date_tokens[2]),int(date_tokens[0]),int(date_tokens[1]),int(date_time[1]), 0, 0))
        # convert to UTC timezone
        utc_date = local_date.astimezone(tz.tzutc())

        #config.logger.console_log(config,None,None,"local date: "+ date_time[0] + "T" + date_time[1],False)
        config.logger.console_log(config,None,None,"local date: "+ str(local_date),False)
        
        
    elif(datatype == 2):
        date_time = date_str.split("T")
        date_tokens = date_time[0].split("-")  
        # print("tokens: " + tokens[0] + " " + tokens[1] + " "  + day_time[0])
        #tz_local = tz.tzlocal() #from OS
        tz_utc = tz.tzutc()

        if(config.date_restrict == False or config.hour_restrict == False):
            date_time[1] = "0"
            config.logger.console_log(config,None,None,"Date restrict or hour restrict off, ignoring time constraint...", False)

        config.logger.console_log(config,None,None,"date tokens: " + date_tokens[0] + "/" + date_tokens[1] + "/" + date_tokens[2],False)
        config.logger.console_log(config,None,None,"hour: " + date_time[1],False)

        #local_date = datetime(int(tokens[0]),int(tokens[1]),int(day_time[0]),0,0,0,0,tzinfo=tz_local)
        #local_date = datetime(int(date_tokens[0]),int(date_tokens[1]),int(date_tokens[2]),int(date_time[1]),0,0,0,tzinfo=tz_local)
        #local_date = datetime(int(date_tokens[2]),int(date_tokens[0]),int(date_tokens[1]),int(date_time[1]),0,0,0,tzinfo=tz_local)
        # create timezone aware datetime using timezone from config
        local_date = config.timezone.localize(datetime(int(date_tokens[2]),int(date_tokens[0]),int(date_tokens[1]),int(date_time[1]), 0, 0))
        # convert to UTC timezone
        utc_date = local_date.astimezone(tz_utc)
        
        config.logger.console_log(config,None,None,"local date: " + str(local_date),False)
        
    utc_date_str = str(utc_date.year)
    if (utc_date.month < 10):
        utc_date_str += "-0" + str(utc_date.month)
    else:
        utc_date_str += "-" + str(utc_date.month)

    if (utc_date.day < 10):
        utc_date_str += "-0" + str(utc_date.day)
    else:
        utc_date_str += "-" + str(utc_date.day)

    if(utc_date.hour < 10):
        utc_date_str += "T0" + str(utc_date.hour)
    else:
        utc_date_str += "T" + str(utc_date.hour)

    config.logger.console_log(config,None,None,"utc_date: "+ utc_date_str, False)
    
    return utc_date_str