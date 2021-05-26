# PM4PY Dependencies
import pandas as pd
from django.conf import settings
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.util import interval_lifecycle
from pm4py.util import xes_constants as xes
from pm4py import format_dataframe
from functools import partial

import group_analysis.datetime_utils as dt_utils
import group_analysis.utils as utils

def get_log_format(file_path):

    """ 
    Function that extracts the file format in lowercase from a valid filepath
    input: file_path str
    output: file_format str
    """

    file_format = file_path.split(".")[-1].lower()

    return file_format


def log_import(file_path, file_format, log_information):
    """ 
    Imports the file using PM4PY functionalitites, formats it in a processable fashion, accoding to the Log information, if it is an CSV
    input: file_path str, file_format str, interval bool
    output: PM4PY default object dependent on Filetype, fromatted in case of csv
            The Set of all trace activities
    """

    activites = set()

    if file_format == "csv":

        # TODO Apply further file integrity check
        log  = pd.read_csv(file_path)

        if log_information["log_type"] == "noninterval": 

            # Format it PM4PY conform
            log  = format_dataframe(log, case_id = log_information["case_id"],
                                               activity_key = log_information["case_concept_name"],
                                               timestamp_key = log_information["timestamp"])

        # Transform the Timestamp to Datetime, and rename the transition:lifecycle 
        elif log_information["log_type"] == "lifecycle":
            
            # Convert the Timestamps to Datetime
            log[log_information["timestamp"]] = pd.to_datetime(log[log_information["timestamp"]], utc = True)

            # Format it PM4PY conform
            log  = format_dataframe(log, case_id=log_information["case_id"],
                                               activity_key=log_information["case_concept_name"],
                                               timestamp_key= log_information["timestamp"])
        
            # Rename the Columns to the XES defaults
            log = log.rename({log_information["lifecycle"] : xes.DEFAULT_TRANSITION_KEY}, axis = 1)
            

        elif log_information["log_type"] == "timestamp":

            # Convert the Timestamps to Datetime
            log[log_information["end_timestamp"]] = pd.to_datetime(log[log_information["end_timestamp"]],  utc = True)
            log[log_information["start_timestamp"]] = pd.to_datetime(log[log_information["start_timestamp"]],  utc = True)

            # Format it PM4PY conform
            log  = format_dataframe(log, case_id=log_information["case_id"],
                                               activity_key=log_information["case_concept_name"],
                                               timestamp_key= log_information["end_timestamp"])
           
            # Rename the Columns to the XES defaults
            log = log.rename({log_information["start_timestamp"] : xes.DEFAULT_START_TIMESTAMP_KEY}, axis = 1)
            activites = set(log[xes.DEFAULT_NAME_KEY].unique())

    # Simply load the log using XES
    elif file_format == "xes": 
        
        log = xes_importer.apply(file_path, parameters = {'show_progress_bar': False})

        for trace in log:
            for event in trace:
                 activites.add(event[log_information["case_concept_name"]])
        
    else:

        #TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")

    return log, activites


def count_group_activities(df, groups): 
    """
    Helper function for CSV grouping, computes the activity count per grouped timeframe
    input: df pd.Dataframe, groups list-like of Groups
    output: pd.Series containing the number of activity per group observed
    """ 

    group_dict = {}
    
    for group in groups: 
        group_dict[group.name] = df[df["concept:name"].isin(group.members)].count()["concept:name"]        
        
    return pd.Series(group_dict)

def csv_create_date_range_frame(log, Groups, parameters = None, freq = 'H'):
    """
    Creates the DateFrame for plotting for csv style data in a pandas dataframe. 
    Allows specifiying of frequency for grouping action of timestamp.
    Only used for Single-Timestamp csv files

    input: log, a PM4PY csv log object, Groups, freq str 
    output: daterange Dataframe used for Plotting
    """
   
    # Prefiltering by Projecting on Group Activites 
    log = log[log[xes.DEFAULT_NAME_KEY].isin(utils.flatten([group.members for group in Groups]))]

    # Create the Dateframe using the count_group_activities helper function
    date_frame = log.groupby(by = pd.Grouper(key = xes.DEFAULT_TIMESTAMP_KEY, freq = freq)).apply(partial(count_group_activities, groups = Groups))
        
    return date_frame

