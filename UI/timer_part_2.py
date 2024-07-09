from Utilities.common_utilities import str_to_sec
from UI.analyser import setup_new_analyzer
from UI.marker import Marker
from Utilities.annotation_utilities import get_customized_annotation_df, FUNC_LIST, update_current_annotation_df_for_is_show
from UI.customization_panel import CustomizationPanel
from Utilities import log_utilities
import UI.color
from pynput.mouse import Listener as MouseListener
from PIL import ImageTk, Image
from tkinter.ttk import Label, Button, Style
import ttkbootstrap as ttk
from tkinter import X, Frame, StringVar, messagebox
from multiprocessing import Process
from datetime import datetime
import tkinter as tk
from customtkinter import CTkProgressBar
import os
import threading
import time

import pygame
from UI.confirmbox import ConfirmBox

from UI.image_note import ImageNoteWindow
from UI.photo_gallery import PhotoGallery
from UI.widget_generator import get_button, get_bordered_frame, get_circular_button, get_label, get_messagebox
from UI.UI_config import MAIN_COLOR_LIGHT, TIMER_MARKER_THICKNESS, TIMER_TIMELINE_THICKNESS, WARNING_COLOR, \
    WARNING_COLOR_DARK
from Utilities.key_listener import KeyListener

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


TIME_STR = '%H:%M:%S'

MARKER_DURATION = 3


