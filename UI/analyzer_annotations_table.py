from UI.custom_table import CustomTable
import pandas as pd
import time
import os
import uuid
from UI.note_window import NoteWindow
import UI.UI_config
import UI.color
from UI.widget_generator import get_messagebox, get_text, get_dropdown_menu
import tkinter as tk
from Utilities.annotation_utilities import get_customized_annotation_df, FUNC_LIST
import sys
import datetime
sys.path.append("./")

_isMacOS = sys.platform.startswith('darwin')
class AnalyzerAnnotationsTable(CustomTable):
    def __init__(self, parent, row_height, header_height, header_text_color, row_normal_bg="#222222", row_selected_bg="#ACA9BB",
                 on_delete_callback=None, messagebox_callback=None, on_unclick_row_callback=None, on_clicked_row_callback=None,
                 on_clicked_multirow_callback=None, is_support_multiselect=True, pid=None, on_edit_timestamp_callback=None,
                 on_edit_type_callback=None, on_open_note_window_callback=None, on_note_window_close_callback=None):
        super().__init__(parent, row_height, header_height, header_text_color, row_normal_bg, row_selected_bg, on_delete_callback,
                         messagebox_callback, on_unclick_row_callback, on_clicked_row_callback, on_clicked_multirow_callback, is_support_multiselect)

        self.pid = pid
        self.on_open_note_window_callback = on_open_note_window_callback
        self.on_note_window_close_callback = on_note_window_close_callback
        self.on_edit_timestamp_callback = on_edit_timestamp_callback
        self.on_edit_type_callback = on_edit_type_callback

        self.annotation_df = get_customized_annotation_df()
        self.top_rows_order = []
        self.top_rows = {}
        self.is_note_window_open = False

    def set_pid(self, pid):
        self.pid = pid

    def set_customization_file_path(self, customization_file_path):
        self.annotation_df = pd.read_csv(customization_file_path)

    def insert(self, obj, cells, iid=uuid.uuid4()):
        # cells is an array of dictionary where each dict has {"value": any_type, "fg": string, "anchor": any, "tag": string}
        row_container = self.create_row_container()

        row = {"UI": row_container, "obj": obj, "is_show": True, "is_deleted": False, "is_bumped": False, "is_select_cb": None}
        self.rows[iid] = row
        counter = 0
        for col_id in self.columns:
            col = self.columns[col_id]
            col_container = self.create_col_container(row_container, col)
            col_container.bind('<Button>', lambda e,
                               r=row: self.on_clicked_row(e, r))
            # control + left click event
            click_multi_row_event_name = '<Control-Button-1>'
            if _isMacOS:
                click_multi_row_event_name = '<Command-Button-1>'
            col_container.bind(click_multi_row_event_name,
                               lambda e, r=row: self.on_clicked_multi_row(r))

            cell = cells[counter]
            if col["type"] == "text":
                cell_lbl = self.create_text_cell(col_container, cell, col)
                
                if cell["tag"] == "note":
                    cell_lbl.bind('<Configure>', lambda e: cell_lbl.config(
                        wraplength=cell_lbl.winfo_width() - 10))
                    # cell_lbl.bind('<Double-Button-1>', lambda e, col_container=col_container, c_lbl=cell_lbl, o=obj: self.on_double_click_notes_cell(col_container, c_lbl, o))
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl,
                                  o=obj: self.on_double_click_notes_cell(c_lbl, o))
                elif cell["tag"] == "timestamp":
                    cell_lbl.bind('<Double-Button-1>', lambda e, cc=col_container, c_lbl=cell_lbl,
                                  o=obj: self.on_double_click_timestamp_cell(cc, c_lbl, o))
                elif cell["tag"] == "type":
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl, o=obj: self.on_double_click_type_cell(c_lbl, o))
                elif cell["tag"] == "role":
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl, o=obj: self.on_double_click_type_cell(c_lbl, o))

                # need to bind all events binded to col_container to cell too as the cell has overlapped over the col_container
                # making the col_container to only have a very limited space to trigger the function
                cell_lbl.bind('<Button>', lambda e,
                              r=row: self.on_clicked_row(e, r))
                cell_lbl.bind(click_multi_row_event_name, lambda e,
                              r=row: self.on_clicked_multi_row(r))
            elif col["type"] == "cb":
                cell_cb = self.create_checkbox_cell(col_container)
                row["is_select_cb"] = cell_cb
                cell_cb.configure(
                    command=lambda: self.on_cb_selected(cell_cb, row))
                cell_cb.select()
            elif col["type"] == "bump":
                is_up = True
                image_name = "bump.png"
                if cell["value"] == True:
                    is_up = False
                    image_name = "remove_bump.png"
                    self.top_rows_order.append(iid)
                    self.top_rows[iid] = self.rows[iid]
                    self.rows[iid]["is_bumped"] = True

                cell_img = self.create_image_cell(col_container, col["anchor"], os.path.join("assets", image_name), 36, 36)
                cell_img.bind('<Button>', lambda e, col_c=col_container, row_iid=iid, is_up=is_up,
                              col_anchor=col["anchor"]: self.on_click_bump(col_c, row_iid, is_up, col_anchor))
            elif col["type"] == "delete":
                cell_img = self.create_delete_cell(col_container, col, iid, os.path.join("assets", "icons8-trash-24.png"))
            counter += 1
        return iid

    def on_click_bump(self, col_container, iid, is_up, col_anchor):
        for child in col_container.winfo_children():
            child.destroy()

        image_name = "bump.png"
        if is_up:
            image_name = "remove_bump.png"
            self.top_rows_order.append(iid)
            self.top_rows[iid] = self.rows[iid]
            self.rows[iid]["is_bumped"] = True
            self.rows[iid]["obj"].set_is_bumped(True)
        else:
            self.rows[iid]["is_bumped"] = False
            self.rows[iid]["obj"].set_is_bumped(False)
            del self.top_rows[iid]
            self.top_rows_order.remove(iid)

        cell_img = self.create_image_cell(col_container, col_anchor, os.path.join("assets", image_name), 36, 36)
        cell_img.bind('<Button>', lambda e, col_c=col_container, row_iid=iid, is_up=is_up,
                      col_anchor=col_anchor: self.on_click_bump(col_c, row_iid, not is_up, col_anchor))
        self.bump_rows()

    def bump_rows(self):
        current_row_no = 1
        for i in range(len(self.top_rows_order) - 1, -1, -1):
            row_iid = self.top_rows_order[i]
            self.top_rows[row_iid]["UI"].grid(row=current_row_no)
            current_row_no += 1
            if not self.top_rows[row_iid]["is_show"]:
                self.top_rows[row_iid]["UI"].grid_remove()

        sorted_rows = list(self.rows.items())

        def task_seconds(row):
            time_obj = datetime.datetime.strptime(row[1]['obj'].get_timestamp(), '%H:%M:%S')
            return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
        sorted_rows.sort(key=task_seconds)

        for row_iid, row in sorted_rows:
            if self.rows[row_iid]["is_bumped"]:
                continue
            self.rows[row_iid]["UI"].grid(row=current_row_no)
            if not self.rows[row_iid]["is_show"]:
                self.rows[row_iid]["UI"].grid_remove()
            current_row_no += 1

    def on_cb_selected(self, cb, row):
        if row["obj"] == None:
            return

        if cb.get() == 1:
            row["obj"].set_is_selected(True)
        else:
            row["obj"].set_is_selected(False)

    def select_row(self, iid):
        if not self.exists(iid) or self.rows[iid]["is_deleted"]:
            return
        self.rows[iid]["is_select_cb"].select()
        self.on_cb_selected(self.rows[iid]["is_select_cb"], self.rows[iid])

    def unselect_row(self, iid):
        if not self.exists(iid):
            return
        self.rows[iid]["is_select_cb"].deselect()
        self.on_cb_selected(self.rows[iid]["is_select_cb"], self.rows[iid])

    """
    # v1
    def on_double_click_notes_cell(self, col_container, cell_lbl, obj):
        # only supports for note column for now
        def done(event):
            #Change item value.
            updated_notes = entry.get("1.0", "end-1c")
            obj.set_notes(updated_notes)
            cell_lbl["text"] = obj.get_display_notes()
            
            entry.destroy()

        width = cell_lbl["width"]
        height = cell_lbl["height"]
        # display the entry  
        entry = get_text(col_container)  # create edition entry
        entry.place(width=width, height=height, anchor='nw')  # display entry on top of cell
        entry.insert(1.0, obj.get_notes())
        entry.bind('<Leave>', lambda e: entry.destroy())  # on mouse cursor leave the entry area, destroy the entry widget
        entry.bind('<Return>', done)  # validate with Enter
        entry.focus_set()
    """

    def on_double_click_notes_cell(self, cell_lbl, obj):
        if self.is_note_window_open:
            return
        self.is_note_window_open = True
        if self.on_open_note_window_callback != None:
            self.on_open_note_window_callback()

        def on_note_window_close():
            cell_lbl["text"] = obj.get_display_notes()
            self.is_note_window_open = False
            if self.on_note_window_close_callback != None:
                self.on_note_window_close_callback()

        NoteWindow(parent=self, task=obj,
                   on_close_note_window_func=on_note_window_close, pid=self.pid)
        
    def on_double_click_timestamp_cell(self, col_container, cell_lbl, obj):
        def done(event):
            # Change item value.
            updated_timestamp = entry.get("1.0", "end-1c")
            try:
                time.strptime(updated_timestamp[:8], '%H:%M:%S')
            except ValueError:
                get_messagebox(self.parent, "Invalid timestamp", callback=self.messagebox_callback)
                return

            obj.set_timestamp(updated_timestamp)
            cell_lbl["text"] = obj.get_timestamp()
            entry.destroy()
            if self.on_edit_timestamp_callback != None:
                self.on_edit_timestamp_callback()

        width = cell_lbl["width"]
        height = cell_lbl["height"]
        # display the entry
        # create edition entry
        entry = get_text(col_container, font=UI.UI_config.TABLE_NORMAL_FONT)
        # display entry on top of cell
        entry.place(width=width, height=height, anchor='nw')
        entry.insert(1.0, obj.get_timestamp())
        # entry.bind('<Leave>', lambda e: entry.destroy())  # on mouse cursor leave the entry area, destroy the entry widget
        self.selected_object = entry

        entry.bind('<Return>', done)  # validate with Enter
        entry.focus_set()

    def on_double_click_type_cell(self, cell_lbl, obj):
        def on_type_change(choice):
            obj.set_display_type(choice)
            func = self.annotation_df[self.annotation_df['type']
                                      == choice]['func'].item()
            obj.set_func(func)
            obj.set_color()
            cell_lbl["text"] = choice
            on_leave(True)

        def on_leave(is_type_change):
            type_dropdown_menu.destroy()
            if is_type_change and self.on_edit_type_callback != None:
                self.on_edit_type_callback()

        # only can change accuracy type for now
        if not (obj.get_func() == FUNC_LIST['correct'] or obj.get_func() == FUNC_LIST['incorrect']):
            return

        width = cell_lbl["width"] - 4
        height = cell_lbl["height"] - 8
        variable = tk.StringVar()
        correct_item = self.annotation_df[self.annotation_df['func']
                                          == FUNC_LIST['correct']]['type'].item()
        incorrect_item = self.annotation_df[self.annotation_df['func']
                                            == FUNC_LIST['incorrect']]['type'].item()
        type_dropdown_menu = get_dropdown_menu(cell_lbl, variable=variable,
                                               values=[correct_item,
                                                       incorrect_item],
                                               command=on_type_change, font=UI.UI_config.TABLE_NORMAL_FONT)
        type_dropdown_menu.set(obj.get_display_type())
        type_dropdown_menu.place(width=width, height=height, anchor='nw')
        type_dropdown_menu.bind('<Leave>', lambda e: on_leave(False))

    