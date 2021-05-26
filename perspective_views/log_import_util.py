# PM4PY Dependencies
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter

import group_analysis.datetime_utils as dt_utils
import group_analysis.utils as utils

import pandas as pd
from pm4py import format_dataframe
from pm4py.util import xes_constants as xes
from django.conf import settings

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
    output: PM4PY default object dependent on Filetype
    """

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
            log  = pm4py.format_dataframe(log, case_id=log_information["case_id"],
                                               activity_key=log_information["case_concept_name"],
                                               timestamp_key= log_information["end_timestamp"])
           
            # Rename the Columns to the XES defaults
            log = log.rename({log_information["start_timestamp"] : xes.DEFAULT_START_TIMESTAMP_KEY}, axis = 1)
        

    # Simply load the log using XES
    elif file_format == "xes": 
        
        log = xes_importer.apply(file_path, parameters = {'show_progress_bar': False})

    else:

        #TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")
    
    return log

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