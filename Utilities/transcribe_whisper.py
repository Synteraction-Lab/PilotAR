import sys
sys.path.append("./")
import whisper
import os
from Utilities.log_utilities import log_manipulation_info
from Utilities.common_utilities import sec_to_str
from Utilities.stable_whisper import modify_model, results_to_word_srt
import datetime
import srt
from Utilities.annotation_utilities import FUNC_LIST

BREAK_DIFFERENCE_THRESHOLD = 3

def transcribe(pid="p1_1", callback=None, annotation_types=None):
    try:
        folder_path = os.path.join("data", pid)
        audio_file_path = os.path.join(folder_path, "output.mp4")
        model = whisper.load_model("base.en")
        modify_model(model)
        result = model.transcribe(audio_file_path, language="en", verbose=False, suppress_silence=True, ts_num=16, lower_quantile=0.05, lower_threshold=0.1)
        srt_file_path = os.path.join(folder_path, "audio.srt")
        results_to_word_srt(result, srt_file_path)
    
        subtitles = None
        with open(srt_file_path) as f:
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
    except Exception as e:
        print(e)
        print("Unable to transcribe successfully")
    finally:
        if callback != None:
            callback()


if __name__ == '__main__':
    start = datetime.datetime.now()
    transcribe(pid="p5_0")
    end = datetime.datetime.now()
    diff = end - start
    print("Time difference in {} seconds".format(diff.total_seconds()))

