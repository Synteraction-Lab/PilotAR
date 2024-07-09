import sys
sys.path.append("./")
import whisper
import os
from Utilities.log_utilities import log_manipulation_info, record_is_transcribe_complete
from Utilities.common_utilities import sec_to_str
from Utilities.stable_whisper import modify_model, results_to_word_srt
import datetime
import srt
import traceback
from Utilities.annotation_utilities import FUNC_LIST

BREAK_DIFFERENCE_THRESHOLD = 3

def transcribe_experiment(pid="p1_1", input_filename='experiment.mp4', output_filename='experiment.srt', callback=None, annotation_types=None):
    try:
        folder_path = os.path.join("data", pid)
        generate_srt(folder_path, input_filename, output_filename)
        paragraphs = get_paragraphs(folder_path, output_filename)
        add_to_log(pid, paragraphs, annotation_types)
    except Exception as e:
        record_is_transcribe_complete(pid, "FALSE")
        print("Unable to transcribe successfully ", e)
        print(traceback.format_exc())
    finally:
        record_is_transcribe_complete(pid, "TRUE")
        if callback != None:
            callback()

def add_to_log(pid, paragraphs, annotation_types):
    # get customization for voice annotation
    voice_type = "voice"
    voice_func = "Voice"
    voice_color = "darkpurple"
    if annotation_types != None:
        for key in annotation_types:
            if annotation_types[key]['func'] == FUNC_LIST["voice"]:
                voice_type = key 
                voice_func = annotation_types[key]['func']
                voice_color = annotation_types[key]['color']
    for p in paragraphs:
        start = sec_to_str(p["start"].total_seconds())
        end = sec_to_str(p["end"].total_seconds())
        log_manipulation_info(participant_session=pid, manipulation_time=start, manipulation_type=voice_type, manipulation_func=voice_func, color=voice_color, manipulation_data=end, manipulation_note='"' + p["text"] + '"')

    
def generate_srt(folder_path, input_filename, output_filename, callback=None):
    audio_file_path = os.path.join(folder_path, input_filename)
    model = whisper.load_model("base.en")
    modify_model(model)
    result = model.transcribe(audio_file_path, language="en", verbose=False, suppress_silence=True, ts_num=16, lower_quantile=0.05, lower_threshold=0.1)
    srt_file_path = os.path.join(folder_path, output_filename)
    results_to_word_srt(result, srt_file_path)

def get_paragraphs(folder_path, output_filename):
    subtitles = None
    with open(os.path.join(folder_path, output_filename)) as f:
        subtitle_generator = srt.parse(f)
        subtitles = list(subtitle_generator)


    # 1st pass
    # 1. identify the words that ends with end of sentence punctuation ".", "?", "!"
    # 2. select the word after after (1) as the next sentence start word
    # 3. if the difference between <end> and <start> of (2) is > threshold set then set start = end
    for i in range(len(subtitles)):
        s = subtitles[i]
        s_content = s.content.strip()
        if (s_content[-1] == "." or s_content[-1] == "?" or s_content[-1] == "!") and (i < (len(subtitles) - 1)):
            subtitles[i+1].start = subtitles[i+1].end 
    
    paragraphs = []
    for i in range(len(subtitles)):
        s = subtitles[i]
        text = s.content.strip()
        start = s.start
        end = s.end
        if len(paragraphs) == 0:
            # p = {"text": text, "start": start, "end": 0, "last_word_end_time": end}
            p = {"text": text, "start": start, "end": datetime.timedelta(seconds=0), "last_word_start_time": start, "last_word_end_time": end}

            paragraphs.append(p)
            continue
        
        p = paragraphs[len(paragraphs) - 1]
        if p["end"] == 0 or p["end"] == datetime.timedelta(seconds=0):
            if i == len(subtitles) - 1:
                p["end"] = end
                p["text"] += (" " + text)
                del p["last_word_end_time"]
                del p["last_word_start_time"]
                break
            difference = start - p["last_word_end_time"]
            # difference = start - p["last_word_start_time"]
            if difference >= datetime.timedelta(seconds=BREAK_DIFFERENCE_THRESHOLD):
                # p["end"] = p["last_word_end_time"]
                # del p["last_word_end_time"]
                # p2 = {"text": text, "start": start, "end": 0, "last_word_end_time" : end}

                p["end"] = p["last_word_end_time"]
                del p["last_word_end_time"]
                del p["last_word_start_time"]
                p2 = {"text": text, "start": start, "end": 0, "last_word_start_time" : start, "last_word_end_time": end}
                paragraphs.append(p2)
            else:
                p["text"] += (" " + text)
                p["last_word_end_time"] = end
                p["last_word_start_time"] = start
    return paragraphs

def transcribe_interview(pid="p1_1", input_filename='experiment.mp4', callback=None):
    try:
        folder_path = os.path.join("data", pid)
        generate_srt(folder_path, input_filename, "interview.srt")
        paragraphs = get_paragraphs(folder_path, "interview.srt")
        with open(os.path.join(folder_path, "interview.txt"), 'w') as f:
            for p in paragraphs:
                f.write(p["text"] + '\n\n')
        f.close()
    except Exception as e:
        print("Unable to transcribe successfully ", e)
        print(traceback.format_exc())
    finally:
        if callback != None:
            callback()
