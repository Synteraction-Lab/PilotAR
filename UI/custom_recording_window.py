import sys

sys.path.append("./")
from tkinter import WORD, Toplevel, Frame, filedialog
from UI.widget_generator import get_bordered_frame, get_label, get_button, get_text, get_messagebox, get_entry_with_placeholder
from Utilities.screen_capture import get_second_monitor_original_pos
import os
import shutil


class CustomRecordingWindow:
    def __init__(self, parent=None, callback=None, font=None, width=160,
                 height=150):
        self.parent = parent
        self.root = Toplevel()
        self.root.wait_visibility()
        self.root.overrideredirect(True)
        self.pid = None
        self.font = font
        self.width = width
        self.height = height
        self.callback = callback
        self.pack_layout()
        self.root.attributes('-topmost', True)
        self.place_window_to_center()

    def pack_layout(self):
        self.main_frame = get_bordered_frame(self.root)
        self.frame = Frame(self.main_frame, width=self.width, height=self.height)
        self.pid_label = get_label(self.frame, text="New Participant & Session ID:")
        self.pid_label.pack(side="left")
        self.pid_txt = get_entry_with_placeholder(self.frame, placeholder="p1_1", width=6)
        self.pid_txt.pack(side="left")
        self.frame.pack(expand=True, padx=10, pady=10, side="top")
        self.main_frame.pack(expand=True)
        self.close_frame = Frame(self.frame)
        self.close_frame.pack(padx=10, pady=10, side="bottom")
        self.video_btn = get_button(self.close_frame, text="Select video", command=self.select_video, pattern=0)
        self.video_btn.pack(side="left")
        self.cancel_btn = get_button(self.close_frame, text="Cancel", command=self.on_close_window, pattern=0)
        self.cancel_btn.pack(padx=5, side="left")

    def set_new_pid(self):
        pid = self.pid_txt.get_text()
        if os.path.isdir(os.path.join("data", pid)):
            return False
        self.pid = pid
        return True
    
    def select_video(self):
        if not self.set_new_pid():
                get_messagebox(self.root, "Please change the PID!")
                return
        source_file = filedialog.askopenfilename()
        if source_file:
            try:
                destination_directory = os.path.join("data", self.pid)
                os.makedirs(destination_directory, exist_ok=True)
                shutil.copy(source_file, destination_directory)
                base_filename = os.path.basename(source_file)
                new_file_path = os.path.join(destination_directory, "experiment.mp4")
                os.rename(os.path.join(destination_directory, base_filename), new_file_path)
                print(f"File '{source_file}' copied to '{destination_directory}'.")

                self.on_close_window()
            except Exception as e:
                print(f"An error occurred: {e}")

    def on_close_window(self):
        self.root.destroy()
        if self.callback != None:
            self.callback(self.pid)

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))


