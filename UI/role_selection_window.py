import os
from tkinter import LEFT

import pandas
import ttkbootstrap as ttk
import tkinter


from UI.widget_generator import get_button, get_dropdown_menu, get_bordered_frame, get_entry_with_placeholder, get_label
from Utilities import log_utilities
from Utilities import default_config

from Utilities.screen_capture import get_second_monitor_original_pos

FILE_NAME = "device_config.csv"


def save_device_config(path, item, data):
    print("Saving to: " + path)
    log_utilities.record_device_config(path, item, data)


class RoleSelectionWindow:
    def __init__(self, root=None, is_run_alone=True):
        # device type: "Wizard" or "Observer" or "Single User"
        self.device_type = tkinter.Variable()
        self.is_run_alone = is_run_alone
        self.path = os.path.join("data", FILE_NAME)
        self.load_config()
        if self.is_run_alone:
            self.root = ttk.Toplevel(root)
            self.root.title('Role Selection')
            self.place_window_to_center()
            self.root.overrideredirect(True)

        else:
            self.root = root
            for widget in self.root.winfo_children():
                widget.destroy()

        self.pack_layout()
        self.place_window_to_center()

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))

    def set_default_device_config(self, path):
        self.target_device_ip = default_config.DEFAULT_TARGET_DEVICE_IP
        self.streaming_port = default_config.DEFAULT_STREAMING_PORT
        self.communication_port = default_config.DEFAULT_COMMUNICATION_PORT
        self.device_type.set("Single User")

        self.fpv_url = default_config.DEFAULT_FPV_URL
        self.fpv_usr = default_config.DEFAULT_FPV_USR
        self.fpv_pw = default_config.DEFAULT_FPV_PW
        self.tpv_url = default_config.DEFAULT_TPV_URL
        self.browser_url = default_config.DEFAULT_BROWSER_URL
        self.video_device_idx = default_config.DEFAULT_VIDEO_DEVICE_IDX
        self.audio_device_1_idx = default_config.DEFAULT_AUDIO_DEVICE_1_IDX
        self.audio_device_2_idx = default_config.DEFAULT_AUDIO_DEVICE_2_IDX
        save_device_config(path, "fpv", self.fpv_url)
        save_device_config(path, "fpv_usr", self.fpv_usr)
        save_device_config(path, "fpv_pw", self.fpv_pw)
        save_device_config(path, "tpv", self.tpv_url)
        save_device_config(path, "woz", self.browser_url)
        save_device_config(path, "video_device", self.video_device_idx)
        save_device_config(path, "audio_device_1", self.audio_device_1_idx)
        save_device_config(path, "audio_device_2", self.audio_device_2_idx)
        save_device_config(path, "target_device_ip", self.target_device_ip)
        save_device_config(path, "streaming_port", self.streaming_port)
        save_device_config(path, "communication_port", self.communication_port)
        save_device_config(path, "device_type", self.device_type.get())

    def load_config(self):
        if not os.path.isfile(self.path):
            self.set_default_device_config(self.path)
        try:
            self.df = pandas.read_csv(self.path)
        except:
            # remove the corrupted file
            os.remove(self.path)
            self.set_default_device_config(self.path)
            self.df = pandas.read_csv(self.path)
        finally:
            self.fpv_url = self.df[self.df['item'] == 'fpv']['details'].item()
            self.fpv_usr = self.df[self.df['item'] == 'fpv_usr']['details'].item()
            self.fpv_pw = self.df[self.df['item'] == 'fpv_pw']['details'].item()
            self.tpv_url = self.df[self.df['item'] == 'tpv']['details'].item()
            self.browser_url = self.df[self.df['item'] == 'woz']['details'].item()
            self.video_device_idx = self.df[self.df['item'] == 'video_device']['details'].item()
            self.audio_device_1_idx = self.df[self.df['item'] == 'audio_device_1']['details'].item()
            self.audio_device_2_idx = self.df[self.df['item'] == 'audio_device_2']['details'].item()
            self.target_device_ip = self.df[self.df['item'] == 'target_device_ip']['details'].item()
            self.streaming_port = self.df[self.df['item'] == 'streaming_port']['details'].item()
            self.communication_port = self.df[self.df['item'] == 'communication_port']['details'].item()
            self.device_type.set(self.df[self.df['item'] == 'device_type']['details'].item())

    def pack_layout(self):
        self.frame = get_bordered_frame(self.root)
        self.frame.pack()
        self.selection_frame = ttk.Frame(self.frame)
        self.selection_frame.pack(padx=10, pady=10)
        self.label = get_label(self.selection_frame, text="Select your role:")
        self.label.pack(side=LEFT)
        self.device_type_list = ["Single User", "Wizard", "Observer"]
        self.device_type_options = get_dropdown_menu(self.selection_frame, values=self.device_type_list,
                                                     variable=self.device_type)
        self.device_type_options.pack(side=LEFT)
        self.close_btn = get_button(self.frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack(pady=10)

    def on_close_window(self):
        self.device_type = self.device_type.get()
        self.df.loc[self.df['item'] == "device_type", ['details']] = self.device_type
        self.df.to_csv(self.path, index=False)
        self.root.destroy()

