import webbrowser

def receive_tool_stream(sender_ip="127.0.0.1", port="5001"):
    webbrowser.get().open(f'http://{sender_ip}:{port}')

if __name__ == "__main__":
    receive_tool_stream()
