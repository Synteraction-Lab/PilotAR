from UI.custom_table import CustomTable
import pandas as pd
import os
import uuid
import UI.UI_config
import UI.color
from UI.widget_generator import get_messagebox, get_text, get_dropdown_menu
import tkinter as tk
from Utilities.annotation_utilities import get_customized_annotation_df, FUNC_LIST
import sys
sys.path.append("./")


class AnnotationsCustomizationTable(CustomTable):
    def __init__(self, parent, row_height, header_height, header_text_color, row_normal_bg="#222222", row_selected_bg="#ACA9BB",
                 on_delete_callback=None, messagebox_callback=None, on_unclick_row_callback=None, on_clicked_row_callback=None,
                 on_clicked_multirow_callback=None, is_support_multiselect=False, on_edit_func_callback=None,
                 on_edit_type_callback=None, on_edit_key_callback=None, on_edit_color_callback=None, on_click_pin_callback=None):
        super().__init__(parent, row_height, header_height, header_text_color, row_normal_bg, row_selected_bg, on_delete_callback,
                         messagebox_callback, on_unclick_row_callback, on_clicked_row_callback, on_clicked_multirow_callback, is_support_multiselect)

        self.on_edit_func_callback = on_edit_func_callback
        self.on_edit_type_callback = on_edit_type_callback
        self.on_edit_key_callback = on_edit_key_callback
        self.on_edit_color_callback = on_edit_color_callback
        self.on_click_pin_callback = on_click_pin_callback

        self.func_options = list(FUNC_LIST.values())
        self.color_options = list(UI.UI_config.COLOR_THEME.keys())

    def insert(self, obj, cells, iid=uuid.uuid4()):
        # cells is an array of dictionary where each dict has {"value": any_type, "fg": string, "anchor": any, "tag": string}
        row_container = self.create_row_container()

        row = {"UI": row_container, "obj": obj,
               "is_show": True, "is_deleted": False}
        self.rows[iid] = row
        counter = 0
        for col_id in self.columns:
            col = self.columns[col_id]
            col_container = self.create_col_container(row_container, col)

            cell = cells[counter]
            if col["type"] == "text":
                cell_lbl = self.create_text_cell(col_container, cell, col)
                if cell["tag"] == "func":
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl, o=obj: self.on_double_click_func_cell(c_lbl, o))
                elif cell["tag"] == "type":
                    cell_lbl.bind('<Double-Button-1>', lambda e, cc=col_container,
                                  c_lbl=cell_lbl, o=obj: self.on_double_click_type_cell(cc, c_lbl, o))
                elif cell["tag"] == "key":
                    if not (obj.get("func") != None and obj.get("func") == FUNC_LIST["voice"]):
                        cell_lbl.bind('<Double-Button-1>', lambda e, cc=col_container,
                                  c_lbl=cell_lbl, o=obj: self.on_double_click_key_cell(cc, c_lbl, o))
                elif cell["tag"] == "color":
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl, o=obj: self.on_double_click_color_cell(c_lbl, o))
            elif col["type"] == "pin":
                if obj.get("func") != None and obj.get("func") == FUNC_LIST["voice"]:
                    continue
                cell_cb = self.create_checkbox_cell(col_container)
                cell_cb.configure(
                    command=lambda: self.on_click_pin(cell_cb, iid))
                if cell["value"] == True:
                    cell_cb.select()
            elif col["type"] == "delete":
                cell_img = self.create_delete_cell(
                    col_container, col, iid, os.path.join("assets", "icons8-trash-24.png"))
            counter += 1
        return iid

    def on_double_click_func_cell(self, cell_lbl, obj):
        def on_func_change(choice):
            on_leave(True, choice)

        def on_leave(is_func_change, updated_func=""):
            func_dropdown_menu.destroy()
            if is_func_change and self.on_edit_func_callback != None:
                #self.on_edit_func_callback()
                is_successful = self.on_edit_func_callback(obj["func"], updated_func, obj["type"])
                if is_successful:
                    obj["func"] = updated_func
                    cell_lbl["text"] = updated_func

        width = cell_lbl["width"] - 4
        height = cell_lbl["height"] - 8
        variable = tk.StringVar()

        func_dropdown_menu = get_dropdown_menu(cell_lbl, variable=variable, values=self.func_options,
                                               command=on_func_change, font=UI.UI_config.TABLE_NORMAL_FONT)
        func_dropdown_menu.set(obj["func"])
        func_dropdown_menu.place(width=width, height=height, anchor='nw')
        func_dropdown_menu.bind('<Leave>', lambda e: on_leave(False))

    def on_double_click_type_cell(self, col_container, cell_lbl, obj):
        def done(event):
            # Change item value.
            updated_type = entry.get("1.0", "end-1c")
            if self.on_edit_type_callback != None:
                is_successful = self.on_edit_type_callback(obj["type"], updated_type, obj["key"])
                if is_successful:
                    obj["type"] = updated_type
                    cell_lbl["text"] = updated_type
            else:
                #obj["type"] = updated_type
                cell_lbl["text"] = updated_type
            entry.destroy()


        width = cell_lbl["width"]
        height = cell_lbl["height"]
        # display the entry
        # create edition entry
        entry = get_text(col_container, font=UI.UI_config.TABLE_NORMAL_FONT)
        # display entry on top of cell
        entry.place(width=width, height=height, anchor='nw')
        entry.insert(1.0, obj["type"])
        self.selected_object = entry

        entry.bind('<Return>', done)  # validate with Enter
        entry.focus_set()

    def on_double_click_key_cell(self, col_container, cell_lbl, obj):
        def done(event):
            # Change item value.
            updated_key = entry.get("1.0", "end-1c")
            if self.on_edit_key_callback != None:
                is_successful = self.on_edit_key_callback(obj["key"], updated_key, obj["type"])
                if is_successful:
                    obj["key"] = updated_key
                    cell_lbl["text"] = updated_key
            else:
                cell_lbl["text"] = updated_key
            entry.destroy()
        
        def limit_characters(event):
            current_val = entry.get("1.0", "end-1c")
            if len(current_val) > 1:
                entry.delete('1.0', "end-1c")
                formatted_val = current_val[:-1]
                entry.insert('1.0', formatted_val)

        width = cell_lbl["width"]
        height = cell_lbl["height"]
        # display the entry
        # create edition entry
        entry = get_text(col_container, font=UI.UI_config.TABLE_NORMAL_FONT)
        # display entry on top of cell
        entry.place(width=width, height=height, anchor='nw')
        entry.insert(1.0, obj["key"])
        self.selected_object = entry

        entry.bind('<Return>', done)  # validate with Enter
        entry.bind('<KeyRelease>', limit_characters)
        entry.focus_set()

    def on_double_click_color_cell(self, cell_lbl, obj):
        def on_color_change(choice):
            obj["color"] = choice
            cell_lbl["text"] = choice
            cell_lbl.configure(fg=UI.color.color_translation(choice))
            on_leave(True)

        def on_leave(is_color_change):
            color_dropdown_menu.destroy()
            if is_color_change and self.on_edit_color_callback != None:
                self.on_edit_color_callback(obj["color"], obj["type"])

        width = cell_lbl["width"] - 4
        height = cell_lbl["height"] - 8
        variable = tk.StringVar()

        color_dropdown_menu = get_dropdown_menu(cell_lbl, variable=variable, values=self.color_options,
                                               command=on_color_change, font=UI.UI_config.TABLE_NORMAL_FONT)
        color_dropdown_menu.set(obj["color"])
        color_dropdown_menu.place(width=width, height=height, anchor='nw')
        color_dropdown_menu.bind('<Leave>', lambda e: on_leave(False))


    def on_click_pin(self, cb, iid):
        is_show = False
        if cb.get() == 1:
            is_show = True
        if self.on_click_pin_callback != None:
            self.on_click_pin_callback(is_show, self.rows[iid]["obj"])
