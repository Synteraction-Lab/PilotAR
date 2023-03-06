import os
import tkinter as tk
from multiprocessing import Process

# import ttkbootstrap as ttk
from tkinter import ttk
from UI.checklist import Checklist
from UI.customization_panel import CustomizationPanel
from UI.device_panel import DevicePanel
from UI.stream_player import StreamPlayer
from UI.widget_generator import get_button
from Utilities.screen_capture import get_second_monitor_original_pos


# from tkinter import ttk


class ConfigurationPanel:
    # to run as a window on its own
    def __init__(self, root, workflow=None, is_run_alone=True, child_frame=None):
        self.checklist = None
        self.is_run_alone = is_run_alone
        if self.is_run_alone:
            self.root = tk.Toplevel(root)
            self.root.title('Configuration')
            self.root.geometry('+{}+{}'.format(get_second_monitor_original_pos()[0] +
                                               int(get_second_monitor_original_pos()[2] / 2),
                                               get_second_monitor_original_pos()[1]))
        else:
            self.root = root
            self.child_frame = child_frame
        self.workflow = workflow
        self.customized_annotations = {}
        self.path = os.path.join('data')
        self.pack_layout()
        self.is_device_panel_opened = False
        self.is_checklist_opened = False
        self.is_customization_panel_opened = False

    def on_close_configuration(self):
        self.device_btn.configure(bootstyle="secondary")

    def load_customization_panel(self):
        if not self.is_customization_panel_opened:
            self.customization_panel = CustomizationPanel(self.child_frame, configuration_panel=self, is_run_alone=True)
            self.is_customization_panel_opened = True

    def on_close_customization_panel(self):
        self.workflow.lower()
        self.is_customization_panel_opened = False

    def load_checklist(self):
        if not self.is_checklist_opened:
            self.checklist = Checklist(self.child_frame, self.workflow, self, True)
            self.is_checklist_opened = True

    def on_close_checklist(self):
        self.workflow.lower()
        self.is_checklist_opened = False

    def load_devices(self):
        if not self.is_device_panel_opened:
            self.device_panel = DevicePanel(self.child_frame, self, True)
            self.is_device_panel_opened = True

    def on_close_device_panel(self):
        self.workflow.lower()
        self.is_device_panel_opened = False

    def close(self, event=None):
        if self.workflow is not None:
            self.workflow.on_close_configuration()
        self.root.destroy()

    def pack_layout(self):
        self.device_btn = get_button(self.root, text="Devices", command=self.load_devices, pattern=0)
        self.device_btn.configure(width=120)
        self.device_btn.grid(column=0, row=1, columnspan=1, padx=10, pady=10)

        self.checklist_btn = get_button(self.root, text="Checklist", command=self.load_checklist, pattern=0)
        self.checklist_btn.configure(width=120)
        self.checklist_btn.grid(column=1, row=1, columnspan=1, padx=10, pady=10)

        self.customization_btn = get_button(self.root, text="Customization", command=self.load_customization_panel,
                                            pattern=0)
        self.customization_btn.configure(width=120)
        self.customization_btn.grid(column=2, row=1, columnspan=1, padx=10, pady=10)
        self.root.grid_columnconfigure((0, 1, 2), weight=1, uniform="column")
        if self.is_run_alone:
            self.root.protocol("WM_DELETE_WINDOW", self.close)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    workflow_panel = ConfigurationPanel()
    workflow_panel.run()
