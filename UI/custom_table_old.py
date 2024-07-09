import pandas as pd
import time
from UI.confirmbox import ConfirmBox
import os
import uuid
from Utilities.common_utilities import str_to_sec
from UI.task import Task
from UI.note_window import NoteWindow
import UI.UI_config
import UI.color
from UI.widget_generator import get_checkbutton, get_messagebox, get_label, get_text, get_bordered_frame, get_image, \
    get_dropdown_menu
import tkinter as tk
from Utilities.annotation_utilities import get_customized_annotation_df, FUNC_LIST
import sys
sys.path.append("./")


# from tkinter import font

_isMacOS = sys.platform.startswith('darwin')


class CustomTable:
    def __init__(self, parent, on_clicked_row_func, on_clicked_multi_row_func, row_height, header_height,
                 header_text_color, pid=None, row_normal_bg="#222222", row_selected_bg="#ACA9BB", on_open_note_window_func=None,
                 on_note_window_close_func=None, delete_func=None, on_edit_timestamp_func=None, on_edit_type_func=None,
                 on_click_pin_func=None, messagebox_callback=None, is_support_multiselect=True, on_unclick_row_func=None):
        self.selected_object = None
        self.parent = parent
        self.on_open_note_window_func = on_open_note_window_func
        self.on_note_window_close_func = on_note_window_close_func
        self.on_clicked_row_func = on_clicked_row_func
        self.on_unclick_row_func = on_unclick_row_func
        self.on_clicked_multi_row_func = on_clicked_multi_row_func
        self.delete_func = delete_func
        self.on_edit_timestamp_func = on_edit_timestamp_func
        self.on_edit_type_func = on_edit_type_func
        self.on_click_pin_func = on_click_pin_func
        self.messagebox_callback = messagebox_callback
        self.is_support_multiselect = is_support_multiselect
        self.pid = pid

        self.hsb_width = 10
        self.vsb_width = 10
        self.vsb = tk.Scrollbar(self.parent, width=self.vsb_width, orient="vertical", highlightthickness=0,
                                borderwidth=0)
        self.hsb = tk.Scrollbar(self.parent, width=self.hsb_width, orient="horizontal", highlightthickness=0,
                                borderwidth=0)
        self.canvas = tk.Canvas(self.parent, height=self.parent["height"] - 10, highlightthickness=0, borderwidth=0,
                                yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(expand=True, fill="both")
        self.hsb.pack(side="bottom", fill="x")
        self.vsb.configure(command=self.canvas.yview)
        self.hsb.configure(command=self.canvas.xview)
        self.vsb.pack_forget()
        self.hsb.pack_forget()

        self.container = tk.Frame(
            self.canvas, highlightthickness=0, borderwidth=0)
        self.container.bind("<Configure>", lambda event: self.on_configure())

        self.parent.bindtags(self.parent.bindtags() + ("custom_table",))
        self.container.bindtags(self.container.bindtags() + ("custom_table",))
        self.canvas.bindtags(self.canvas.bindtags() + ("custom_table",))

        # for Windows/Mac OS
        # for vertical scrolling
        self.canvas.bind_class(
            "custom_table", "<MouseWheel>", lambda event: self.on_mousewheel(event, True))
        # for horizontal scrolling
        self.canvas.bind_class("custom_table", "<Shift-MouseWheel>",
                               lambda event: self.on_mousewheel(event, False))

        # for Linux
        # for vertical scrolling
        self.canvas.bind_class("custom_table", "<Button-4>",
                               lambda event: self.on_mousewheel(event, True))
        self.canvas.bind_class("custom_table", "<Button-5>",
                               lambda event: self.on_mousewheel(event, True))
        # for horizontal scrolling
        self.canvas.bind_class("custom_table", "<Shift-Button-4>",
                               lambda event: self.on_mousewheel(event, False))
        self.canvas.bind_class("custom_table", "<Shift-Button-5>",
                               lambda event: self.on_mousewheel(event, False))
        self.canvas.create_window(
            (0, 0), window=self.container, anchor='nw', tags="self.container")

        self.row_height = row_height
        self.header_height = header_height
        self.header_text_color = header_text_color
        self.row_normal_bg = row_normal_bg
        self.row_selected_bg = row_selected_bg
        self.row_width = 0
        self.no_of_columns = 0
        self.no_of_columns_set = 0
        self.columns = {}
        self.top_rows_order = []
        self.top_rows = {}
        self.rows = {}
        self.clicked_row = None
        self.clicked_multi_row = None

        self.current_table_height = 0
        self.is_scrollbar_y_visible = False
        self.is_note_window_open = False
        self.parent.bind(
            '<Button-1>', lambda event: self.destroy_object(event))
        self.annotation_df = get_customized_annotation_df()

        self.yview_pos = 0.0

    def set_customization_file_path(self, customization_file_path):
        self.annotation_df = pd.read_csv(customization_file_path)

    def on_mousewheel(self, event, is_vertical):
        x, y = self.canvas.winfo_pointerxy()
        widget_path = str(self.canvas.winfo_containing(x, y))
        if not widget_path.startswith(str(self.container)):
            return

        delta = 0
        if sys.platform == 'darwin':  # for OS X # also, if platform.system() == 'Darwin':
            delta = event.delta
        else:                            # for Windows, Linux
            delta = event.delta // 120   # event.delta is some multiple of 120
        if is_vertical:
            self.canvas.yview_scroll(int(-1*(delta)), "units")
        # else:
        #     self.canvas.xview_scroll(int(-1*(delta)), "units")

    def set_pid(self, pid):
        self.pid = pid

    def on_configure(self):
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def toggle_scrollbar_y_visibility(self):
        if self.current_table_height >= self.parent["height"] - self.hsb_width - 20:
            if not self.is_scrollbar_y_visible:
                self.canvas.pack_forget()
                self.vsb.pack(side="right", fill="y")
                self.canvas.pack(expand=True, fill="both")
                self.is_scrollbar_y_visible = True
        else:
            if self.is_scrollbar_y_visible:
                self.vsb.pack_forget()
                self.is_scrollbar_y_visible = False

    def define_column_ids(self, column_ids=[]):
        for cid in column_ids:
            self.columns[cid] = {}
        self.no_of_columns = len(column_ids)

    def column(self, col_id, header_text="", width=50, anchor=tk.CENTER, type="text"):
        self.no_of_columns_set += 1
        self.columns[col_id] = {"header_text": header_text, "width": width, "anchor": anchor, "type": type,
                                "col_no": self.no_of_columns_set}
        self.row_width += width
        if self.no_of_columns_set == self.no_of_columns:
            if self.row_width > self.parent["width"] - self.vsb_width:
                self.hsb.pack(side="bottom", fill="x")
            self.generate_headers()

    def generate_headers(self):
        self.headers_container = tk.Frame(self.container)
        self.headers_container.configure(
            height=self.header_height, width=self.row_width)
        self.headers_container.grid_propagate(0)
        self.headers_container.grid(row=0)
        self.headers_container.bindtags(
            self.headers_container.bindtags() + ("custom_table",))

        self.current_table_height += self.header_height

        # default_font = font.nametofont("TkDefaultFont")
        for col_id in self.columns:
            col = self.columns[col_id]
            # col_container = tk.Frame(self.headers_container, borderwidth=1, highlightthickness=1, highlightbackground=self.border_color, bg=self.row_normal_bg)
            col_container = get_bordered_frame(self.headers_container)
            col_container.configure(
                width=col["width"], height=self.header_height, bg=self.row_normal_bg)
            col_container.pack(side="left", fill="x", expand=True)
            col_container.pack_propagate(0)
            col_container.bindtags(
                col_container.bindtags() + ("custom_table",))

            # cell_text = tk.Label(col_container, text=col["header_text"], fg=self.header_text_color, bg=self.row_normal_bg, font=(default_font.actual()['family'], default_font.actual()['size'], 'bold'))
            cell_text = get_label(
                col_container, text=col["header_text"], pattern=3)
            cell_text.configure(fg=self.header_text_color,
                                bg=self.row_normal_bg)
            cell_text.pack(anchor=col["anchor"])
            cell_text.bindtags(cell_text.bindtags() + ("custom_table",))

    def insert(self, obj, cells, iid=uuid.uuid4()):
        # cells is an array of dictionary where each dict has {"value": any_type, "fg": string, "anchor": any, "tag": string}
        self.row_container = tk.Frame(self.container)
        self.row_container.configure(
            height=self.row_height, width=self.row_width)
        self.row_container.grid_propagate(0)
        self.row_container.grid(row=len(self.rows) + 1)
        self.row_container.bindtags(
            self.row_container.bindtags() + ("custom_table",))

        self.current_table_height += self.row_height
        self.toggle_scrollbar_y_visibility()

        row = {"UI": self.row_container, "obj": obj,
               "is_deleted": False, "is_bumped": False}
        self.rows[iid] = row
        counter = 0
        for col_id in self.columns:
            col = self.columns[col_id]
            # col_container = tk.Frame(self.row_container, borderwidth=1, highlightthickness=1, highlightbackground=self.border_color, bg=self.row_normal_bg)
            col_container = get_bordered_frame(self.row_container)
            col_container.configure(
                width=col["width"], height=self.row_height, bg=self.row_normal_bg)
            col_container.pack(side="left", fill="both", expand=True)
            col_container.pack_propagate(0)

            col_container.bind('<Button>', lambda e,
                               r=row: self.on_clicked_row(e, r))
            # control + left click event
            click_multi_row_event_name = '<Control-Button-1>'
            if _isMacOS:
                click_multi_row_event_name = '<Command-Button-1>'
            col_container.bind(click_multi_row_event_name,
                               lambda e, r=row: self.on_clicked_multi_row(r))
            col_container.bindtags(
                col_container.bindtags() + ("custom_table",))

            cell = cells[counter]
            if col["type"] == "text":
                # cell_lbl = tk.Label(col_container, text=cell["value"], justify=tk.LEFT, anchor=col["anchor"], bg=self.row_normal_bg)
                cell_lbl = get_label(
                    col_container, text=cell["value"], pattern=4)
                # must set fg using configure or else it doesn't 100% work
                cell_lbl.configure(width=col["width"] - 4, height=self.row_height - 4, fg=cell["fg"], justify=tk.LEFT,
                                   anchor=col["anchor"], bg=self.row_normal_bg)
                cell_lbl.pack(anchor=col["anchor"],
                              side="left", fill="both", expand=True)

                # cell_lbl.pack(anchor=col["anchor"], side="left", expand=True)
                if cell["tag"] == "note":
                    cell_lbl.bind('<Configure>', lambda e: cell_lbl.config(
                        wraplength=cell_lbl.winfo_width() - 10))
                    # cell_lbl.bind('<Double-Button-1>', lambda e, col_container=col_container, c_lbl=cell_lbl, o=obj: self.on_double_click_cell(col_container, c_lbl, o))
                    cell_lbl.bind('<Double-Button-1>', lambda e, c_lbl=cell_lbl,
                                  o=obj: self.on_double_click_cell(c_lbl, o))
                elif cell["tag"] == "timestamp":
                    cell_lbl.bind('<Double-Button-1>', lambda e, cc=col_container, c_lbl=cell_lbl,
                                  o=obj: self.on_double_click_timestamp_cell(cc, c_lbl, o))
                elif cell["tag"] == "type":
                    cell_lbl.bind('<Double-Button-1>',
                                  lambda e, cc=col_container, c_lbl=cell_lbl, o=obj: self.on_double_click_type_cell(cc,
                                                                                                                    c_lbl,
                                                                                                                    o))

                # need to bind all events binded to col_container to cell too as the cell has overlapped over the col_container
                # making the col_container to only have a very limited space to trigger the function
                cell_lbl.bind('<Button>', lambda e,
                              r=row: self.on_clicked_row(e, r))
                cell_lbl.bind(click_multi_row_event_name, lambda e,
                              r=row: self.on_clicked_multi_row(r))
                cell_lbl.bindtags(cell_lbl.bindtags() + ("custom_table",))
            elif col["type"] == "cb":
                cell_cb = get_checkbutton(col_container)
                cell_cb.configure(
                    command=lambda: self.on_cb_selected(cell_cb, row))
                cell_cb.select()
                # note anchor doesn't seem to work if using fill="both"
                # cell_cb.pack(side="left", expand=True, anchor=col["anchor"])
                # cell_cb.pack(side="left", padx=(
                #     col["width"] / 2) - 14, anchor=col["anchor"])
                cell_cb.pack(side="left")
                cell_cb._canvas.grid(column=1, padx=cell_cb.cget("width")/3)
                cell_cb.bindtags(cell_cb.bindtags() + ("custom_table",))
                cell_cb._canvas.bindtags(
                    cell_cb._canvas.bindtags() + ("custom_table",))
            elif col["type"] == "bump":
                is_up = True
                image_name = "bump.png"
                if cell["value"] == True:
                    is_up = False
                    image_name = "remove_bump.png"
                    self.top_rows_order.append(iid)
                    self.top_rows[iid] = self.rows[iid]
                    self.rows[iid]["is_bumped"] = True
                cell_img = get_image(col_container, os.path.join(
                    "assets", image_name), 36, 36)
                cell_img.configure(bg=self.row_normal_bg)
                cell_img.pack(anchor=col["anchor"],
                              side="left", fill="both", expand=True)
                cell_img.bind('<Button>', lambda e, col_c=col_container, row_iid=iid, is_up=is_up,
                              col_anchor=col["anchor"]: self.on_click_bump(col_c, row_iid, is_up,
                                                                           col_anchor))
                cell_img.bindtags(cell_img.bindtags() + ("custom_table",))
            elif col["type"] == "delete":
                cell_img = get_image(col_container, os.path.join(
                    "assets", "icons8-trash-24.png"))
                cell_img.configure(bg=self.row_normal_bg)
                cell_img.pack(anchor=col["anchor"],
                              side="left", fill="both", expand=True)
                cell_img.bind('<Button>', lambda e,
                              row_iid=iid: self.on_click_delete(row_iid))
                cell_img.bindtags(cell_img.bindtags() + ("custom_table",))
            elif col["type"] == "pin":
                if obj.get("func") != None and obj.get("func") == FUNC_LIST["voice"]:
                    continue
                cell_cb = get_checkbutton(col_container)
                cell_cb.configure(
                    command=lambda: self.on_click_pin(cell_cb, iid))
                if cell["value"] == True:
                    cell_cb.select()
                # note anchor doesn't seem to work if using fill="both"
                # cell_cb.pack(side="left", expand=True, anchor=col["anchor"])
                # cell_cb.pack(side="left", padx=10, anchor=col["anchor"])
                cell_cb.pack(side="left")
                cell_cb._canvas.grid(column=1, padx=cell_cb.cget("width")/3)
                cell_cb.bindtags(cell_cb.bindtags() + ("custom_table",))
            counter += 1
        return iid

    def on_click_pin(self, cb, iid):
        is_show = False
        if cb.get() == 1:
            is_show = True
        if self.on_click_pin_func != None:
            self.on_click_pin_func(is_show, self.rows[iid]["obj"])

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

        cell_img = get_image(col_container, os.path.join(
            "assets", image_name), 36, 36)
        cell_img.configure(bg=self.row_normal_bg)
        cell_img.pack(anchor=col_anchor, side="left", fill="both", expand=True)
        cell_img.bind('<Button>', lambda e, col_c=col_container, row_iid=iid, is_up=is_up,
                      col_anchor=col_anchor: self.on_click_bump(col_c, row_iid, not is_up,
                                                                col_anchor))
        cell_img.bindtags(cell_img.bindtags() + ("custom_table",))
        self.bump_rows()

    def bump_rows(self):
        current_row_no = 1
        for i in range(len(self.top_rows_order) - 1, -1, -1):
            row_iid = self.top_rows_order[i]
            self.top_rows[row_iid]["UI"].grid(row=current_row_no)
            current_row_no += 1
            if not self.top_rows[row_iid]["is_show"]:
                self.top_rows[row_iid]["UI"].grid_remove()

        for row_iid in self.rows:
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

    def on_clicked_row(self, event=None, row=None):
        if self.clicked_row != None:
            self.destroy_object(event)
            self.change_row_bg(self.clicked_row["UI"], self.row_normal_bg)
        if self.clicked_multi_row != None:
            self.change_row_bg(
                self.clicked_multi_row["UI"], self.row_normal_bg)
            self.clicked_multi_row = None
        self.clicked_row = row
        if row == None:
            return
        self.change_row_bg(row["UI"], self.row_selected_bg)
        if row["obj"] != None and self.on_clicked_row_func != None:
            self.on_clicked_row_func(row["obj"])

    # for unselect/select single/multi row
    def on_clicked_multi_row(self, row):
        if self.clicked_row == None:
            self.on_clicked_row(row)
            return

        if self.clicked_row == row:
            # unselect it
            self.change_row_bg(self.clicked_row["UI"], self.row_normal_bg)
            self.clicked_row = self.clicked_multi_row
            self.clicked_multi_row = None
            if self.on_unclick_row_func != None:
                self.on_unclick_row_func()
            return

        if not self.is_support_multiselect:
            return

        # selected another row
        if self.clicked_multi_row != None:
            if self.clicked_multi_row != row:
                get_messagebox(
                    self.parent, "Can only select up to 2 rows at a time", callback=self.messagebox_callback)
            else:
                self.change_row_bg(
                    self.clicked_multi_row["UI"], self.row_normal_bg)
                self.clicked_multi_row = None
        else:
            self.clicked_multi_row = row
            self.change_row_bg(row["UI"], self.row_selected_bg)
            if self.on_clicked_multi_row_func != None:
                self.on_clicked_multi_row_func(
                    self.clicked_row["obj"], self.clicked_multi_row["obj"])

    def change_row_bg(self, row_ui, bg):
        for col in row_ui.winfo_children():
            col.configure(bg=bg)
            for cell in col.winfo_children():
                if isinstance(cell, tk.Label):
                    cell.configure(bg=bg)

    """
    # v1
    def on_double_click_cell(self, col_container, cell_lbl, obj):
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

    # for notes
    def on_double_click_cell(self, cell_lbl, obj):
        if self.is_note_window_open:
            return
        self.is_note_window_open = True
        if self.on_open_note_window_func != None:
            self.on_open_note_window_func()

        def on_note_window_close():
            cell_lbl["text"] = obj.get_display_notes()
            self.is_note_window_open = False
            if self.on_note_window_close_func != None:
                self.on_note_window_close_func()

        NoteWindow(parent=self, task=obj,
                   on_close_note_window_func=on_note_window_close, pid=self.pid)

    def on_double_click_timestamp_cell(self, col_container, cell_lbl, obj):
        def done(event):
            # Change item value.
            updated_timestamp = entry.get("1.0", "end-1c")
            try:
                time.strptime(updated_timestamp[:8], '%H:%M:%S')
            except ValueError:
                get_messagebox(self.parent, "Invalid timestamp",
                               callback=self.messagebox_callback)
                return

            obj.set_timestamp(updated_timestamp)
            cell_lbl["text"] = obj.get_timestamp()
            entry.destroy()
            if self.on_edit_timestamp_func != None:
                self.on_edit_timestamp_func()

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

    def destroy_object(self, event=None):
        # Get the widget that was clicked on
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        # Destroy the object if the widget that was clicked on is not the same as the object
        if widget != self.selected_object and self.selected_object is not None:
            self.selected_object.destroy()

    def on_double_click_type_cell(self, col_container, cell_lbl, obj):
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
            if is_type_change and self.on_edit_type_func != None:
                self.on_edit_type_func()

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

    def exists(self, iid):
        return iid in self.rows

    def set(self, row_iid, col_id, value, row_obj, cell_color=""):
        # only supports updating of text cell for now
        row = self.rows[row_iid]
        col = self.columns[col_id]
        target_col = row["UI"].winfo_children()[col["col_no"] - 1]
        cell = target_col.winfo_children()[0]
        cell["text"] = value
        self.rows[row_iid]["obj"] = row_obj
        if cell_color != "":
            cell.configure(fg=cell_color)

    def on_click_yes_option_for_delete(self, iid):
        self.rows[iid]["is_deleted"] = True
        self.hide_row(iid)
        if self.delete_func != None:
            self.delete_func(self.rows[iid]["obj"])

    def on_click_delete(self, iid):
        ConfirmBox(self.parent, "Are you sure you want to DELETE this annotation?", font=(None, 12),
                   on_click_yes_func=lambda row_iid=iid: self.on_click_yes_option_for_delete(
                       row_iid),
                   on_click_option_callback=self.messagebox_callback)

    def hide_row(self, iid):
        if not self.exists(iid):
            return
        self.rows[iid]["is_show"] = False
        # self.update_table_ui()
        self.update_row_ui_visibility(False, iid)

    def show_row(self, iid):
        if not self.exists(iid) or self.rows[iid]["is_deleted"]:
            return
        self.rows[iid]["is_show"] = True
        # self.update_table_ui()
        self.update_row_ui_visibility(True, iid)

    # def update_table_ui(self):
    #     self.current_table_height = self.header_height
    #     for row_iid in self.rows:
    #         if self.rows[row_iid]["is_show"]:
    #             self.rows[row_iid]["UI"].grid()
    #             self.current_table_height += self.row_height
    #         else:
    #             self.rows[row_iid]["UI"].grid_remove()
    #     #print("done updating")
    #     self.toggle_scrollbar_y_visibility()

    def update_row_ui_visibility(self, is_show, iid):
        if is_show:
            self.current_table_height += self.row_height
            self.rows[iid]["UI"].grid()
        else:
            self.current_table_height -= self.row_height
            self.rows[iid]["UI"].grid_remove()
        # need to use update_idletasks() to make it instantly reload the UI
        self.rows[iid]["UI"].update_idletasks()
        self.toggle_scrollbar_y_visibility()

    def get_all_row_objects(self):
        objs = []
        for row_iid in self.rows:
            if self.rows[row_iid]["is_deleted"]:
                continue
            obj = self.rows[row_iid]["obj"]
            if obj != None:
                objs.append(obj)
        return objs

    def clear_table(self):
        self.yview_pos = self.canvas.yview()[0]
        # print(self.canvas.yview()[0])
        is_header = True
        for child in self.container.winfo_children():
            if is_header:
                is_header = False
                continue
            child.destroy()
        self.rows = {}
        self.top_rows = {}
        self.top_rows_order = []
        self.clicked_row = None
        self.clicked_multi_row = None
        self.current_table_height = self.header_height

    def remember_current_yview_pos(self):
        self.yview_pos = self.canvas.yview()[0]

    def move_view(self):
        self.canvas.yview_moveto(self.yview_pos)


def on_select_row(row_obj):
    print(row_obj.get_timestamp())


def get_rows_diff(r1_obj, r2_obj):
    duration = str_to_sec(r2_obj.get_timestamp()) - \
        str_to_sec(r1_obj.get_timestamp())
    duration = abs(duration)
    print("Duration Diff: {} s".format(duration))


if __name__ == "__main__":
    root = tk.Tk()
    # root.geometry("700x300")

    table_frame = tk.Frame(root)
    table_frame.configure(width=680, height=300)
    table_frame.pack()
    table_frame.pack_propagate(0)

    table = CustomTable(table_frame, on_select_row,
                        get_rows_diff, 50, 25, "white")
    table.define_column_ids(
        ["bump", "select", "time", "type", "note", "delete", "pin"])
    table.column("bump", header_text="", width=40, type="bump")
    table.column("select", header_text="Select", width=60, type="cb")
    table.column("time", header_text="Time", width=80)
    table.column("type", header_text="Type", width=120)
    table.column("note", header_text="Note", width=325)
    table.column("delete", header_text="", width=40, type="delete")
    table.column("pin", header_text="", width=40, type="pin")

    t1 = Task(1, "00:00:00", "start", "Start", "white", "N.A.", "")
    r1 = table.insert(obj=t1, cells=[{"value": False, "anchor": "center", "tag": ""},
                                     {"value": "selected", "fg": "white",
                                         "anchor": "center", "tag": ""},
                                     {"value": t1.get_timestamp(), "fg": "white", "anchor": "center",
                                      "tag": "timestamp"},
                                     {"value": t1.get_display_type(), "fg": "white",
                                      "anchor": "center", "tag": "type"},
                                     {"value": t1.get_display_notes(
                                     ), "fg": "white", "anchor": "w", "tag": "note"},
                                     {"anchor": "center", "tag": ""},
                                     {"value": True, "anchor": "center", "tag": ""}], iid=t1.get_id())
    t2 = Task(2, "00:00:01", "voice", "Voice", "darkpurple", "N.A.",
              "once upon a time there was an old mother pig who had trained litter pick and not enough to defeat them so and they were all now she said the or into the was sick their fortunes")
    r2 = table.insert(obj=t2, cells=[{"value": False, "anchor": "center", "tag": ""},
                                     {"value": "selected", "fg": "white",
                                         "anchor": "center", "tag": ""},
                                     {"value": t2.get_timestamp(), "fg": "white", "anchor": "center",
                                      "tag": "timestamp"},
                                     {"value": t2.get_display_type(), "fg": UI.color.color_translation("lightgrey"),
                                      "anchor": "center", "tag": "type"},
                                     {"value": t2.get_display_notes(
                                     ), "fg": "white", "anchor": "w", "tag": "note"},
                                     {"anchor": "center", "tag": ""},
                                     {"value": True, "anchor": "center", "tag": ""}], iid=t2.get_id())
    t3 = Task(3, "00:00:03", "screenshot", "Screenshot (Whole)",
              "blue", "N.A.", "marking here")
    r3 = table.insert(obj=t3, cells=[{"value": False, "anchor": "center", "tag": ""},
                                     {"value": "selected", "fg": "white",
                                         "anchor": "center", "tag": ""},
                                     {"value": t3.get_timestamp(), "fg": "white", "anchor": "center",
                                      "tag": "timestamp"},
                                     {"value": t3.get_display_type(), "fg": UI.color.color_translation("blue"),
                                      "anchor": "center", "tag": "type"},
                                     {"value": t3.get_display_notes(
                                     ), "fg": "white", "anchor": "w", "tag": "note"},
                                     {"anchor": "center", "tag": ""},
                                     {"value": True, "anchor": "center", "tag": ""}], iid=t3.get_id())
    t4 = Task(4, "00:00:05", "correct", "Correct", "green", "N.A.", "")
    r4 = table.insert(obj=t4, cells=[{"value": False, "anchor": "center", "tag": ""},
                                     {"value": "selected", "fg": "white",
                                         "anchor": "center", "tag": ""},
                                     {"value": t4.get_timestamp(), "fg": "white", "anchor": "center",
                                      "tag": "timestamp"},
                                     {"value": t4.get_display_type(), "fg": UI.color.color_translation("green"),
                                      "anchor": "center", "tag": "type"},
                                     {"value": t4.get_display_notes(
                                     ), "fg": "white", "anchor": "w", "tag": "note"},
                                     {"anchor": "center", "tag": ""},
                                     {"value": True, "anchor": "center", "tag": ""}], iid=t4.get_id())
    table.hide_row(t2.get_id())
    table.hide_row(t1.get_id())
    table.show_row(t2.get_id())
    table.show_row(t1.get_id())

    t3.set_notes("screenshot 1")
    table.set(row_iid=r3, col_id="note",
              value=t3.get_display_notes(), row_obj=t3)
    root.mainloop()
