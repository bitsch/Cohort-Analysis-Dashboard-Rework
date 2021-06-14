import re
import os
import json
from datetime import datetime
from django.http.response import JsonResponse


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

from pm4py.algo.filtering.pandas.variants import variants_filter
from pm4py.algo.filtering.pandas.attributes import attributes_filter
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
            caseID=request.GET.get('caseID', '')
            variantID=request.GET.get('variantID', '')
            listCaseID=[caseID]
            result = stats.get_log_statistics(log, log_format, log_information)
            filteredresult=None
            if caseID != "":
                filtered_log = pm4py.filter_event_attribute_values(log, "case:concept:name", listCaseID, level="case", retain=True)
                dfg = dfg_discovery.apply(filtered_log)
            elif variantID!='':
                variantID=variantID[8:]
                intVariantID=int(variantID)
                variants=case_statistics.get_variants_df(log,
                                          parameters={case_statistics.Parameters.CASE_ID_KEY: "case:concept:name",
                                                      case_statistics.Parameters.ACTIVITY_KEY: "concept:name"})
                variant=[variants.variant[intVariantID]]
                filtered_log = variants_filter.apply(log, variant,
                                          parameters={variants_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                      variants_filter.Parameters.ACTIVITY_KEY: "concept:name"})
                dfg = dfg_discovery.apply(filtered_log)
                filteredresult = stats.get_log_statistics(filtered_log, log_format, log_information)
                filteredresult["Nunique_Activities"]= len(activites)

            else :
                dfg = dfg_discovery.apply(log)
                

            this_data, temp_file = plotting.dfg_to_g6(dfg)
            re.escape(temp_file)
            network = {}

            result["Nunique_Activities"] = len(activites)
            if filteredresult is None:
                filteredresult=result
            
            return render(
                request,
                "perspective_view.html",
                {
                    "log_name": settings.EVENT_LOG_NAME,
                    "json_file": temp_file,
                    "data": json.dumps(this_data),
                    "activities": activites,
                    "result": result,
                    "filteredresult": filteredresult,
                },
            )

        else:

            return render(request, "perspective_view.html")



def  activity_filter(request):
    event_logs_path = os.path.join(settings.MEDIA_ROOT, "event_logs")
    load_log_succes = False
    log_information = None
    filteredresult=None
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
        selected_activity = request.POST["selected_activity"]
        result = stats.get_log_statistics(log, log_format, log_information)
        filtered_log = pm4py.filter_event_attribute_values(log, log_information["concept_name"], [selected_activity], level="case", retain=True)
        filteredresult = stats.get_log_statistics(filtered_log, log_format, log_information)

        dfg = dfg_discovery.apply(filtered_log)
        this_data, temp_file = plotting.dfg_to_g6(dfg)
        re.escape(temp_file)
        network = {}
        if filteredresult is None:
            filteredresult=result
        result["Nunique_Activities"] = len(activites)



    message = {"success": True ,"responseText": "Inactivated successfully!"}
    return JsonResponse(message)

def change_view(request):
    if request.method == "POST":
        selected_view = request.POST["selected_view"]
    message = {"success": True, "responseText": "Inactivated successfully!"}
    return JsonResponse(message)