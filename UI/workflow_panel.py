from gc import unfreeze
import datetime
import tkinter as tk
from multiprocessing import Process
from tkinter import Frame, Label, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from UI.analyser import setup_new_analyzer
from UI.configuration_panel import ConfigurationPanel
from UI.timer_part_1 import Timer_Part_1
from UI.widget_generator import get_button, get_bordered_frame, get_messagebox
from UI.UI_config import MAIN_COLOR_LIGHT, BUTTON_FG_COLOR
from Utilities.key_listener import KeyListener
from Utilities.screen_capture import get_second_monitor_original_pos

TIME_PERIOD_FOR_DEBOUNCE = 1

class WorkflowPanel:
    def __init__(self):
        self.ready_to_jump_to_timer = False
        self.configuration_panel = None
        self.root = tk.Tk()
        style = ttk.Style("darkly")
        self.root.geometry('{}x{}+{}+{}'.format(int(get_second_monitor_original_pos()[2]),
                                                int(get_second_monitor_original_pos()[3]),
                                                get_second_monitor_original_pos()[0],
                                                get_second_monitor_original_pos()[1]))
        self.root.title('Wizard')
        self.is_pilot_ready = False
        self.last_open_analyzer_time = datetime.datetime.now()
        self.pack_layout()
        self.is_setup_window_running = False
        self.is_pilot_window_running = False
        self.is_analyzer_window_running = False
        self.key_listener = KeyListener()
        self.key_listener.start_listener()

    def load_configuration(self):
        if not self.is_setup_window_running:
            self.timer_panel_frame.pack_forget()
            self.configuration_panel = ConfigurationPanel(self.configuration_panel_frame, self, False)
            self.configuration_frame.pack(side="top", fill=X, padx=10)
            self.configuration_panel_frame.pack(side="top")
            self.is_setup_window_running = True
            self.is_pilot_window_running = False

    def on_close_configuration(self):
        self.setup_btn.configure(color="grey")
        self.is_setup_window_running = False

    def set_pilot_start_flag(self, flag):
        self.is_pilot_ready = flag
        print("Flag: " + str(self.is_pilot_ready))

    def set_analyzer_ready_color(self):
        self.pilot_btn.configure(fg_color=BUTTON_FG_COLOR)

    def on_close_checklist(self):
        self.lower()
        if self.ready_to_jump_to_timer:
            self.load_timer()
            self.ready_to_jump_to_timer = False
            
    def load_timer(self):
        if not self.is_pilot_ready:
            # get_messagebox(self.root, "You haven't checked all the items in Setup's Checklist.")
            if self.configuration_panel is not None:
                if not self.configuration_panel.is_checklist_opened:
                    self.configuration_panel.load_checklist()
            else:
                self.load_configuration()
                self.configuration_panel.load_checklist()
            self.ready_to_jump_to_timer = True
            return

        if not self.is_pilot_window_running:
            self.pilot_btn.configure(fg_color=BUTTON_FG_COLOR)
            # run_timer(self.root, self)
            self.configuration_frame.pack_forget()
            self.timer_panel = Timer_Part_1(self.root, self.timer_panel_frame, self)
            self.timer_panel_frame.pack(side="top", padx=10)
            self.is_pilot_window_running = True
            self.is_setup_window_running = False

    def on_close_timer(self):
        self.is_pilot_window_running = False
        self.pilot_btn.configure(fg_color="grey")

    def load_analyzer(self):
        # if not self.is_analyzer_window_running:
        current_time = datetime.datetime.now()
        difference = current_time - self.last_open_analyzer_time
        if difference <= datetime.timedelta(seconds=TIME_PERIOD_FOR_DEBOUNCE):
            return
        self.is_analyzer_window_running = True
        self.last_open_analyzer_time = current_time
        self.set_analyzer_ready_color()
        analyzer_process = Process(target=setup_new_analyzer)
        analyzer_process.start()

    def on_close_analyzer(self):
        self.is_analyzer_window_running = False
        self.analyzer_btn.configure(fg_color="grey")

    def reset(self):
        self.is_setup_window_running = False
        for widget in self.right_side_frame.winfo_children():
            widget.destroy()
        for widget in self.top_right_frame.winfo_children():
            widget.destroy()
        for widget in self.top_left_frame.winfo_children():
            widget.destroy()
        self.timer_panel = Timer_Part_1(self.root, self.timer_panel_frame, self)
        self.is_pilot_window_running = True
        # self.top_left_frame.configure(highlightthickness=0)
        self.big_container_frame.configure(highlightthickness=0)
        self.right_side_frame.configure(highlightthickness=0)

    def lower(self, event=None):
        self.root.lower()

    def pack_layout(self):
        self.top_view = Frame(self.root)
        self.top_view.pack(fill=X, side="top")
        self.big_container_frame = Frame(self.top_view, borderwidth=1, highlightthickness=0,  highlightbackground=MAIN_COLOR_LIGHT)
        self.center_frame = Frame(self.big_container_frame)
        self.workflow_frame = Frame(self.center_frame)
        self.top_left_frame = Frame(self.top_view, borderwidth=1, highlightthickness=0, highlightbackground=MAIN_COLOR_LIGHT)
        self.top_right_frame = Frame(self.big_container_frame)
        self.interaction_frame = Frame(self.center_frame)

        self.right_side_frame = get_bordered_frame(self.root)


        # self.setup_btn = get_button(self.workflow_frame, text="Setup", pattern=3,
        self.setup_btn = get_button(self.workflow_frame, text="Setup", pattern=1,
                                    command=self.load_configuration)

        self.setup_btn.grid(column=0, row=0, columnspan=1, padx=10, pady=10, ipady=5, ipadx=5)

        self.type_label = Label(self.workflow_frame, text="---------->")
        self.type_label.grid(column=1, row=0, columnspan=1, padx=10, pady=5)

        # self.pilot_btn = get_button(self.workflow_frame, text="Pilot", pattern=3,
        self.pilot_btn = get_button(self.workflow_frame, text="Pilot", pattern=1,
                                    command=self.load_timer, fg_color="gray")
        self.pilot_btn.grid(column=2, row=0, columnspan=1, padx=10, pady=10, ipady=5, ipadx=5)

        self.type_label = Label(self.workflow_frame, text="---------->")
        self.type_label.grid(column=3, row=0, columnspan=1, padx=10, pady=5)

        # self.analyzer_btn = get_button(self.workflow_frame, text="Analyzer", pattern=3,
        self.analyzer_btn = get_button(self.workflow_frame, text="Analyzer", pattern=1,
                                       command=self.load_analyzer, fg_color="gray")
        self.analyzer_btn.grid(column=4, row=0, columnspan=1, padx=10, pady=10, ipady=5, ipadx=5)

        # self.big_container_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="column")
        # self.center_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="column")
        self.workflow_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="column")
        self.top_right_frame.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.top_left_frame.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.top_left_frame.grid_rowconfigure((0,), weight=1, uniform="row")

        self.top_left_frame.grid(column=0, row=0, columnspan=1, rowspan=2, sticky='NSEW')
        self.big_container_frame.grid(column=1, row=0, columnspan=1, rowspan=2, sticky='NSEW')
        self.center_frame.grid(column=0, row=0, columnspan=1, rowspan=2, sticky="NSEW")
        self.top_right_frame.grid(column=1, row=0, sticky='NSEW')
        self.workflow_frame.grid(column=0, row=0, columnspan=1, sticky='NSEW')
        self.interaction_frame.grid(column=0, row=1, sticky="NSEW")

        # self.right_side_frame.grid(column=2, row=2, columnspan=1, sticky='E', pady=5)
        self.right_side_frame.pack(side="right", fill="y", pady=0)
        # self.interaction_frame.grid(column=1, row=1, columnspan=1, ipady=5, ipadx=5, sticky="NSEW")
        
        self.top_view.grid_columnconfigure((0), weight=1, uniform="column")
        self.top_view.grid_columnconfigure((1,), weight=3, uniform="column")
        self.big_container_frame.grid_columnconfigure((0), weight=3, uniform="column")
        self.big_container_frame.grid_columnconfigure((1,), weight=2, uniform="column")
        self.center_frame.grid_columnconfigure((0,), weight=1, uniform="column")
        # self.root.grid_rowconfigure((0, 1), weight=1, uniform="row")
        # self.root.grid_rowconfigure((2,), weight=8, uniform="row")

        self.configuration_frame = Frame(self.interaction_frame)
        self.configuration_frame.pack(side="top", fill=X, padx=10)
        self.configuration_panel_frame = Frame(self.configuration_frame)
        self.configuration_panel_frame.pack(side="top", anchor="center")

        self.timer_panel_frame = Frame(self.interaction_frame)
        self.timer_panel_frame.pack(side="top", padx=10)
        self.timer_panel_frame.pack_forget()
        self.root.bind("<Button-1>", self.lower)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    workflow_panel = WorkflowPanel()
    workflow_panel.run()
