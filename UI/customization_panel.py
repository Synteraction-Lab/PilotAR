import csv
import os
import tkinter as tk
import uuid
from tkinter import StringVar

# from tkinter import ttk
import pandas as pd
import ttkbootstrap as ttk

from pynput.keyboard import Listener as KeyboardListener

import UI.color
from UI.widget_generator import get_button, get_dropdown_menu, get_bordered_frame, get_entry_with_placeholder, \
    get_messagebox, get_label
from UI.custom_table_old import CustomTable
from UI.annotations_customization_table import AnnotationsCustomizationTable
from UI.UI_config import MAIN_FONT, COLOR_THEME
from Utilities import log_utilities
from Utilities.annotation_utilities import FILE_NAME, set_default_annotations, FUNC_LIST, update_current_annotation_df_for_is_show
from Utilities.key_listener import KeyListener
from Utilities.screen_capture import get_second_monitor_original_pos


class CustomizationPanel:
    def __init__(self, root=None, configuration_panel=None, workflow=None, is_run_alone=True,
                 is_minimized_window=False, on_click_pin_callback=None):
        self.selected_type = None
        self.selected_key = None
        self.selected_color = None
        self.selected_func = None
        self.key_press_flag = False
        self.is_run_alone = is_run_alone
        self.is_selected_row = False
        if configuration_panel != None:
            self.workflow = configuration_panel.workflow
        else:
            self.workflow = workflow
        self.on_click_pin_callback = on_click_pin_callback
        if self.is_run_alone:
            self.root = tk.Toplevel(root)
            self.root.title('Customization Panel')
            self.place_window_to_center()
            self.root.overrideredirect(True)
        else:
            self.root = root
            for widget in self.root.winfo_children():
                widget.destroy()

        self.configuration_panel = configuration_panel
        self.customized_annotations = {}
        self.path = os.path.join('data', FILE_NAME)
        self.pack_layout(is_minimized_window)
        self.__load_customized_annotations()
        if not is_minimized_window:
            self.key_listener = KeyListener()
            self.key_listener.set_state("customization", self.on_press)
        self.place_window_to_center()
        # for annotation in self.customized_annotations.keys():
        #     self.annotations_table.tag_configure(annotation, foreground=self.customized_annotations[annotation]['color'])
        # self.start_listener()

    def on_click_pin(self, is_show, obj):
        df = pd.read_csv(self.path)
        if obj['type'] in self.customized_annotations.keys():
            self.customized_annotations[obj['type']]['is_show'] = is_show
            df.loc[df['type'] == obj['type'], ['is_show']] = is_show
            df.to_csv(self.path, index=False)

        if self.on_click_pin_callback != None:
            self.on_click_pin_callback()

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[
                             2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))

    def on_press(self, key):
        if self.key_press_flag:
            self.key_txt.set(str(key).strip("''").lower())
            self.key_press_flag = False
            self.key_inp.config(bg="#a68f3f")
            self.enable_entry()

    def start_listener(self):
        self.keyboard_listener = KeyboardListener(on_press=self.on_press)
        self.keyboard_listener.start()

    def enable_entry(self, event=None):
        self.color_entry.config(state="normal")
        self.func_entry.config(state="normal")
        self.type_entry.config(state="normal")
        self.key_press_flag = False
        self.key_inp.config(bg="grey")

    def disable_entry(self, event=None):
        self.color_entry.config(state="disabled")
        self.func_entry.config(state="disabled")
        self.type_entry.config(state="disabled")

    def on_click_key_entry(self, event):
        if not self.key_press_flag:
            self.key_press_flag = True
            self.key_inp.config(bg="#a68f3f")
            self.disable_entry()

        else:
            self.key_press_flag = False
            self.key_inp.config(bg="grey")
            self.enable_entry()

    def parse_row(self, row):
        annotation_type, key, color, func = row[0], row[1], row[2], row[3]
        is_show = True
        if len(row) > 4:
            is_show = row[4] == 'True'
        if self.check_key_conflicts(annotation_type, key) == 1:
            get_messagebox(
                self.root, "Detect key conflicts in the config file!", workflow=self.workflow, callback=self.messagebox_callback)
            return

        if annotation_type not in self.customized_annotations.keys():
            self.customized_annotations.update({annotation_type: {'key': key, 'color': color, 'id': uuid.uuid4(),
                                                                  'func': func, 'is_show': is_show}})

        self.insert_annotation(annotation_type, key, color, func, is_show)

    def check_key_conflicts(self, annotation, key):
        if self.selected_type != annotation and self.selected_key == key:
            return -1
        return any(annotation != item and key == self.customized_annotations[item]['key'] for item in
                   self.customized_annotations)

    def has_func_conflicts(self, func):
        for item in self.customized_annotations:
            if func == self.customized_annotations[item]['func'] and func != FUNC_LIST['counter']:
                return True
        return False

    def insert_annotation(self, annotation_type, key, color, func, is_show):
        item_uuid = self.customized_annotations[annotation_type]['id']
        row_obj = {"type": annotation_type, "key": key,
                   "color": color, "func": func, "is_show": is_show}
        if self.annotations_table.exists(item_uuid):
            self.annotations_table.set(
                row_iid=item_uuid, col_id='type', value=annotation_type, row_obj=row_obj)
            self.annotations_table.set(
                row_iid=item_uuid, col_id='key', value=key, row_obj=row_obj)
            self.annotations_table.set(
                row_iid=item_uuid, col_id='func', value=func, row_obj=row_obj)
            self.annotations_table.set(row_iid=item_uuid, col_id='color', value=color, row_obj=row_obj,
                                       cell_color=UI.color.color_translation(color))
            self.annotations_table.set(
                row_iid=item_uuid, col_id='pin', value=is_show, row_obj=row_obj)
        else:
            # self.annotations_table.insert(parent='', index='end',
            #                               iid=self.customized_annotations[annotation_type]['id'],
            #                               text='', values=(annotation_type, key, color), tags=(annotation_type,))
            cells = [{"value": func, "fg": "white", "anchor": "center", "tag": "func"},
                     {"value": annotation_type, "fg": "white",
                         "anchor": "center", "tag": "type"},
                     {"value": key, "fg": "white", "anchor": "center", "tag": "key"},
                     {"value": color, "fg": UI.color.color_translation(
                         color), "anchor": "center", "tag": "color"},
                     {"value": is_show, "anchor": "center", "tag": ""},
                     {"anchor": "center", "tag": ""},]
            self.annotations_table.insert(
                row_obj, cells=cells, iid=self.customized_annotations[annotation_type]['id'])
        # self.annotations_table.tag_configure(annotation_type, foreground=color)

    def __load_customized_annotations(self):
        if not os.path.isfile(self.path):
            set_default_annotations(self.customized_annotations, self.path)

        update_current_annotation_df_for_is_show()

        with open(self.path, newline='') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)
            next(reader, None)
            for row in reader:
                self.parse_row(row)

    def delete_annotation(self, annotation):
        updated_annotations = []
        for annotation_type in self.customized_annotations.keys():
            if annotation_type == annotation["type"]:
                continue
            updated_annotations.append({"type": annotation_type, "key": self.customized_annotations[annotation_type]["key"], "color": self.customized_annotations[
                                       annotation_type]["color"], "func": self.customized_annotations[annotation_type]["func"], "is_show": self.customized_annotations[annotation_type]["is_show"]})

        df = pd.DataFrame(updated_annotations)
        file_path = os.path.join("data", 'customization.csv')
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)

        del self.customized_annotations[annotation["type"]]

    def on_click_insert(self):
        annotation_type, key, color, func = self.type_entry.get_text(), self.key_txt.get(), self.color_txt.get(), \
            self.func_txt.get()
        is_show = True
        if self.workflow is not None:
            self.workflow.lower()

        if func == "Select Function Here":
            get_messagebox(self.root, "Please select a function!", workflow=self.workflow, callback=self.messagebox_callback)
            return

        if self.check_key_conflicts(annotation_type, key) == 1:
            get_messagebox(self.root, "Please change the key!", workflow=self.workflow, callback=self.messagebox_callback)
            return

        if self.has_func_conflicts(func):
            get_messagebox(
                self.root, "Only support 1 annotation for func: \"{}\"!".format(func), workflow=self.workflow, callback=self.messagebox_callback)
            return
        
        self.customized_annotations.update({annotation_type: {'key': key, 'color': color, 'id': uuid.uuid4(),
                                                                'func': func, 'is_show': is_show}})
        log_utilities.record_customized_annotations(self.path, annotation_type,
                                                    self.customized_annotations[annotation_type]['key'],
                                                    self.customized_annotations[annotation_type]['color'],
                                                    self.customized_annotations[annotation_type]['func'],
                                                    self.customized_annotations[annotation_type]['is_show'])
        self.insert_annotation(annotation_type, key, color, func, is_show)

        get_messagebox(self.root, "Successfully Insert!",
                       workflow=self.workflow, callback=self.messagebox_callback)

    """ buggy and too complicated
    def update_annotation(self):
        annotation_type, key, color, func = self.type_entry.get_text(), self.key_txt.get(), self.color_txt.get(), \
            self.func_txt.get()
        is_show = True
        if self.workflow is not None:
            self.workflow.lower()

        if self.check_key_conflicts(annotation_type, key) == 1:
            get_messagebox(self.root, "Please change the key!",
                           workflow=self.workflow, callback=self.messagebox_callback)
            return

        # updating existing entry + change of func so must not have func conflict else violates
        # or inserting new entry so must not have func conflict else violates
        if (annotation_type in self.customized_annotations.keys() and self.selected_func != func and self.has_func_conflicts(func)) or\
                (annotation_type not in self.customized_annotations.keys() and self.has_func_conflicts(func)):
            get_messagebox(
                self.root, "Only support 1 annotation for func: \"{}\"!".format(func), workflow=self.workflow, callback=self.messagebox_callback)
            return

        df = pd.read_csv(self.path)
        # updating existing entry (same annotation type but different values for other properties)
        if annotation_type in self.customized_annotations.keys():
            self.customized_annotations[annotation_type]['key'] = key
            self.customized_annotations[annotation_type]['color'] = color
            self.customized_annotations[annotation_type]['func'] = func
            df.loc[df['type'] == annotation_type, ['key']] = key
            df.loc[df['type'] == annotation_type, ['color']] = color
            df.loc[df['type'] == annotation_type, ['func']] = func
            df.to_csv(self.path, index=False)
        # updating existing entry's (new annotation type and others)
        elif self.check_key_conflicts(annotation_type, key) == -1:
            delete_item = None
            prev_uuid = None
            for item in self.customized_annotations.keys():
                if self.customized_annotations[item]['key'] == key:
                    delete_item = item
                    prev_uuid = self.customized_annotations[item]['id']
                    break
            self.customized_annotations.pop(delete_item)
            self.customized_annotations.update({annotation_type: {'key': key, 'color': color, 'id': prev_uuid,
                                                                  'func': func, 'is_show': is_show}})
            df.loc[df['key'] == key, ['type']] = annotation_type
            df.loc[df['key'] == key, ['color']] = color
            df.loc[df['key'] == key, ['func']] = func
            df.to_csv(self.path, index=False)
        else:  # insert new entry
            self.customized_annotations.update({annotation_type: {'key': key, 'color': color, 'id': uuid.uuid4(),
                                                                  'func': func, 'is_show': is_show}})
            log_utilities.record_customized_annotations(self.path, annotation_type,
                                                        self.customized_annotations[annotation_type]['key'],
                                                        self.customized_annotations[annotation_type]['color'],
                                                        self.customized_annotations[annotation_type]['func'],
                                                        self.customized_annotations[annotation_type]['is_show'])

        self.insert_annotation(annotation_type, key, color, func, is_show)

        get_messagebox(self.root, "Successfully Update!",
                       workflow=self.workflow, callback=self.messagebox_callback)
    """

    def messagebox_callback(self):
        # self.root.attributes("-topmost", True)
        # self.root.focus()
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)

    def get_customized_annotations(self):
        return self.customized_annotations

    # def select_row(self, event):
    #     row = self.annotations_table.focus()
    #     if row == "":
    #         return
    #     row_values = self.annotations_table.item(row)['values']
    #     self.type_entry.set_text(row_values[0])
    #     self.key_txt.set(row_values[1])
    #     self.color_txt.set(row_values[2])

    # def on_clicked_row(self, row_obj):
    #     self.type_entry.set_text(row_obj["type"])
    #     self.key_txt.set(row_obj["key"])
    #     self.color_txt.set(row_obj["color"])
    #     self.func_txt.set(row_obj["func"])
    #     self.selected_type = row_obj["type"]
    #     self.selected_key = row_obj["key"]
    #     self.selected_color = row_obj["color"]
    #     self.selected_func = row_obj["func"]

    #     self.is_selected_row = True

    # def on_unclick_row(self):
    #     self.is_selected_row = False

    def on_edit_func_callback(self, original_func, updated_func, annotation_type):
        if original_func == updated_func:
            return False
        
        if self.has_func_conflicts(updated_func):
            get_messagebox(
                self.root, "Only support 1 annotation for func: \"{}\"!".format(updated_func), workflow=self.workflow, callback=self.messagebox_callback)
            return False
        
        self.customized_annotations[annotation_type]['func'] = updated_func
        df = pd.read_csv(self.path)
        df.loc[df['type'] == annotation_type, ['func']] = updated_func
        df.to_csv(self.path, index=False)
        return True

    def on_edit_type_callback(self, original_type, updated_type, annotation_key):
        if original_type == updated_type:
            return False
        
        if updated_type in self.customized_annotations.keys():
            get_messagebox(self.root, "Please change annotation type!", workflow=self.workflow, callback=self.messagebox_callback)
            return False
        
        values = self.customized_annotations[original_type]
        self.customized_annotations[updated_type] = values
        del self.customized_annotations[original_type] 
        df = pd.read_csv(self.path)
        df.loc[df['key'] == annotation_key, ['type']] = updated_type
        df.to_csv(self.path, index=False)
        return True

        
    def on_edit_key_callback(self, original_key, updated_key, annotation_type):
        if original_key == updated_key:
            return False

        if self.check_key_conflicts(annotation_type, updated_key) == 1:
            get_messagebox(self.root, "Please change the key!", workflow=self.workflow, callback=self.messagebox_callback)
            return False
        
        self.customized_annotations[annotation_type]['key'] = updated_key
        df = pd.read_csv(self.path)
        df.loc[df['type'] == annotation_type, ['key']] = updated_key
        df.to_csv(self.path, index=False)
        return True
    

    def on_edit_color_callback(self, updated_color, annotation_type):
        self.customized_annotations[annotation_type]['color'] = updated_color
        df = pd.read_csv(self.path)
        df.loc[df['type'] == annotation_type, ['color']] = updated_color
        df.to_csv(self.path, index=False)


    def on_close_window(self):
        self.root.destroy()
        if self.workflow is not None:
            self.workflow.lower()
        if self.configuration_panel is not None:
            self.configuration_panel.on_close_customization_panel()

    def pack_layout(self, is_minimized_window=False):
        self.root_frame = get_bordered_frame(self.root)
        self.root_frame.pack()
        self.annotations_table_frame = ttk.Frame(
            self.root_frame, style='light')
        self.annotations_table_frame.configure(width=730, height=250)
        self.annotations_table_frame.pack(pady=5)
        self.annotations_table_frame.pack_propagate(0)


        self.annotations_table = AnnotationsCustomizationTable(parent=self.annotations_table_frame, row_height=35, header_height=35, header_text_color="white",
                                                               on_delete_callback=self.delete_annotation, on_click_pin_callback=self.on_click_pin,
                                                               messagebox_callback=self.messagebox_callback, on_edit_type_callback=self.on_edit_type_callback,
                                                               on_edit_key_callback=self.on_edit_key_callback, on_edit_func_callback=self.on_edit_func_callback,
                                                               on_edit_color_callback=self.on_edit_color_callback)
        self.annotations_table.define_column_ids(
            ["func", "type", "key", "color", "pin", "delete"])
        self.annotations_table.column(
            "func", header_text="Function", width=150)
        self.annotations_table.column("type", header_text="Type", width=150)
        self.annotations_table.column("key", header_text="Key", width=150)
        self.annotations_table.column("color", header_text="Color", width=150)
        self.annotations_table.column(
            "pin", header_text="Pin", width=80, type="pin")
        self.annotations_table.column(
            "delete", header_text="", width=40, type="delete")

        self.close_frame = ttk.Frame(self.root_frame)
        self.close_frame.pack(pady=10, side="bottom")
        self.close_btn = get_button(
            self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

        if is_minimized_window:
            return

        self.motification_panel = ttk.Frame(self.root_frame)
        self.motification_panel.pack()
        self.add_btn = get_button(self.motification_panel, text="Insert", command=self.on_click_insert,
                                  pattern=0)
        self.add_btn.grid(column=8, row=1, columnspan=1, padx=10, pady=10)

        self.type_label = get_label(self.motification_panel, text="Type:")
        self.type_label.grid(column=0, row=1, columnspan=1, padx=10, pady=5)

        self.type_txt = StringVar()
        self.type_entry = get_entry_with_placeholder(
            self.motification_panel, placeholder="Enter annotation type here.")
        self.type_entry.grid(column=1, row=1, columnspan=1, padx=10, pady=10)
        self.type_entry.bind("<1>", self.enable_entry)

        self.key_label = get_label(self.motification_panel, text="Key:")
        self.key_label.grid(column=2, row=1, columnspan=1, padx=10, pady=5)
        self.key_label.bind("<1>", self.on_click_key_entry)

        self.key_txt = StringVar()
        self.key_txt.set("Click here & Press the key")
        self.key_inp = tk.Label(self.motification_panel, textvariable=self.key_txt, bg="grey",
                                width=20, font=MAIN_FONT)
        self.key_inp.config(bg="grey")
        self.key_inp.grid(column=3, row=1, columnspan=1, padx=10, pady=10)
        self.key_inp.bind("<1>", self.on_click_key_entry)

        self.color_label = get_label(self.motification_panel, text="Color:")
        self.color_label.grid(column=4, row=1, columnspan=1, padx=10, pady=10)

        self.color_txt = StringVar()
        self.color_txt.set("Select Color Here")
        self.color_entry = ttk.Entry(
            self.motification_panel, textvariable=self.color_txt)

        options = list(COLOR_THEME.keys())
        self.color_options = get_dropdown_menu(
            self.motification_panel, values=options, variable=self.color_txt)

        # Adding combobox drop down list
        self.color_options.grid(
            column=5, row=1, columnspan=1, padx=10, pady=10)
        self.color_entry.bind("<1>", self.enable_entry)

        self.func_label = get_label(self.motification_panel, text="Function:")
        self.func_label.grid(column=6, row=1, columnspan=1, padx=10, pady=10)

        self.func_txt = StringVar()
        self.func_txt.set("Select Function Here")
        self.func_entry = ttk.Entry(
            self.motification_panel, textvariable=self.func_txt)

        func_options = list(FUNC_LIST.values())
        # print(func_options)
        self.func_options = get_dropdown_menu(
            self.motification_panel, values=func_options, variable=self.func_txt)

        # Adding combobox drop down list
        self.func_options.grid(column=7, row=1, columnspan=1, padx=10, pady=10)
        self.func_entry.bind("<1>", self.enable_entry)


if __name__ == '__main__':
    root = tk.Tk()
    customization_panel = CustomizationPanel(root)
    root.mainloop()
