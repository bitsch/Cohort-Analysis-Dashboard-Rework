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

def create_group(request):
    return render(request, 'create_group_view.html')































