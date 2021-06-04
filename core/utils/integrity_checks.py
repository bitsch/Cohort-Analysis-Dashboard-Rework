import json
import traceback
import os


def check_valid_json(file):
    """
    Description: get data from json file and check its validity
    Used: to check whether user input userpattern required json format
    Input: json file path
    Output: return True if valid json format, otherwise return false
    """
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
            """error occured during the loading the xes file. """
            """Please check if the file is valid XES\n\n""",
            e,
        )
        exit(0)
        return False


def import_pattern_json(path):
    """
    Returns the pattern.json specified in the path argument
    """
    patterns = None
    try:
        json_data = open(path, "r").read()
        patterns = json.loads(json_data)
        if not is_valid_user_input(patterns):
            print(
                "There apears to be an error in the provided user patterns. Patterns will not be abstracted"
            )
    except Exception as e:
        print("User Patterns could not be loaded. Patterns will not be abstracted")
        print(traceback.format_exc())
        return

    return patterns


def is_valid_user_input(patterns):
    """given the input of a pattern.json file it returns
    a trruth value of weather or not it is a valid patter input"""
    if type(patterns) != list:
        return False

    ids = []
    names = []
    for element in patterns:

        if type(element) != dict:
            return False

        if "ID" not in element.keys():
            return False
        if type(element["ID"]) != int:
            return False
        ids.append(element["ID"])

        if "Name" not in element.keys():
            return False
        if type(element["Name"]) != str:
            return False
        names.append(element["Name"])

        if "Pattern" not in element.keys():
            return False
        if type(element["Pattern"]) != list:
            return False
        for event in element["Pattern"]:
            if type(event) != str:
                return False

    if len(set(ids)) != len(ids):
        return False
    if len(set(names)) != len(names):
        return False

    return True
