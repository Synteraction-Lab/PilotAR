# coding=utf-8
import os
import time
import datetime
import csv
from Utilities.common_utilities import get_role

MANIPULATION_REALTIME = "realtime"
MANIPULATION_TIME = "time"
MANIPULATION_TYPE = "type"
MANIPULATION_FUNC = "func"
MANIPULATION_DATA = "data"
MANIPULATION_NOTE = "note"
MANIPULATION_ROLE = "role"

ANNOTATION_TYPE = "type"
ANNOTATION_KEY = "key"
ANNOTATION_COLOR = "color"
ANNOTATION_FUNC = "func"
ANNOTATION_IS_SHOW = "is_show"

ITEM = "item"
DETAILS = "details"


def get_tzinitials():
    try:
        if time.tzname:
            non_local, _ = time.tzname
            initials = [word[0] for word in non_local.split(" ")]
            result = "".join(initials)

            if result == "MPST": return "SGT"
            return result
    except:
        # Require more timezone testing to see possible exceptions
        return "SGT"


def get_datetime():
    tzone = get_tzinitials()
    time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return tzone + " " + time

def get_manipulation_log_file(participant_session):
    role = get_role()
    if role == 'Wizard':
        return f'data/{participant_session}/wizard_task_info.csv'
    if role == 'Observer':
        return f'data/{participant_session}/observer_task_info.csv'
    return f'data/{participant_session}/task_info.csv'


def log_manipulation_info(participant_session, manipulation_time, manipulation_type, manipulation_func, color="white",
                          manipulation_data="N.A.", manipulation_note='""'):
    file_name = get_manipulation_log_file(participant_session)

    if not is_file_exists(file_name):
        write_data(file_name,
                   f'{MANIPULATION_TIME},{MANIPULATION_TYPE},{MANIPULATION_FUNC},{ANNOTATION_COLOR},'
                   f'{MANIPULATION_DATA},{MANIPULATION_NOTE},{MANIPULATION_ROLE},{MANIPULATION_REALTIME}\n')

    write_data(file_name,
               f'{manipulation_time},{manipulation_type},{manipulation_func},{color},{manipulation_data},'
               f'{manipulation_note},{get_role()},{get_datetime()}\n')


def record_customized_annotations(file_name, annotation_type, key, color, func, is_show):
    if not is_file_exists(file_name):
        write_data(file_name,
                   f'{ANNOTATION_TYPE},{ANNOTATION_KEY},{ANNOTATION_COLOR},{ANNOTATION_FUNC},{ANNOTATION_IS_SHOW}\n')

    write_data(file_name,
               f'{annotation_type},{key},{color},{func},{is_show}\n')


def record_customized_checklist(file_name, details):
    if not is_file_exists(file_name):
        write_data(file_name, f'{DETAILS}\n')

    write_data(file_name, f'{details}\n')


def record_device_config(file_name, item, details):
    if not is_file_exists(file_name):
        write_data(file_name, f'{ITEM},{DETAILS}\n')

    write_data(file_name, f'{item},{details}\n')


def record_is_transcribe_complete(participant_session, is_complete):
    file_name = f'data/{participant_session}/transcribe_is_complete.txt'
    write_data(file_name, is_complete, "w")


def read_is_transcribe_complete_file(participant_session):
    file_name = f'data/{participant_session}/transcribe_is_complete.txt'
    try:
        with open(file_name) as f:
            line = f.readline()
            return line == "TRUE"
    except Exception as e:
        print("Failed to read: ", file_name, e)
        return -1


def write_data(file_name, data, write_type="a"):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    try:
        file = open(file_name, write_type)
        file.write(data)
        file.close()
    except Exception as e:
        print("Failed to write: ", e)


def is_file_exists(file_name):
    return os.path.exists(file_name)
