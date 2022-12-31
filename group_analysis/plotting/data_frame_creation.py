import pandas as pd
from pm4py import convert_to_dataframe
from pm4py.util import xes_constants as xes
from datetime import timedelta as td
import core.utils.utils as utils
import core.data_transformation.data_transform_utils as data_transform
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
import ruptures as rpt

sensitivity=1.5
timeframe='D'
##usage= get_labels_set(input_transition_set)
def get_labels_set(net,input_transition_set):
    label_set=set()
    for transition in input_transition_set:
        label_set.add(transition._Transition__get_label())
    return label_set

##usage= get_input_transitions('n4')
def get_initial_start(net,intial_place):
    print(intial_place)
    initial_start=None
    for place in net.places:
        if place._Place__get_name()==intial_place:
            initial_start=place
    return initial_start

##usage= get_input_transitions(net,initial_start)
def get_input_transitions(net,place):
    transition=list()
    if place in net.places:
        for arc in net.arcs:
            if arc._Arc__get_target()==place:
                if arc._Arc__get_source()._Transition__get_label() is None:
                    for new_place in arc._Arc__get_source()._Transition__get_in_arcs():
                        transition.extend(get_input_transitions(net,new_place._Arc__get_source()))
                else:
                    transition.append(arc._Arc__get_source())
        return transition
    else:
        return None

##usage= get_output_transitions(net,initial_start)
def get_output_transitions(net,place):
    transition=list()
    if place in net.places:
        for arc in net.arcs:
            if arc._Arc__get_source()==place:
                if arc._Arc__get_target()._Transition__get_label() is None:
                    for new_place in arc._Arc__get_target()._Transition__get_out_arcs():
                        transition.extend(get_output_transitions(net,new_place._Arc__get_target()))
                else:
                    transition.append(arc._Arc__get_target())
        return transition
    else:
        return None

def getdataframe(log, net,initial_marking, final_marking, places):

	replayed_traces = token_replay.apply(log, net, initial_marking, final_marking)
	places=places.members

	input_transition_set=set()
	input_transition_label_set=set()
	output_transition_set=set()
	output_transition_label_set=set()

	for start in places:
	    initial_start=get_initial_start(net,start)
	    input_transition_set|=set(get_input_transitions(net,initial_start))
	    temp=input_transition_set.difference(output_transition_set)
	    output_transition_set|=set(get_output_transitions(net,initial_start))
	    output_transition_label_set|=get_labels_set(net,output_transition_set)


	input_transition_label_set|=get_labels_set(net,input_transition_set)
	output_transition_label_set|=get_labels_set(net,output_transition_set)


	print(input_transition_set)
	print(input_transition_label_set)
	print(output_transition_set)
	print(output_transition_label_set)

	token_produced=0
	token_consumed=0
	token_left=0
	predictordf=pd.DataFrame(columns= ['StartEvent','StartTime','EndEvent','EndTime','User'])
	for trace,case in zip(replayed_traces, log):
	    last_event=None
	    first_event=None
	    if trace['trace_is_fit']==True:
	        for active_trace in trace['activated_transitions']:
	            if active_trace in input_transition_set :
	                for events in case:
	                    if events['concept:name'] in input_transition_label_set:
	                        last_event=events
	            if active_trace in output_transition_set:
	                for events in case:
	                    if events['concept:name'] in output_transition_label_set and first_event is None:
	                        first_event=events
	    if last_event is not None and first_event is not None:
	        token_produced=token_produced+1
	        token_consumed=token_consumed+1
	        row_df = pd.DataFrame([[last_event['concept:name'], last_event['time:timestamp'],first_event['concept:name'], first_event['time:timestamp'], case.attributes['concept:name']]],columns= ['StartEvent','StartTime','EndEvent','EndTime','User'])
	        predictordf = pd.concat([row_df, predictordf], ignore_index=True)

	predictordf['StartDateTime'] = pd.to_datetime(predictordf['StartTime'], utc=True)
	predictordf['StartDate'] = pd.to_datetime(predictordf['StartDateTime']).dt.date
	predictordf['EndDateTime'] = pd.to_datetime(predictordf['EndTime'], utc=True)
	predictordf['EndDate'] = pd.to_datetime(predictordf['EndDateTime']).dt.date
	predictordf['TotalWaitingTime']=  (pd.to_datetime(predictordf['EndTime'], utc=True)-pd.to_datetime(predictordf['StartTime'], utc=True))
	minstartdate=min(predictordf['StartDate'])
	maxenddate=max(predictordf['EndDate'])

	predictordatedataframe = pd.DataFrame({'date':pd.date_range(start=minstartdate, end=maxenddate, freq=timeframe),'tokenproduced':0,'tokenconsumed':0,'tokenleft':0,'WaitingTime':0,'Count':0})
	for index, row in predictordatedataframe.iterrows():
		currentdate=row['date']
		produced=0
		left=0
		consumed=0
		waiting=td(days=0)
		waitingdays=0
		#print(type(waiting))
		count=0
		#if currentdate.strftime('%Y-%m-%d')<='1999-10-13':
		#	continue
		print(currentdate.strftime('%Y-%m-%d'))
		for indexdata, rowdata in predictordf.iterrows():
			StartDate=rowdata['StartDate']
			EndDate=rowdata['EndDate']
			#TotalWaitingTime=rowdata['TotalWaitingTime']
			TotalWaitingTime=rowdata['TotalWaitingTime']
			#print(type(waiting)," ",type(TotalWaitingTime))
			WaitingTimeTillDate=currentdate+td(hours=24)
			if currentdate.date()==StartDate:
				produced=produced+1
			if currentdate.date()==EndDate:
				consumed=consumed+1
				WaitingTimeTillDate=rowdata['EndDateTime']
			if currentdate.date()<EndDate and currentdate.date()>=StartDate:
				left=left+1
			if currentdate.date()<=EndDate and currentdate.date()>=StartDate:
				TotalWaitingTime=WaitingTimeTillDate.replace(tzinfo=None)-rowdata['StartDateTime'].replace(tzinfo=None)
				if waiting is None:
					waiting=TotalWaitingTime
				else:
					if waiting.days<100000:
						waiting=waiting+TotalWaitingTime
						waitingdays=waiting.days
					else :
						waitingdays=TotalWaitingTime.days+waitingdays
				count=count+1
		predictordatedataframe.at[index, 'tokenproduced']=produced
		predictordatedataframe.at[index, 'tokenconsumed']=consumed
		predictordatedataframe.at[index, 'tokenleft']=left
		if waiting.days<100000:
			predictordatedataframe.at[index, 'WaitingTime']=waiting
		else:
			predictordatedataframe.at[index, 'WaitingTime']=waitingdays
		predictordatedataframe.at[index, 'Count']=count
	return predictordatedataframe

