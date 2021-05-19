import json
import traceback
from pm4py.algo.filtering.log.attributes import attributes_filter
from functools import partial
from pm4py.util import constants
import numpy as np
from pm4py.objects.log.importer.xes import importer as xes_import_factory
from pm4py.algo.discovery.dfg import algorithm as dfg_factory
from pm4py.visualization.dfg import visualizer as dfg_vis_factory

import os

def import_pattern_json(path):
    '''
    Returns the pattern.json specified in the path argument
    '''
    patterns = None
    try:
        json_data = open(path, "r").read()
        patterns = json.loads(json_data)
        if not is_valid_user_input(patterns):
            print('There apears to be an error in the provided user patterns. Patterns will not be abstracted')
    except Exception as e:
        print('User Patterns could not be loaded. Patterns will not be abstracted')
        print(traceback.format_exc())
        return

    return patterns


def check_valid_json(file):
    '''
    Description: get data from json file and check its validity
    Used: to check whether user input userpattern required json format
    Input: json file path
    Output: return True if valid json format, otherwise return false
    '''
    try:
        json_data = open(path, "r").read()
        patterns = json.loads(json_data)
        if not is_valid_user_input(patterns):
            msg = "%s is not the XES/CSV file" % file
            raise argparse.ArgumentTypeError(msg)
        else:
            return file
    except Exception as e:
        print(
            '''error occured during the loading the xes file. '''
            '''Please check if the file is valid XES\n\n''', e)
        exit(0)
        return False


def is_valid_user_input(patterns):
    '''given the input of a pattern.json file it returns
    a trruth value of weather or not it is a valid patter input'''
    if type(patterns) != list:
        return False

    ids = []
    names = []
    for element in patterns:

        if type(element) != dict:
            return False

        if 'ID' not in element.keys():
            return False
        if type(element['ID']) != int:
            return False
        ids.append(element['ID'])

        if 'Name' not in element.keys():
            return False
        if type(element['Name']) != str:
            return False
        names.append(element['Name'])

        if 'Pattern' not in element.keys():
            return False
        if type(element['Pattern']) != list:
            return False
        for event in element['Pattern']:
            if type(event) != str:
                return False

    if len(set(ids)) != len(ids):
        return False
    if len(set(names)) != len(names):
        return False

    return True


def export_process_model(dfgModel, log, filename):
    '''
    Description: to export graphical process model in .svg format
    using pm4py library function
    Used: generate and export process model under provided file name
    Input: dfgModel, log file, file name
    Output: N/A
    '''

    # dfg = dfg_factory.apply(log, variant="performance")
    parameters = {"format": "svg"}
    gviz = dfg_vis_factory.apply(
                                dfgModel, log=log,
                                variant="frequency",
                                parameters=parameters
                                )
    dfg_vis_factory.save(gviz, filename)

def generate_process_model(log):
    '''
    Description: to generate graphical process model in
                .svg format using pm4py library function
    Used: generate process model under provided log
    Input: log file
    Output: Display process model
    '''

    dfg = dfg_factory.apply(log)
    '''To decorate DFG with the frequency of activities'''
    gviz = dfg_vis_factory.apply(dfg, log=log, variant="frequency")
    dfg_vis_factory.view(gviz)
    return dfg

def flatten(ls):
    """
    Flattens a list of list into a single list
    input ls, List of Lists
    output list
    """

    return [item for sublist in ls for item in sublist]


def first_last_nonzero(arr, axis, invalid_val=-1):
    """
    Fast search for the first and last values in each column that isn't zero. 
    """
    mask = arr!=0
    val = arr.shape[axis] - np.flip(mask, axis=axis).argmax(axis=axis) - 1

    return np.where(mask.any(axis=axis), mask.argmax(axis=axis), invalid_val), np.where(mask.any(axis=axis), val, invalid_val)
