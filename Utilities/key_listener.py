from pynput.keyboard import Listener as KeyboardListener


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class KeyListener:
    def __init__(self):
        self.keyboard_listener = None
        self.state = None
        self.func = None
        self.key = None

    def on_press(self, key):
        # print(key, self.state, self.func)
        if self.func is not None:
            self.func(key)
        self.key = key

    def get_key(self):
        return self.key

    def set_state(self, state, func):
        if self.keyboard_listener is None:
            self.keyboard_listener = KeyboardListener(on_press=self.on_press)
        self.func = func
        self.state = state

    def start_listener(self):
        if self.keyboard_listener is None:
            self.keyboard_listener = KeyboardListener(on_press=self.on_press)
        self.keyboard_listener.start()

    def stop(self):
        self.keyboard_listener.stop()
