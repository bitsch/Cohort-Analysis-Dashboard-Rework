import pandas as pd
from datetime import timedelta
from django.conf import settings
from plotly.offline import plot 
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio


def create_div_block(fig):
    """

    """
    return plot(fig, output_type='div')

def timeframe_plot_factory(date_frame, Groups, freq = "M"):
    """    
    Adds 
    """ 
    pio.templates.default = settings.DEFAULT_PLOT_STYLE
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


# TODO Making this Right-aligned or improving the overall Hovertemplate
def trace_plotting_styler(variant_tuple, offset = 3):
    
    sublists = [", ".join(variant_tuple[x:x+offset])  for x in range(0, len(variant_tuple), offset)]
    styled_variant = "<br>".join(sublists)
    
    return styled_variant


def lifetime_plot_factory(df):
    """
    Creates a Lifetime plot of the provided DataFrame given that it has the form of a DataFrame with 
    Name, Start and End, where Name is some String and Start and End represent datetime Timestamps
    """
    ## Add HTML breaks into the trace event, to make it plottable, without breaking the Hover
    hover_data_dict = { 
                        'Start' :True,
                        'End' :True,
                      }
    
    ## Add HTML breaks into the trace event, to make it plottable
    if "variant" in df.columns: 
        styled_trace_events = [trace_plotting_styler(x) for x in df["variant"]]
        hover_data_dict['Events'] = styled_trace_events


    fig = px.timeline(df, x_start='Start', x_end='End', y = "Name", color = "Name", hover_name = "Name", hover_data = hover_data_dict)


    # TODO Add a better hovertemplate
    #fig.update_traces(hovertemplate=None)

    return create_div_block(fig)