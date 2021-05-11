import shutil

from django.shortcuts import render
from django.conf import settings
import os
from os import path
from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter

from django.contrib import messages
from plotly.offline import plot
import plotly.graph_objs as go
import pandas as pd






# Create your views here.

def group_analysis(request):
    event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
    load_log_succes = False

    # Make this much smarter and as a modularized function that throws an import warning
    if settings.EVENT_LOG_NAME != ":notset:":

        
        event_log = os.path.join(event_logs_path, settings.EVENT_LOG_NAME)
        log_format = get_log_format(settings.EVENT_LOG_NAME)

        print(log_format)

        # Import the Log considering the given Format
        log = log_import(event_log, log_format)
        load_log_succes = True


    if request.method == 'POST':
        if "uploadButton" in request.POST:
            print("in request")
        event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")

        if settings.EVENT_LOG_NAME == ':notset:':
            return HttpResponseRedirect(request.path_info)

        return render(request,'group_analysis.html', {'log_name': settings.EVENT_LOG_NAME, 'data':this_data})

    else:

        if load_log_succes:
            
            #TODO Extend this to CSV Data
            Groups = [Group(name = "Release", members = ['Release B','Release A','Release D','Release C', 'Release E']), Group(name = "Treat", members = ["Test"])]    
            min_time, max_time = xes_compute_min_max_time(log)
            date_frame = xes_create_date_range_frame(log, Groups, min_time, max_time, parameters = None, freq = 'H', interval = False)
            plt_div = concurrency_plot_factory(date_frame, Groups, freq = "W")
            return render(request, "group_analysis.html", context={'plt_div': plt_div})

        else:
            
             return render(request, "group_analysis.html")

       
            



def get_log_format(file_path):

    """ 
    Function that extracts the file format in lowercase from a valid filepath
    input: file_path str
    output: file_format str
    """

    file_format = file_path.split(".")[-1].lower()

    return file_format




def log_import(file_path, file_format, interval = False):
    """ 
    Imports the file using PM4PY functionalitites
    input: file_path str, file_format str, interval bool
    output: PM4PY default object dependent on Filetype
    """

    if file_format == "csv":

        #TODO Apply further file integrity check
        log  = pd.read_csv(file_path)

        #TODO imporve on Handling of Ill-Formed Data
        log  = pm4py.format_dataframe(log, case_id="Patient", activity_key="Activity", timestamp_key="Timestamp")


    elif file_format == "xes": 


        log = xes_importer.apply(file_path, parameters = {'show_progress_bar': False})
        
        # Tries to read meta_data from XES object, under the assumption that the XES is well-formed, else compute the time
        

        # Check if Log is either timeframe or single event


    else: 
        #TODO Throw some Warning / Show a warning Message in the Console
        print("Invalid Filepath")
    

    return log



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



    from functools import partial

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


def create_div_block(fig):
    """

    """
    return plot(fig, output_type='div')


def csv_create_date_range_frame(log, Groups, parameters = None, freq = 'H', interval = False):
    """
    Creates the DateFrame for plotting for csv style data in a pandas dataframe. 
    Allows specifiying of frequency for grouping action of timestamp.
    Differentiaties between interval and case-event type data

    input: log, a PM4PY csv log object, Groups, freq str 
    output: min_time Timestamp, max_time Timestamp
    """
    INTERVAL_FREQ = "2T"
    if interval:
        #TODO Change to Default
        log = log[log["concept:name"].isin(flatten([group.members for group in Groups]))]

        #TODO Need to get this TimeStamp
        log["start_timestamp"] = pd.to_datetime(log["start_timestamp"], utc=True)

        min_time = log.start_timestamp.min()
        #TODO Change to Default
        max_time = log["time:timestamp"].max()
        

        #TODO Currently creating large dataframe with a given freq, between min and max time
        date_range = pd.date_range(datetime_floor(min_time, "D"), datetime_ceil(max_time, "D"), freq = INTERVAL_FREQ)
        date_frame = pd.DataFrame({group.name:0 for group in Groups}, index = date_range)

        for group in Groups:
            #TODO Change to Default
            for index, row in log[log["concept:name"].isin(group.members)].iterrows(): 
                date_frame.loc[row["start_timestamp"]:row["time:timestamp"], group.name] += 1

    else: 
        # Prefiltering by Projecting on Group Activites 
        log = log[log["concept:name"].isin(flatten([group.members for group in Groups]))]

        # Create the Dateframe using the count_group_activities helper function
        date_frame = log.groupby(by = pd.Grouper(key = "time:timestamp", freq = freq)).apply(partial(count_group_activities, groups = Groups))
        



    return date_frame

