from json.encoder import JSONEncoder
import re
import os
import json
from datetime import datetime


# Django Dependencies
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, render
from django.conf import settings
import re
from django.http import JsonResponse

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore


# Application Modules

# Create your views here.

def group_management(request):
    active_groups = None
    activites = None

    ## Export this into a general function checking existance of the values in the session, for activities, we might assume this
    # But better be safe than sorry 
    if 'activites' in request.session: 
        activites = request.session["activites"]

    if 'group_details' in request.session:
        active_groups = get_active_groups(request)
        
    context = {'activites' : activites,
               'active_group_details' : active_groups
              }

    return render(request, 'create_group_view.html', context)



def save_group_info(request):
    context = {
        'activites' : request.session["activites"],
    }
    if request.method == 'POST':
        if "create_new_group" in request.POST:
            print(dict(request.POST.items()))
        group_name = request.POST['group_name']
        selected_activities = request.POST['selected_activities']
        status = 'active'
        data = {}
        data[group_name] = {
            'group_name' : group_name,
            'selected_activities' : selected_activities,
            'status' : 'active'
        }
        if('group_details' in request.session and request.session['group_details'] != None):
            saved_dict = request.session['group_details']
            saved_dict.update(data)
            request.session['group_details'] = saved_dict
        else:
            request.session['group_details'] = data
    message = {
        'success': True,
        'responseText': 'Saved successfully!'
    }

    return JsonResponse(message);



def get_active_groups(request):
    
    if request.session['group_details'] is None: 
        return None
    
    existing_groups = request.session['group_details']
    datas = {}
    counter = 1
    for key, value in existing_groups.items():
        if(existing_groups[key]['status'] == "active"):
            group_name = key
            number_of_activities = format(len(existing_groups[key]['selected_activities'].split(',')))
            data = {
                'group_name' : group_name,
                'number_of_activities' : number_of_activities
            }
            datas[counter] = data
            counter = counter+1
    return datas


def change_group_status(request):
    abc =""
    if request.method == 'POST':
        SESSION_SAVE_EVERY_REQUEST=True
        group_name = request.POST['group_name']
        existing_groups = request.session['group_details']
        for key, value in existing_groups.items():
            if (key == group_name and existing_groups[key]['status'] == "active"):
                request.session['group_details'][key]['status'] = "inactive"
                request.session.save()
    message = {
        'success': True,
        'responseText': 'Inactivated successfully!'
    }
    print(request.POST)
    return JsonResponse(message);


























