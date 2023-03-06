import sys

from Utilities.streaming_server import StreamServer

sys.path.append("./")
import threading
from tkinter import W, Tk, Label, ttk, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

from UI.entry_with_placeholder import EntryWithPlaceholder
from Utilities.screen_capture import get_second_monitor_original_pos

FPS_SCALE = 3


class SocketStreamPlayer:
    def __init__(self, isFPV):
        self.running_flag = False
        self.stream_server = None
        self.video_size = (1920, 1080)
        self.NO_OF_GRID_ROWS = 5
        self.NO_OF_GRID_COLS = 5
        self.isFPV = isFPV
        self.port = 8080
        if isFPV:
            self.lbl_text = "Socket"
            self.title = "FPV"
        else:
            self.lbl_text = "Camera"
            self.title = "TPV"

    def run(self):
        # Replace the video capture attributes based on the need
        self.root = Tk()
        self.root.title(self.title)
        if self.isFPV:
            self.root.geometry('500x380+{}+{}'.format(get_second_monitor_original_pos()[0],
                                                      get_second_monitor_original_pos()[1] + 60))
        else:
            self.root.geometry('500x380+{}+{}'.format(get_second_monitor_original_pos()[0],
                                                      get_second_monitor_original_pos()[1] +
                                                      get_second_monitor_original_pos()[3] // 2))
        self.movieLabel = Label(self.root)
        self.movieLabel.pack(padx=10, pady=10, side="top")
        self.sep = ttk.Separator(self.root, orient='horizontal')
        self.sep.pack(side="top", fill='x')

        self.input_row_frame = ttk.Frame(self.root)
        self.lbl = ttk.Label(self.input_row_frame, text=self.lbl_text, font='Helvetica 18 bold')
        self.lbl.pack(side="left", padx=5)
        self.port_txt = EntryWithPlaceholder(master=self.input_row_frame, placeholder="Enter Port")
        self.port_txt.pack(side="left", padx=5)
        self.load_btn = ttk.Button(self.input_row_frame, text="Load", command=self.load)
        self.load_btn.pack(side="left", padx=5)
        self.input_row_frame.pack(side="top", anchor=W, pady=10)
        self.root.bind("<Configure>", self.resize)
        self.init_video_frame()
        self.running_flag = True
        self.load_thread = threading.Thread(target=self.load)
        self.load_thread.start()
        self.port_txt.insert_text(self.port)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        self.root.mainloop()

    def resize(self, event):
        try:
            if event.widget == self.root:
                if event.width / event.height < self.stream_server.get_height() / self.stream_server.get_width():
                    width = int(event.width) - 10
                    height = int(
                        self.stream_server.get_height() * width / self.stream_server.get_width())
                else:
                    height = int(event.height) - 10
                    width = int(
                        self.stream_server.get_width() * height / self.stream_server.get_height())
                if height != 0 and width != 0:
                    self.video_size = (width, height)
                print(self.video_size)
        except:
            pass

    def load(self):
        print("start loading streaming")
        self.stream_server = StreamServer(port=int(self.port_txt.get()))

        self.init_video_frame()
        self.movieLabel.update()

        while self.running_flag:
            while self.stream_server.isOpened():
                frame = self.stream_server.read()
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                current_image = Image.fromarray(img)
                if not self.running_flag:
                    return
                if current_image != None:
                    imgtk = ImageTk.PhotoImage(image=current_image)
                self.movieLabel.config(image=imgtk)
                self.movieLabel.image = imgtk
                self.movieLabel.update()

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

    def on_close_window(self):
        self.running_flag = False

        self.stream_server.close()
        self.root.destroy()


if __name__ == '__main__':
    socket_stream_player = SocketStreamPlayer(isFPV=True)
    socket_stream_player.run()
