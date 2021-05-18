from logging import Logger, LoggerAdapter
import shutil

import re
import os
import json
from datetime import datetime


from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery

from pm4py.visualization.dfg import visualizer as dfg_visualization


# Django Dependencies
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages

# Application Modules
import group_analysis.utils as utils
import group_analysis.group_managment as gm
import group_analysis.plotting as plotting
import group_analysis.log_import_util as log_import
import group_analysis.datetime_utils as dt_utils
from group_analysis.group_managment import Group

import pandas as pd






# Create your views here.

def perspective(request):
    event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
    load_log_succes = False
    
    
    

    # TODO Running Example, on how to display Plot

    # Use this to include it in the UI

    if settings.EVENT_LOG_NAME != ":notset:":

        
        event_log = os.path.join(event_logs_path, settings.EVENT_LOG_NAME)
        log_format = log_import.get_log_format(settings.EVENT_LOG_NAME)

        print(log_format)

        # Import the Log considering the given Format
        log = log_import.log_import(event_log, log_format)
        load_log_succes = True


    if request.method == 'POST':
        if "uploadButton" in request.POST:
            print("in request")
        event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")

        if settings.EVENT_LOG_NAME == ':notset:':
            return HttpResponseRedirect(request.path_info)

        return render(request,'perspective_view.html', {'log_name': settings.EVENT_LOG_NAME, 'data':this_data})

    else:

        if load_log_succes:
            dfg = dfg_discovery.apply(log)
            this_data, temp_file = dfg_to_g6(dfg)
            re.escape(temp_file)
            network = {}   
            return render(request, 'perspective_view.html', {'log_name': settings.EVENT_LOG_NAME, 'json_file': temp_file, 'data':json.dumps(this_data)})

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

       
            































