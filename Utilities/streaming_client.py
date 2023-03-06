from queue import Queue
import multiprocessing as mp
from threading import Thread

import cv2
import socket
import pickle
import struct

IP_ADDR = "172.25.102.54"


def _send(flag, queue, ip_addr, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip_addr, port))
        while flag.value:
            data = pickle.dumps(queue.get())
            message_size = struct.pack("Q", len(data))
            client_socket.sendall(message_size + data)
    except:
        print("Fail to connect to server.")


# Send streaming frame getting from HoloLens to the other laptop (server)
class StreamClient:
    def __init__(self, ip_addr=IP_ADDR, port=8080):
        self.queue = mp.Queue()
        self.flag = mp.Value('b', True)
        self.send_process = mp.Process(target=_send, args=(self.flag, self.queue, ip_addr, port,))
        self.send_process.start()

    def send_frame(self, frame):
        self.queue.put(frame)

    def stop(self):
        print("stop socket connection")
        self.flag.value = False
        self.send_process.terminate()


if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    stream_client = StreamClient()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        stream_client.send_frame(frame)
