import csv
import os
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
# from tkinter import ttk
from UI.widget_generator import get_button, get_checkbutton, get_bordered_frame, get_entry_with_placeholder, \
    get_messagebox
from Utilities import log_utilities
from Utilities.screen_capture import get_second_monitor_original_pos

FILE_NAME = 'checklist.csv'


def check_saving_file(path):
    if not os.path.isdir(path):
        return False
    return True


def set_default_checklist(customized_checklist, path):
    customized_checklist.append("Setup HoloLens")
    save_customized_checklist(path, customized_checklist[len(customized_checklist) - 1])

    customized_checklist.append("Setup TPV Camera")
    save_customized_checklist(path, customized_checklist[len(customized_checklist) - 1])

    customized_checklist.append("Record the wizard")
    save_customized_checklist(path, customized_checklist[len(customized_checklist) - 1])


def save_customized_checklist(path, data):
    print("Saving to: " + path)
    log_utilities.record_customized_checklist(path, data)


class Checklist:
    def __init__(self, root=None, workflow=None, configuration_panel=None, is_run_alone=True):
        self.is_run_alone = is_run_alone
        if self.is_run_alone:
            self.root = tk.Toplevel(root)
            self.place_window_to_center()
            # self.root.title('Checklist')
            self.root.overrideredirect(True)
        else:
            self.root = root
            for widget in self.root.winfo_children():
                widget.destroy()

        self.item_list = []
        self.is_editing = False
        self.path = os.path.join('data', FILE_NAME)
        self.checklist = []
        self.load_checklist()
        self.pack_layout()
        self.place_window_to_center()
        self.workflow = workflow
        self.configuration_panel = configuration_panel

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))

    def load_checklist(self):
        if not os.path.isfile(self.path):
            set_default_checklist(self.checklist, self.path)
            return

        with open(self.path, newline='') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)
            next(reader, None)
            for row in reader:
                self.checklist.append(row[0])

    def check_all_item(self):
        for cb, is_selected in self.item_list:
            if not is_selected.get():
                if self.workflow is not None:
                    self.workflow.set_pilot_start_flag(False)
                return False
        self.workflow.set_pilot_start_flag(True)
        return True

    def add_item(self, frame, text):
        is_selected = tk.BooleanVar()
        is_selected.set(False)
        cb = get_checkbutton(frame, text=text, variable=is_selected, command=self.check_all_item)
        cb.configure(text_color="white")
        cb.pack(pady=20, anchor="w")
        self.item_list.append((cb, is_selected))

    def on_close_window(self):
        self.root.destroy()
        self.configuration_panel.on_close_checklist()
        self.workflow.on_close_checklist()

    def pack_layout(self):
        self.root_frame = get_bordered_frame(self.root)
        self.root_frame.pack()
        self.frame = tk.Frame(self.root_frame)
        self.frame.pack(padx=20)
        for c in self.checklist:
            self.add_item(self.frame, text=c)

        self.add_frame = ttk.Frame(self.root_frame)
        self.sep = ttk.Separator(self.add_frame, orient='horizontal')
        self.sep.pack(side="top", fill='x')
        self.txt = get_entry_with_placeholder(master=self.add_frame, placeholder="Enter checklist details")
        self.txt.pack(side="left", padx=5)
        # self.add_btn = ttk.Button(self.add_frame, text="Add", command=self.add)
        self.add_btn = get_button(self.add_frame, text="Add", command=self.add, pattern=0)
        self.add_btn.pack(side="left", padx=10, pady=10)
        self.add_frame.pack(side="top")

        self.close_frame = ttk.Frame(self.frame)
        self.close_frame.pack(pady=10, side="bottom")
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()


    def add(self):
        details = self.txt.get_text()
        if details == "":
            get_messagebox(self.root, "Please enter the details")
            return

        save_customized_checklist(self.path, details)
        self.checklist.append(details)
        self.add_frame.pack_forget()
        self.add_item(self.frame, text=details)
        self.check_all_item()
        self.add_frame.pack(side="top")
        self.check_all_item()

    """
    def select_row(self, event):
        row = self.table.focus()
        if row == "":
            return
        row_values = self.table.item(row)['values']
        # self.type_txt.set(row_values[0])
        # self.key_txt.set(row_values[1])
        # self.color_txt.set(row_values[2])

    
    def edit(self):
        if self.is_editing:
            self.is_editing = False 
            self.frame.pack()
            self.edit_frame.pack_forget()
            self.edit_btn.config(text="Edit")
            self.edit_btn.update()
            
            return 
        
        self.is_editing = True
        self.frame.pack_forget()
        self.edit_frame.pack(side="top")
        self.edit_btn.config(text="Done")
        self.edit_btn.update()
    """


if __name__ == '__main__':
    root = tk.Tk()
    customization_panel = Checklist(root)
    root.mainloop()
