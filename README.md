# PilotAR - Python
A toolkit for experimenters to conduct pilot studies more efficiently with AR smart glasses (Optical See-Through Head-Mounted Displays)



## Project links
- PilotAR usage: [offline video](docs/WOzTool_user_guide.mp4)
- [Version info](VERSION.md)


## Requirements
- A computer with `Windows` (10/11) OR `MacOS`
- For `MacOS`
  - Please install [vb-cable](https://vb-audio.com/Cable/index.htm) to enable you to record your computer's sound.
  - Give access to enable your terminal or IDE (e.g., PyCharm) Input Monitoring and Screen Recording in System Settings -> Privacy & Security.
- For `Windows`
  - Please enable [Stereo Mix](https://www.itechtics.com/stereo-mix/) to allow you to record your computer's sound.
- Currently, the tool support HoloLens 2 device for first-person view (or webcam using `0` as the IP address). So, you need to know the smart glasses' IP address, username, and password. If you forgot, [request a new pin](https://learn.microsoft.com/en-us/windows/mixed-reality/develop/advanced-concepts/using-the-windows-device-portal#creating-a-username-and-password) via Windows Device Portal


## Installation & Preparation
1. Install `conda`, if you haven't done it (e.g., [Anaconda](https://docs.anaconda.com/anaconda/install/)/[Miniconda](https://docs.conda.io/en/latest/miniconda.html)).
2. Create conda environment `woz` via `conda env create -f environment.yml`.
3. Activate `woz` environment via `conda activate woz`


## Execution (Running the PilotAR)
- See PilotAR usage: [offline video](docs/WOzTool_user_guide.mp4)

1. Run `main.py` (e.g., `python main.py` via terminal)
2. You can set up the configurations by clicking `Setup`.
   1. The device configuration, including FPV, TPV, Woz Interface address, and recording sources, can be modified in `Devices`.
   2. You can also set up the checklist by clicking `Checklist`.
   3. To customize the `Annotations` for the pilot recording, you can click `Customization`
3. To start the pilot study, you can click `Pilot` in the top panel. 
   1. In the GUI, you can modify the ``Anticipated duration (in seconds)``, ``Participant & Session ID``. 
   2. You can then click ``Start`` to start one session. 
   3. Add annotations according to your study needs (e.g., Screenshots -> `shortcut key "5"`, Accuracy -> `shortcut key "1/2"` by default)
   4. Once you finish one session, you can click ``Stop``.
   5. You can modify the ``Participant & Session ID`` and click ``Start`` again to start new session.
4. You can then analyze the recordings after pilot. The program will automatically pop up the analyzer. 
You can also click the `Analyzer` in the top panel to open the analyzer's window.

## Known Issues & Solutions
- ``AttributeError: CFMachPortCreateRunLoopSource``
  - Follow this [link](https://github.com/moses-palmer/pynput/issues/55#issuecomment-924820627) to solve this problem

- Unclear images in the Analyzer UI
  - You can go to the file ``tkvideoplayer.py`` and the change ``self._resampling_method: int = Image.NEAREST`` to 
  ``self._resampling_method: int = Image.BICUBIC``.

- File is Missing on `Windows`
  - Virus guard (e.g., Microsoft Defender) blocks the customization file and will not run. 
  - Please need to allow the file in "Windows Security" / Antivirus software.

- Issue with video playing in the Analyzer UI on `Mac M1 chip`
  - Need to install VLC player's Intel version (Enable Rosetta for your terminal).

## References
- Credits to @jianfch for Utilities/stable_whisper.py (code from https://github.com/jianfch/stable-ts)


## [Optional] Generate App (For `MacOS`)
1. In terminal, ``pip install py2app`` and run ``rm -rf build dist``.
2. Run ``python setup.py py2app -A``. Note: Please run this command with conda environment activated.
3. Go to the ``dist`` and open the App.
4. If they are any issues with the App, right-click the App's icon, then select ``Show Package Content`` and go to the ``Content\MacOS``. You can click ``main`` to run the program within the terminal.
