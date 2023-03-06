import ast
import os
import pandas as pd

from Utilities.annotation_utilities import FUNC_START, FUNC_STOP, FUNC_LIST


class Task:
    def __init__(self, id, timestamp, type, func, color, data, notes, folder_path=os.path.join("data", "p1_1"),
                 is_bumped=False):
        self.id = id
        self.is_bumped = is_bumped
        self.timestamp = timestamp
        str(self.timestamp).zfill(8)
        self.data = data
        self.display_type = type
        self.func = func
        self.color = color
        self.notes = notes
        self.folder_path = folder_path
        self.image_file_name = ""
        self.is_selected = True
        self.type_colors = {}
        if func == FUNC_LIST['screenshot_whole'] or func == FUNC_LIST['screenshot_roi']:
            self.image_file_name = self.timestamp.replace(":", "_")
        elif func == FUNC_LIST['mark']:
            self.coordinates = ast.literal_eval(data)
            self.image_file_name = self.timestamp.replace(":", "_")
        elif type == "start":
            self.func = FUNC_START
        elif type == "stop":
            self.func = FUNC_STOP

    def get_id(self):
        return self.id

    def get_is_bumped(self):
        return self.is_bumped

    def set_is_bumped(self, is_bumped):
        self.is_bumped = is_bumped

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp
        if self.func == FUNC_LIST['screenshot_whole'] or self.func == FUNC_LIST['screenshot_roi'] \
                or self.func == FUNC_LIST['mark']:
            updated_file_name = self.timestamp.replace(":", "_")
            os.rename(os.path.join(self.folder_path, self.image_file_name + ".png"),
                      os.path.join(self.folder_path, updated_file_name + ".png"))
            self.image_file_name = updated_file_name

    def get_func(self):
        return self.func

    def get_display_type(self):
        return self.display_type

    def set_display_type(self, type):
        self.display_type = type

    def set_func(self, func):
        self.func = func

    def get_data(self):
        if self.func == FUNC_LIST['mark']:
            return "x: " + str(self.coordinates.get('x', 0)) + ", y: " + str(self.coordinates.get('y', 0))
        return self.data

    def get_notes(self):
        return self.notes

    def get_color(self):
        return self.color

    def set_color(self):
        # get colors from session's customization csv file (if haven't gotten before)
        if len(self.type_colors) == 0:
            file_path = os.path.join(self.folder_path, 'customization.csv')
            df = pd.read_csv(file_path)
            for index, row in df.iterrows():
                self.type_colors.update({row['func']: row['color']})
        self.color = self.type_colors[self.func]

    def is_notes_existing(self, returning_marker=True):
        if returning_marker:
            return "√" if self.notes != "" else "×"
        return True if self.notes != "" else False

    def get_display_notes(self):
        if len(self.notes) > 100:
            return self.notes[0:99] + " ..."
        return self.notes

    def set_notes(self, notes):
        self.notes = notes

    def get_image_name(self):
        return self.image_file_name

    def get_is_selected(self):
        return self.is_selected

    def set_is_selected(self, is_selected):
        self.is_selected = is_selected

    def __str__(self):
        return "Id: {}, Time: {}, Type: {}, FUNC: {}, Color: {}, Data: {}, Notes: {}, Is Bumped: {}".format(self.id,
                                                                                                 self.timestamp,
                                                                                                 self.display_type,
                                                                                                 self.func, self.color,
                                                                                                 self.data, self.notes,
                                                                                                 self.is_bumped)

    def to_dict(self):
        dict = {
            'time': self.timestamp,
            'type': self.display_type,
            'func': self.func,
            'color': self.color,
            'data': self.data,
            'note': self.notes,
            'is_bumped': self.is_bumped
        }
        return dict