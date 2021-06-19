import pandas as pd
from datetime import timedelta
from django.conf import settings
from plotly.offline import plot
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio


def create_div_block(fig):
    """ """
    return plot(fig, output_type="div")


def concurrency_plot_factory(date_frame, Groups, freq="M", interval=False):
    """
    Create a concurrency plot from a dateframe
    input date_time_obj, the freq, to ceil to.
    output ceiled date_time_obj
    """
    # Create a graph object

    pio.templates.default = settings.DEFAULT_PLOT_STYLE
    fig = go.Figure()

    # Groupe the Data, if it is an interval, simply use the dateframe
    if interval:
        date_frame = date_frame.groupby(by=pd.Grouper(freq=freq)).max()
    else:
        date_frame = date_frame.groupby(by=pd.Grouper(freq=freq)).sum()

    # Add the lines to the Plot object
    for group in Groups:
        fig.add_trace(
            go.Scatter(
                x=date_frame.index,
                y=date_frame[group.name],
                mode="lines",
                name=group.name,
            )
        )

    # TODO Add the Legend in a Place of Convenience

    # Add a timerange selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    ## Return a Div Block

    return create_div_block(fig)


def timeframe_plot_factory(date_frame, Groups, freq="M"):
    """
    Adds
    """
    pio.templates.default = settings.DEFAULT_PLOT_STYLE
    dict_list = []

    for group in Groups:

        for index, block in date_frame[date_frame[group.name] != 0].groupby(
            (date_frame[group.name] == 0).cumsum()
        ):

            if block.index[0] != block.index[-1]:
                dict_list.append(
                    {
                        "Start": block.index[0],
                        "End": block.index[-1],
                        "Task": group.name,
                        "Number of activities": block[group.name].sum(),
                    }
                )

            else:
                # Add some Time Delta depending on Freq so that the event doesn't have zero width
                dict_list.append(
                    {
                        "Start": block.index[0],
                        "End": block.index[-1] + timedelta(days=1),
                        "Task": group.name,
                        "Number of activities": block[group.name].sum(),
                    }
                )

    hover_data_dict = {
        "Task": False,
        "Start": True,
        "End": True,
        "Number of activities": True,
    }

    fig = px.timeline(
        pd.DataFrame.from_dict(dict_list),
        x_start="Start",
        x_end="End",
        y="Task",
        color="Task",
        hover_name="Task",
        hover_data=hover_data_dict,
    )

    return create_div_block(fig)


def amplitude_plot_factory(date_frame, Groups, freq="M", Unified=True):
    """
    Produces an DIV Block containing an Plotly Graphobject in the Style of a Amplitude Plot.
    Used in the Timeframe view as a way to represent



    """

    pio.templates.default = settings.DEFAULT_PLOT_STYLE
    fig = go.Figure()

    # Compute the Scaling factor depedent on all groups
    if Unified:

        # Assume that at least one event did happen, else the plot remains empty, and compute highest group value
        scaling = date_frame.max().max()

    # Add the lines to the Plot object
    for group in Groups:

        series = date_frame[date_frame[group.name] > 0][group.name]

        # Compute the Scaling factor per individual group
        if not Unified:
            scaling = series.max()

        # TODO Implement Individual and Unified Scaling
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.apply(lambda x: group.name),
                mode="markers",
                name=group.name,
                marker_symbol="line-ns-open",
                marker=dict(size=65 * series / scaling),
                hovertemplate="Group: %{y} <br>Date: %{x}<br>%{text}<extra></extra>",
                text=["Concurrent Events: {}".format(i) for i in list(series)],
            )
        )

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    return create_div_block(fig)


# TODO Making this Right-aligned or improving the overall Hovertemplate
def trace_plotting_styler(variant_tuple, offset=3):

    sublists = [
        ", ".join(variant_tuple[x : x + offset]) for x in range(0, len(variant), offset)
    ]
    styled_variant = "<br>".join(sublists)

    return styled_variant


def lifetime_plot_factory(df):
    """
    Creates a Lifetime plot of the provided DataFrame given that it has the form of a DataFrame with
    Name, Start and End, where Name is some String and Start and End represent datetime Timestamps
    """
    # Add HTML breaks into the trace event, to make it plottable, without breaking the Hover
    hover_data_dict = {
        "Start": True,
        "End": True,
    }

    # Add HTML breaks into the trace event, to make it plottable
    if "variant" in df.columns:
        styled_trace_events = [trace_plotting_styler(x) for x in df["variant"]]
        hover_data_dict["Events"] = styled_trace_events

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Name",
        color="Name",
        hover_name="Name",
        hover_data=hover_data_dict,
    )

    # TODO Add a better hovertemplate
    # fig.update_traces(hovertemplate=None)

    return create_div_block(fig)
