from datetime import timezone, timedelta
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta



def xes_compute_min_max_time(xes_log): 
    """
    Computes min and max times for an XES log
    input: xes_log A PM4PY XES Log object
    output: min_time Timestamp, max_time Timestamp
    """


    if set(["meta_time:log_start_time", "meta_time:log_end_time"]).issubset(xes_log.attributes.keys()):
            min_time = xes_log.attributes["meta_time:log_start_time"]
            max_time = xes_log.attributes["meta_time:log_end_time"]
    else: 
    
        min_times = []
        max_times = []


    
        for trace in xes_log: 
            timestamps = [event["time:timestamp"] for event in trace]
            min_times.append(min(timestamps))
            max_times.append(max(timestamps))

        min_time =  min(min_times)
        max_time =  max(max_times)

    
    return min_time, max_time



def datetime_floor(date_time_obj, freq = 'H'): 
    """
    Computes the floor value of a date_time_obj
    input date_time_obj, the freq, to floor to. 
    output floor date_time_obj
    """
    
    if date_time_obj.tzinfo is not None:
        date_time_obj = (date_time_obj + date_time_obj.utcoffset()).replace(tzinfo = None)
    
    if freq == "H": 
        
        date = dt.min.replace(year = date_time_obj.year, month = date_time_obj.month, day = date_time_obj.day, hour = date_time_obj.hour) 
        
    elif freq == "D":
        
        date = dt.min.replace(year = date_time_obj.year, month = date_time_obj.month, day = date_time_obj.day) 
          
    elif freq == "M":
        
        date = dt.min.replace(year = date_time_obj.year, month = date_time_obj.month) 
        
    elif freq == "Y":
        
        date = dt.min.replace(year = date_time_obj.year) 
    
    return date.replace(tzinfo = timezone.utc)

def datetime_ceil(date_time_obj, freq = 'H'): 
    """
    Computes the ceil value of a date_time_obj
    input date_time_obj, the freq, to ceil to. 
    output ceiled date_time_obj
    """
    
    if freq == "H": 
        
        date = datetime_floor(date_time_obj, "H") + relativedelta(hours = 1, seconds = -1)
        
    elif freq == "D":
        
        date = datetime_floor(date_time_obj, "D") + relativedelta(days = 1, seconds = -1)
        
    elif freq == "M":
        
        date = datetime_floor(date_time_obj, "M") + relativedelta(months = 1, seconds = -1)
        
    elif freq == "Y":
        
        date =  datetime_floor(date_time_obj, "Y") + relativedelta(years = 1, seconds = -1)
        
    return date.replace(tzinfo = timezone.utc)