def xes_create_date_range_frame(log, Groups, min_time, max_time, attribute_names, interval_freq = 'H', floor_freq = "D", interval = False):
    
    # Create a DataFrame to fill 
    date_range = pd.date_range(dt_utils.datetime_floor(min_time, "D"), dt_utils.datetime_ceil(max_time, "D"), freq = interval_freq)
    date_frame = pd.DataFrame({group.name:0 for group in Groups}, index = date_range)
    
    for trace in log:

        for event in trace:
            
            # Consider Grouping
            for group in Groups: 
            
                #TODO Replace default Concept Name
                if event[attribute_names["concept:name"]] in group.members:
                    
                    if interval:
                        #TODO Replace default Name
                        date_frame.loc[event[attribute_names["start_timestamp"]]:event[attribute_names["time:timestamp"]], group.name] += 1

                    else:
                        #TODO Replace default Name
                        date_frame.loc[dt_utils.datetime_floor(event[attribute_names["time:timestamp"]], freq = floor_freq), group.name] += 1
                       
    
    #Check for Consecutive strands of 0 at the End (Could be done in Loop instead)
    date_frame = date_frame[date_frame.sum(axis = 1).apply(lambda x: bool(x))]

    return date_frame


def create_plotting_data(log, Groups, file_format, log_information, floor_freq):

    # Stores the Attribut Names for later references, makes renaming attributes inside the XES unnecessary
    attribute_names = {}

    if file_format == "csv":

        # Project the Log onto the Group Activites
        log = log[log[xes.DEFAULT_TRACEID_KEY].isin(utils.flatten([group.members for group in Groups]))]
        
         # Select only the Relevant columns of the Dataframe
        if log_information["log_type"] == "noninterval":
           log = log[["case:concept:name", xes.DEFAULT_TIMESTAMP_KEY, xes.DEFAULT_TRACEID_KEY]]
           return csv_create_date_range_frame(log, Groups, parameters = None, freq = floor_freq)
            
        elif log_information["log_type"] == "lifecycle":

            min_time = log[log[xes.DEFAULT_TRANSITION_KEY] == "start"][xes.DEFAULT_TIMESTAMP_KEY].min() 
            max_time = log[log[xes.DEFAULT_TRANSITION_KEY] == "complete"][xes.DEFAULT_TIMESTAMP_KEY].max() 

            log = log[["case:concept:name", xes.DEFAULT_TIMESTAMP_KEY, xes.DEFAULT_TRACEID_KEY, xes.DEFAULT_TRANSITION_KEY]]
            log = log_converter.apply(log)
            log = interval_lifecycle.to_interval(log)

        elif log_information["log_type"] == "timestamp":

            min_time = log[xes.DEFAULT_START_TIMESTAMP_KEY].min() 
            max_time = log[xes.DEFAULT_TIMESTAMP_KEY].max() 

            log = log[["case:concept:name", xes.DEFAULT_TIMESTAMP_KEY, xes.DEFAULT_TRACEID_KEY, xes.DEFAULT_START_TIMESTAMP_KEY ]]
            
            log = log_converter.apply(log)
        
        attribute_names["start_timestamp"] = xes.DEFAULT_START_TIMESTAMP_KEY
        attribute_names["time:timestamp"] = xes.DEFAULT_TIMESTAMP_KEY
        attribute_names["concept:name"] = xes.DEFAULT_NAME_KEY

        # Convert the Lifecycle Log into an Interval Log using the PM4PY Functionality
        


    # Simply load the log using XES
    elif file_format == "xes": 
   
        min_time, max_time = dt_utils.xes_compute_min_max_time(log, log_information)

        if log_information["log_type"] == "noninterval": 

            # TODO Compute Min and Max Time
            attribute_names["time:timestamp"] = log_information["timestamp"]
            attribute_names["concept:name"] = log_information["case_concept_name"]

            return xes_create_date_range_frame(log, Groups, min_time, max_time, attribute_names, interval_freq = floor_freq, floor_freq = floor_freq,  interval = False)
        
        elif log_information["log_type"] == "lifecycle":

            attribute_names["time:timestamp"] = log_information["timestamp"]
            attribute_names["concept:name"] = log_information["case_concept_name"]
            attribute_names["start_timestamp"] = xes.DEFAULT_START_TIMESTAMP_KEY

            log = interval_lifecycle.to_interval(log)

        elif log_information["log_type"] == "timestamp":
            attribute_names["time:timestamp"] = log_information["end_timestamp"]
            attribute_names["concept:name"] = log_information["case_concept_name"]
            attribute_names["start_timestamp"] = log_information["start_timestamp"]

    print("Min Time:", min_time)
    print("Max Time:", max_time)
    return xes_create_date_range_frame(log, Groups, min_time, max_time, attribute_names, interval_freq = '5T', interval = True)
    
