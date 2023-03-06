import threading
from queue import Queue

import cv2
import pickle
import socket
import struct

BUFFER_SIZE = 4096


# Receive and play frames getting from the other laptop (i.e., client, which receives video streaming from HoloLens)
class StreamServer:
    def __init__(self, host_ip='', port=8080):
        self.running_flag = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host_ip, port))
        self.server_socket.listen(5)
        conn, addr = self.server_socket.accept()
        print("Successfully build socket connect.")
        data = b''
        payload_size = struct.calcsize("Q")
        self.queue = Queue()
        self.running_flag = True
        self.thread = threading.Thread(target=self._recv, args=(conn, data, payload_size,))
        self.thread.start()

    def isOpened(self):
        return self.running_flag

    def _recv(self, conn, data, payload_size):
        while self.running_flag:
            while len(data) < payload_size:
                data += conn.recv(BUFFER_SIZE)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += conn.recv(BUFFER_SIZE)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data)
            self.width = frame.shape[0]
            self.height = frame.shape[1]
            self.queue.put(frame)

            # cv2.imshow('Stream', frame)
            #
            # if cv2.waitKey(25) & 0xFF == ord('q'):
            #     break

    def close(self):
        self.running_flag = False
        # self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()

    def read(self):
        return self.queue.get()

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width


if __name__ == '__main__':
    stream_server = StreamServer()
