from UI.confirmbox import ConfirmBox
from UI.widget_generator import get_checkbutton, get_messagebox, get_label, get_text, get_bordered_frame, get_image, \
    get_dropdown_menu
import tkinter as tk
import sys
sys.path.append("./")


class CustomTable:
    def __init__(self, parent, row_height, header_height, header_text_color, row_normal_bg="#222222", row_selected_bg="#ACA9BB",
                 on_delete_callback=None, messagebox_callback=None, on_unclick_row_callback=None, on_clicked_row_callback=None, on_clicked_multirow_callback=None,
                 is_support_multiselect=False):
        self.selected_object = None
        self.parent = parent
        self.on_clicked_row_callback = on_clicked_row_callback
        self.on_unclick_row_func = on_unclick_row_callback
        self.on_clicked_multirow_callback = on_clicked_multirow_callback
        self.on_delete_callback = on_delete_callback
        self.messagebox_callback = messagebox_callback
        self.is_support_multiselect = is_support_multiselect

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
        self.current_table_height = 0
        self.is_scrollbar_y_visible = False
        self.is_scrollbar_x_visible = False

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
        self.rows = {}
        self.clicked_row = None
        self.clicked_multi_row = None

        self.parent.bind(
            '<Button-1>', lambda event: self.destroy_object(event))
        self.yview_pos = 0.0

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
        if is_vertical and self.is_scrollbar_y_visible:
            self.canvas.yview_scroll(int(-1*(delta)), "units")
        elif not is_vertical and self.is_scrollbar_x_visible:
            self.canvas.xview_scroll(int(-1*(delta)), "units")

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
                self.is_scrollbar_x_visible = True
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
        if row["obj"] != None and self.on_clicked_row_callback != None:
            self.on_clicked_row_callback(row["obj"])

    # for unselect/select single/multi row
    # currently only support up to 2 rows being selected
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
            if self.on_clicked_multirow_callback != None:
                self.on_clicked_multirow_callback(
                    self.clicked_row["obj"], self.clicked_multi_row["obj"])

    def change_row_bg(self, row_ui, bg):
        for col in row_ui.winfo_children():
            col.configure(bg=bg)
            for cell in col.winfo_children():
                if isinstance(cell, tk.Label):
                    cell.configure(bg=bg)

    def destroy_object(self, event=None):
        # Get the widget that was clicked on
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        # Destroy the object if the widget that was clicked on is not the same as the object
        if widget != self.selected_object and self.selected_object is not None:
            self.selected_object.destroy()

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

    def create_row_container(self):
        row_container = tk.Frame(self.container)
        row_container.configure(
            height=self.row_height, width=self.row_width)
        row_container.grid_propagate(0)
        row_container.grid(row=len(self.rows) + 1)
        row_container.bindtags(
            row_container.bindtags() + ("custom_table",))

        self.current_table_height += self.row_height
        self.toggle_scrollbar_y_visibility()
        return row_container

    def create_col_container(self, row_container, col):
        col_container = get_bordered_frame(row_container)
        col_container.configure(
            width=col["width"], height=self.row_height, bg=self.row_normal_bg)
        col_container.pack(side="left", fill="both", expand=True)
        col_container.pack_propagate(0)
        col_container.bindtags(col_container.bindtags() + ("custom_table",))
        return col_container

    def create_text_cell(self, col_container, cell, col):
        cell_lbl = get_label(col_container, text=cell["value"], pattern=4)
        # must set fg using configure or else it doesn't 100% work
        cell_lbl.configure(width=col["width"] - 4, height=self.row_height - 4, fg=cell["fg"], justify=tk.LEFT,
                           anchor=col["anchor"], bg=self.row_normal_bg)
        # cell_lbl.pack(anchor=col["anchor"], side="left", expand=True)
        cell_lbl.pack(anchor=col["anchor"],
                      side="left", fill="both", expand=True)
        cell_lbl.bindtags(cell_lbl.bindtags() + ("custom_table",))
        return cell_lbl

    def create_checkbox_cell(self, col_container):
        cell_cb = get_checkbutton(col_container)
        # note anchor doesn't seem to work if using fill="both"
        # cell_cb.pack(side="left", expand=True, anchor=col["anchor"])
        # cell_cb.pack(side="left", padx=(
        #     col["width"] / 2) - 14, anchor=col["anchor"])
        cell_cb.pack(side="left")
        cell_cb._canvas.grid(column=1, padx=cell_cb.cget("width")/3)
        cell_cb.bindtags(cell_cb.bindtags() + ("custom_table",))
        cell_cb._canvas.bindtags(
            cell_cb._canvas.bindtags() + ("custom_table",))
        return cell_cb

    def create_image_cell(self, col_container, col_anchor, image_filepath, width, height):
        cell_img = get_image(col_container, image_filepath, width, height)
        cell_img.configure(bg=self.row_normal_bg)
        cell_img.pack(anchor=col_anchor, side="left", fill="both", expand=True)
        cell_img.bindtags(cell_img.bindtags() + ("custom_table",))
        return cell_img

    def create_delete_cell(self, col_container, col, row_iid, image_filepath):
        cell_img = get_image(col_container, image_filepath)
        cell_img.configure(bg=self.row_normal_bg)
        cell_img.pack(anchor=col["anchor"],
                      side="left", fill="both", expand=True)
        cell_img.bind('<Button>', lambda e,
                      row_iid=row_iid: self.on_click_delete(row_iid))
        cell_img.bindtags(cell_img.bindtags() + ("custom_table",))
        return cell_img

    def on_click_yes_option_for_delete(self, iid):
        self.rows[iid]["is_deleted"] = True
        self.hide_row(iid)
        if self.on_delete_callback != None:
            self.on_delete_callback(self.rows[iid]["obj"])

    def on_click_delete(self, iid):
        ConfirmBox(self.parent, "Are you sure you want to DELETE this annotation?", font=(None, 12),
                   on_click_yes_func=lambda row_iid=iid: self.on_click_yes_option_for_delete(
                       row_iid),
                   on_click_option_callback=self.messagebox_callback)

    def hide_row(self, iid):
        if not self.exists(iid):
            return
        self.rows[iid]["is_show"] = False
        self.update_row_ui_visibility(False, iid)

    def show_row(self, iid):
        if not self.exists(iid) or self.rows[iid]["is_deleted"]:
            return
        self.rows[iid]["is_show"] = True
        self.update_row_ui_visibility(True, iid)

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
