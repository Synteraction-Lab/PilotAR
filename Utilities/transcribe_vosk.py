import sys
sys.path.append("./")
import wave
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import os
from Utilities.log_utilities import log_manipulation_info
from Utilities.common_utilities import sec_to_str
import datetime

BREAK_DIFFERENCE_THRESHOLD = 3

class Word:
    ''' A class representing a word from the JSON format for vosk speech recognition API '''

    def __init__(self, dict):
        '''
        Parameters:
          dict (dict) dictionary from JSON, containing:
            conf (float): degree of confidence, from 0 to 1
            end (float): end time of the pronouncing the word, in seconds
            start (float): start time of the pronouncing the word, in seconds
            word (str): recognized word
        '''

        self.conf = dict["conf"]
        self.end = dict["end"]
        self.start = dict["start"]
        self.word = dict["word"]

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end

    def get_word(self):
        return self.word

    def to_string(self):
        ''' Returns a string describing this instance '''
        return "{:20} from {:.2f} sec to {:.2f} sec, confidence is {:.2f}%".format(
            self.word, self.start, self.end, self.conf*100)

def transcribe(pid="p1_1", callback=None):
    folder_path = os.path.join("data", pid)
    to_convert_audio_file_path = os.path.join(folder_path, "output.mp4")
    output_audio_file_path = os.path.join(folder_path, "output_pcm.wav")
    # transcript_file_path = os.path.join(folder_path, "transcript.json")

    if not os.path.exists(output_audio_file_path):
        sound = AudioSegment.from_file(to_convert_audio_file_path, format='mp4')
        sound = sound.set_channels(1)
        sound.export(output_audio_file_path, format="wav")

    wf = wave.open(output_audio_file_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
        return 

    model = Model(lang="en-us")

    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    # get the list of JSON dictionaries
    results = []
    # recognize speech using vosk model
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
    part_result = json.loads(rec.FinalResult())
    results.append(part_result)
    wf.close()  # close audiofile

    # convert list of JSON dictionaries to list of 'Word' objects
    words = []
    for sentence in results:
        if len(sentence) == 1:
            # sometimes there are bugs in recognition and it returns an empty dictionary {'text': ''}
            continue
        for obj in sentence['result']:
            w = Word(obj)  # create custom Word object
            words.append(w)  # and add it to list


    paragraphs = []
    for i in range(len(words)):
        word = words[i]
        if len(paragraphs) == 0:
            p = {"text": word.get_word(), "start": word.get_start(), "end": 0, "last_word_end_time" : word.get_end()}
            paragraphs.append(p)
            continue

        p = paragraphs[len(paragraphs) - 1]
        if p["end"] == 0:
            if i == len(words) - 1:
                p["end"] = word.get_end()
                p["text"] += (" " + word.get_word())
                del p["last_word_end_time"]
                break
            difference = word.get_start() - p["last_word_end_time"]
            if difference >= BREAK_DIFFERENCE_THRESHOLD:
                p["end"] = p["last_word_end_time"]
                del p["last_word_end_time"]
                p2 = {"text": word.get_word(), "start": word.get_start(), "end": 0, "last_word_end_time" : word.get_end()}
                paragraphs.append(p2)
            else:
                p["text"] += (" " + word.get_word())
                p["last_word_end_time"] = word.get_end()

    # data = {"paragraphs": paragraphs}
    # json_string = json.dumps(data)
    # with open(transcript_file_path, 'w') as f:
    #     f.write(json_string)

    for p in paragraphs:
        log_manipulation_info(pid, sec_to_str(p["start"]), "voice", sec_to_str(p["end"]), '"' + p["text"] + '"')
    
    if callback != None:
        callback()

if __name__ == '__main__':
    start = datetime.datetime.now()
    transcribe(pid="p15_1")
    end = datetime.datetime.now()
    diff = end - start
    print("Time difference in {} seconds".format(diff.total_seconds()))