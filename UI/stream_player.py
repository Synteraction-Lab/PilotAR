import sys
from time import sleep

from Utilities.streaming_client import StreamClient

sys.path.append("./")
import threading
from tkinter import W, Tk, Label, ttk, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

from UI.entry_with_placeholder import EntryWithPlaceholder
from UI.widget_generator import get_messagebox
from Utilities.screen_capture import get_second_monitor_original_pos

FPS_SCALE = 3

class StreamPlayer:
    def __init__(self, isFPV, ip="192.168.31.144", user="helloabc", pw="testing1234"):
        self.video_size = (1920, 1080)
        self.NO_OF_GRID_ROWS = 5
        self.NO_OF_GRID_COLS = 5
        self.USERNAME = user
        self.PASSWORD = pw
        self.IP = ip
        self.isFPV = isFPV
        self.SETTINGS = "holo=true&pv=true&mic=false&loopback=false&vstab=true"
        if isFPV:
            self.lbl_text = "HoloLens"
            self.title = "FPV"
        else:
            self.lbl_text = "Camera"
            self.title = "TPV"
        self.stream_client = None

    # def run(self, mode="tk"):
    def run(self, mode="tk"):
        if mode == "tk":
            self.run_with_tk()
        else:
            self.run_with_opencv()

    def run_with_tk(self):
        # Replace the video capture attributes based on the need
        self.root = Tk()
        self.root.title(self.title)
        if self.isFPV:
            self.root.geometry('500x350+{}+{}'.format(get_second_monitor_original_pos()[0],
                                                      get_second_monitor_original_pos()[1] + 60))
        else:
            self.root.geometry('500x350+{}+{}'.format(get_second_monitor_original_pos()[0],
                                                      get_second_monitor_original_pos()[1] +
                                                      get_second_monitor_original_pos()[3] // 2))
        self.movieLabel = Label(self.root)
        self.movieLabel.pack(padx=10, pady=10, side="top")
        self.sep = ttk.Separator(self.root, orient='horizontal')
        self.sep.pack(side="top", fill='x')

        self.input_row_frame = ttk.Frame(self.root)
        self.lbl = ttk.Label(self.input_row_frame, text=self.lbl_text, font='Helvetica 18 bold')
        self.lbl.pack(side="left", padx=5)
        self.ip_txt = EntryWithPlaceholder(master=self.input_row_frame, placeholder="Enter IP Address")
        self.ip_txt.pack(side="left", padx=5)
        self.load_btn = ttk.Button(self.input_row_frame, text="Load", command=self.load)
        self.load_btn.pack(side="left", padx=5)
        # self.input_row_frame.pack(side="top", anchor=W, pady=10)
        self.root.bind("<Configure>", self.resize)
        self.init_video_frame()

        t1 = threading.Thread(target=self.load)
        t1.start()
        self.ip_txt.insert_text(self.IP)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()


    def on_close(self):
        if self.stream_client is not None:
            self.stream_client.stop()
        self.root.destroy()


    def resize(self, event):
        try:
            if event.widget == self.root:
                if event.width / event.height < self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / self.cap.get(
                        cv2.CAP_PROP_FRAME_WIDTH):
                    width = int(event.width) - 10
                    height = int(
                        self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * width / self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                else:
                    height = int(event.height) - 10
                    width = int(
                        self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) * height / self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if height != 0 and width != 0:
                    self.video_size = (width, height)

                # print(self.video_size)
        except:
            pass

    def load(self):
        print("start loading streaming")
        if self.ip_txt.get_text() != "":
            self.IP = self.ip_txt.get()
        self.set_cap()

        if self.cap is None or not self.cap.isOpened():
            self.init_video_frame()
            self.movieLabel.update()
        else:
            size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / 2), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2))
            self.video_size = size
            # print("init_size", self.video_size)
            try:
                self.stream_client = StreamClient()
            except:
                print("Can't connect to stream server")
                self.stream_client = None
            while True:
                count = 0
                while self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        count += 1
                        if count == FPS_SCALE and self.stream_client is not None:
                            count = 0
                            resized_frame = cv2.resize(frame, size)
                            self.stream_client.send_frame(resized_frame)
                        img = cv2.cvtColor(
                            self.draw_grid(frame, grid_shape=(self.NO_OF_GRID_ROWS, self.NO_OF_GRID_COLS)),
                            cv2.COLOR_BGR2RGBA)
                        current_image = Image.fromarray(img).resize(self.video_size)
                        if current_image != None:
                            imgtk = ImageTk.PhotoImage(image=current_image)
                        self.movieLabel.config(image=imgtk)
                        self.movieLabel.image = imgtk
                        self.movieLabel.update()
                    else:
                        print("Stop streaming")
                        self.cap.release()
                        break
                sleep(0.1)
                print("Reconnecting to Hololens...")
                self.set_cap()

    def set_cap(self):
        if self.IP == "0":
            self.cap = cv2.VideoCapture(0)
        else:
            try:
                self.cap = cv2.VideoCapture("https://{}:{}@{}/api/holographic/stream/live_med.mp4?{}".
                                            format(self.USERNAME, self.PASSWORD, self.IP, self.SETTINGS))
            except:
                get_messagebox(self.root, "Please check the IP address")

    def init_video_frame(self):
        img = None
        try:
            img = Image.open("../assets/no_video_icon.png")
        except:
            img = Image.open("./assets/no_video_icon.png")
        img = img.resize((500, 300))
        imgtk = ImageTk.PhotoImage(image=img)
        self.movieLabel.config(image=imgtk)
        self.movieLabel.image = imgtk

    def run_with_opencv(self):
        # Replace the video capture attributes based on the need
        self.cap = cv2.VideoCapture("https://{}:{}@{}/api/holographic/stream/live.mp4?{}".
                                    format(self.USERNAME, self.PASSWORD, self.IP, self.SETTINGS))
        size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / 2), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2))
        cv2.namedWindow("FPV")
        x, y = get_second_monitor_original_pos()[0], get_second_monitor_original_pos()[1]
        # Known Issue: macOS doesn't support move window to negative position
        cv2.moveWindow("FPV", x, y)
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Can't receive frame.")
                break

            frame = cv2.resize(frame, size)
            frame = self.draw_grid(img=frame, grid_shape=(self.NO_OF_GRID_ROWS, self.NO_OF_GRID_COLS))

            cv2.imshow("FPV", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    def draw_grid(self, img, grid_shape, color=(0, 255, 0), thickness=1):
        h, w, _ = img.shape
        rows, cols = grid_shape
        dy, dx = h / rows, w / cols

        # draw vertical lines
        for x in np.linspace(start=dx, stop=w - dx, num=cols - 1):
            x = int(round(x))
            cv2.line(img, (x, 0), (x, h), color=color, thickness=thickness)

        # draw horizontal lines
        for y in np.linspace(start=dy, stop=h - dy, num=rows - 1):
            y = int(round(y))
            cv2.line(img, (0, y), (w, y), color=color, thickness=thickness)

        return img


if __name__ == '__main__':
    stream_player = StreamPlayer(isFPV=True)
    stream_player.run("tk")
