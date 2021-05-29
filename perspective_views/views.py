import re
import os
import json
from datetime import datetime
import pandas as pd


from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.statistics.traces.pandas import case_statistics
import pm4py

# Django Dependencies
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.conf import settings

# Application Modules
import perspective_views.plotting.plot_creation as plotting
import perspective_views.retrieval.statistics as stats
import core.data_loading.data_loading as log_import

from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import interval_lifecycle, dataframe_utils
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py import get_trace_attributes
from pm4py import get_attributes
from pm4py.objects.log.util.sampling import sample


# Create your views here.


def perspective(request):
    event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
    load_log_succes = False
    log_information = None

    # TODO Load the Log Information, else throw/redirect to Log Selection
    if "current_log" in request.session and request.session["current_log"] is not None:
        log_information = request.session["current_log"]
        print(log_information)

    if log_information is not None:

        event_log = os.path.join(event_logs_path, log_information["log_name"])
        log_format = log_import.get_log_format(log_information["log_name"])

        # Import the Log considering the given Format
        log, activites = log_import.log_import(event_log, log_format, log_information)
        load_log_succes = True

    if request.method == "POST":
        # TODO Throw some error
        print("Not yet implemented")

    else:

        if load_log_succes:

            dfg = dfg_discovery.apply(log)
            this_data, temp_file = plotting.dfg_to_g6(dfg)
            re.escape(temp_file)
            network = {}

            result = stats.get_log_statistics(log, log_format, log_information)

            result["Nunique_Activities"] = len(activites)

            return render(
                request,
                "perspective_view.html",
                {
                    "log_name": settings.EVENT_LOG_NAME,
                    "json_file": temp_file,
                    "data": json.dumps(this_data),
                    "result": result,
                },
            )

        else:

            return render(request, "perspective_view.html")