def xes_create_date_range_frame(log, Groups, min_time, max_time, parameters = None, freq = 'H', interval = False):
    
    # Create a DataFrame to fill 
    date_range = pd.date_range(datetime_floor(min_time, "D"), datetime_ceil(max_time, "D"), freq = freq)
    date_frame = pd.DataFrame({group.name:0 for group in Groups}, index = date_range)
    
    for trace in log:

        for event in trace:
            
            # Consider Grouping
            for group in Groups: 
            
                #TODO Replace default Concept Name
                if event["concept:name"] in group.members:
                    
                    if interval: 
                        #TODO Replace default Name
                        date_frame.loc[event["start_timestamp"]:event["time:timestamp"], group.name] += 1

                    else:
                        #TODO Replace default Name
                        date_frame.loc[datetime_floor(event["time:timestamp"], freq = freq), group.name] += 1
                       
    
    #Check for Consecutive strands of 0 at the End (Could be done in Loop instead)
    index_frame = date_frame.iloc[::-1].applymap(lambda x : bool(x)).cumsum().sum(axis = 1).apply(lambda x : bool(x)).iloc[::-1]
    date_frame = date_frame[index_frame]
    
    return date_frame



class Group():
    """
    Represents a Group, including its name and member activities
    Attr: 
        name str
        members list


    """

    def __init__(self, name: str, members: list):
        
        if name is not None:
            self.name = name
            
        if members is not None:
            self.members = members




def flatten(ls):
    """
    Flattens a list of list into a single list
    input ls, List of Lists
    output list
    """

    return [item for sublist in ls for item in sublist]



from datetime import timezone, timedelta
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

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



def concurrency_plot_factory(date_frame, Groups, freq = "M", interval = False):
    """
    Create a concurrency plot from a dateframe
    input date_time_obj, the freq, to ceil to. 
    output ceiled date_time_obj
    """
    #Create a graph object
    
    fig = go.Figure()
    
    ## Groupe the Data, if it is an interval, simply use the dateframe
    if interval:
        date_frame = date_frame.groupby(by = pd.Grouper(freq = freq)).max()
    else:
        date_frame = date_frame.groupby(by = pd.Grouper(freq = freq)).sum()
    
    ## Add the lines to the Plot object 
    for group in Groups: 
        fig.add_trace(go.Scatter(x = date_frame.index, y = date_frame[group.name],
                  mode='lines',
                  name= group.name))
    
    #TODO Add the Legend in a Place of Convenience
    
    
    
    ## Add a timerange selector 
    fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
    )
    
    
    ## Return a Div Block 
    
    return create_div_block(fig)




def timeframe_plot_factory(date_frame, Groups, freq = "M"):
    
    dict_list = []

    for group in Groups: 
        
        for index, block in date_frame[date_frame[group.name] != 0].groupby((date_frame[group.name] == 0).cumsum()):
            
            if block.index[0] != block.index[-1]:
                dict_list.append({"Start" : block.index[0], "End": block.index[-1], "Task": group.name, "Number of Activites": block[group.name].sum()})
            
            else: 
                # Add some Time Delta depending on Freq so that the event doesn't have zero width
                dict_list.append({"Start" : block.index[0], "End": block.index[-1] + timedelta(days = 1), "Task": group.name, "Number of Activites": block[group.name].sum()})
            
    hover_data_dict = { 'Task' : False,
                        'Start':True,
                        'End':True,
                        'Number of Activites':True, 
                    }
            
    fig = px.timeline(pd.DataFrame.from_dict(dict_list), x_start="Start", x_end="End", y="Task", color="Task", hover_name = "Task", hover_data = hover_data_dict)

    return create_div_block(fig)


def amplitude_plot_factory(date_frame, Groups):
    
    fig = go.Figure()
    
    ## Add the lines to the Plot object 
    for group in groups: 
        fig.add_trace(go.Scatter(x = date_frame[date_frame[group.name] > 0].index, y = date_frame[date_frame[group.name] > 0][group.name].apply(lambda x: group.name),
                    mode='markers',
                    name= group.name, 
                    marker_symbol = "line-ns-open",
                    marker=dict(size = 45 * date_frame[date_frame[group.name] > 0][group.name]/date_frame[date_frame[group.name] > 0][group.name].max()), 
                    hovertemplate = "Group: %{y} <br>Date: %{x}<br>%{text}<extra></extra>", 
                    text = ['Concurrent Events: {}'.format(i) for i in list(date_frame[date_frame[group.name] > 0][group.name])])
                    )
        
    return create_div_block(fig)