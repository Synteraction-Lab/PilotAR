import os
import re
import subprocess
import webbrowser
from multiprocessing import Process
import sounddevice as sd

import pandas
import ttkbootstrap as ttk
import tkinter

from UI.messagebox import MessageBox
from UI.stream_player import StreamPlayer
from UI.widget_generator import get_button, get_dropdown_menu, get_bordered_frame, get_entry_with_placeholder, get_label
from Utilities import log_utilities
from Utilities import default_config
from Utilities.WOZ_video_streaming_client import receive_tool_stream
from Utilities.WOZ_video_streaming_server import send_tool_stream
from Utilities.common_utilities import get_system_name
from Utilities.screen_capture import get_second_monitor_original_pos
import socket

FILE_NAME = "device_config.csv"


def save_device_config(path, item, data):
    print(f'Saving {item} to: ' + path)
    log_utilities.record_device_config(path, item, data)


def get_my_ip_address():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
        sock.close()
        return ip_address
    except socket.error:
        return None


class DevicePanel:
    def __init__(self, root=None, configuration_panel=None, is_run_alone=False):
        self.server_frame = None
        self.client_frame = None
        self.audio_device_list = []
        self.video_device_list = []
        # device type: "Wizard" or "Observer"
        self.device_type = tkinter.Variable()
        self.target_device_ip = ""
        self.streaming_port = ""
        self.communication_port = ""
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
             self.get_windows_device_old()

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

    def get_windows_device(self):
        try:
            devices = sd.query_devices()
            audio_input_names = [device['name'] for device in devices if device['max_input_channels'] > 0]
            self.audio_device_list = list(set(audio_input_names))
            self.video_device_list.append("Desktop")
        except Exception as e:
            print("get_windows_device")
            print(e)


    def get_windows_device_old(self):
        self.video_device_list.append("Desktop")
        try:
            command = 'ffmpeg -list_devices true -f dshow -i dummy'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = process.communicate()[1].decode("utf-8")
            for line in output.split("\n"):
                if line.__contains__("[dshow") and line.__contains__("(audio)"):
                    self.audio_device_list.append(line.split("\"")[1])            
        except Exception as e:
            print("get_windows_device_old")
            print(e)


    def set_default_device_config(self, path):

        self.target_device_ip = default_config.DEFAULT_TARGET_DEVICE_IP
        self.streaming_port = default_config.DEFAULT_STREAMING_PORT
        self.communication_port = default_config.DEFAULT_COMMUNICATION_PORT
        self.device_type.set("Wizard")

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
        except:
            # remove the corrupted file
            os.remove(self.path)
            self.set_default_device_config(self.path)
            self.df = pandas.read_csv(self.path)
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

    def start_tool_stream_server(self):
        self.streaming_port = self.streaming_port_txt.get_text()
        self.df.loc[self.df['item'] == "streaming_port", ['details']] = self.streaming_port
        self.df.loc[self.df['item'] == "communication_port", ['details']] = self.communication_port
        self.df.to_csv(self.path, index=False)

        print(f"This is the: {self.audio_device_2.get()}")
        send_tool_stream(self.audio_device_1.get(), self.audio_device_2.get(), self.video_device.get(), self.streaming_port)
        self.tool_stream_btn.configure(state='disabled')
        MessageBox(self.root, "Start to stream your screen to the client device", font=(None, 12))

    def start_tool_stream_client(self):
        self.target_device_ip = self.target_device_ip_txt.get_text()
        self.streaming_port = self.streaming_port_txt.get_text()
        self.df.loc[self.df['item'] == "target_device_ip", ['details']] = self.target_device_ip
        self.df.loc[self.df['item'] == "streaming_port", ['details']] = self.streaming_port
        self.df.loc[self.df['item'] == "communication_port", ['details']] = self.communication_port
        self.df.to_csv(self.path, index=False)
        self.tool_stream_btn.configure(state='disabled')
        receive_tool_stream(self.target_device_ip, self.streaming_port)

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
        # self.device_type_list = ["Server", "Client"]
        # self.device_type_options = get_dropdown_menu(self.frame, values=self.device_type_list,
        #                                              variable=self.device_type)
        # self.device_type_options.pack()
        self.select_layout()

        # listen self.device_type variable change and bind with function pack_server_layout or pack_client_layout
        self.device_type.trace("w", self.select_layout)

    def select_layout(self, *args):
        if self.device_type.get() == "Wizard":
            self.server_frame = ttk.Frame(self.frame)
            self.server_frame.pack()
            self.pack_server_layout()
        elif self.device_type.get() == "Observer":
            self.client_frame = ttk.Frame(self.frame)
            self.client_frame.pack()
            self.pack_client_layout()
        elif self.device_type.get() == "Single User":
            self.single_user_frame = ttk.Frame(self.frame)
            self.single_user_frame.pack()
            self.pack_single_user_layout()

    def pack_client_layout(self):
        self.head_frame = ttk.Frame(self.client_frame)
        self.head_frame.pack(pady=10, anchor="w")
        self.tool_stream_frame = ttk.Frame(self.client_frame)
        self.tool_stream_frame.pack(pady=10, anchor="w")
        self.woz_frame = ttk.Frame(self.client_frame)
        self.woz_frame.pack(pady=10, anchor="w")
        self.recording_device_frame = ttk.Frame(self.client_frame)
        self.recording_device_frame.pack(pady=10, anchor="w")

        self.head_label = get_label(self.head_frame,
                                    text=f"My Role: {self.device_type.get()} | IP Address: {get_my_ip_address()}")
        self.head_label.pack(side="left", padx=5)

        self.tool_stream_btn = get_button(self.tool_stream_frame, text="Receive Wizard Stream", pattern=0,
                                          command=self.start_tool_stream_client)
        self.tool_stream_btn.pack(side="left", padx=5)
        self.target_device_ip_txt = get_entry_with_placeholder(master=self.tool_stream_frame,
                                                               placeholder=self.target_device_ip, width=15)
        self.target_device_ip_txt.pack(side="left", padx=5)
        self.streaming_port_txt = get_entry_with_placeholder(master=self.tool_stream_frame,
                                                                 placeholder=self.streaming_port, width=15)
        self.streaming_port_txt.pack(side="left", padx=5)
        self.communication_port_txt = get_entry_with_placeholder(master=self.tool_stream_frame,
                                                                 placeholder=self.communication_port, width=15)
        self.communication_port_txt.pack(side="left", padx=5)

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
        self.audio_label = get_label(self.recording_device_frame, text="Microphone Audio Source:")
        self.audio_label.grid(column=0, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                               variable=self.audio_device_1)
        self.audio_label_2 = get_label(self.recording_device_frame, text="Screen Audio Source:")
        self.audio_label_2.grid(column=0, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2 = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                                 variable=self.audio_device_2)
        self.video_options.grid(column=1, row=1, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options.grid(column=1, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2.grid(column=1, row=3, columnspan=1, padx=10, pady=10, sticky="w")

        self.close_frame = ttk.Frame(self.client_frame)
        self.close_frame.pack(pady=10)
        # self.close_btn = ttk.Button(self.close_frame, text="OK", command=self.on_close_window, width=10)
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

    def pack_single_user_layout(self):
        self.fpv_frame = ttk.Frame(self.single_user_frame)
        self.fpv_frame.pack(pady=10, anchor="w")
        self.tpv_frame = ttk.Frame(self.single_user_frame)
        self.tpv_frame.pack(pady=10, anchor="w")
        self.woz_frame = ttk.Frame(self.single_user_frame)
        self.woz_frame.pack(pady=10, anchor="w")
        self.recording_device_frame = ttk.Frame(self.single_user_frame)
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
        self.audio_label = get_label(self.recording_device_frame, text="Microphone Audio Source:")
        self.audio_label.grid(column=0, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                               variable=self.audio_device_1)
        self.audio_label_2 = get_label(self.recording_device_frame, text="Screen Audio Source:")
        self.audio_label_2.grid(column=0, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2 = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                                 variable=self.audio_device_2)
        self.video_options.grid(column=1, row=1, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options.grid(column=1, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2.grid(column=1, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.close_frame = ttk.Frame(self.single_user_frame)
        self.close_frame.pack(pady=10)
        # self.close_btn = ttk.Button(self.close_frame, text="OK", command=self.on_close_window, width=10)
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

    def pack_server_layout(self):
        print("pack_server_layout")
        self.head_frame = ttk.Frame(self.server_frame)
        self.head_frame.pack(pady=10, anchor="w")
        self.tool_stream_frame = ttk.Frame(self.server_frame)
        self.tool_stream_frame.pack(pady=10, anchor="w")

        self.head_label = get_label(self.head_frame,
                                    text=f"My Role: {self.device_type.get()} | IP Address: {get_my_ip_address()}")
        self.head_label.pack(side="left", padx=5)

        self.tool_stream_btn = get_button(self.tool_stream_frame, text="Stream to Observer", pattern=0,
                                          command=self.start_tool_stream_server)
        self.tool_stream_btn.pack(side="left", padx=5)
        self.streaming_port_txt = get_entry_with_placeholder(master=self.tool_stream_frame,
                                                               placeholder=self.streaming_port)
        self.streaming_port_txt.pack(side="left", padx=5)
        self.communication_port_txt = get_entry_with_placeholder(master=self.tool_stream_frame,
                                                                 placeholder=self.communication_port)
        self.communication_port_txt.pack(side="left", padx=5)

        self.fpv_frame = ttk.Frame(self.server_frame)
        self.fpv_frame.pack(pady=10, anchor="w")
        self.tpv_frame = ttk.Frame(self.server_frame)
        self.tpv_frame.pack(pady=10, anchor="w")
        self.woz_frame = ttk.Frame(self.server_frame)
        self.woz_frame.pack(pady=10, anchor="w")
        self.recording_device_frame = ttk.Frame(self.server_frame)
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
        self.audio_label = get_label(self.recording_device_frame, text="Microphone Audio Source:")
        self.audio_label.grid(column=0, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                               variable=self.audio_device_1)
        self.audio_label_2 = get_label(self.recording_device_frame, text="Screen Audio Source:")
        self.audio_label_2.grid(column=0, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2 = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                                 variable=self.audio_device_2)
        self.video_options.grid(column=1, row=1, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options.grid(column=1, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options_2.grid(column=1, row=3, columnspan=1, padx=10, pady=10, sticky="w")
        self.close_frame = ttk.Frame(self.server_frame)
        self.close_frame.pack(pady=10)
        # self.close_btn = ttk.Button(self.close_frame, text="OK", command=self.on_close_window, width=10)
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()