def create_case_dataframe(log, log_type = "xes"): 
    """
    Creates a dataframe for plotting the case lifetime plot, taking into account the log type
    The plot has columns corresponding to each Case, its Variant, its Start and End Times, and a Case Name
    """
        
    if log_type == "xes":
        
        case_dicts = []
        
        for trace in log:
            
            timestamps = []
            variant = []
            
            for event in trace:
                # TODO Differentiate between Interval and Single TimeStamp Logs
                timestamps.append(event["time:timestamp"])
                variant.append(event["concept:name"])
                
            case_dicts.append({"variant": tuple(variant), "Name": trace.attributes["concept:name"],  "Start" : min(timestamps), "End" : max(timestamps)})
        
        df_case = pd.DataFrame.from_dict(case_dicts)
        
    else: 
    
        # Group the Data into traces and discover the variants, plus store the Start and End Time of each Trace
        df_case = log.groupby("case:concept:name").agg({"concept:name" : lambda x : tuple(x) , "time:timestamp" : [min, max]})

        # Reform the Dataframe to make it easier workable
        df_case = df_case.droplevel(0, axis = 1).rename({"<lambda>" : "variant"}, axis = 1).rename({"min" : "Start", "max" : "End"}, axis = 1)
        df_case["Name"] = ["Case " + str(x) for x in df_case.index]
    
    return df_case

    
    
def create_variant_dataframe(log, log_type = "xes"):
    """
    Creates a dataframe for plotting the variant lifetime plot, taking into account the log type
    The plot has columns corresponding to each Variant, its Start and End Times, and a Variant Name
    """
    variant_dataframe = create_case_dataframe(log, log_type)
    
    variant_dataframe = variant_dataframe.groupby("variant").agg({"Start" : min, "End": max, "Name": lambda x : list(x)})
    
    variant_dataframe = variant_dataframe.reset_index().rename({"Name" : "Cases"}, axis = 1)
    
    variant_dataframe["Name"] = ["Variant " + str(x) for x in variant_dataframe.index]
    
    return variant_dataframe

def create_group_lifetime_dataframe_from_dateframe(df, Groups):
    """
    Creates a Dataframe, with the First and Last Time of an Activity for each Group
    """
    
    first_idxs, last_idxs = utils.first_last_nonzero(df.values, axis = 0)

    group_dicts = []
    for index, group in enumerate(Groups):

        if first_idxs[index] != -1: 
            group_dicts.append({"Name" : group.name, "Start" : df.index[first_idxs[index]], "End": df.index[last_idxs[index]]})

   
    return  pd.DataFrame.from_dict(group_dicts)
