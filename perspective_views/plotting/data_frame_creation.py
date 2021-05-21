from pm4py.util import xes_constants as xes
import pandas as pd
from pm4py import format_dataframe, convert_to_dataframe

import core.utils.utils as utils
import core.data_transformation.data_transform_utils as data_transform



def create_df_case(log, file_format, case_names, log_information):
    
    if file_format == "csv":

        if log_information["log_type"] == "noninterval": 
            print("This operation is not supported for this log type")
            ## Throw some Error as Interval Data is needed
            
        elif log_information["log_type"] == "lifecycle":
            
            df = data_transform.transform_lifecycle_csv_to_interval_csv(log[log["case:concept:name"].isin(case_names)])
            
        elif log_information["log_type"] == "timestamp":
    
            df = log[log["case:concept:name"].isin(case_names)].copy()

    # Simply load the log using XES
    elif file_format == "xes": 
        res_dicts = {}
        if log_information["log_type"] == "noninterval": 
            print("This operation is not supported for this log type")
             
        else: 
            
            counter = 0 
            dicts = []
            
            for trace in log:
               
                if trace.attributes[log_information["case_id"]] in case_names:
                    
                    for event in trace: 
                        dicts.append({**event, "case:concept:name" : trace.attributes[log_information["case_id"]]})
                    
                    # Break early, if all Cases have been found
                    counter += 1
                    if counter == len(case_names):
                        break
                
            df = pd.DataFrame.from_dict(dicts)
            
            if log_information["log_type"] == "lifecycle":
                                
                    df = df.rename({log_information["timestamp"] : xes.DEFAULT_TIMESTAMP_KEY,
                                    log_information["case_concept_name"] : xes.DEFAULT_NAME_KEY,
                                    log_information["lifecycle"] : xes.DEFAULT_TRANSITION_KEY}, axis = 1)
                                    
                    df = data_transform.transform_lifecycle_csv_to_interval_csv(df)           
                            
            elif log_information["log_type"] == "timestamp":
                    
                    df = df.rename({log_information["timestamp"] : xes.DEFAULT_TIMESTAMP_KEY, 
                                    log_information["case_concept_name"] : xes.DEFAULT_NAME_KEY,
                                    log_information["start_timestamp"] : xes.DEFAULT_START_TIMESTAMP_KEY}, axis = 1)
                      
    else:

        #TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")
    
    # Remove unneeded information
    df = df[[xes.DEFAULT_START_TIMESTAMP_KEY, xes.DEFAULT_TIMESTAMP_KEY, xes.DEFAULT_NAME_KEY, "case:concept:name"]]
    df.loc[:,xes.DEFAULT_START_TIMESTAMP_KEY] = pd.to_datetime(df.loc[:,xes.DEFAULT_START_TIMESTAMP_KEY] ,  utc = True)
    df.loc[:,xes.DEFAULT_TIMESTAMP_KEY] = pd.to_datetime(df.loc[:,xes.DEFAULT_TIMESTAMP_KEY] ,  utc = True)
    
    return df


def create_df_variant(log, file_format, log_information):
    
    if file_format == "csv":

        if log_information["log_type"] == "noninterval": 
            print("This operation is not supported for this log type")
            ## Throw some Error as Interval Data is needed
            
        elif log_information["log_type"] == "lifecycle":
            
            df = log.groupby("case:concept:name").agg({xes.DEFAULT_NAME_KEY : lambda x : tuple(x) , xes.DEFAULT_TIMESTAMP_KEY : [min, max]})

            # Reform the Dataframe to make it easier workable
            df = df.droplevel(0, axis = 1).rename({"<lambda>" : "variant"}, axis = 1).rename({"min" : "Start", "max" : "End"}, axis = 1)
            df["Name"] = [str(x) for x in df.index]
    

        elif log_information["log_type"] == "timestamp":
    
            df = log.groupby("case:concept:name").agg({xes.DEFAULT_NAME_KEY : lambda x : tuple(x) , xes.DEFAULT_TIMESTAMP_KEY : [max], xes.DEFAULT_START_TIMESTAMP_KEY : [min]})
        
            # Reform the Dataframe to make it easier workable
            df = df.droplevel(0, axis = 1).rename({"<lambda>" : "variant"}, axis = 1).rename({"min" : "Start", "max" : "End"}, axis = 1)
            df["Name"] = [str(x) for x in df.index]

    # Simply load the log using XES
    elif file_format == "xes": 
        res_dicts = {}
        if log_information["log_type"] == "noninterval": 
            
            print("This operation is not supported for this log type")
             
        elif log_information["log_type"] == "lifecycle":
            case_dicts = []
            for trace in log:

                timestamps = []
                variant = []

                for event in trace:
                    # TODO Differentiate between Interval and Single TimeStamp Logs
                    timestamps.append(event[log_information["timestamp"]])
                    variant.append(event[log_information["case_concept_name"]])

                case_dicts.append({"variant": tuple(variant), "Name": trace.attributes[log_information["case_id"]],  "Start" : min(timestamps), "End" : max(timestamps)})

            df = pd.DataFrame.from_dict(case_dicts)
                           
                            
        elif log_information["log_type"] == "timestamp":
            
            case_dicts = []
            for trace in log:

                start_timestamps = []
                end_timestamps = []
                variant = []

                for event in trace:
                    # TODO Differentiate between Interval and Single TimeStamp Logs
                    start_timestamps.append(event[log_information["start_timestamp"]])
                    end_timestamps.append(event[log_information["end_timestamp"]])
                    variant.append(event[log_information["case_concept_name"]])

                case_dicts.append({"variant": tuple(variant), "Name": trace.attributes[log_information["case_id"]],  "Start" : min(start_timestamps), "End" : max(end_timestamps)})

            df = pd.DataFrame.from_dict(case_dicts)
        
    else:

        #TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")
    
    # Aggregate the base dataframes to the variant level
    df = df.groupby("variant").agg({"Start" : min, "End": max, "Name": lambda x : list(x)})
    df = df.reset_index().rename({"Name" : "Cases"}, axis = 1)
    df["Name"] = ["Variant " + str(x) for x in df.index]
    
    return df