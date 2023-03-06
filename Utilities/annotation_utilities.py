import os
import uuid
import csv
import pandas as pd

from Utilities import log_utilities

FILE_NAME = 'customization.csv'

FUNC_START = "start"
FUNC_STOP = "stop"
FUNC_NULL = "null"
FUNC_LIST = {'screenshot_whole': 'Whole Screenshot',
             'screenshot_roi': 'Screenshot With ROI',
             'mark': 'Focus',
             'correct': 'Correct',
             'incorrect': 'Incorrect',
             'voice': 'Voice',
             'counter': 'Counter'}


def check_saving_file(path):
    if not os.path.isdir(path):
        return False
    return True


def get_customized_annotation_df():
    file_path = os.path.join('data', FILE_NAME)
    if not os.path.isfile(file_path):
        set_default_annotations({}, file_path)
    df = pd.read_csv(file_path)
    return df


def update_current_annotation_df_for_is_show(df=None):
    if not isinstance(df, pd.DataFrame):
        df = get_customized_annotation_df()
    if 'is_show' in df:
        return df
    # by default all annotations will be shown during pilot
    no_of_rows = len(df.index)
    is_show_col = []
    for i in range(no_of_rows):
        is_show_col.append(True)
    df['is_show'] = is_show_col
    file_path = os.path.join('data', FILE_NAME)
    df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)
    return df


def set_default_annotations(customized_annotations, path):
    customized_annotations.update(
        {'screenshot': {'key': '5', 'color': 'blue', 'id': uuid.uuid4(), 'func': FUNC_LIST['screenshot_whole'], 'is_show': True}})
    customized_annotations.update({'screenshot(ROI)': {'key': '4', 'color': 'blue', 'id': uuid.uuid4(),
                                                       'func': FUNC_LIST['screenshot_roi'], 'is_show': True}})
    customized_annotations.update({'mark': {'key': '3', 'color': 'yellow', 'id': uuid.uuid4(),
                                            'func': FUNC_LIST['mark'], 'is_show': True}})
    customized_annotations.update({'correct': {'key': '2', 'color': 'green', 'id': uuid.uuid4(),
                                               'func': FUNC_LIST['correct'], 'is_show': True}})
    customized_annotations.update({'incorrect': {'key': '1', 'color': 'red', 'id': uuid.uuid4(),
                                                 'func': FUNC_LIST['incorrect'], 'is_show': True}})
    customized_annotations.update({'voice': {'key': 'N.A.', 'color': 'darkpurple', 'id': uuid.uuid4(),
                                             'func': FUNC_LIST['voice'], 'is_show': True}})
    __save_customized_annotations(customized_annotations, path)


def __save_customized_annotations(customized_annotations, path):
    print("Saving to: " + path)
    for annotation in customized_annotations.keys():
        log_utilities.record_customized_annotations(path, annotation,
                                                    customized_annotations[annotation]['key'],
                                                    customized_annotations[annotation]['color'],
                                                    customized_annotations[annotation]['func'],
                                                    customized_annotations[annotation]['is_show'])
