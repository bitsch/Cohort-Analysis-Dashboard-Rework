import re
import os
import json
from datetime import datetime


from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.algo.organizational_mining.resource_profiles import algorithm
from pm4py.algo.filtering.log.variants import variants_filter

from pm4py.statistics.traces.pandas import case_statistics


# Django Dependencies
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.conf import settings

# Application Modules

import group_analysis.log_import_util as log_import

import pandas as pd



# Create your views here.

def perspective(request):
    log_information = request.session["current_log"]
    event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
    load_log_succes = False


    #TODO Load the Log Information, else throw/redirect to Log Selection
    if "current_log" in request.session and request.session["current_log"] is not None: 
        log_information = request.session["current_log"]
        print(log_information)

    if log_information is not None:

        event_log = os.path.join(event_logs_path, log_information["log_name"])
        log_format = log_import.get_log_format(log_information["log_name"])

        # Import the Log considering the given Format
        log = log_import.log_import(event_log, log_format, log_information)
        load_log_succes = True

    if request.method == 'POST':
        # TODO Throw some error 
        print("Not yet implemented")


    else:

        if load_log_succes:

            dfg = dfg_discovery.apply(log)
            this_data, temp_file = dfg_to_g6(dfg)
            re.escape(temp_file)
            network = {}   
            variants = variants_filter.get_variants(log)
            return render(request, 'perspective_view.html', {'log_name': settings.EVENT_LOG_NAME, 'json_file': temp_file, 'data':json.dumps(this_data),'variant_count':len(variants)})

        else:

             return render(request, 'perspective_view.html')

def dfg_to_g6(dfg):
    unique_nodes = []

    for i in dfg:
        unique_nodes.extend(i)
    unique_nodes = list(set(unique_nodes))

    unique_nodes_dict = {}

    for index, node in enumerate(unique_nodes):
        unique_nodes_dict[node] = "node_" + str(index)

    nodes = [{'id': unique_nodes_dict[i], 'label': i} for i in unique_nodes_dict]
    edges = [{'from': unique_nodes_dict[i[0]], 'to': unique_nodes_dict[i[1]], "data": {"freq": dfg[i]}} for i in
             dfg]
    data = {
        "nodes": nodes,
        "edges": edges,
    }
    temp_path = os.path.join(settings.MEDIA_ROOT, "temp")
    temp_file = os.path.join(temp_path, 'data.json')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data, temp_file

       
            































