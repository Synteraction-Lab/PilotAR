import math
import os.path
import platform
import subprocess
import time
from datetime import datetime

import cv2
import ffmpeg
import numpy as np
import pandas
from mss import mss
from screeninfo import get_monitors

from Utilities.common_utilities import check_saving_path, str_to_sec, get_system_name

CONFIG_FILE_NAME = "device_config.csv"

def print_monitors():
    for m in get_monitors():
        print(m)


class VideoInfo:
    def __init__(self, path, duration, mark_frames_no):
        self.path = path
        self.duration = duration
        self.mark_frame_info = mark_frames_no


def get_marked_frame_info(mark_frames_no):
    if len(mark_frames_no) > 0:
        info = mark_frames_no.pop(0)
        return info
    return None


def add_circular_mark_to_video(mark_frames_no, path):
    while True:
        try:
            videoCapture = cv2.VideoCapture(os.path.join(path, 'experiment.mp4'))
            break
        except:
            print("video is not ready")
            time.sleep(2)
    frame_count = videoCapture.get(cv2.CAP_PROP_FRAME_COUNT)
    # fps = frame_count / duration
    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    SCREEN_SIZE = (int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    videoWriter = cv2.VideoWriter(os.path.join(path, 'output_amended.mp4'), fourcc, fps, SCREEN_SIZE)
    duration_to_show_mark = 5
    frames_required_for_mark = math.floor(duration_to_show_mark * fps)
    count = 0
    info = get_marked_frame_info(mark_frames_no)
    current_frame_to_mark = -1
    current_center_coordinates = None
    if info is not None:
        current_frame_to_mark = math.floor(str_to_sec(info[0]) * fps)
        current_center_coordinates = info[1]
    for i in range(int(frame_count)):
        success, frame = videoCapture.read()
        if i % int(frame_count / 20) == 0:
            print("Processing: {:.0%}".format(i / frame_count))
        if not success:
            break

        frame = cv2.resize(frame, SCREEN_SIZE)
        if i == current_frame_to_mark or count > 0:
            frame = generate_circular_mark(frame, current_center_coordinates)
            count += 1

        if count == frames_required_for_mark:
            count = 0
            info = get_marked_frame_info(mark_frames_no)
            if info is None:
                current_frame_to_mark = -1
                current_center_coordinates = None
                continue
            current_frame_to_mark = math.floor(str_to_sec(info[0]) * fps)
            current_center_coordinates = info[1]

        videoWriter.write(frame)
    videoWriter.release()


def generate_circular_mark(frame, center_coordinates):
    # Create circular mark
    radius = 20
    color = (255, 0, 0)
    thickness = 3
    return cv2.circle(frame, center_coordinates, radius, color, thickness)


def get_second_monitor_original_pos():
    if len(get_monitors()) == 1:
        selected_monitor_idx = 0
        return 0, 0, get_monitors()[selected_monitor_idx].width, get_monitors()[selected_monitor_idx].height
    else:
        selected_monitor_idx = 1
        if platform.uname().system == "Windows":
            y = get_monitors()[selected_monitor_idx].y
        else:
            y = -get_monitors()[selected_monitor_idx].y + get_monitors()[0].height - get_monitors()[1].height
        return get_monitors()[selected_monitor_idx].x, y, \
               get_monitors()[selected_monitor_idx].width, \
               get_monitors()[selected_monitor_idx].height


class ScreenCapture:
    def __init__(self, pid="p1_1"):
        self.thread = None
        self.fourcc = None
        self.is_thread_running = False
        try:
            self.pid = pid
            self.path = os.path.join("data", pid)
            self.config_path = os.path.join("data", CONFIG_FILE_NAME)
            print_monitors()

            # set main monitor
            self.main_monitor_idx = 0

            # set the monitor to capture screen
            if len(get_monitors()) == 1:
                self.selected_monitor_idx = 0
            else:
                self.selected_monitor_idx = 1
            self.SCREEN_SIZE = tuple((get_monitors()[self.selected_monitor_idx].width,
                                      get_monitors()[self.selected_monitor_idx].height))
            self.ORIGINAL_POINT = tuple((get_monitors()[self.selected_monitor_idx].x,
                                         get_monitors()[self.selected_monitor_idx].y
                                         + get_monitors()[self.selected_monitor_idx].height))

            self.is_recording = False
            self.out = None
            self.mark_frames_no = []
        except:
            raise RuntimeError("Please connect to the extended monitor")

    def set_pid_path(self, pid):
        self.pid = pid
        self.path = os.path.join("data", pid)
        check_saving_path(self.path)

    def load_config(self):
        try:
            self.df = pandas.read_csv(self.config_path)
            self.VIDEO_SOURCE_IDX = self.df[self.df['item'] == 'video_device']['details'].item()
            self.AUDIO_DEVICES_IDX_1 = self.df[self.df['item'] == 'audio_device_1']['details'].item()
            self.AUDIO_DEVICES_IDX_2 = self.df[self.df['item'] == 'audio_device_2']['details'].item()
        except:
            print("Config file has an error!")

    def start_recording(self):
        self.AUDIO_DEVICES_IDX = "1"
        self.VIDEO_SOURCE_IDX = "3"
        self.AUDIO_NAME = "Jack Mic (Realtek(R) Audio)"
        self.AUDIO2_NAME = "Stereo Mix (Realtek(R) Audio)"
        self.AUDIO3_NAME = "VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)"
        self.load_config()
        if get_system_name() == "Windows":
            self.recording_cmd = 'ffmpeg -f dshow -i audio=\"{}\" -f dshow -i audio=\"{}\" -f gdigrab -framerate 12 -draw_mouse 1 -i desktop -filter_complex \"[0:a][1:a]amerge=inputs=2[a]\" -map 2 -map \"[a]\" -f mp4 {}'.format(
                self.AUDIO_DEVICES_IDX_1, self.AUDIO_DEVICES_IDX_2, os.path.join(self.path, "experiment.mp4"))

        elif get_system_name() == "Linux":
            self.recording_cmd = 'ffmpeg -video_size 1024x768 -framerate 12 -f x11grab -i :0.0+100,200 -f pulse -ac 2 -i default {}'.format(
                os.path.join(self.path, "experiment.mpr"))

        elif get_system_name() == "Darwin":
            self.recording_cmd = 'ffmpeg -f avfoundation -capture_cursor 1 -i "{}":"{}" -r 12 {}'.format(
                self.VIDEO_SOURCE_IDX, self.AUDIO_DEVICES_IDX, os.path.join(self.path, "experiment.mp4"))
        # self.recording_cmd = self.recording_cmd.split(" ")
        self.process = subprocess.Popen(self.recording_cmd, stdin=subprocess.PIPE, shell=True)

    def stop_recording(self):
        self.process.stdin.write('q'.encode("GBK"))
        self.process.communicate()
        self.process.wait()

    def get_current_frame(self):
        mon = mss().monitors[self.selected_monitor_idx + 1]

        img = mss().grab(mss().monitors[self.selected_monitor_idx + 1])

        img = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        img = cv2.resize(img, self.SCREEN_SIZE)
        return img

    def get_partial_current_frame(self, x, y, w, h):
        mon = mss().monitors[self.selected_monitor_idx + 1]
        monitor = {
            "top": mon["top"] + y,
            "left": mon["left"] + x,
            "width": w,
            "height": h,
            "mon": self.selected_monitor_idx + 1,
        }
        output = "sct-mon{mon}_{top}x{left}_{width}x{height}.png".format(**monitor)
        img = mss().grab(monitor)
        size = img.size
        img = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        img = cv2.resize(img, size)
        print(output, size)
        return img

    def take_screenshot(self, time=None):
        img = self.get_current_frame()
        if time is None:
            time = datetime.now().strftime("%H_%M_%S")
        cv2.imwrite(os.path.join(self.path, "{time}.png".format(time=time)), img)

    def take_partial_screenshot(self, x, y, w, h, time=None):
        img = self.get_partial_current_frame(x, y, w, h)
        if time is None:
            time = datetime.now().strftime("%H_%M_%S")
        cv2.imwrite(os.path.join(self.path, "{time}.png".format(time=time)), img)

    def draw_circle(self, center_point, time=None):
        img, center_coordinates = self.overlay_circular_mark(center_point)

        if time is None:
            time = datetime.now().strftime("%H_%M_%S")

        self.mark_frames_no.append([time, center_coordinates])
        cv2.imwrite(os.path.join(self.path, "{time}.png".format(time=time)), img)
        return center_coordinates

    def overlay_circular_mark(self, center_point):
        # Change coordinate
        center_point = (center_point[0], -center_point[1] + get_monitors()[self.main_monitor_idx].height)
        center_coordinates = (np.subtract(center_point, self.ORIGINAL_POINT))
        center_coordinates = (int(center_coordinates[0]), -int(center_coordinates[1]))
        print(center_coordinates)
        # Get and resize screenshot
        img = self.get_current_frame()
        # Overlay the circle on screenshot
        # img = generate_circular_mark(img, center_coordinates)
        return img, center_coordinates

    def get_path(self):
        return self.path

    def get_video_info(self, duration):
        return VideoInfo(self.path, duration, self.mark_frames_no)


if __name__ == '__main__':
    screen_capture = ScreenCapture()
    screen_capture.start_recording()
