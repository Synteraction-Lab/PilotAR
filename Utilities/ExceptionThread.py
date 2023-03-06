import threading
import traceback
import logging


class ExceptionThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception:
            logging.error(traceback.format_exc())
            # print("[ERROR] thread raises exception")


def test_function_1(input):
    raise IndexError(input)


if __name__ == "__main__":
    input = 'useful'

    t1 = ExceptionThread(target=test_function_1, args=[input])
    t1.start()
