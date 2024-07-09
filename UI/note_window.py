import sys

sys.path.append("./")
import tkinter
from tkinter import WORD, Toplevel, Frame
from UI.task import Task
from UI.widget_generator import get_bordered_frame, get_bordered_label_frame, get_button, get_text
from Utilities.screen_capture import get_second_monitor_original_pos
import os


class NoteWindow:
    def __init__(self, pid="p1_1", parent=None, on_close_note_window_func=None, font=None, task=None, width=160,
                 height=150):
        self.parent = parent
        self.root = Toplevel()
        self.root.wait_visibility()
        self.root.overrideredirect(True)
        self.font = font
        self.width = width
        self.height = height
        self.task = task
        self.pid = pid
        self.folder_path = os.path.join("data", pid)
        self.on_close_note_window_func = on_close_note_window_func
        self.pack_layout()
        self.root.attributes('-topmost', True)
        self.place_window_to_center()

    def save(self, notes):
        self.task.set_notes(notes)

    def pack_layout(self):
        self.main_frame = get_bordered_frame(self.root)
        self.frame = Frame(self.main_frame, width=self.width, height=self.height)
        self.notes_row = get_bordered_label_frame(self.frame, text="Note:")
        self.notes_txt = get_text(self.notes_row)
        if self.task != None:
            self.notes_txt.insert(1.0, self.task.get_notes())
        self.notes_txt.configure(height=10, borderwidth=0, highlightthickness=0)
        self.notes_txt.pack(padx=5)
        self.notes_row.pack()
        self.frame.pack(expand=True, padx=10)
        self.main_frame.pack(expand=True)
        self.close_frame = Frame(self.frame)
        self.close_frame.pack(pady=10, side="bottom")
        self.close_btn = get_button(self.close_frame, text="Save", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

    def on_close_window(self):
        try:
            if self.on_close_note_window_func == None or self.task == None:
                return
            updated_notes = self.notes_txt.get("1.0", "end-1c")
            self.save(updated_notes)
            self.on_close_note_window_func()
        except:
            print("[ERROR] something went wrong during the closing of note window")
        self.root.destroy()

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))


if __name__ == '__main__':
    root = tkinter.Tk()
    t1 = Task(2, "00:00:01", "voice", "N.A.",
              "once upon a time there was an old mother pig who had trained litter pick and not enough to defeat them so and they were all now she said the or into the was sick their fortunes")

    NoteWindow(root, task=t1, pid="p15_1")
    # root.mainloop()
