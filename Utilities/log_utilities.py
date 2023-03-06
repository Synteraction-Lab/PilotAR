# coding=utf-8
import os

MANIPULATION_TIME = "time"
MANIPULATION_TYPE = "type"
MANIPULATION_FUNC = "func"
MANIPULATION_DATA = "data"
MANIPULATION_NOTE = "note"

ANNOTATION_TYPE = "type"
ANNOTATION_KEY = "key"
ANNOTATION_COLOR = "color"
ANNOTATION_FUNC = "func"
ANNOTATION_IS_SHOW = "is_show"

ITEM = "item"
DETAILS = "details"


def _get_manipulation_log_file(participant_session):
    return f'data/{participant_session}/task_info.csv'


def log_manipulation_info(participant_session, manipulation_time, manipulation_type, manipulation_func, color="white",
                          manipulation_data="N.A.", manipulation_note='""'):
    file_name = _get_manipulation_log_file(participant_session)

    if not is_file_exists(file_name):
        append_data(file_name,
                    f'{MANIPULATION_TIME},{MANIPULATION_TYPE},{MANIPULATION_FUNC},{MANIPULATION_DATA},'
                    f'{ANNOTATION_COLOR},{MANIPULATION_NOTE}\n')

    append_data(file_name,
                f'{manipulation_time},{manipulation_type},{manipulation_func},{color},{manipulation_data},'
                f'{manipulation_note}\n')


def record_customized_annotations(file_name, annotation_type, key, color, func, is_show):
    if not is_file_exists(file_name):
        append_data(file_name,
                    f'{ANNOTATION_TYPE},{ANNOTATION_KEY},{ANNOTATION_COLOR},{ANNOTATION_FUNC},{ANNOTATION_IS_SHOW}\n')

    append_data(file_name,
                f'{annotation_type},{key},{color},{func},{is_show}\n')


def record_customized_checklist(file_name, details):
    if not is_file_exists(file_name):
        append_data(file_name, f'{DETAILS}\n')

    append_data(file_name, f'{details}\n')


def record_device_config(file_name, item, details):
    if not is_file_exists(file_name):
        append_data(file_name, f'{ITEM},{DETAILS}\n')

    append_data(file_name, f'{item},{details}\n')


def append_data(file_name, data):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    try:
        file = open(file_name, "a")
        file.write(data)
        file.close()
    except Exception as e:
        print("Failed to write: ", e.__class__)


def is_file_exists(file_name):
    return os.path.exists(file_name)
