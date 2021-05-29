# PM4PY Dependencies
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter

import group_analysis.datetime_utils as dt_utils
import group_analysis.utils as utils
from group_analysis.group_managment import Group

import pandas as pd

from django.conf import settings


def get_log_format(file_path):
    """
    Function that extracts the file format in lowercase from a valid filepath
    input: file_path str
    output: file_format str
    """

    file_format = file_path.split(".")[-1].lower()

    return file_format


def log_import(file_path, file_format, interval=False):
    """
    Imports the file using PM4PY functionalitites
    input: file_path str, file_format str, interval bool
    output: PM4PY default object dependent on Filetype
    """

    if file_format == "csv":

        # TODO Apply further file integrity check
        log = pd.read_csv(file_path)

        # TODO improve on Handling of Ill-Formed Data
        log = pm4py.format_dataframe(
            log, case_id="Patient", activity_key="Activity", timestamp_key="Timestamp"
        )

    elif file_format == "xes":

        log = xes_importer.apply(file_path, parameters={"show_progress_bar": False})

        # Tries to read meta_data from XES object, under the assumption that the XES is well-formed, else compute the time

        # Check if Log is either timeframe or single event

    else:
        # TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")

    return log


def count_group_activities(df, groups):
    """
    Helper function for CSV grouping, computes the activity count per grouped timeframe
    input: df pd.Dataframe, groups list-like of Groups
    output: pd.Series containing the number of activity per group observed
    """

    group_dict = {}

    for group in groups:
        group_dict[group.name] = df[df["concept:name"].isin(group.members)].count()[
            "concept:name"
        ]

    return pd.Series(group_dict)


def csv_create_date_range_frame(log, Groups, parameters=None, freq="H", interval=False):
    """
    Creates the DateFrame for plotting for csv style data in a pandas dataframe.
    Allows specifiying of frequency for grouping action of timestamp.
    Differentiaties between interval and case-event type data

    input: log, a PM4PY csv log object, Groups, freq str
    output: min_time Timestamp, max_time Timestamp
    """

    if interval:
        # TODO Change to Default
        log = log[
            log["concept:name"].isin(flatten([group.members for group in Groups]))
        ]

        # TODO Need to get this TimeStamp
        log["start_timestamp"] = pd.to_datetime(log["start_timestamp"], utc=True)

        min_time = log.start_timestamp.min()
        # TODO Change to Default
        max_time = log["time:timestamp"].max()

        # TODO Currently creating large dataframe with a given freq, between min and max time
        date_range = pd.date_range(
            dt_utils.datetime_floor(min_time, "D"),
            dt_utils.datetime_ceil(max_time, "D"),
            freq=settings.INTERVAL_GRANULARITY,
        )
        date_frame = pd.DataFrame({group.name: 0 for group in Groups}, index=date_range)

        for group in Groups:
            # TODO Change to Default
            for index, row in log[log["concept:name"].isin(group.members)].iterrows():
                date_frame.loc[
                    row["start_timestamp"] : row["time:timestamp"], group.name
                ] += 1

    else:
        # Prefiltering by Projecting on Group Activites
        log = log[
            log["concept:name"].isin(flatten([group.members for group in Groups]))
        ]

        # Create the Dateframe using the count_group_activities helper function
        date_frame = log.groupby(by=pd.Grouper(key="time:timestamp", freq=freq)).apply(
            partial(count_group_activities, groups=Groups)
        )

    return date_frame


def xes_create_date_range_frame(
    log, Groups, min_time, max_time, parameters=None, freq="H", interval=False
):

    # Create a DataFrame to fill
    date_range = pd.date_range(
        dt_utils.datetime_floor(min_time, "D"),
        dt_utils.datetime_ceil(max_time, "D"),
        freq=freq,
    )
    date_frame = pd.DataFrame({group.name: 0 for group in Groups}, index=date_range)

    for trace in log:

        for event in trace:

            # Consider Grouping
            for group in Groups:

                # TODO Replace default Concept Name
                if event["concept:name"] in group.members:

                    if interval:
                        # TODO Replace default Name
                        date_frame.loc[
                            event["start_timestamp"] : event["time:timestamp"],
                            group.name,
                        ] += 1

                    else:
                        # TODO Replace default Name
                        date_frame.loc[
                            dt_utils.datetime_floor(event["time:timestamp"], freq=freq),
                            group.name,
                        ] += 1

    # Check for Consecutive strands of 0 at the End (Could be done in Loop instead)
    index_frame = (
        date_frame.iloc[::-1]
        .applymap(lambda x: bool(x))
        .cumsum()
        .sum(axis=1)
        .apply(lambda x: bool(x))
        .iloc[::-1]
    )
    date_frame = date_frame[index_frame]

    return date_frame


def create_case_dataframe(log, log_type="xes"):
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

            case_dicts.append(
                {
                    "variant": tuple(variant),
                    "Name": trace.attributes["concept:name"],
                    "Start": min(timestamps),
                    "End": max(timestamps),
                }
            )

        df_case = pd.DataFrame.from_dict(case_dicts)

    else:

        # Group the Data into traces and discover the variants, plus store the Start and End Time of each Trace
        df_case = log.groupby("case:concept:name").agg(
            {"concept:name": lambda x: tuple(x), "time:timestamp": [min, max]}
        )

        # Reform the Dataframe to make it easier workable
        df_case = (
            df_case.droplevel(0, axis=1)
            .rename({"<lambda>": "variant"}, axis=1)
            .rename({"min": "Start", "max": "End"}, axis=1)
        )
        df_case["Name"] = ["Case " + str(x) for x in df_case.index]

    return df_case


def create_variant_dataframe(log, log_type="xes"):
    """
    Creates a dataframe for plotting the variant lifetime plot, taking into account the log type
    The plot has columns corresponding to each Variant, its Start and End Times, and a Variant Name
    """
    variant_dataframe = create_case_dataframe(log, log_type)

    variant_dataframe = variant_dataframe.groupby("variant").agg(
        {"Start": min, "End": max, "Name": lambda x: list(x)}
    )

    variant_dataframe = variant_dataframe.reset_index().rename(
        {"Name": "Cases"}, axis=1
    )

    variant_dataframe["Name"] = ["Variant " + str(x) for x in variant_dataframe.index]

    return variant_dataframe


def create_group_lifetime_dataframe_from_dateframe(df, Groups):
    """
    Creates a Dataframe,
    with the First and Last Time of an Activity for each Group
    """

    first_idxs, last_idxs = utils.first_last_nonzero(df.values, axis=0)

    group_dicts = []
    for index, group in enumerate(Groups):

        if first_idxs[index] != -1:
            group_dicts.append(
                {
                    "Name": group.name,
                    "Start": df.index[first_idxs[index]],
                    "End": df.index[last_idxs[index]],
                }
            )

    return pd.DataFrame.from_dict(group_dicts)
