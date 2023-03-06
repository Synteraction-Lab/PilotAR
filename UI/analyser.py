import csv
import datetime
import os
# from re import T
import sys

sys.path.append("./")
import tkinter as tk
from tkinter import StringVar, filedialog
import pandas as pd
# import PIL
import glob
import ttkbootstrap as ttk
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, TableStyle, LongTable
from reportlab.lib.enums import TA_CENTER
import shutil

import UI.color
from UI.custom_table import CustomTable
from Utilities.annotation_utilities import get_customized_annotation_df, FUNC_START, FUNC_STOP, FUNC_LIST
from UI.marker import Marker
from UI.video_player import Player
from UI.photo_gallery import PhotoGallery
from UI.widget_generator import get_button, get_checkbutton, get_dropdown_menu, get_messagebox, get_label, \
    get_bordered_frame, get_bordered_label_frame, get_slider, get_text
from UI.task import Task
from UI.UI_config import ANALYZER_TIMELINE_THICKNESS, MAIN_COLOR_LIGHT, BACK_AND_PLUS_SECONDS, ANALYZER_MARKER_THICKNESS
from Utilities.common_utilities import str_to_sec, sec_to_str, str_to_mins
from Utilities.ExceptionThread import ExceptionThread
from Utilities.screen_capture import get_second_monitor_original_pos
# from Utilities.transcribe_vosk import transcribe
from Utilities.transcribe_whisper import transcribe

# TYPE_SCREENSHOT = "screenshot"
# TYPE_MARK = "mark"
# TYPE_CORRECT = "Correct"
# TYPE_INCORRECT = "incorrect"
# TYPE_START = "start"
# TYPE_STOP = "stop"
TYPE_NULL = "null"

_isMacOS = sys.platform.startswith('darwin')
_isWindows = sys.platform.startswith('win')
_isLinux = sys.platform.startswith('linux')


def all_children(widget):
    _list = widget.winfo_children()
    for item in _list:
        if item.winfo_children():
            _list.extend(item.winfo_children())
    return _list


