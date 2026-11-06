import os
import tempfile
import unittest
from pathlib import Path

from moviepy import AudioFileClip

from shorts_maker.windows_tts import create_windows_voiceover


@unittest.skipUnless(os.name == "nt", "Windows built-in speech is only available on Windows.")
class WindowsSpeechTests(unittest.TestCase):
    def test_creates_playable_wav_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "voiceover.wav"
            create_windows_voiceover("This is a local speech test.", destination)

            self.assertTrue(destination.is_file())
            with AudioFileClip(str(destination)) as audio:
                self.assertGreater(audio.duration, 0)


if __name__ == "__main__":
    unittest.main()
