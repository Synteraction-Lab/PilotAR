import tkinter as tk
from PIL import ImageTk, Image
import sys

sys.path.append("./")
from UI.widget_generator import get_label


class PhotoGallery:
    def __init__(self, parent, on_click_photo_func, width=400, height=220, bg="#222222", fg="white", is_run_alone=True,
                 orient="horizontal", img_width=300, img_height=150):
        self.parent = parent
        self.height = height
        self.width = width
        self.bg = bg
        self.fg = fg
        self.orient = orient
        self.img_width = img_width
        self.img_height = img_height
        if is_run_alone:
            # root
            self.parent.geometry("{}x{}".format(self.width, self.height))
        else:
            if orient == "horizontal":
                self.parent.configure(height=self.height)
            else:
                self.parent.configure(width=self.width)

        self.on_click_photo_func = on_click_photo_func
        self.parent.bindtags(self.parent.bindtags() + ("photo_gallery",))

        self.is_horizontal = True
        if orient == "horizontal":
            sb = tk.Scrollbar(self.parent, orient="horizontal", highlightthickness=0, borderwidth=0)
            sb.pack(side="bottom", fill="x")
            self.canvas = tk.Canvas(self.parent, highlightthickness=0, borderwidth=0, xscrollcommand=sb.set)
            self.canvas.pack(fill="x")
            sb.configure(command=self.canvas.xview)
        else:
            sb = tk.Scrollbar(self.parent, orient=orient, highlightthickness=0, borderwidth=0)
            self.canvas = tk.Canvas(self.parent, highlightthickness=0, borderwidth=0, yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            self.canvas.pack(fill="y", expand=True)
            self.is_horizontal = False
            sb.configure(command=self.canvas.yview)

        self.canvas.bindtags(self.canvas.bindtags() + ("photo_gallery",))
        self.frame = tk.Frame(self.canvas, highlightthickness=0, borderwidth=0)
        self.frame.bind("<Configure>", lambda event: self.on_configure())
        self.frame.bindtags(self.frame.bindtags() + ("photo_gallery",))

        # for Windows/Mac OS
        # for vertical scrolling
        self.canvas.bind_class("photo_gallery", "<MouseWheel>", lambda event: self.on_mousewheel(event))
        # for horizontal scrolling
        self.canvas.bind_class("photo_gallery", "<Shift-MouseWheel>", lambda event: self.on_mousewheel(event))

        # for Linux
        # for vertical scrolling
        self.canvas.bind_class("photo_gallery", "<Button-4>", lambda event: self.on_mousewheel(event))
        self.canvas.bind_class("photo_gallery", "<Button-5>", lambda event: self.on_mousewheel(event))
        # for horizontal scrolling
        self.canvas.bind_class("photo_gallery", "<Shift-Button-4>", lambda event: self.on_mousewheel(event))
        self.canvas.bind_class("photo_gallery", "<Shift-Button-5>", lambda event: self.on_mousewheel(event))
        self.canvas.create_window((4, 4), window=self.frame, anchor='nw')

    
    def on_mousewheel(self, event):
        x,y = self.canvas.winfo_pointerxy()
        widget_path = str(self.canvas.winfo_containing(x,y))
        if not widget_path.startswith(str(self.canvas)):
            return

        delta = 0
        if sys.platform == 'darwin': # for OS X # also, if platform.system() == 'Darwin':
            delta = event.delta
        else:                            # for Windows, Linux
            delta = event.delta // 120   # event.delta is some multiple of 120
        if not self.is_horizontal:
            self.canvas.yview_scroll(int(-1*(delta)), "units")
        else:
            self.canvas.xview_scroll(int(-1*(delta)), "units")
           
    def on_configure(self):
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def insert_photo(self, timestamp, image_path):
        try:
            photo = Image.open(image_path)
            photo = photo.resize((self.img_width, self.img_height))
            photo = ImageTk.PhotoImage(image=photo)

            child_frame = tk.Frame(self.frame, highlightthickness=0, borderwidth=0)
            child_frame.bindtags(child_frame.bindtags() + ("photo_gallery",))

            label = tk.Label(child_frame, image=photo, highlightthickness=0, borderwidth=0)
            label.image = photo  # keep a reference
            label.bind("<Button-1>", lambda e, timestamp=timestamp: self.on_click_photo_func(timestamp))
            label.bindtags(label.bindtags() + ("photo_gallery",))
            label.pack(side="top", padx=10)
            # timestamp_label = tk.Label(child_frame, text=timestamp, highlightthickness=0, borderwidth=0)
            timestamp_label = get_label(child_frame, text=timestamp.replace("_", ":"))
            timestamp_label.pack(side="top", anchor=tk.CENTER, padx=10)
            timestamp_label.bindtags(timestamp_label.bindtags() + ("photo_gallery",))
            if self.orient == "horizontal":
                child_frame.pack(side="left")
            else:
                child_frame.pack(side="bottom")
        except:
            print("[ERROR] {} not found".format(image_path))

    def clear_photos(self):
        for child in self.frame.winfo_children():
            child.destroy()


def on_click_photo(timestamp):
    print("clicked " + timestamp)


if __name__ == "__main__":
    root = tk.Tk()
    pg = PhotoGallery(parent=root, on_click_photo_func=on_click_photo)
    pg.insert_photo("00:00:05", "./data/p20_10/00_00_15.png")
    pg.insert_photo("00:00:12", "./data/p20_10/00_00_37.png")
    pg.insert_photo("00:00:19", "./data/p20_10/00_01_06.png")
    root.mainloop()