class Timer_Part_2:
    def __init__(self, root, frame, pid, anticipated_duration, screen_capture=None, workflow=None):
        self.annotation_df = None
        # key - func, value - dict of key value pairs for 'type', 'color', 'value', 'is_show'
        self.annotations_counter_details = {}
        self.setup_annotations_counter_details()
        self.screenshot_flag = False
        self.is_selection_window_existed = False
        self.selection_window = None
        self.root = frame
        self.top_level_root = root
        self.top_level_root = root
        self.annotations_counter_frame = None
        for widget in self.root.winfo_children():
            widget.destroy()

        self.INCORRECT_ACTION_KEY = 'f'
        self.CORRECT_ACTION_KEY = 't'
        self.MARK_KEY = 'w'
        self.SCREENSHOT_KEY = 'q'
        self.hot_keys = {}
        self.pid = pid
        self.anticipated_duration = anticipated_duration
        self.current_accuracy = None

        self.pb_idx = None
        self.pb_frame = None
        self.timeDelta = None
        self.pb = None
        self.is_pb_stop = False

        self.begin = datetime.now()
        self.end = datetime.now()
        self.now_time_label = None
        self.nowTime = StringVar()
        self.is_started = False
        self.nowTime.set(self.get_now_time_string())

        self.marking_flag = False
        self.is_mark_window_existed = False
        self.mark_window_list = []

        self.screen_capture = screen_capture

        self.workflow = workflow

        self.image_note_window_status = False

        self.trial_record = {'total_trial': 0, 'correct_trial': 0}
        self.accuracyText = StringVar()
        self.isAccuracyVisible = tk.IntVar()
        self.isAccuracyVisible.set(1)
        # self.accuracyText.set("Correct: {}\nIncorrect: {}".format(self.CORRECT_ACTION_KEY, self.INCORRECT_ACTION_KEY))
        self.accuracyText.set("Accuracy: NIL")

        self.annotations_txt = StringVar()
        self.no_of_marks = 0
        self.no_of_screenshots_whole = 0
        self.no_of_screenshots_roi = 0
        pygame.mixer.init()
        self.beep_sound = pygame.mixer.Sound('./assets/beep.mp3')
        self.beep_sound.set_volume(0.7)
        self.alarm_sound = pygame.mixer.Sound('./assets/time_up_ringtone.mp3')
        self.alarm_sound.set_volume(0.7)
        self.is_confirm = False
        self.pack_layout()
        # self.parse_hot_keys()

    def setup_annotations_counter_details(self):
        self.annotation_df = get_customized_annotation_df()
        self.annotation_df = update_current_annotation_df_for_is_show(
            self.annotation_df)

        is_show_accuracy = False
        if not self.annotation_df[self.annotation_df['func'] == FUNC_LIST['correct']]['key'].empty:
            correct_annotation = self.annotation_df[self.annotation_df['func']
                                                    == FUNC_LIST['correct']]
            self.annotations_counter_details[correct_annotation['type'].item()] = {
                'func': FUNC_LIST['correct'], 'color': correct_annotation['color'].item(), 'value': 0, 'is_show': correct_annotation['is_show'].item(), 'label': None, 'key': correct_annotation['key'].item()}
            is_show_accuracy = True if (
                correct_annotation['is_show'] == True).bool() else is_show_accuracy

        if not self.annotation_df[self.annotation_df['func'] == FUNC_LIST['incorrect']]['key'].empty:
            incorrect_annotation = self.annotation_df[self.annotation_df['func']
                                                      == FUNC_LIST['incorrect']]
            self.annotations_counter_details[incorrect_annotation['type'].item()] = {
                'func': FUNC_LIST['incorrect'], 'color': incorrect_annotation['color'].item(), 'value': 0, 'is_show': incorrect_annotation['is_show'].item(), 'label': None, 'key': incorrect_annotation['key'].item()}
            is_show_accuracy = True if (
                incorrect_annotation['is_show'] == True).bool() else is_show_accuracy

        if self.annotations_counter_details.get('Accuracy') == None:
            self.annotations_counter_details['accuracy'] = {
                'func': 'Accuracy', 'color': 'white', 'value': 'N.A.', 'is_show': is_show_accuracy, 'label': None}

        for index, row in self.annotation_df.iterrows():
            if row['func'] == FUNC_LIST['voice']:
                continue
            # add it to dict (self.annotations_counter_details) if not yet added (dict's key - type, value - dict of key value pairs for 'func', 'color', 'value', 'is_show', 'label', 'key')
            if self.annotations_counter_details.get(row['type']) == None:
                self.annotations_counter_details[row['type']] = {
                    'func': row['func'], 'color': row['color'], 'value': 0, 'is_show': row['is_show'], 'label': None}
            else:
                self.annotations_counter_details[row['type']
                                                 ]['is_show'] = row['is_show']
            
            self.annotations_counter_details[row['type']]['key'] = row['key']

    def update_annotation_counter_details(self):
        self.annotation_df = get_customized_annotation_df()
        is_show_accuracy = False
        for index, row in self.annotation_df.iterrows():
            if row['func'] == FUNC_LIST['voice']:
                continue
            if (row['func'] == FUNC_LIST['correct'] or row['func'] == FUNC_LIST['incorrect']) and row['is_show']:
                is_show_accuracy = True
            self.annotations_counter_details[row['type']
                                             ]['is_show'] = row['is_show']
        self.annotations_counter_details['accuracy']['is_show'] = is_show_accuracy
        self.generate_annotations_counter_labels()

    def set_screen_capture(self, screen_capture):
        self.screen_capture = screen_capture

    def run(self):
        self.start_stop()
        self.start_listener()
        self.root.mainloop()

    # Listen the mouse click
    def on_click(self, x, y, button, pressed):
        if pressed:
            if self.marking_flag:
                center_point = (x, y)
                if self.mark_window is not None:
                    self.mark_window.configure(bg='red')
                    self.marking_flag = False
                    t = threading.Thread(target=self.thread_destroy_window)
                    t.start()
                self.set_time_index_with_marker(center_point)
            elif self.screenshot_flag:
                self.selection_window_x, self.selection_window_y = int(
                    x), int(y)
                self.generate_selection_window(int(x), int(y))
        else:
            if self.screenshot_flag:
                self.screenshot_flag = False
                self.selection_window_x_prime, self.selection_window_y_prime = int(
                    x), int(y)
                self.destroy_selection_window()
                self.set_time_index_with_roi()

    def generate_selection_window(self, x, y):
        if self.is_selection_window_existed:
            return
        self.is_selection_window_existed = True
        self.selection_window = tk.Toplevel()
        self.selection_window.geometry("0x0+%s+%s" % (x, y))
        self.selection_window.attributes("-alpha", 0.35)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(bg='blue')
        self.selection_window.overrideredirect(True)

    def resize_selection_window(self, x, y):
        if self.selection_window is not None:
            origin_x = min(self.selection_window_x, x)
            origin_y = min(self.selection_window_y, y)
            width = abs(self.selection_window_x - x)
            height = abs(self.selection_window_y - y)
            self.selection_window.geometry(
                "%sx%s+%s+%s" % (width, height, origin_x, origin_y))

    def thread_destroy_window(self):
        time.sleep(MARKER_DURATION)
        self.mark_window.destroy()
        self.is_mark_window_existed = False

    def destroy_selection_window(self):
        self.selection_window.destroy()
        self.is_selection_window_existed = False

    def move_marker(self, x, y):
        self.mark_window.geometry(
            f"+{int(x) - self.mark_window.winfo_width() // 2}+{int(y) - self.mark_window.winfo_height() // 2}")

    def on_move(self, x, y):
        if self.marking_flag:
            self.move_marker(x, y)
        elif self.screenshot_flag and self.is_selection_window_existed:
            self.resize_selection_window(int(x), int(y))

    def generate_mark_window(self):
        if self.is_mark_window_existed:
            return

        self.is_mark_window_existed = True
        self.mark_window = tk.Toplevel()
        self.mark_window.geometry("160x160")
        self.mark_window.attributes("-alpha", 0.35)
        self.mark_window.attributes('-topmost', True)
        self.mark_window.configure(bg='gray8')
        self.mark_window.overrideredirect(True)
        self.marking_flag = True
        self.mark_window_list.append(self.mark_window)

    # Listen the key release
    def on_release(self, key):
        pass

    # Listen the key press
    def on_press(self, key):
        if not (self.is_started and str(key).strip("''").lower() in self.hot_keys.keys()):
            return
        
        if self.image_note_window_status:
            return

        color = self.hot_keys[str(key).strip("''").lower()]['color']

        if str(key).strip("''").lower() == self.SCREENSHOT_KEY:
            self.set_time_index(color)
        elif str(key).strip("''").lower() == self.SCREENSHOT_ROI_KEY:
            self.enable_screenshot_flag()
        elif str(key).strip("''").lower() == self.MARK_KEY:
            self.enable_marking_flag()
        elif str(key).strip("''").lower() == self.CORRECT_ACTION_KEY:
            self.update_accuracy_true(color)
        elif str(key).strip("''").lower() == self.INCORRECT_ACTION_KEY:
            self.update_accuracy_false(color)
        else:
            annotation_type = self.hot_keys[str(
                key).strip("''").lower()]['type']
            annotation_func = self.hot_keys[str(
                key).strip("''").lower()]['func']
            self.add_other_annotation(annotation_type, annotation_func, color)

    def parse_hot_keys(self):
        self.hot_keys = {}
        # self.annotation_df = get_customized_annotation_df()
        for index, row in self.annotation_df.iterrows():
            self.hot_keys.update(
                {row['key']: {'type': row['type'], 'color': row['color'], 'func': row['func']}})
        try:
            if not self.annotation_df[self.annotation_df['func'] == 'Whole Screenshot']['key'].empty:
                self.SCREENSHOT_KEY = self.annotation_df[self.annotation_df['func'] == 'Whole Screenshot']['key'].item(
                )
                self.SCREENSHOT_TYPE_NAME = self.annotation_df[self.annotation_df['func'] == 'Whole Screenshot'][
                    'type'].item()
                screenshot_color = self.annotation_df[self.annotation_df['func']
                                                      == 'Whole Screenshot']['color'].item()
                # self.screenshots_label.configure(fg=UI.color.color_translation(screenshot_color))
            else:
                print("No Whole Screenshot")

            if not self.annotation_df[self.annotation_df['func'] == 'Screenshot With ROI']['key'].empty:
                self.SCREENSHOT_ROI_KEY = self.annotation_df[self.annotation_df['func'] == 'Screenshot With ROI'][
                    'key'].item()
                self.SCREENSHOT_ROI_TYPE_NAME = self.annotation_df[self.annotation_df['func'] == 'Screenshot With ROI'][
                    'type'].item()
                screenshot_ROI_color = self.annotation_df[self.annotation_df['func'] == 'Screenshot With ROI'][
                    'color'].item()
            else:
                print("No Screenshot With ROI")

            if not self.annotation_df[self.annotation_df['func'] == 'Focus']['key'].empty:
                self.MARK_KEY = self.annotation_df[self.annotation_df['func'] == 'Focus']['key'].item(
                )
                self.MARK_TYPE_NAME = self.annotation_df[self.annotation_df['func'] == 'Focus']['type'].item(
                )
                mark_color = self.annotation_df[self.annotation_df['func'] == 'Focus']['color'].item(
                )
                # self.mark_label.configure(fg=UI.color.color_translation(mark_color))
            else:
                print("No Focus")

            if not self.annotation_df[self.annotation_df['func'] == 'Correct']['key'].empty:
                self.CORRECT_ACTION_KEY = self.annotation_df[self.annotation_df['func'] == 'Correct']['key'].item(
                )
                self.CORRECT_TYPE_NAME = self.annotation_df[self.annotation_df['func'] == 'Correct']['type'].item(
                )
                correct_color = self.annotation_df[self.annotation_df['func'] == 'Correct']['color'].item(
                )
                # self.correct_label.configure(
                #     fg=UI.color.color_translation(correct_color))
            else:
                print("No Correct")

            if not self.annotation_df[self.annotation_df['func'] == 'Incorrect']['key'].empty:
                incorrect_color = self.annotation_df[self.annotation_df['func'] == 'Incorrect']['color'].item(
                )
                self.INCORRECT_ACTION_KEY = self.annotation_df[self.annotation_df['func'] == 'Incorrect']['key'].item(
                )
                self.INCORRECT_TYPE_NAME = self.annotation_df[self.annotation_df['func'] == 'Incorrect']['type'].item(
                )
                # self.incorrect_label.configure(
                #     fg=UI.color.color_translation(incorrect_color))
            else:
                print("No Incorrect")

            if not self.annotation_df[self.annotation_df['func'] == 'Counter']['key'].empty:
                counter_color = self.annotation_df[self.annotation_df['func'] == 'Counter']['color'].tolist(
                )
                self.COUNTER_ACTION_KEY = self.annotation_df[self.annotation_df['func'] == 'Counter']['key'].tolist(
                )
                print(counter_color)
            else:
                print("No Counter")
        except Exception as e:
            print(e)
            get_messagebox(
                self.root, "Can't find necessary keys in config file")

    def update_accuracy_true(self, color="green"):
        self.update_accuracy(True)
        timeDelta = self.timeDelta
        self.capture_screen(timeDelta)
        self.mark(timeDelta, color)
        log_utilities.log_manipulation_info(
            self.get_pid(), timeDelta, self.CORRECT_TYPE_NAME, FUNC_LIST['correct'], color)

    def update_accuracy_false(self, color="red"):
        self.update_accuracy(False)
        timeDelta = self.timeDelta
        self.capture_screen(timeDelta)
        self.mark(timeDelta, color)
        log_utilities.log_manipulation_info(self.get_pid(), timeDelta,
                                            self.INCORRECT_TYPE_NAME, FUNC_LIST['incorrect'], color)

    def start_listener(self):
        self.keyboard_listener = KeyListener()
        self.mouse_listener = MouseListener(
            on_click=self.on_click, on_move=self.on_move)

        self.keyboard_listener.set_state("timer", self.on_press)
        self.mouse_listener.start()

    def join_listener(self):
        if self.mouse_listener is not None:
            self.mouse_listener.join()

    def stop_listener(self):
        if self.keyboard_listener is not None and self.mouse_listener is not None:
            self.keyboard_listener.stop()
            self.mouse_listener.stop()

    def get_pid(self):
        return self.pid

    def get_now_time_string(self, mode=None):
        if mode == 'start':
            self.begin = datetime.now()
            return str(self.begin.strftime(TIME_STR))
        elif mode == 'stop':
            self.end = datetime.now()
            return str(self.end.strftime(TIME_STR))
        if self.is_started:
            self.timeDelta = "{:0>8}".format(
                str(datetime.now() - self.begin).split('.')[0])
            return self.timeDelta
        return "00:00:00"

    def update_time(self):
        self.nowTime.set(self.get_now_time_string())
        if self.is_started:
            self.progress()
        self.now_time_label.after(1000, self.update_time)

    def capture_screen(self, time_stamp):
        if self.screen_capture is not None:
            self.screen_capture.take_screenshot(time_stamp.replace(':', '_'))
            self.no_of_screenshots_whole += 1
            self.show_image_captured_preview(time_stamp.replace(':', '_'))
        else:
            get_messagebox(self.root, "Screen capture is not activated!")

    # Mark the important moment
    def set_time_index(self, color="blue"):
        if not self.is_started:
            return
        time_stamp = self.timeDelta
        self.capture_screen(time_stamp)
        # Add Marker to timer
        self.mark(time_stamp, color)
        log_utilities.log_manipulation_info(self.get_pid(), time_stamp, self.SCREENSHOT_TYPE_NAME,
                                            FUNC_LIST['screenshot_whole'], color)
        screenshot_whole_annotation_type = self.annotation_df[self.annotation_df['func']
                                                              == FUNC_LIST['screenshot_whole']]['type'].item()
        self.annotations_counter_details[screenshot_whole_annotation_type]['value'] = self.no_of_screenshots_whole
        self.annotations_counter_details[screenshot_whole_annotation_type]['label'].configure(
            text=self.get_annotation_display_label(screenshot_whole_annotation_type))

    def get_annotation_display_label(self, annotation_type):
        label_text = annotation_type + "= " + str(self.annotations_counter_details[annotation_type]['value'])
        key_code = self.annotations_counter_details[annotation_type].get('key', None)
        if key_code is not None:
            label_text += "\n(key: " + str(key_code) + ")"
        return label_text

    # Set index for screenshot with selected region
    def set_time_index_with_roi(self):
        if not self.is_started:
            return
        time_stamp = self.timeDelta
        if self.screen_capture is not None:
            x = min(self.selection_window_x, self.selection_window_x_prime)
            y = min(self.selection_window_y, self.selection_window_y_prime)
            w = abs(self.selection_window_x - self.selection_window_x_prime)
            h = abs(self.selection_window_y - self.selection_window_y_prime)
            print(x, y, w, h)
            self.screen_capture.take_partial_screenshot(
                x=x, y=y, w=w, h=h, time=time_stamp.replace(':', '_'))
            self.no_of_screenshots_roi += 1
            self.show_image_captured_preview(time_stamp.replace(':', '_'))
        else:
            get_messagebox(self.root, "Screen capture is not activated!")
        # Add Marker to timer
        color = self.hot_keys[self.SCREENSHOT_KEY]['color']
        self.mark(time_stamp, color)
        log_utilities.log_manipulation_info(self.get_pid(), time_stamp, self.SCREENSHOT_ROI_TYPE_NAME,
                                            FUNC_LIST['screenshot_roi'], color)
        screenshot_roi_annotation_type = self.annotation_df[self.annotation_df['func']
                                                            == FUNC_LIST['screenshot_roi']]['type'].item()
        self.annotations_counter_details[screenshot_roi_annotation_type]['value'] = self.no_of_screenshots_roi
        self.annotations_counter_details[screenshot_roi_annotation_type]['label'].configure(
            text=self.get_annotation_display_label(screenshot_roi_annotation_type))


    def enable_screenshot_flag(self):
        if (not self.is_started) or self.is_selection_window_existed:
            return
        self.screenshot_flag = True

    def enable_marking_flag(self):
        print(self.is_mark_window_existed)
        if (not self.is_started) or self.is_mark_window_existed:
            return
        self.generate_mark_window()

    def set_time_index_with_marker(self, center_point):
        if not self.is_started:
            return
        time_stamp = self.timeDelta
        color = self.hot_keys[self.MARK_KEY]['color']
        if self.screen_capture is not None:
            center_coordinates = self.screen_capture.draw_circle(
                center_point, time=time_stamp.replace(':', '_'))
            self.no_of_marks += 1
            self.show_image_captured_preview(time_stamp.replace(':', '_'))
            log_utilities.log_manipulation_info(self.get_pid(), time_stamp, self.MARK_TYPE_NAME,
                                                FUNC_LIST['mark'], color,
                                                "\"{}\"".format(
                                                    {'x': center_coordinates[0], 'y': center_coordinates[1]}))
            mark_annotation_type = self.annotation_df[self.annotation_df['func']
                                                      == FUNC_LIST['mark']]['type'].item()
            self.annotations_counter_details[mark_annotation_type]['value'] = self.no_of_marks
            self.annotations_counter_details[mark_annotation_type]['label'].configure(
                text=self.get_annotation_display_label(mark_annotation_type))
        else:
            get_messagebox(self.root, "Screen capture is not activated!")
        self.marking_flag = False
        # Add Marker to timer
        self.mark(time_stamp, color)

    def mark(self, time_stamp=None, color="blue"):
        if self.is_started:
            if time_stamp is None:
                time_stamp = self.timeDelta
            position = str_to_sec(time_stamp) / self.anticipated_duration
            print(position, self.pb.get())
            marker = Marker(self.pb_frame, width=4, background=color)
            # marker.place(relx=position, rely=0.45, anchor="w", relheight=0.5)
            marker.place(relx=position, rely=0.45, anchor='w',
                         height=TIMER_MARKER_THICKNESS)
            ## self.annotations_txt.set("Screenshots: {}\n Marks: {}".format(self.no_of_screenshots, self.no_of_marks))
            # self.screenshots_txt_var.set(
            #     "Screenshots: {}".format(self.no_of_screenshots))
            # self.mark_txt_var.set("Mark: {}".format(self.no_of_marks))

            self.beep_sound.play()

    def add_other_annotation(self, annotation_type, annotation_func, color):
        timeDelta = self.timeDelta
        self.mark(timeDelta, color)
        log_utilities.log_manipulation_info(
            self.get_pid(), timeDelta, annotation_type, annotation_func, color)
        self.annotations_counter_details[annotation_type
                                         ]['value'] += 1
        self.annotations_counter_details[annotation_type]['label'].configure(
            text=self.get_annotation_display_label(annotation_type))

    # ProgressBar component
    def create_progress_bar(self, root):
        self.is_pb_stop = False
        self.pb_frame = Frame(
            root, borderwidth=1, highlightthickness=0, highlightbackground="white")

        self.determinate_speed = 1 / self.anticipated_duration
        print("determinate_speed: {}".format(self.determinate_speed))
        self.pb = CTkProgressBar(master=self.pb_frame, width=600, corner_radius=0, height=TIMER_TIMELINE_THICKNESS,
                                 orientation="horizontal", bg_color="#6D8389", progress_color="#C2C2C2",
                                 determinate_speed=self.determinate_speed)
        self.pb.pack()

        self.pb_frame.pack(side="left")
        # self.Pb_frame.pack(side="top", ipady=10)

    def update_progress_label(self):
        return f"Current Progress: {self.pb['value']}%"

    def progress(self):
        if self.pb.get() < 1:
            self.pb.set(
                (datetime.now() - self.begin).total_seconds() / self.anticipated_duration)

        if self.is_pb_stop:
            return

        if ((self.pb.get() + self.determinate_speed) >= 1) or (
                (datetime.now() - self.begin).total_seconds() >= self.anticipated_duration):
            self.pb.set(1)
            self.pb.stop()
            self.alarm_sound.play()
            self.is_pb_stop = True

    def pb_stop(self):
        self.pb.stop()

    def on_click_yes_option(self):
        self.on_stop()
        self.start_stop_btn_txt.set("Start")
        self.workflow.lower()

    def start_stop(self):
        if self.is_started:
            ConfirmBox(self.root, "Are you sure you want to STOP the pilot now?", font=(None, 12),
                       on_click_yes_func=self.on_click_yes_option)
        else:
            self.on_start()

    def on_start(self):
        if self.screen_capture is not None:
            self.start_stop_btn_txt.set("Stop")
            self.start_stop_button.configure(
                fg_color=WARNING_COLOR, hover_color=WARNING_COLOR_DARK)
            self.parse_hot_keys()
            # self.generate_annotations_counter_labels()
            self.screen_capture.set_pid_path(self.get_pid())
            print(self.get_pid())
            self.screen_capture.start_recording()

        self.pb_frame.destroy()
        self.create_progress_bar(self.first_row)
        self.pb.set(0)
        self.pb.start()
        self.set_accuracy_visibility()
        self.is_started = True

        self.no_of_screenshots_whole = 0
        self.no_of_screenshots_roi = 0
        self.no_of_marks = 0
        # self.annotations_txt.set("Screenshots: {}\nMarks: {}".format(
        #     self.no_of_screenshots, self.no_of_marks))
        # self.endTime.set('Stop: N.A.')
        # self.durationText.set('Click Stop to end this trial')
        # self.startTime.set('Start: ' + self.get_now_time_string(mode='start'))
        self.get_now_time_string(mode="start")
        log_utilities.log_manipulation_info(
            self.get_pid(), "00:00:00", "Start", "Start", manipulation_note=datetime.utcnow())

    def on_stop(self):
        if not self.is_started:
            return
        self.is_started = False

        self.get_now_time_string(mode="stop")
        self.timeDelta = self.end - self.begin

        if self.screen_capture is not None:
            self.screen_capture.stop_recording()
            analyzer_process = Process(
                target=setup_new_analyzer, args=(self.get_pid(),))
            analyzer_process.start()
        log_utilities.log_manipulation_info(self.get_pid(), str(
            self.timeDelta).split('.')[0], "Stop", "Stop")
        self.workflow.reset()

    # Accuracy Component
    def set_accuracy_visibility(self):
        self.reset_accuracy()

    def update_accuracy(self, is_correct_trial):
        if self.is_started:
            self.trial_record['total_trial'] += 1
            if is_correct_trial:
                self.trial_record['correct_trial'] += 1
            self.current_accuracy = (
                self.trial_record['correct_trial'] / self.trial_record['total_trial']) * 100
            incorrect_trial = self.trial_record['total_trial'] - \
                self.trial_record['correct_trial']

            # self.correct_txt_var.set("Correct: {}".format(
            #     self.trial_record['correct_trial']))
            # self.incorrect_txt_var.set("Incorrect: {}".format(incorrect_trial))
            # self.accuracyText.set(
            #     "Accuracy: {:.2f}%".format(self.current_accuracy))

            correct_annotation_type = self.annotation_df[self.annotation_df['func']
                                                         == FUNC_LIST['correct']]['type'].item()
            self.annotations_counter_details[correct_annotation_type]['value'] = self.trial_record['correct_trial']
            incorrect_annotation_type = self.annotation_df[self.annotation_df['func']
                                                           == FUNC_LIST['incorrect']]['type'].item()
            self.annotations_counter_details[incorrect_annotation_type]['value'] = incorrect_trial
            self.annotations_counter_details['accuracy']['value'] = "{:.2f}%".format(
                self.current_accuracy)
            self.annotations_counter_details[correct_annotation_type]['label'].configure(
                text=self.get_annotation_display_label(correct_annotation_type))
            self.annotations_counter_details[incorrect_annotation_type]['label'].configure(
                text=self.get_annotation_display_label(incorrect_annotation_type))
            self.annotations_counter_details['accuracy']['label'].configure(
                text=self.get_annotation_display_label('accuracy'))

    def reset_accuracy(self):
        # self.accuracyText.set("Correct: {}\nIncorrect: {}".format(self.CORRECT_ACTION_KEY, self.INCORRECT_ACTION_KEY))
        self.accuracyText.set("Accuracy= NIL")
        self.trial_record['total_trial'] = 0
        self.trial_record['correct_trial'] = 0

    def start_customization_panel(self):
        self.customization_panel = CustomizationPanel(self.top_level_root, workflow=self.workflow,
                                                      is_minimized_window=True, on_click_pin_callback=self.update_annotation_counter_details)

    def show_image_captured_preview(self, time_stamp):
        image_path = os.path.join("data", self.pid, time_stamp + ".png")
        try:
            self.photo_gallery.insert_photo(time_stamp, image_path, )
        except:
            print("[ERROR] " + image_path + " does not exists")

    def on_photo_click(self, timestamp):
        if self.image_note_window_status:
            return
        image_path = os.path.join("data", self.pid, timestamp + ".png")
        img = Image.open(image_path)
        img = img.resize((400, int(400 * img.height / img.width)))
        imgtk = ImageTk.PhotoImage(image=img)
        self.image_note_window_status = True
        ImageNoteWindow(parent=self, pid=self.pid,
                        timestamp=timestamp, image=imgtk)

    def on_close_image_note_window(self):
        self.workflow.lower()
        self.image_note_window_status = False

    def generate_annotations_counter_labels(self):
        if self.annotations_counter_frame != None:
            for widget in self.annotations_counter_frame.winfo_children():
                widget.destroy()

        self.annotations_counter_frame = get_bordered_frame(
            self.workflow.top_left_frame)

        column_no = 0
        row_no = 0
        no_of_columns_per_row = 2

        for key in self.annotations_counter_details:
            label_text = self.get_annotation_display_label(key)
            label = get_label(self.annotations_counter_frame, None, label_text)
            label.configure(wraplength=180, justify='left')

            label.configure(fg=UI.color.color_translation(
                self.annotations_counter_details[key]['color']), anchor='w')
            self.annotations_counter_details[key]['label'] = label
            if not self.annotations_counter_details[key]['is_show']:
                continue
            label.grid(column=column_no, row=row_no,
                       pady=5, padx=5, sticky="nsew")
            column_no += 1
            if column_no == no_of_columns_per_row:
                column_no = 0
                row_no += 1

        self.annotations_counter_frame.grid(
            column=0, row=0, columnspan=2, sticky='NSEW', ipady=5, ipadx=5)

    def pack_layout(self):
        self.first_row = Frame(self.root)
        # progressbar
        self.create_progress_bar(self.first_row)

        for widget in self.workflow.top_right_frame.winfo_children():
            widget.destroy()

        # self.workflow.top_left_frame.configure(highlightthickness=1)
        self.workflow.big_container_frame.configure(highlightthickness=1)
        self.workflow.right_side_frame.configure(highlightthickness=1)

        self.start_stop_btn_txt = StringVar()
        self.start_stop_btn_txt.set("Stop")
        self.start_stop_button = get_circular_button(self.workflow.top_right_frame, text="Stop",
                                                     command=self.start_stop)
        self.start_stop_button.configure(fg_color=WARNING_COLOR)

        self.start_stop_button.grid(
            column=1, row=0, columnspan=1, rowspan=2, padx=10, pady=20, sticky="e")

        self.pid_frame = Frame(self.workflow.top_right_frame)
        self.pid_frame.grid(column=0, row=0, columnspan=2,
                            rowspan=1, padx=10, pady=20, sticky="w")
        # self.pid_label = get_label(self.workflow.top_right_frame, text="Participant & Session ID: {}".format(self.pid))
        self.pid_label = get_label(
            self.pid_frame, text="Participant & Session ID: ")
        # self.pid_label.pack(side="left")
        self.pid_label.grid(column=0, row=0, columnspan=1,
                            rowspan=1, sticky="w")
        self.pid_val_label = get_label(self.pid_frame, text=self.pid)
        self.pid_val_label.configure(fg=MAIN_COLOR_LIGHT)
        self.pid_val_label.grid(
            column=1, row=0, columnspan=1, rowspan=1, sticky="w")
        # self.pid_val_label.pack(side="left", padx=0, expand=True)
        # self.pid_label.grid(column=0, row=0, columnspan=1, rowspan=1, padx=50, pady=20, sticky="w")

        self.duration_frame = Frame(self.workflow.top_right_frame)
        self.duration_frame.grid(
            column=0, row=1, columnspan=2, rowspan=1, padx=10, pady=20, sticky="w")
        self.duration_label = get_label(
            self.duration_frame, text="Duration (min): ")
        self.duration_label.grid(
            column=0, row=0, columnspan=1, rowspan=1, sticky="w")
        # self.duration_label.pack(side="left")
        #  self.duration_label.grid(column=0, row=1, columnspan=1, rowspan=1, padx=50, pady=20, sticky="w")
        self.duration_val_label = get_label(
            self.duration_frame, text=int(self.anticipated_duration // 60))
        self.duration_val_label.configure(fg=MAIN_COLOR_LIGHT)
        self.duration_val_label.grid(
            column=1, row=0, columnspan=1, rowspan=1, sticky="w")
        # self.duration_val_label.pack(side="left", padx=(50, 0))

        self.now_time_label = get_label(
            self.first_row, textvariable=self.nowTime, pattern=1)
        self.now_time_label.after(1000, self.update_time)
        self.now_time_label.configure(fg=MAIN_COLOR_LIGHT)
        self.now_time_label.pack(side="left", padx=5)
        # self.now_time_label.grid(column=2, row=1, columnspan=1, sticky='EW')

        self.customization_button = get_button(self.first_row, text="Customization",
                                               command=self.start_customization_panel)
        self.customization_button.pack(side="right", padx=10, pady=5)

        self.image_frame = get_bordered_frame(self.workflow.right_side_frame)

        self.first_row.pack(side="top", fill=X)

        self.generate_annotations_counter_labels()

        self.photo_gallery = PhotoGallery(parent=self.workflow.right_side_frame,
                                          on_click_photo_func=self.on_photo_click,
                                          is_run_alone=False, orient="vertical",
                                          img_width=150, img_height=75, width=180)
        self.workflow.right_side_frame.pack_propagate(0)
        self.root.update()
