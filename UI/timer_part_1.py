import os
import ttkbootstrap as ttk
import tkinter as tk
import socket
from threading import Thread

from UI.timer_part_2 import Timer_Part_2
from UI.widget_generator import get_circular_button, get_entry_with_placeholder, get_messagebox, get_label, get_bordered_frame
from Utilities.screen_capture import ScreenCapture
from Utilities import default_config
from Utilities.common_utilities import get_my_ip_address, get_role, get_target_ip, get_communication_port

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

    def get_waiting_popup(self, text):
        loading = get_bordered_frame(self.root)
        frame = tk.Frame(loading, width=300, height=300)
        message_txt = tk.Label(frame, text=text, font=48)
        message_txt.pack(pady=10)
        frame.pack(expand=True, padx=10)
        loading.pack(expand=True)
        return loading

    def start(self):
        if not self.get_anticipated_duration():
            return
        
        if not self.set_pid():
            get_messagebox(self.root, "Please change the PID!")
            return
        self.myTimer = Timer_Part_2(root=self.top_level_root, frame=self.root, pid=self.pid,
                                    anticipated_duration=self.get_anticipated_duration(), workflow=self.workflow)

        def start_pilot():
            try:
                myScreen_capture = ScreenCapture()
                print("start capture")
                self.myTimer.set_screen_capture(myScreen_capture)
            except RuntimeError:
                print("Screen Capture and/or Audio Recorder is not loaded")
            self.workflow.lower()
            self.myTimer.run()

        if get_role() == 'Observer':
            loading = self.get_waiting_popup('Waiting for Wizard to start the pilot.')

            def wait_for_wizard():
                try:
                    observer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    observer_socket.connect((get_target_ip(), get_communication_port()))
                    loading.destroy()
                except:
                    loading.destroy()
                    start_without_wizard = self.get_waiting_popup('Starting pilot without Wizard')
                    start_without_wizard.mainloop()
                finally:
                    start_pilot()
            
            Thread(target=wait_for_wizard).start()
            loading.mainloop()
        elif get_role() == 'Wizard':
            loading = self.get_waiting_popup('Waiting for Observer to be ready.')

            def wait_for_observer():
                try:
                    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_socket.bind((get_my_ip_address(), get_communication_port()))
                    server_socket.listen(1)  # Listen for incoming connections
                    server_socket.settimeout(default_config.DEFAULT_CONNECTION_TIMEOUT)
                    conn, addr = server_socket.accept()
                    loading.destroy()
                    conn.close()  # Close the connection
                except:
                    loading.destroy()
                    start_without_observer = self.get_waiting_popup('Starting pilot without Observer')
                    start_without_observer.mainloop()
                finally:
                    start_pilot()
            
            Thread(target=wait_for_observer).start()
            loading.mainloop()
        else:
            start_pilot()
    