class Analyser:
    def __init__(self, frame=None, is_run_alone=True, pid=""):
        # have to use Toplevel if there are multiple tk windows instead of tk.Tk()
        self.customization_df = None
        self.video_duration = 0
        self.is_annotation_loaded = False
        self.annotation_types = {}
        if is_run_alone:
            self.root = tk.Tk()
            self.root.geometry(
                '+{}+{}'.format(get_second_monitor_original_pos()[0], get_second_monitor_original_pos()[1]))
            self.root.title('Analyzer')
        else:
            self.root = frame
            for widget in self.root.winfo_children():
                widget.destroy()

        style = ttk.Style("darkly")
        self.is_indicated_pid = True
        self.is_run_transcribe = True
        if pid == "":
            print("empty folder path")
            self.is_indicated_pid = False
            self.is_run_transcribe = False
            pid = "p1_1"

        self.pid = pid
        self.folder_path = os.path.join("data", self.pid)
        # self.is_audio_existed = is_audio_existed
        self.accuracy = 0.0
        self.total_trial = 0
        self.correct_trial = 0
        self.types = None
        self.editing_record = -1
        self.tasks = None

        self.duration_in_mins = 0

        self.is_initial_load_of_pid = True
        self.get_possible_pids()
        self.is_note_window_open = False

    def note_window_open_callback(self):
        self.is_note_window_open = True
        self.pid_dd.configure(state="disabled")

    def note_window_close_callback(self):
        self.is_note_window_open = False
        if self.is_run_transcribe:
            self.run_transcribe_callback()
        self.pid_dd.configure(state="normal")

    def run_transcribe_callback(self):
        if self.is_note_window_open:
            return
        self.sort_tasks_file()
        self.generate_annotations()
        self.transcribe_in_progress_label.pack_forget()
        self.is_run_transcribe = False

    def run_transcribe(self):
        t1 = ExceptionThread(target=transcribe, args=[self.pid, self.run_transcribe_callback, self.annotation_types])
        t1.start()

    def set_folder_path(self):
        # set path & load video
        # self.pid = self.pid_txt.get()
        if self.is_initial_load_of_pid:
            self.is_initial_load_of_pid = False
        else:
            self.save()
        self.pid = self.pid_dd.get()
        self.folder_path = os.path.join("data", self.pid)
        # duplicate global customization csv file to the session's if session does not have its own customization file
        session_customization_file = os.path.join(self.folder_path, "customization.csv")
        if not os.path.isfile(session_customization_file):
            global_customization_file = os.path.join("data", "customization.csv")
            shutil.copyfile(global_customization_file, session_customization_file)
        self.parse_annotations()
        self.load_video()
        self.play_pause()

    def get_creation_date(self, path):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        """
        if _isWindows:
            return os.path.getctime(path)
        else:
            stat = os.stat(path)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def get_possible_pids(self):
        dir_name = "./data/"
        # Get list of all dirs only in the given directory
        list_of_files = filter(os.path.isdir, glob.glob(dir_name + '*'))
        list_of_files = sorted(list_of_files, key=lambda path: self.get_creation_date(path), reverse=True)
        self.pids = []
        is_first_pid = True
        for folder_path in list_of_files:
            # timestamp_str = time.ctime(os.path.getctime(folder_path))
            pid = os.path.basename(folder_path)
            self.pids.append(pid)
            if is_first_pid and not self.is_indicated_pid:
                self.pid = pid
                self.folder_path = os.path.join("data", self.pid)
                is_first_pid = False

    def sort_tasks_file(self):
        file_path = os.path.join(self.folder_path, 'task_info.csv')
        df = pd.read_csv(file_path)
        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
        df = df.sort_values(by='time')
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)

    def update_duration(self, event):
        """ updates the duration after finding the duration """
        duration = self.vid_player.video_info()["duration"]
        # self.end_time["text"] = str(datetime.timedelta(seconds=duration))
        self.end_time["text"] = sec_to_str(duration)
        self.duration_in_mins = str_to_mins(self.end_time["text"])
        self.progress_slider.configure(to=duration, from_=0)
        # self.progress_slider["to"] = duration
        if not self.is_annotation_loaded:
            self.sort_tasks_file()
            self.generate_annotations()
            # self.generate_voice_annotations()
            self.is_annotation_loaded = True

    def update_scale(self, event):
        """ updates the scale value """
        self.progress_value.set(self.vid_player.current_duration())
        self.current_time_txt_var.set(sec_to_str(self.vid_player.current_duration()))

    def load_video(self):
        """ loads the video """
        file_path = os.path.join(self.folder_path, 'output.mp4')
        if not os.path.exists(file_path):
            get_messagebox(self.root, "Can't find the video.")
        try:
            self.vid_player.load(file_path)
            # self.progress_slider.configure(to=self.vid_player.video_info()["duration"], from_=0)
            self.play_pause_btn.configure(text="Play")
            self.progress_value.set(0)
            self.is_annotation_loaded = False
            self.update_video_duration()
        except:
            get_messagebox(self.root, "Can't load the video.")

    def seek(self, value):
        """ used to seek a specific timeframe """
        if self.video_duration == 0:
            self.get_video_duration()
        if value >= self.video_duration:
            value = self.video_duration - 0.1
        self.vid_player.seek(float(value))

    def on_press_key(self, event):
        if event.keysym == "Right":
            self.skip_plus_x_seconds(BACK_AND_PLUS_SECONDS)
        elif event.keysym == "Left":
            self.skip_minus_x_seconds(BACK_AND_PLUS_SECONDS)

    def skip_plus_x_seconds(self, x, event=None):
        self.skip_seconds(x)

    def skip_minus_x_seconds(self, x, event=None):
        self.skip_seconds(-x)

    def skip_seconds(self, value: int):
        # get current duration
        current_duration = self.vid_player.current_duration()
        end_duration = self.vid_player.video_info()["duration"]
        if value > 0 and current_duration + value >= end_duration:
            self.vid_player.seek(int(end_duration))
            self.progress_value.set(int(end_duration))
        elif value < 0 and current_duration + value < 0:
            self.vid_player.seek(0)
            self.progress_value.set(0)
        else:
            self.vid_player.seek(int(self.progress_slider.get()) + value)
            self.progress_value.set(int(self.progress_slider.get() + value))

    def skip_to(self, time="", index=-1, timestamp=""):
        if index != -1:
            timestamp = str_to_sec(self.annotations[index].get_timestamp())
        elif time != "":
            timestamp = str_to_sec(time)
        if self.vid_player.is_paused():
            self.play_pause()
            self.seek(timestamp)
            self.play_pause()
        else:
            self.seek(timestamp)
        self.progress_value.set(timestamp)

    def play_pause(self):
        """ pauses and plays """
        if self.vid_player.is_paused():
            self.vid_player.play()
            self.play_pause_btn.configure(text="Pause")

        else:
            self.vid_player.pause()
            self.play_pause_btn.configure(text="Play")

    def video_ended(self, event):
        """ handle video ended """
        # self.progress_slider.set(self.progress_slider["to"])
        self.play_pause_btn.configure(text="Play")
        # self.progress_slider.set(0)
        self.progress_value.set(0)

    def generate_annotation_type_filter(self):
        widget_list = all_children(self.annotations_type_frame)
        for item in widget_list:
            item.pack_forget()
        for t in self.types:
            # type_cb = Checkbutton(self.annotations_type_frame, text=t + " (" + str(
            #         self.types[t][0]) + ")", command=lambda at=t: self.toggle_rows_visibility(at))
            type_cb = get_checkbutton(self.annotations_type_frame, text=t + " (" + str(self.types[t][0]) + ")",
                                      command=lambda at=t: self.toggle_rows_visibility(at))
            if self.annotation_types.get(t) != None:
                # type_cb.configure(fg=UI.color.color_translation(self.annotation_types[t]['color']))  
                type_cb.configure(text_color=UI.color.color_translation(self.annotation_types[t]['color']))
            else:
                type_cb.configure(text_color="white")
            if self.types[t][1]:
                type_cb.select()
            type_cb.pack(side="left", padx=10, pady=5)

    def toggle_rows_visibility(self, type):
        if self.types[type][1]:
            for i in self.types[type][2]:
                self.tasks_table.hide_row(i)
            for marker in self.types[type][3]:
                marker.place_forget()
            self.types[type][1] = False
            return
        for i in self.types[type][2]:
            self.tasks_table.show_row(i)
        for marker in self.types[type][3]:
            marker.place()
        self.types[type][1] = True

    def on_clicked_row(self, row_obj):
        self.skip_to(time=row_obj.get_timestamp())

    def get_rows_diff(self, r1_obj, r2_obj):
        duration = str_to_sec(r2_obj.get_timestamp()) - str_to_sec(r1_obj.get_timestamp())
        duration = abs(duration)
        self.row_diff_label_txt.set("Duration Diff: {} s".format(duration))

    def save(self):
        if self.tasks == None or len(self.tasks) == 0:
            return
        df = pd.DataFrame.from_records([t.to_dict() for t in self.tasks])
        file_path = os.path.join(self.folder_path, 'task_info.csv')
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)

    def export(self):
        tasks = self.tasks_table.get_all_row_objects()
        if tasks == None or len(tasks) == 0:
            get_messagebox(self.root, "No data to export")
            return
        selected_tasks = []
        for t in tasks:
            if t.get_is_selected():
                selected_tasks.append(t)
        if len(selected_tasks) == 0:
            get_messagebox(self.root, "No data to export")
            return
        folder_path = filedialog.askdirectory()
        if folder_path == "":  # user cancelled the choosing of directory
            return
        self.export_summary(folder_path=folder_path, selected_tasks=selected_tasks)
        self.export_data(folder_path=folder_path, selected_tasks=selected_tasks)
        self.save()
        get_messagebox(self.root, "Exported summary & data")

    def export_data(self, folder_path, selected_tasks):
        file_path = os.path.join(folder_path, "data_{}.csv".format(self.pid))
        df = pd.DataFrame.from_records([t.to_dict() for t in selected_tasks])
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)

    def export_summary(self, folder_path, selected_tasks):
        def set_normal_style():
            style = styles['Normal']
            style.wordWrap = 'CJK'
            style.alignment = TA_CENTER
            return style

        file_path = os.path.join(folder_path, "summary_{}.pdf".format(self.pid))
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        spacer = Spacer(1, 0.11 * inch)

        styleHeader = set_normal_style()
        styleHeader.textColor = 'white'

        h1 = Paragraph('Timestamp', styleHeader)
        h2 = Paragraph('Type', styleHeader)
        h3 = Paragraph('Notes', styleHeader)
        h4 = Paragraph('Image', styleHeader)
        data = [[h1, h2, h3, h4]]  # header

        tableStyle = [
            ('BACKGROUND', (0, 0), (-1, 0), "#222222"),
            ('INNERGRID', (0, 0), (-1, -1), 1, MAIN_COLOR_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, MAIN_COLOR_LIGHT),
        ]

        styleNormal = set_normal_style()

        selected_tasks_types = {}
        selected_tasks_total_trial = 0
        selected_tasks_correct_trial = 0
        for t in selected_tasks:
            styleNormal.textColor = 'black'
            c1 = Paragraph(t.get_timestamp(), styleNormal)
            c3 = Paragraph(t.get_notes(), styleNormal)

            styleNotes = set_normal_style()
            c4 = Paragraph("", styleNotes)
            if t.get_func() == FUNC_LIST['screenshot_roi'] or t.get_func() == FUNC_LIST['screenshot_whole'] \
                    or t.get_func() == FUNC_LIST['mark']:
                c4 = Image(filename=os.path.join(self.folder_path, t.get_image_name() + ".png"), width=160, height=160,
                           kind="proportional")
            elif t.get_func() == FUNC_LIST['correct']:
                selected_tasks_total_trial += 1
                selected_tasks_correct_trial += 1
            elif t.get_func() == FUNC_LIST['incorrect']:
                selected_tasks_total_trial += 1

            c2 = Paragraph(t.get_display_type(), styleNormal)
            if t.get_display_type() in self.annotation_types:
                styleType = set_normal_style()
                styleType.textColor = UI.color.color_translation(self.annotation_types[t.get_display_type()]['color'])
                c2 = Paragraph(t.get_display_type(), styleType)

            selected_tasks_types[t.get_display_type()] = selected_tasks_types.get(t.get_display_type(), 0) + 1
            d = [c1, c2, c3, c4]
            data.append(d)

        selected_tasks_accuracy = 0
        if selected_tasks_total_trial > 0 and selected_tasks_correct_trial > 0:
            selected_tasks_accuracy = (selected_tasks_correct_trial / selected_tasks_total_trial) * 100

        # colWidths = ['*'] # to stretch the entire allowable horizontal space
        colWidths = (1 * inch, 1 * inch, 2.4 * inch, 2.4 * inch)
        table = LongTable(data, colWidths=colWidths)
        table.setStyle(TableStyle(tableStyle))

        styleHeader = styles['BodyText']
        styleHeader.borderColor = MAIN_COLOR_LIGHT
        styleHeader.borderPadding = 0.1 * inch
        styleHeader.borderWidth = 1
        styleHeader.leftIndent = -(0.25 * inch)
        styleHeader.rightIndent = -(0.25 * inch)
        session_details_header_text = ""
        if selected_tasks_total_trial == 0:
            session_details_header_text = "Participant & Session ID: {},<br />Duration (min): {},<br />Accuracy: N.A.".format(
                self.pid, self.duration_in_mins)
        else:
            session_details_header_text = "Participant & Session ID: {},<br />Duration (min): {},<br />Accuracy: {:.2f}%".format(
                self.pid, self.duration_in_mins, selected_tasks_accuracy)
        session_details_header_text = Paragraph(session_details_header_text, styleHeader)
        elements.append(session_details_header_text)
        elements.append(spacer)

        styleBodyText = styles['BodyText']
        styleBodyText.borderColor = MAIN_COLOR_LIGHT
        styleBodyText.borderPadding = 0.1 * inch
        styleBodyText.borderWidth = 1
        styleBodyText.leftIndent = -(0.25 * inch)
        styleBodyText.rightIndent = -(0.25 * inch)
        annotation_types_text = ""
        for t in self.types:
            color = "black"
            if t in self.annotation_types:
                color = UI.color.color_translation(self.annotation_types[t]['color'])
            text = "<font color={}>{} ({})</font> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".format(color, t,
                                                                                         selected_tasks_types.get(t, 0))
            annotation_types_text += text
        annotation_types_paragraph = Paragraph(annotation_types_text, styleBodyText)
        elements.append(annotation_types_paragraph)
        elements.append(spacer)

        elements.append(table)
        doc.build(elements)

    def add_new_marker(self):
        time_stamp = sec_to_str(self.progress_value.get())
        notes = self.mark_notes_txt.get("1.0", "end-1c")
        screenshot_type_name = self.customization_df[self.customization_df['func'] == 'Whole Screenshot']['type'].item()
        screenshot_color = self.customization_df[self.customization_df['func'] == 'Whole Screenshot']['color'].item()
        new_task = Task(len(self.tasks) + 1, time_stamp, screenshot_type_name, FUNC_LIST['screenshot_whole'],
                        screenshot_color, 'N.A.', notes)
        self.tasks.append(new_task)
        self.vid_player.screenshot_current_frame(os.path.join(self.folder_path, new_task.get_image_name() + ".png"))

        file_path = os.path.join(self.folder_path, 'task_info.csv')
        df = pd.DataFrame.from_records([t.to_dict() for t in self.tasks])
        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
        df = df.sort_values(by='time')
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_MINIMAL)
        self.mark_notes_txt.delete("1.0", "end-1c")
        self.generate_annotations()

    def _AnchorButtonsPanel(self):
        video_height = self.root.winfo_height()
        video_width = self.root.winfo_width()
        bottom_panel_x = self.root.winfo_x()
        bottom_panel_y = self.root.winfo_y() + video_height + 23
        side_panel_x = self.root.winfo_x() + video_width
        side_panel_y = self.root.winfo_y()
        bottom_panel_height = self.bottom_panel.winfo_height()
        bottom_panel_width = self.root.winfo_width()
        # side_panel_height = max(self.side_panel.winfo_height(),
        #                         self.root.winfo_height() + self.bottom_panel.winfo_height() + 23)
        # side_panel_width = self.side_panel.winfo_width()
        self.bottom_panel.geometry(
            "%sx%s+%s+%s" % (bottom_panel_width, bottom_panel_height, bottom_panel_x, bottom_panel_y))
        self.side_panel.geometry("+%s+%s" % (side_panel_x, side_panel_y))

    def on_configure(self, event):
        self._AnchorButtonsPanel()

    def pack_layout(self):
        if _isMacOS:
            self.pack_layout_mac()
        else:
            self.pack_layout_win_linux()

    def pack_layout_win_linux(self):
        self.vid_player_frame = ttk.Frame(self.root)

        _video = os.path.join('data', 'p1_1')
        self.vid_player = Player(self.vid_player_frame, video=_video)

        self.vid_player.pack()

        self.vid_controls_row = ttk.Frame(self.vid_player_frame)
        self.back_btn = get_button(self.vid_controls_row, text="-{}s".format(BACK_AND_PLUS_SECONDS),
                                   command=lambda: self.skip_minus_x_seconds(BACK_AND_PLUS_SECONDS), pattern=0)
        self.back_btn.pack(side="left", padx=5)
        self.play_pause_btn = get_button(self.vid_controls_row, text="Play", command=self.play_pause, pattern=0)
        self.play_pause_btn.pack(side="left", padx=5)
        self.plus_btn = get_button(self.vid_controls_row, text="+{}s".format(BACK_AND_PLUS_SECONDS),
                                   command=lambda: self.skip_plus_x_seconds(BACK_AND_PLUS_SECONDS), pattern=0)
        self.plus_btn.pack(side="left", padx=5)

        self.vid_timeline_row = ttk.Frame(self.vid_player_frame)
        self.current_time_txt_var = StringVar()
        self.current_time_txt_var.set(str(datetime.timedelta(seconds=0)))
        self.current_time = get_label(self.vid_timeline_row, textvariable=self.current_time_txt_var)
        self.current_time.pack(side="left")

        self.progress_value = tk.IntVar(self.vid_timeline_row)

        self.progress_slider = get_slider(self.vid_timeline_row, variable=self.progress_value, orient="horizontal",
                                          command=self.seek)
        self.progress_slider.pack(side="left", fill="x", expand=True)

        self.end_time = get_label(self.vid_timeline_row, text=str(datetime.timedelta(seconds=0)))
        self.end_time.pack(side="right")

        # self.mark_notes_row = get_bordered_label_frame(self.vid_player_frame, text="Note:")
        # self.mark_notes_txt = get_text(self.mark_notes_row)
        # self.mark_notes_txt.configure(borderwidth=0, highlightthickness=0, height=10)
        # self.mark_notes_txt.pack(pady=5, padx=5, fill="x")

        # self.add_annotation_btn_row = ttk.Frame(self.mark_notes_row)
        # self.add_annotation_btn = get_button(self.add_annotation_btn_row, text="Mark", command=self.add_new_marker,
        #                                      pattern=0)
        # self.add_annotation_btn.pack()
        self.mark_notes_row = get_bordered_label_frame(self.vid_player_frame, text="New Note:")
        self.mark_notes_txt_frame = tk.Frame(self.mark_notes_row)
        self.mark_notes_txt_frame.configure(height=80)
        self.mark_notes_txt_frame.pack(side="top", pady=5, padx=5, fill="x")
        self.mark_notes_txt_frame.pack_propagate(0)
        self.mark_notes_txt = get_text(self.mark_notes_txt_frame)
        self.mark_notes_txt.configure(borderwidth=0, highlightthickness=0)
        self.mark_notes_txt.pack(side="top", fill="x")

        self.add_annotation_btn_row = tk.Frame(self.mark_notes_row)
        self.add_annotation_btn = get_button(self.add_annotation_btn_row, text="Add Note", command=self.add_new_marker,
                                             pattern=0)
        self.add_annotation_btn.pack()
        self.add_annotation_btn_row.pack(side="bottom", pady=5)

        self.vid_controls_row.pack(side="top")
        self.vid_timeline_row.pack(side="top", fill="x")
        # self.add_annotation_btn_row.pack(side="top", pady=5)
        self.mark_notes_row.pack(side="top", fill="x")

        self.vid_player.bind("<<Duration>>", self.update_duration)
        self.vid_player.bind("<<SecondChanged>>", self.update_scale)
        self.vid_player.bind("<<Ended>>", self.video_ended)

        self.summary_view_frame = ttk.Frame(self.root)

        self.pid_frame = tk.Frame(self.summary_view_frame)
        self.pid_label = get_label(self.pid_frame, text="Participant & Session ID:")
        self.pid_label.pack(side="left")
        self.pid_dd_var = tk.StringVar()
        self.pid_dd_var.set(self.pid)
        self.pid_dd = get_dropdown_menu(self.pid_frame, values=self.pids, variable=self.pid_dd_var,
                                        command=lambda event: self.set_folder_path())
        self.pid_dd.pack(side="left")
        self.pid_frame.pack(side="top", anchor='w', padx=20, pady=5)

        self.info_frame = get_bordered_frame(self.summary_view_frame)
        self.info_frame.pack(side="top", pady=5, padx=25, fill="x")

        self.summary_text = StringVar()
        self.summary_text.set("")
        self.summary_label = get_label(self.info_frame, textvariable=self.summary_text, pattern=1)
        self.summary_label.pack(side="top", anchor='w', pady=5, padx=6)

        self.photo_gallery_frame = tk.Frame(self.info_frame, borderwidth=0, highlightthickness=0)
        self.photo_gallery = PhotoGallery(parent=self.photo_gallery_frame, on_click_photo_func=self.on_photo_click,
                                          is_run_alone=False)
        self.photo_gallery_frame.pack(side="top", anchor='w', expand=True, fill="x")
        self.photo_gallery_frame.pack_propagate(0)

        self.transcribe_in_progress_label = get_label(self.summary_view_frame, text="Transcribing voice in progress...",
                                                      pattern=1)
        self.transcribe_in_progress_label.pack(side="top", padx=25, pady=5, anchor='w')

        self.annotations_type_parent_frame = get_bordered_label_frame(self.summary_view_frame, text="Annotation Type")
        self.annotations_type_parent_frame.pack(side="top", pady=10, padx=25, fill="x")
        self.create_scrolling_for_annotations_type(self.annotations_type_parent_frame)

        self.tasks_table_frame = ttk.Frame(self.summary_view_frame)
        self.tasks_table_frame.configure(width=700, height=300)
        self.tasks_table_frame.pack(padx=20, fill="both", expand=True)
        self.tasks_table_frame.pack_propagate(0)

        self.row_diff_label_txt = StringVar()
        self.row_diff_label_txt.set("Row Diff: (Press and hold {} and click two rows.)".format("Cmd" if _isMacOS
                                                                                               else "Ctrl"))
        self.row_diff_label = get_label(self.tasks_table_frame, textvariable=self.row_diff_label_txt, pattern=1)
        self.row_diff_label.pack()

        self.tasks_table = CustomTable(self.tasks_table_frame, on_clicked_row_func=self.on_clicked_row,
                                       on_clicked_multi_row_func=self.get_rows_diff, row_height=50, header_height=25,
                                       header_text_color="white",
                                       on_open_note_window_func=self.note_window_open_callback,
                                       on_note_window_close_func=self.note_window_close_callback,
                                       delete_func=self.on_delete_annotation,
                                       on_edit_timestamp_func=self.on_edit_annotation_timestamp,
                                       on_edit_type_func=self.on_edit_annotation_type)
        self.tasks_table.define_column_ids(["bump", "select", "time", "type", "note", "delete"])
        self.tasks_table.column("bump", header_text="", width=40, type="bump")
        self.tasks_table.column("select", header_text="Select", width=80, type="cb")
        self.tasks_table.column("time", header_text="Time", width=80)
        self.tasks_table.column("type", header_text="Type", width=120)
        self.tasks_table.column("note", header_text="Note", width=320)
        self.tasks_table.column("delete", header_text="", width=40, type="delete")

        self.export_frame = ttk.Frame(self.summary_view_frame)
        self.export_frame.pack(side="top", pady=10)
        self.export_btn = get_button(self.export_frame, text="Export Summary & Data", command=self.export, pattern=0)
        self.export_btn.pack()

        self.vid_player_frame.pack(fill="both", side="left", expand=True)
        self.summary_view_frame.pack(fill="both", side="right")

        self.root.protocol("WM_DELETE_WINDOW", self.vid_player.OnClose)

    def pack_layout_mac(self):
        _video = os.path.join('data', 'p1_1')
        self.vid_player = Player(self.root, video=_video)

        self.vid_player.pack(expand=True, fill="both")
        self.vid_player.config(bg="black")

        self.side_panel = ttk.Toplevel(self.root)
        self.side_panel.title("")
        self.side_panel.overrideredirect(True)

        self.bottom_panel = ttk.Toplevel(self.root)
        self.bottom_panel.title("")
        self.bottom_panel.config(height=200)
        self.bottom_panel.overrideredirect(True)

        self.bottom_panel_frame = ttk.Frame(self.bottom_panel)

        self.vid_controls_row = ttk.Frame(self.bottom_panel_frame)
        self.back_btn = get_button(self.vid_controls_row, text="-{}s".format(BACK_AND_PLUS_SECONDS),
                                   command=lambda: self.skip_minus_x_seconds(BACK_AND_PLUS_SECONDS), pattern=0)
        # self.back_btn.bind('<Key-Left>', lambda e: self.skip_minus_x_seconds(BACK_AND_PLUS_SECONDS))
        # self.back_btn.focus_set()
        self.back_btn.pack(side="left", padx=5)
        self.play_pause_btn = get_button(self.vid_controls_row, text="Play", command=self.play_pause, pattern=0)
        self.play_pause_btn.pack(side="left", padx=5)
        self.plus_btn = get_button(self.vid_controls_row, text="+{}s".format(BACK_AND_PLUS_SECONDS),
                                   command=lambda: self.skip_plus_x_seconds(BACK_AND_PLUS_SECONDS), pattern=0)
        # self.plus_btn.bind('<Key-Right>', lambda e: self.skip_plus_x_seconds(BACK_AND_PLUS_SECONDS))
        # self.plus_btn.focus_set()
        self.plus_btn.pack(side="left", padx=5)

        self.vid_timeline_row = ttk.Frame(self.bottom_panel_frame)
        self.current_time_txt_var = StringVar()
        self.current_time_txt_var.set(str(datetime.timedelta(seconds=0)))
        self.current_time = get_label(self.vid_timeline_row, textvariable=self.current_time_txt_var)
        self.current_time.pack(side="left")

        self.progress_value = tk.DoubleVar(self.vid_timeline_row)
        self.progress_slider = get_slider(self.vid_timeline_row, variable=self.progress_value, orient="horizontal",
                                          command=self.seek)
        self.progress_slider.pack(side="left", fill="x", expand=True)

        self.end_time = get_label(self.vid_timeline_row, text=str(datetime.timedelta(seconds=0)))
        self.end_time.pack(side="right")

        self.mark_notes_row = get_bordered_label_frame(self.bottom_panel_frame, text="New Note:")
        self.mark_notes_txt_frame = tk.Frame(self.mark_notes_row)
        self.mark_notes_txt_frame.configure(height=80)
        self.mark_notes_txt_frame.pack(side="top", pady=5, padx=5, fill="x")
        self.mark_notes_txt_frame.pack_propagate(0)
        self.mark_notes_txt = get_text(self.mark_notes_txt_frame)
        self.mark_notes_txt.configure(borderwidth=0, highlightthickness=0)
        self.mark_notes_txt.pack(side="top", fill="x")

        self.add_annotation_btn_row = tk.Frame(self.mark_notes_row)
        self.add_annotation_btn = get_button(self.add_annotation_btn_row, text="Add Note", command=self.add_new_marker,
                                             pattern=0)
        self.add_annotation_btn.pack()
        self.add_annotation_btn_row.pack(side="bottom", pady=5)

        self.vid_controls_row.pack(side="top")
        self.vid_timeline_row.pack(side="top", fill="x")
        self.mark_notes_row.pack(side="top", fill="x")

        self.vid_player.bind("<<Duration>>", self.update_duration)
        self.vid_player.bind("<<SecondChanged>>", self.update_scale)
        self.vid_player.bind("<<Ended>>", self.video_ended)

        self.summary_view_frame = ttk.Frame(self.side_panel)

        self.pid_frame = tk.Frame(self.summary_view_frame)
        self.pid_label = get_label(self.pid_frame, text="Participant & Session ID:")
        self.pid_label.pack(side="left")
        self.pid_dd_var = tk.StringVar()
        self.pid_dd_var.set(self.pid)
        self.pid_dd = get_dropdown_menu(self.pid_frame, values=self.pids, variable=self.pid_dd_var,
                                        command=lambda event: self.set_folder_path())
        self.pid_dd.pack(side="left")
        self.pid_frame.pack(side="top", anchor='w', padx=20, pady=5)

        self.info_frame = get_bordered_frame(self.summary_view_frame)
        self.info_frame.pack(side="top", pady=5, padx=25, fill="x")

        self.summary_text = StringVar()
        self.summary_text.set("")
        self.summary_label = get_label(self.info_frame, textvariable=self.summary_text, pattern=1)
        self.summary_label.pack(side="top", anchor='w', pady=5, padx=6)

        self.photo_gallery_frame = tk.Frame(self.info_frame, borderwidth=0, highlightthickness=0)
        self.photo_gallery = PhotoGallery(parent=self.photo_gallery_frame, on_click_photo_func=self.on_photo_click,
                                          is_run_alone=False)
        self.photo_gallery_frame.pack(side="top", anchor='w', expand=True, fill="x")
        self.photo_gallery_frame.pack_propagate(0)

        self.transcribe_in_progress_label = get_label(self.summary_view_frame, text="Transcribing voice in progress...",
                                                      pattern=1)
        self.transcribe_in_progress_label.pack(side="top", padx=25, pady=5, anchor='w')

        self.annotations_type_parent_frame = get_bordered_label_frame(self.summary_view_frame, text="Annotation Type")
        self.annotations_type_parent_frame.pack(side="top", padx=25, pady=10, fill="x")
        self.create_scrolling_for_annotations_type(self.annotations_type_parent_frame)

        self.tasks_table_frame = ttk.Frame(self.summary_view_frame)
        self.tasks_table_frame.configure(width=700, height=300)
        self.tasks_table_frame.pack(padx=20)
        self.tasks_table_frame.pack_propagate(0)

        self.row_diff_label_txt = StringVar()
        self.row_diff_label_txt.set("Row Diff: (Press and hold {} and click two rows.)".format("Cmd" if _isMacOS
                                                                                               else "Ctrl"))
        self.row_diff_label = get_label(self.tasks_table_frame, textvariable=self.row_diff_label_txt, pattern=1)
        self.row_diff_label.pack()

        self.tasks_table = CustomTable(self.tasks_table_frame, on_clicked_row_func=self.on_clicked_row,
                                       on_clicked_multi_row_func=self.get_rows_diff, row_height=50, header_height=25,
                                       header_text_color="white",
                                       on_open_note_window_func=self.note_window_open_callback,
                                       on_note_window_close_func=self.note_window_close_callback,
                                       delete_func=self.on_delete_annotation,
                                       on_edit_timestamp_func=self.on_edit_annotation_timestamp,
                                       on_edit_type_func=self.on_edit_annotation_type)
        self.tasks_table.define_column_ids(["bump", "select", "time", "type", "note", "delete"])
        self.tasks_table.column("bump", header_text="", width=40, type="bump")
        self.tasks_table.column("select", header_text="Select", width=80, type="cb")
        self.tasks_table.column("time", header_text="Time", width=80)
        self.tasks_table.column("type", header_text="Type", width=120)
        self.tasks_table.column("note", header_text="Note", width=320)
        self.tasks_table.column("delete", header_text="", width=40, type="delete")

        self.export_frame = ttk.Frame(self.summary_view_frame)
        self.export_frame.pack(side="top", pady=10)
        self.export_btn = get_button(self.export_frame, text="Export Summary & Data", command=self.export, pattern=0)
        self.export_btn.pack()

        # self.vid_player_frame.pack(fill="both", side="left", expand=True)
        self.bottom_panel_frame.pack(fill="both")
        self.summary_view_frame.pack(fill="both")
        self.root.minsize(width=502, height=0)
        self.root.protocol("WM_DELETE_WINDOW", self.vid_player.OnClose)
        self.root.bind("<Configure>", self.on_configure)
        self._AnchorButtonsPanel()

    def on_photo_click(self, timestamp):
        self.skip_to(time=timestamp)

    def on_delete_annotation(self, task):
        self.photo_gallery.clear_photos()

        # remove annotation's marker (if any) and update self.types' count 
        if self.types is not None:
            if self.types[task.get_display_type()][1]:
                for i in range(len(self.types[task.get_display_type()][2])):
                    if self.types[task.get_display_type()][2][i] == task.get_id():
                        self.types[task.get_display_type()][3][i].place_forget()
            self.types[task.get_display_type()][0] -= 1
        self.generate_annotation_type_filter()

        # update task list and remove annotation's image (in both photo gallery and file [if any])
        updated_task_list = []
        for t in self.tasks:
            if t.get_id() == task.get_id():
                if t.get_func() == FUNC_LIST['screenshot_roi'] or t.get_func() == FUNC_LIST['screenshot_whole'] \
                        or t.get_func() == FUNC_LIST['mark']:
                    os.remove(os.path.join(self.folder_path, t.get_image_name() + ".png"))
                continue
            if t.get_func() == FUNC_LIST['screenshot_roi'] or t.get_func() == FUNC_LIST['screenshot_whole'] \
                    or t.get_func() == FUNC_LIST['mark']:
                self.photo_gallery.insert_photo(t.get_timestamp(),
                                                os.path.join(self.folder_path, t.get_image_name() + ".png"))
            updated_task_list.append(t)
        self.tasks = updated_task_list

        # Update accuracy (if the deleted annotation is incorrect/correct)
        if task.get_func() == FUNC_LIST['correct'] or task.get_func() == FUNC_LIST['incorrect']:
            self.total_trial -= 1
            if task.get_func() == FUNC_LIST['correct']:
                self.correct_trial -= 1

            if self.total_trial != 0:
                self.accuracy = (self.correct_trial / self.total_trial) * 100
                self.summary_text.set(
                    "Duration (min): {}             Accuracy: {:.2f}%".format(self.duration_in_mins, self.accuracy))
            else:
                self.summary_text.set("Duration (min): {}             Accuracy: N.A.".format(self.duration_in_mins))

        self.root.focus_set()

    def on_edit_annotation_timestamp(self):
        self.save()
        self.sort_tasks_file()
        self.generate_annotations()
        self.root.focus_set()

    def on_edit_annotation_type(self):
        self.save()
        self.sort_tasks_file()
        self.generate_annotations()
        self.root.focus_set()

    def create_scrolling_for_annotations_type(self, parent):
        self.at_sb = tk.Scrollbar(parent, orient="horizontal", highlightthickness=0, borderwidth=0)
        self.at_canvas = tk.Canvas(parent, highlightthickness=0, borderwidth=0, height=50,
                                   xscrollcommand=self.at_sb.set)
        self.at_canvas.pack(side="top", fill="x", padx=5)
        self.at_sb.pack(side="bottom", fill="x")
        self.at_sb.config(command=self.at_canvas.xview)

        self.annotations_type_frame = tk.Frame(self.at_canvas, highlightthickness=0, borderwidth=0)
        self.annotations_type_frame.bind("<Configure>", lambda event, c=self.at_canvas: self.on_frame_configure(c))
        self.at_canvas.create_window((4, 4), window=self.annotations_type_frame, anchor='nw')

    def on_frame_configure(self, canvas):
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        canvas.configure(scrollregion=canvas.bbox('all'))

    def generate_annotations(self):
        # Clear history records
        self.tasks_table.clear_table()
        self.tasks_table.set_pid(self.pid)
        self.tasks_table.set_customization_file_path(os.path.join(self.folder_path, "customization.csv"))
        self.photo_gallery.clear_photos()
        if self.types is not None:
            for key in self.types.keys():
                if self.types[key][1]:
                    for marker in self.types[key][3]:
                        marker.place_forget()

        # self.types = {"start": [0, True, [], []], "stop": [0, True, [], []], "screenshot": [0, True, [], []],
        #               "mark": [0, True, [], []], "correct": [0, True, [], []], "incorrect": [0, True, [], []],
        #               "voice": [0, True, [], []]}
        self.types = {}

        self.total_trial = 0
        self.correct_trial = 0
        self.annotations = []
        self.tasks = []

        with open(os.path.join(self.folder_path, 'task_info.csv')) as file:
            reader = csv.reader(file, delimiter=',', quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
            next(reader, None)
            annotation_id = 0
            for row in reader:
                is_bumped = False
                if len(row) >= 7:
                    is_bumped = row[6] == 'True'

                task = Task(len(self.tasks) + 1, row[0], row[1], row[2], row[3], row[4], row[5], self.folder_path,
                            is_bumped)
                if task in self.tasks:
                    continue
                if task.get_func() == FUNC_LIST['correct'] or task.get_func() == FUNC_LIST['incorrect']:
                    self.total_trial += 1
                if task.get_func() == FUNC_LIST['correct']:
                    self.correct_trial += 1
                if task.get_func() == FUNC_LIST['screenshot_roi'] or task.get_func() == FUNC_LIST['screenshot_whole'] \
                        or task.get_func() == FUNC_LIST['mark']:
                    self.photo_gallery.insert_photo(task.get_timestamp(),
                                                    os.path.join(self.folder_path, task.get_image_name() + ".png"))
                self.tasks.append(task)
                if task.get_display_type() not in self.types.keys():
                    self.types.update({task.get_display_type(): [0, True, [], []]})
                self.types[task.get_display_type()][0] += 1
                self.types[task.get_display_type()][2].append(task.get_id())

                type_color = UI.color.color_translation(task.get_color())
                cells = [{"value": task.get_is_bumped(), "anchor": "center", "tag": ""},
                         {"value": "selected", "fg": "white", "anchor": "center", "tag": ""},
                         {"value": task.get_timestamp(), "fg": "white", "anchor": "center", "tag": "timestamp"},
                         {"value": task.get_display_type(), "fg": type_color, "anchor": "center", "tag": "type"},
                         {"value": task.get_display_notes(), "fg": "white", "anchor": "w", "tag": "note"},
                         {"anchor": "center", "tag": ""}]
                self.tasks_table.insert(obj=task, cells=cells, iid=task.get_id())

                if task.get_func() != FUNC_START and task.get_func() != FUNC_STOP:
                    self.add_annotation_to_progress_bar(task, annotation_id)
                    annotation_id += 1
        self.tasks_table.bump_rows()
        self.generate_annotation_type_filter()
        if self.total_trial != 0:
            self.accuracy = (self.correct_trial / self.total_trial) * 100
            self.summary_text.set(
                "Duration (min): {}             Accuracy: {:.2f}%".format(self.duration_in_mins, self.accuracy))
        else:
            self.summary_text.set("Duration (min): {}             Accuracy: N.A.".format(self.duration_in_mins))

    def parse_annotations(self):
        file_path = os.path.join(self.folder_path, 'customization.csv')
        self.customization_df = pd.read_csv(file_path)
        if 'color' not in self.customization_df.columns:
            self.customization_df = get_customized_annotation_df()
        for index, row in self.customization_df.iterrows():
            self.annotation_types.update({row['type']: {'color': row['color'], 'func': row['func']}})

    def get_video_duration(self):
        self.update_video_duration()
        return self.video_duration

    def update_video_duration(self):
        duration = self.vid_player.video_info()["duration"]
        if float(duration) != 0.0:
            self.video_duration = self.vid_player.video_info()["duration"]

    def add_annotation_to_progress_bar(self, annotation, i):
        if annotation.get_display_type() in self.annotation_types.keys():
            self.annotations.append(annotation)
            timestamp = str_to_sec(annotation.get_timestamp())
            try:
                position = timestamp / self.get_video_duration()
            except:
                position = 0
                print("[ERROR] Can't calculate the marker position")

            marker = Marker(self.progress_slider, width=8,
                            background=self.annotation_types[annotation.get_display_type()]['color'])
            marker.place(relx=position, rely=0.8, anchor="w", height=ANALYZER_MARKER_THICKNESS)
            marker.bind("<Button-1>", lambda event,
                                             index=i: self.skip_to(index=index))
            self.types[annotation.get_display_type()][3].append(marker)

    def on_closing(self):
        self.save()
        self.root.destroy()

    def run(self):
        self.pack_layout()
        if len(self.pids) > 0:
            self.set_folder_path()
        self.parse_annotations()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        if self.is_run_transcribe:
            self.run_transcribe()
        else:
            self.transcribe_in_progress_label.pack_forget()
        self.root.bind('<Key>', self.on_press_key)
        self.root.mainloop()


def setup_new_analyzer(pid=None, frame=None):
    if pid is not None:
        analyzer = Analyser(frame=frame, is_run_alone=True, pid=pid)
    else:
        analyzer = Analyser()
    analyzer.run()


if __name__ == '__main__':
    setup_new_analyzer()
    # setup_new_analyzer(pid="p1_2")
