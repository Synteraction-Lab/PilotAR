# from tkinter import ttkf
import tkinter as tk
import UI.color


class Marker:
    def __init__(self, container, width, background, height=20):
        self.container = container
        self.width = width
        self.background = background
        self.frame = tk.Frame(self.container, width=self.width, height=height)
                            #    bootstyle="{}".format(UI.color.color_translation(background)))
        self.frame.configure(bg=UI.color.color_translation(self.background))

    def place(self, relx=None, rely=None, anchor=None, height=None):
        if relx is not None:
            self.relx, self.rely, self.anchor, self.height = relx, rely, anchor, height

        # self.frame.place(relx=self.relx, rely=self.rely, anchor=self.anchor, relheight=self.relheight)
        self.frame.place(relx=self.relx, rely=self.rely, anchor=self.anchor, height=self.height)

    def place_forget(self):
        self.frame.place_forget()

    def bind(self, *args, **kwargs):
        self.frame.bind(*args, **kwargs)
