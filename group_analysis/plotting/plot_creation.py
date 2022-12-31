import pandas as pd
from django.conf import settings
import plotly.graph_objs as go
import plotly.io as pio
import core.plotting.plotting_utils as plt_util
import plotly.express as px
import datetime
from sklearn import tree,metrics
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix



def concurrency_plot_factory(date_frame, Groups, aggregate, freq):
    """
    Create a concurrency plot from a dateframe
    input: pandas df created with the create_concurrency_dataframe function,
           list-like of Group obj,
           pandas aggregate fnc,
           pandas freq str
    output: plotly div containing a line-style concurreny plot
    """
    # Create a graph object

    pio.templates.default = settings.DEFAULT_PLOT_STYLE
    fig = go.Figure()

    # Groupe the Data, if it is an interval, simply use the dateframe

    date_frame = date_frame.groupby(by=pd.Grouper(freq=freq)).agg(aggregate)

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

    # Return a Div Block

    return plt_util.create_div_block(fig)


def amplitude_plot_factory(date_frame, Groups, Unified=True):
    """
    Produces an div Block containing an Plotly Graphobject in the Style of a Amplitude Plot.
    Used in the Concurrency GroupAnalysis view as a way to represent concurrency.
    Use Unified to indicate if the bars should be scaled per group or uniform.

    input: pandas df created with the create_concurrency_dataframe function,
           list-like of Group obj,
           bool Unified
    output: plotly plot div cotaining an ampliude plot
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

    return plt_util.create_div_block(fig)


def timeframe_plot_factory(df):

    fig = px.timeline(
        df,
        x_start="start_timestamp",
        x_end="time:timestamp",
        y="case:concept:name",
        color="case:concept:name",
        hover_name="case:concept:name",
    )

    return plt_util.create_div_block(fig)

def delay(predictordatedataframe,targetdatedataframe):
    result=[]
    predictordatedataframe=predictordatedataframe.merge(targetdatedataframe[['date','tokenproduced', 'tokenconsumed', 'tokenleft','chunkmean', 'Count', 'rolledmean']], on='date', how='left')
    print(predictordatedataframe)
    #add seven days
    def categorise(row,numdays):
        return row['date'] -  datetime.timedelta(days=1)
    for i in range (7):
        predictordatedataframe=predictordatedataframe.merge(targetdatedataframe[['date','delayed']].rename({'delayed': 'delayed_'+str(i)}, axis=1), on='date', how='left')
        targetdatedataframe['date'] = targetdatedataframe.apply(lambda row: categorise(row,i), axis=1)
    test=predictordatedataframe.loc[predictordatedataframe.index[-2:-1]]
    predictordatedataframe=predictordatedataframe.drop(predictordatedataframe.index[-2:-1])
    predictordatedataframe=predictordatedataframe.dropna()
    predictordatedataframe["delayed_0"] = predictordatedataframe["delayed_0"].astype(int)
    predictordatedataframe["delayed_1"] = predictordatedataframe["delayed_1"].astype(int)
    predictordatedataframe["delayed_2"] = predictordatedataframe["delayed_2"].astype(int)
    predictordatedataframe["delayed_3"] = predictordatedataframe["delayed_3"].astype(int)
    predictordatedataframe["delayed_4"] = predictordatedataframe["delayed_4"].astype(int)
    predictordatedataframe["delayed_5"] = predictordatedataframe["delayed_5"].astype(int)
    predictordatedataframe["delayed_6"] = predictordatedataframe["delayed_6"].astype(int)
    def traindtmultiple(y,i):
        clf = tree.DecisionTreeRegressor()
        clf = clf.fit(x, y)
        predictiontest=clf.predict(testpred)
        if predictiontest==1:
            result.append("High chance of having batching in target zone on "+ str(i) +" timeframe")
    x = predictordatedataframe[['index', 'tokenproduced_x', 'tokenconsumed_x', 'tokenleft_x','Count_x', 'WaitingDays', 'AverageWaitingTime','rolledmean_x', 'totaltokenleft', 'Averagetokenleft','totaltokenconsumed', 'Averagetokenconsumed', 'totaltokenproduced','Averagetokenproduced','tokenproduced_y', 'tokenconsumed_y', 'tokenleft_y','Count_y','rolledmean_y','chunkmean_y']]
    testpred= test [['index', 'tokenproduced_x', 'tokenconsumed_x', 'tokenleft_x','Count_x', 'WaitingDays', 'AverageWaitingTime','rolledmean_x', 'totaltokenleft', 'Averagetokenleft','totaltokenconsumed', 'Averagetokenconsumed', 'totaltokenproduced','Averagetokenproduced','tokenproduced_y', 'tokenconsumed_y', 'tokenleft_y','Count_y','rolledmean_y','chunkmean_y']]
    for i in range(7):
        y = predictordatedataframe['delayed_'+str(i)].fillna(0)
        traindtmultiple(y,i)
    print(result)
    return result

def batch(predictordatedataframe,targetdatedataframe):
    result=[]
    predictordatedataframe=predictordatedataframe.merge(targetdatedataframe[['date','tokenproduced', 'tokenconsumed', 'tokenleft','chunkmean', 'Count', 'rolledmean']], on='date', how='left')
    print(predictordatedataframe)
    #add seven days
    def categorise(row,numdays):
        return row['date'] -  datetime.timedelta(days=1)
    for i in range (7):
        predictordatedataframe=predictordatedataframe.merge(targetdatedataframe[['date','chunkbatched']].rename({'chunkbatched': 'batched_'+str(i)}, axis=1), on='date', how='left')
        targetdatedataframe['date'] = targetdatedataframe.apply(lambda row: categorise(row,i), axis=1)
    test=predictordatedataframe.loc[predictordatedataframe.index[-2:-1]]
    predictordatedataframe=predictordatedataframe.drop(predictordatedataframe.index[-2:-1])
    predictordatedataframe=predictordatedataframe.dropna()
    predictordatedataframe["batched_0"] = predictordatedataframe["batched_1"].astype(int)
    predictordatedataframe["batched_1"] = predictordatedataframe["batched_1"].astype(int)
    predictordatedataframe["batched_2"] = predictordatedataframe["batched_2"].astype(int)
    predictordatedataframe["batched_3"] = predictordatedataframe["batched_3"].astype(int)
    predictordatedataframe["batched_4"] = predictordatedataframe["batched_4"].astype(int)
    predictordatedataframe["batched_5"] = predictordatedataframe["batched_5"].astype(int)
    predictordatedataframe["batched_6"] = predictordatedataframe["batched_6"].astype(int)
    def traindtmultiple(y,i):
        clf = tree.DecisionTreeRegressor()
        clf = clf.fit(x, y)
        predictiontest=clf.predict(testpred)
        if predictiontest==1:
            result.append("High chance of having batching in target zone on "+ str(i) +" timeframe")
    x = predictordatedataframe[['index', 'tokenproduced_x', 'tokenconsumed_x', 'tokenleft_x','Count_x', 'WaitingDays', 'AverageWaitingTime','rolledmean_x', 'totaltokenleft', 'Averagetokenleft','totaltokenconsumed', 'Averagetokenconsumed', 'totaltokenproduced','Averagetokenproduced','tokenproduced_y', 'tokenconsumed_y', 'tokenleft_y','Count_y','rolledmean_y','chunkmean_y']]
    testpred= test [['index', 'tokenproduced_x', 'tokenconsumed_x', 'tokenleft_x','Count_x', 'WaitingDays', 'AverageWaitingTime','rolledmean_x', 'totaltokenleft', 'Averagetokenleft','totaltokenconsumed', 'Averagetokenconsumed', 'totaltokenproduced','Averagetokenproduced','tokenproduced_y', 'tokenconsumed_y', 'tokenleft_y','Count_y','rolledmean_y','chunkmean_y']]
    for i in range(7):
        y = predictordatedataframe['batched_'+str(i)].fillna(0)
        traindtmultiple(y,i)
    print(result)
    return result

def make_prediction(preddf,targetdf):
    result=[]
    result.extend(delay(preddf,targetdf))
    result.extend(batch(preddf,targetdf))
    return result