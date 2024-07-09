# Implementation is based on aiortc example
# https://github.com/aiortc/aiortc/blob/main/examples/webcam/webcam.py 

import asyncio
import json
import os
import sys
import multiprocessing

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
from Utilities.screen_capture import get_second_monitor_original_pos

ROOT = os.path.dirname(__file__)
_isMacOS = sys.platform.startswith('darwin')
_isWindows = sys.platform.startswith('win')

def create_tracks(microphone_audio, screen_audio, screen_device):

    screen_width = int(get_second_monitor_original_pos()[2])
    screen_height = int(get_second_monitor_original_pos()[3])

    video_options = {
        'c:v': 'libx264', 
        "preset": "ultrafast", # fast encoding speed
        "tune": "zerolatency", # fast encoding and low-latency streaming
        'video_size': f'{screen_width}x{int(0.8 * screen_height)}', # adjust streaming size
        'offset_y': f'{int(screen_height * 0.1)}',
    }
    audio_options = {
        'c:a': 'aac', 
        "b:a": "32k", # bitrate
        "tune": "zerolatency", # fast encoding and low-latency streaming
        "framerate": "30", # required setting
    }

    if _isWindows:
        desktop = MediaPlayer('desktop', format='gdigrab', options=video_options)
        microphone = MediaPlayer(f'audio={microphone_audio}', format='dshow', options=audio_options)
        screen = MediaPlayer(f'audio={screen_audio}', format='dshow', options=audio_options)
    elif _isMacOS:
        desktop = MediaPlayer(f'{screen_device}:none', format='avfoundation', options=video_options)
        microphone = MediaPlayer(f'default:{microphone_audio}', format='avfoundation', options=audio_options)
        screen = MediaPlayer(f'default:{screen_audio}', format='avfoundation', options=audio_options)

    return [desktop.video, microphone.audio, screen.audio]
    

async def index(request):
    content = open(os.path.join(ROOT, "static/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "static/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request, microphone_audio, screen_audio, screen_device="0"):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    media = create_tracks(microphone_audio, screen_audio, screen_device)

    for track in media:
        pc.addTrack(track)

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

pcs = set()

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

def start_app(microphone_audio, screen_audio, screen_device, port):
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", lambda request: offer(request, microphone_audio, screen_audio, screen_device))
    web.run_app(app, host="0.0.0.0", port=int(port))

def send_tool_stream(microphone_audio, screen_audio, screen_device="0", port="5001", ):
    multiprocessing.Process(target=start_app, args= (microphone_audio, screen_audio, screen_device, port),daemon=True).start()

