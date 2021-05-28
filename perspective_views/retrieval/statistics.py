from perspective_views.plotting.data_frame_creation import create_df_variant
from core.utils.utils import flatten


def get_log_statistics(log, file_format, log_information): 

    """
    Computes Log Statisitcs from the Variant Dataframe in a log type insensitive Way
    """
    result = {}

    activites = set()

    variants = create_df_variant(log, file_format, log_information)
    cases =  set(flatten(variants["Cases"]))

    result["variant"] = variants["variant"]
    result["Nvariant"] = variants.shape[0]
    result["case"] = cases
    result["Ncase"] = len(cases)
    result["Nactivities"] = variants.apply(lambda x : len(x["variant"]) * len(x["Cases"]), axis = 1).sum()
    
    start_time = variants["Start"].min()
    end_time = variants["End"].max()

    result["StartTime"] = str(start_time)
    result["EndTime"] =  str(end_time)
    result["Duration"] = str(end_time - start_time)
    return result



