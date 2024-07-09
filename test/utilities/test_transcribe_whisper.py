import unittest
from Utilities.transcribe_whisper import generate_srt, get_paragraphs
import os

class TestTranscibeWhisper(unittest.TestCase):

    def test_generate_srt(self):
        generate_srt('test/utilities/data', 'whisper_test.mp3', 'whisper_test.srt')
        self.assertTrue(os.path.exists("test/utilities/data/whisper_test.srt"))       

    def test_get_paragraphs(self):
        expected_paragraphs = ['Hello, this is a test.', 'Testing 1, 2, 3.']
        paragraphs = get_paragraphs('test/utilities/data', 'whisper_test.srt')
        text = []
        for p in paragraphs:
            text.append(p['text'])
        self.assertEqual(expected_paragraphs, text)
    
    @classmethod
    def tearDownClass(cls):
        if os.path.exists("test/utilities/data/whisper_test.srt"):
            os.remove("test/utilities/data/whisper_test.srt")

if __name__ == '__main__':
    unittest.main()