def create_concurrency_frame(df, Groups, freq="5T"):
    """
    Compute a dataframe for plotting of concurrent
    events used in the associated plotting functions

    input:  pandas DF log in a double timestamp format
            list-like of Group Objects
            pandsa freq str

    output: pandas DF containing the count of
            concurrent activities per group on
            a freq-level
    """

    df = df.copy()
    df = df.loc[
        df[xes.DEFAULT_TRACEID_KEY].isin(
            utils.flatten([group.members for group in Groups])
        ),
        :,
    ]

    for group in Groups:
        df.loc[:, group.name] = df[xes.DEFAULT_TRACEID_KEY].isin(group.members)

    df = df.drop(["case:concept:name", xes.DEFAULT_TRACEID_KEY], axis=1)

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

    agg_func = {group.name: sum for group in Groups}

    date_frame = df.groupby(pd.Grouper(key="interpolate_date", freq=freq)).agg(agg_func)

    return date_frame


def create_plotting_data(log, file_format, log_information):
    """
    Transforms a log, such that it can be easer
    used for plotting, removes unnecessary data,
    creates df from xes data, and renames columns

    input: XES/CSV log ,
           file_format str,
           log_information django session dict

    output: pandas df with pm4py default names for attributes in a two timestamp format
    """
    if file_format == "csv":

        # Select only the Relevant columns of the Dataframe
        if log_information["log_type"] == "noninterval":

            # Project the Log onto the Group activities

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

def create_analysis_dataframe(log, net,initial_marking, final_marking, group):
    df=getdataframe(log, net,initial_marking, final_marking, group)
    index=df.index.values
    df.insert( 0, column='index',value = index+1)
    df['totaltokenleft'] = df['tokenleft'].cumsum()
    def categorise(row):
        if row['index']==0:
            return 0
        return row['totaltokenleft']/row['index']
    df['Averagetokenleft'] = df.apply(lambda row: categorise(row), axis=1)

    df['totaltokenconsumed'] = df['tokenconsumed'].cumsum()
    def categorise(row):
        if row['index']==0:
            return 0
        return row['totaltokenconsumed']/row['index']
    df['Averagetokenconsumed'] = df.apply(lambda row: categorise(row), axis=1)
    df['totaltokenproduced'] = df['tokenproduced'].cumsum()
    def categorise(row):
        if row['index']==0:
            return 0
        return row['totaltokenproduced']/row['index']
    df['Averagetokenproduced'] = df.apply(lambda row: categorise(row), axis=1)
    def categorise(row):
        if type( row['WaitingTime']) is int :
            return row['WaitingTime']
        return row['WaitingTime'].days
    df['WaitingDays'] = df.apply(lambda row: categorise(row), axis=1)

    def categorise(row):
        if row['Count']==0:
            return 0
        return row['WaitingDays']/row['Count']
    df['AverageWaitingTime'] = df.apply(lambda row: categorise(row), axis=1)
    AverageWaitingTimemean=df[df['AverageWaitingTime']!=0][["AverageWaitingTime"]].mean()
    def categorise(row):
        if row['AverageWaitingTime'] >= 0.5 :
            return 1
        return 0
    df['delayed'] = df.apply(lambda row: categorise(row), axis=1)
    df['rolledmean']=df['tokenconsumed'].rolling(30,  min_periods=1, win_type='gaussian').mean(std=100)
    def categorise(row):
        if row['rolledmean']/max(row['tokenconsumed'],1) < 0.3 and row['tokenconsumed']>0 :
            return 1
        return 0

    df['batched'] = df.apply(lambda row: categorise(row), axis=1)
    algo_python = rpt.Pelt(model="rbf", jump=2, min_size=1).fit(df[['tokenconsumed']])  # written in pure python
    penalty_value = 1  # beta
    result = algo_python.predict(pen=penalty_value)
    df['chunkmean'] = 0
    df['chunkindex'] = 1
    start=0
    i=1
    for index in result:
        df['chunkmean'].iloc[start:index]=df[ ['tokenconsumed'] ].iloc[start:index].mean(axis=0)[0]
        df['chunkindex'].iloc[start:index]=i
        i=i+1
        start=index
    def categorise(row):
        global sensitivity
        if row['chunkmean']*sensitivity < row['tokenconsumed'] :
            return 1
        return 0
    df['chunkbatched'] = df.apply(lambda row: categorise(row), axis=1)
    return df

def set_sensitivity(param_sensitivity):
    global sensitivity
    sensitivity=float(param_sensitivity)
    return

def set_timeframe(param_timeframe):
    global timeframe
    timeframe=param_timeframe
    return