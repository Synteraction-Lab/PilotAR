import os
import ttkbootstrap as ttk

from UI.timer_part_2 import Timer_Part_2
from UI.widget_generator import get_circular_button, get_button, get_entry_with_placeholder, get_messagebox, get_label
from Utilities.screen_capture import ScreenCapture


class Timer_Part_1:
    def __init__(self, root, frame, workflow):
        self.root = frame
        self.top_level_root = root
        self.workflow = workflow
        for widget in self.root.winfo_children():
            widget.destroy()
        self.pack_layout()

    def set_pid(self):
        pid = self.pid_txt.get_text()
        if os.path.isdir(os.path.join("data", pid)):
            return False
        self.pid = self.pid_txt.get_text()
        return True

    def get_anticipated_duration(self):
        try:
            duration = float(self.inputtxt.get_text()) * 60
            return duration
        except:
            return None

    def pack_layout(self):

        self.input_label = get_label(self.root, text="Anticipated Duration (min):")
        self.input_label.grid(column=0, row=1, columnspan=1, padx=5, pady=5)

        self.inputtxt = get_entry_with_placeholder(self.root, placeholder="3", width=6)
        self.inputtxt.grid(column=1, row=1, columnspan=1, padx=10, pady=5)

        self.pid_label = get_label(self.root, text="Participant & Session ID:")
        self.pid_label.grid(column=2, row=1, columnspan=1, padx=5, pady=5)

        self.pid_txt = get_entry_with_placeholder(self.root, placeholder="p1_1", width=6)
        self.pid_txt.grid(column=3, row=1, columnspan=1, padx=10, pady=5)
        self.start_btn = get_circular_button(self.workflow.top_right_frame, text="Start", command=self.start)

        self.start_btn.grid(column=1, row=1, columnspan=1, rowspan=2, padx=10, pady=20, sticky="e")

    def start(self):
        if self.get_anticipated_duration():
            if not self.set_pid():
                get_messagebox(self.root, "Please change the PID!")
                return
            self.myTimer = Timer_Part_2(root=self.top_level_root, frame=self.root, pid=self.pid,
                                        anticipated_duration=self.get_anticipated_duration(), workflow=self.workflow)
            try:
                myScreen_capture = ScreenCapture()
                self.myTimer.set_screen_capture(myScreen_capture)
            except RuntimeError:
                print("Screen Capture and/or Audio Recorder is not loaded")
            self.workflow.lower()
            self.myTimer.run()
