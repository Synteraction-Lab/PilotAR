import csv
import os
import re
import subprocess
import webbrowser
from multiprocessing import Process

import pandas
import ttkbootstrap as ttk
import tkinter

from UI.stream_player import StreamPlayer
from UI.widget_generator import get_button, get_dropdown_menu, get_bordered_frame, get_entry_with_placeholder, get_label
from Utilities import log_utilities
from Utilities.common_utilities import get_system_name
from Utilities.screen_capture import get_second_monitor_original_pos

FILE_NAME = "device_config.csv"


def save_device_config(path, item, data):
    print("Saving to: " + path)
    log_utilities.record_device_config(path, item, data)


class DevicePanel:
    def __init__(self, root=None, configuration_panel=None, is_run_alone=False):
        self.audio_device_list = []
        self.video_device_list = []
        self.tpv_url = ""
        self.fpv_usr = ""
        self.fpv_pw = ""
        self.fpv_url = ""
        self.browser_url = ""
        self.is_run_alone = is_run_alone
        self.configuration_panel = configuration_panel
        self.path = os.path.join("data", FILE_NAME)
        self.load_config()
        self.load_screen_recording_device_index()
        if self.is_run_alone:
            self.root = ttk.Toplevel(root)
            self.root.title('Device Panel')
            self.place_window_to_center()
            self.root.overrideredirect(True)

        else:
            self.root = root
            for widget in self.root.winfo_children():
                widget.destroy()

        self.pack_layout()
        self.place_window_to_center()
        # print(self.screen_recording_device_list)

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))

    def load_screen_recording_device_index(self):
        if get_system_name() == "Darwin":
            command = 'ffmpeg -f avfoundation -list_devices true -i ""'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = process.communicate()[1].decode("utf-8")
            self.get_mac_device(output)
        elif get_system_name() == "Windows":
            command = 'ffmpeg -list_devices true -f dshow -i dummy'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = process.communicate()[1].decode("utf-8")
            self.get_windows_device(output)

    def get_mac_device(self, output):
        is_video_line = False
        is_audio_line = False
        for line in output.split("\n"):
            if line.__contains__("AVFoundation video devices:"):
                is_video_line = True
                continue
            elif line.__contains__("AVFoundation audio devices:"):
                is_audio_line = True
                is_video_line = False
                continue
            if line.__contains__("[AVFoundation indev") and is_video_line:
                self.video_device_list.append(line.split("] ")[-1])
            elif line.__contains__("[AVFoundation indev") and is_audio_line:
                self.audio_device_list.append(line.split("] ")[-1])

    def get_windows_device(self, output):
        self.video_device_list.append("Desktop")
        for line in output.split("\n"):
            if line.__contains__("[dshow") and line.__contains__("(audio)"):
                self.audio_device_list.append(line.split("\"")[1])

    def set_default_device_config(self, path):
        self.fpv_url = "192.168.31.144"
        self.fpv_usr = "helloabc"
        self.fpv_pw = "testing1234"
        self.tpv_url = "0"
        self.browser_url = "figma.com"
        self.video_device_idx = 0
        self.audio_device_1_idx = 0
        self.audio_device_2_idx = 1
        save_device_config(path, "fpv", self.fpv_url)
        save_device_config(path, "fpv_usr", self.fpv_usr)
        save_device_config(path, "fpv_pw", self.fpv_pw)
        save_device_config(path, "tpv", self.tpv_url)
        save_device_config(path, "woz", self.browser_url)
        save_device_config(path, "video_device", self.video_device_idx)
        save_device_config(path, "audio_device_1", self.audio_device_1_idx)
        save_device_config(path, "audio_device_2", self.audio_device_2_idx)

    def load_config(self):
        if not os.path.isfile(self.path):
            self.set_default_device_config(self.path)
        try:
            self.df = pandas.read_csv(self.path)
            self.fpv_url = self.df[self.df['item'] == 'fpv']['details'].item()
            self.fpv_usr = self.df[self.df['item'] == 'fpv_usr']['details'].item()
            self.fpv_pw = self.df[self.df['item'] == 'fpv_pw']['details'].item()
            self.tpv_url = self.df[self.df['item'] == 'tpv']['details'].item()
            self.browser_url = self.df[self.df['item'] == 'woz']['details'].item()
            self.video_device_idx = self.df[self.df['item'] == 'video_device']['details'].item()
            self.audio_device_1_idx = self.df[self.df['item'] == 'audio_device_1']['details'].item()
            self.audio_device_2_idx = self.df[self.df['item'] == 'audio_device_2']['details'].item()
        except:
            print("Config file has an error!")

    def load_fpv_device(self):
        self.fpv_url = self.fpv_txt.get_text()
        self.fpv_usr = self.fpv_usr_txt.get_text()
        self.fpv_pw = self.fpv_pw_txt.get_text()
        self.df.loc[self.df['item'] == "fpv", ['details']] = self.fpv_url
        self.df.loc[self.df['item'] == "fpv_usr", ['details']] = self.fpv_usr
        self.df.loc[self.df['item'] == "fpv_pw", ['details']] = self.fpv_pw
        self.df.to_csv(self.path, index=False)
        fpv = StreamPlayer(isFPV=True, ip=self.fpv_url, user=self.fpv_usr, pw=self.fpv_pw)
        p1 = Process(target=fpv.run)
        print("start streaming")
        p1.start()

    def load_tpv_device_stream(self):
        self.tpv_url = self.tpv_txt.get_text()
        self.df.loc[self.df['item'] == "tpv", ['details']] = self.tpv_url
        self.df.to_csv(self.path, index=False)
        tpv = StreamPlayer(isFPV=False, ip=self.tpv_url)
        p1 = Process(target=tpv.run)
        print("start streaming")
        p1.start()

    def load_tpv_device_browser(self):
        self.tpv_url = self.tpv_txt.get_text()
        if not re.match('(?:http|ftp|https)://', self.tpv_url):
            self.browser_url = 'https://{}'.format(self.tpv_url)
        webbrowser.get().open(self.tpv_url)
        self.df.loc[self.df['item'] == "tpv", ['details']] = self.tpv_url
        self.df.to_csv(self.path, index=False)

    def load_browser(self):
        self.browser_url = self.woz_txt.get_text()
        if self.browser_url.__contains__(".py"):
            import sys
            import subprocess
            subprocess.Popen(f"{sys.executable} {self.browser_url}", stdin=subprocess.PIPE, shell=True)
        else:
            if not re.match('(?:http|ftp|https)://', self.browser_url):
                self.browser_url = 'https://{}'.format(self.browser_url)
            webbrowser.get().open(self.browser_url)
        self.df.loc[self.df['item'] == "woz", ['details']] = self.browser_url
        self.df.to_csv(self.path, index=False)

    def save_screen_recording_source(self):
        self.video_device_idx = self.video_device.get()
        self.audio_device_1_idx = self.audio_device_1.get()
        self.audio_device_2_idx = self.audio_device_2.get()
        self.df.loc[self.df['item'] == "video_device", ['details']] = self.video_device_idx
        self.df.loc[self.df['item'] == "audio_device_1", ['details']] = self.audio_device_1_idx
        self.df.loc[self.df['item'] == "audio_device_2", ['details']] = self.audio_device_2_idx
        self.df.to_csv(self.path, index=False)

    def on_close_window(self):
        self.save_screen_recording_source()
        self.root.destroy()
        self.configuration_panel.on_close_device_panel()

    def pack_layout(self):
        self.frame = get_bordered_frame(self.root)
        self.frame.pack()

        self.fpv_frame = ttk.Frame(self.frame)
        self.fpv_frame.pack(pady=10, anchor="w")

        self.tpv_frame = ttk.Frame(self.frame)
        self.tpv_frame.pack(pady=10, anchor="w")

        self.woz_frame = ttk.Frame(self.frame)
        self.woz_frame.pack(pady=10, anchor="w")

        self.recording_device_frame = ttk.Frame(self.frame)
        self.recording_device_frame.pack(pady=10, anchor="w")

        # self.fpv_btn = ttk.Button(self.fpv_frame, text="FPV", command=self.load_fpv_device, width=10)
        self.fpv_btn = get_button(self.fpv_frame, text="FPV", command=self.load_fpv_device, pattern=0)
        self.fpv_btn.pack(side="left", padx=5)
        self.fpv_txt = get_entry_with_placeholder(master=self.fpv_frame, placeholder=self.fpv_url)
        self.fpv_txt.pack(side="left", padx=5)
        self.fpv_usr_txt = get_entry_with_placeholder(master=self.fpv_frame, placeholder=self.fpv_usr)
        self.fpv_usr_txt.pack(side="left", padx=5)
        self.fpv_pw_txt = get_entry_with_placeholder(master=self.fpv_frame, placeholder=self.fpv_pw)
        self.fpv_pw_txt.pack(side="left", padx=5)

        # self.tpv_btn = ttk.Button(self.tpv_frame, text="TPV", width=10, command=self.load_tpv_device)
        self.tpv_btn = get_button(self.tpv_frame, text="TPV", command=self.load_tpv_device_browser, pattern=0)
        self.tpv_btn.pack(side="left", padx=5)
        self.tpv_txt = get_entry_with_placeholder(master=self.tpv_frame, placeholder=self.tpv_url)
        self.tpv_txt.pack(side="left", padx=5)

        # self.woz_btn = ttk.Button(self.woz_frame, text="WoZ", command=self.load_browser, width=10)
        self.woz_btn = get_button(self.woz_frame, text="WoZ", command=self.load_browser, pattern=0)
        self.woz_btn.pack(side="left", padx=5)
        self.woz_txt = get_entry_with_placeholder(master=self.woz_frame, placeholder=self.browser_url)
        self.woz_txt.pack(side="left", padx=5)

        self.video_device = tkinter.StringVar()
        self.video_device.set(self.video_device_idx)
        self.audio_device_1 = tkinter.StringVar()
        self.audio_device_1.set(self.audio_device_1_idx)
        self.audio_device_2 = tkinter.StringVar()
        self.audio_device_2.set(self.audio_device_2_idx)

        self.video_label = get_label(self.recording_device_frame, text="Screen Recording Video Source:")
        self.video_label.grid(column=0, row=1, columnspan=1, padx=10, pady=10, sticky="w")
        self.video_options = get_dropdown_menu(self.recording_device_frame, values=self.video_device_list,
                                               variable=self.video_device)

        self.audio_label = get_label(self.recording_device_frame, text="Screen Recording Audio Source 1:")
        self.audio_label.grid(column=0, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                               variable=self.audio_device_1)

        self.audio_label_2 = get_label(self.recording_device_frame, text="Screen Recording Audio Source 2:")
        self.audio_label_2.grid(column=0, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2 = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                                 variable=self.audio_device_2)

        self.video_options.grid(column=1, row=1, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options.grid(column=1, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2.grid(column=1, row=3, columnspan=1, padx=10, pady=10, sticky="w")

        self.close_frame = ttk.Frame(self.frame)
        self.close_frame.pack(pady=10)
        # self.close_btn = ttk.Button(self.close_frame, text="OK", command=self.on_close_window, width=10)
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()
