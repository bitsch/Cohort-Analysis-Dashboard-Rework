import pandas as pd
from pm4py import format_dataframe, convert_to_dataframe
from pm4py.util import xes_constants as xes

import core.utils.utils as utils
import core.data_transformation.data_transform_utils as data_transform


def create_concurrency_frame(df, Groups, freq="5T"):
    """
    Compute a dataframe for plotting of concurrent events used in the associated plotting functions

    input:  pandas df log in a double timestamp format
            list-like of Group Objects
            pandsa freq str   

    output: pandas df containing the count of concurrent activities per group on a freq-level
    """
    df = df.copy()
    df = df.loc[
        df[xes.DEFAULT_TRACEID_KEY].isin(
            utils.flatten([group.members for group in Groups])
        ),
        :,
    ]

    for group in Groups:
        df.loc[:, group.name] = df["concept:name"].isin(group.members)

    df = df.drop(["case:concept:name", "concept:name"], axis=1)

    df.loc[:, xes.DEFAULT_START_TIMESTAMP_KEY] = pd.to_datetime(
        df.loc[:, xes.DEFAULT_START_TIMESTAMP_KEY], utc=True
    )
    df.loc[:, xes.DEFAULT_TIMESTAMP_KEY] = pd.to_datetime(
        df.loc[:, xes.DEFAULT_TIMESTAMP_KEY], utc=True
    )

    df.loc[:, "interpolate_date"] = [
        pd.date_range(s, e, freq=freq)
        for s, e in zip(
            pd.to_datetime(df.loc[:, xes.DEFAULT_START_TIMESTAMP_KEY]),
            pd.to_datetime(df.loc[:, xes.DEFAULT_TIMESTAMP_KEY]),
        )
    ]

    df = df.drop(
        [xes.DEFAULT_START_TIMESTAMP_KEY, xes.DEFAULT_TIMESTAMP_KEY], axis=1
    ).explode("interpolate_date")

    date_frame = df.groupby(pd.Grouper(key="interpolate_date", freq=freq)).sum()

    return date_frame


def create_plotting_data(log, file_format, log_information):
    """
    Transofrms a log, such that it can be easer used for plotting, removes unnecessary data, creates df from xes data, and renames columns

    input: XES/CSV log ,
           file_format str,
           log_information django session dict

    output: pandas df with pm4py default names for attributes in a two timestamp format       
    """
    # Stores the Attribut Names for later references, makes renaming attributes inside the XES unnecessary
    attribute_names = {}

    if file_format == "csv":

        # Select only the Relevant columns of the Dataframe
        if log_information["log_type"] == "noninterval":

            # Project the Log onto the Group Activites

            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                ]
            ]

        elif log_information["log_type"] == "lifecycle":

            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                    xes.DEFAULT_TRANSITION_KEY,
                ]
            ]
            log = data_transform.transform_lifecycle_csv_to_interval_csv(log)

        elif log_information["log_type"] == "timestamp":

            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                    xes.DEFAULT_START_TIMESTAMP_KEY,
                ]
            ]
            log = log.rename(
                {
                    log_information["start_timestamp"]: xes.DEFAULT_START_TIMESTAMP_KEY,
                    log_information["end_timestamp"]: xes.DEFAULT_TIMESTAMP_KEY,
                },
                axis=1,
            )

    # Simply load the log using XES
    elif file_format == "xes":

        log = convert_to_dataframe(log)

        if log_information["log_type"] == "noninterval":

            log[log_information["timestamp"]] = pd.to_datetime(
                log[log_information["timestamp"]], utc=True
            )
            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                ]
            ]

        # Transform the Timestamp to Datetime, and rename the transition:lifecycle
        elif log_information["log_type"] == "lifecycle":

            # Convert the Timestamps to Datetime
            log[log_information["timestamp"]] = pd.to_datetime(
                log[log_information["timestamp"]], utc=True
            )

            # Rename the Columns to the XES defaults
            log = log.rename(
                {log_information["lifecycle"]: xes.DEFAULT_TRANSITION_KEY}, axis=1
            )
            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                    xes.DEFAULT_TRANSITION_KEY,
                ]
            ]
            log = data_transform.transform_lifecycle_csv_to_interval_csv(log)

        elif log_information["log_type"] == "timestamp":

            # Convert the Timestamps to Datetime
            log[log_information["end_timestamp"]] = pd.to_datetime(
                log[log_information["end_timestamp"]], utc=True
            )
            log[log_information["start_timestamp"]] = pd.to_datetime(
                log[log_information["start_timestamp"]], utc=True
            )

            log = log[
                [
                    "case:concept:name",
                    xes.DEFAULT_TIMESTAMP_KEY,
                    xes.DEFAULT_TRACEID_KEY,
                    xes.DEFAULT_START_TIMESTAMP_KEY,
                ]
            ]
            log = log.rename(
                {
                    log_information["start_timestamp"]: xes.DEFAULT_START_TIMESTAMP_KEY,
                    log_information["end_timestamp"]: xes.DEFAULT_TIMESTAMP_KEY,
                },
                axis=1,
            )

    return log


def create_timeframe_dataframe(df, Group, start_time, end_time): 
    
    return(df.loc[(df[xes.DEFAULT_TRACEID_KEY].isin(Group.members)) & (df[xes.DEFAULT_START_TIMESTAMP_KEY].between(start_time, end_time))])
    
