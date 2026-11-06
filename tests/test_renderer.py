import tempfile
import unittest
import wave
from pathlib import Path

from moviepy import VideoFileClip
from PIL import Image

from shorts_maker.config import Settings
from shorts_maker.models import Story
from shorts_maker.renderer import render_video


class RendererIntegrationTests(unittest.TestCase):
    def test_renders_portrait_mp4_with_target_duration(self):
        story = Story.from_dict(
            {
                "title": "Test short",
                "scenes": [
                    {"narration": f"Scene {index}.", "image_prompt": f"Image {index}"}
                    for index in range(1, 6)
                ],
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_paths = []
            for index in range(5):
                image_path = root / f"scene-{index}.png"
                Image.new("RGB", (72, 128), (30 * index, 80, 120)).save(image_path)
                image_paths.append(image_path)

            voiceover_path = root / "voiceover.wav"
            sample_rate = 8000
            with wave.open(str(voiceover_path), "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(sample_rate)
                audio_file.writeframes(b"\0\0" * (sample_rate * 3))

            destination = root / "render.mp4"
            settings = Settings(
                api_key="test-key",
                duration_seconds=2,
                width=108,
                height=192,
                fps=5,
                music_volume=0.05,
            )
            render_video(story, image_paths, voiceover_path, destination, settings)

            self.assertTrue(destination.is_file())
            with VideoFileClip(str(destination)) as video:
                self.assertEqual(video.size, [108, 192])
                self.assertAlmostEqual(video.duration, 2, delta=0.15)
                self.assertIsNotNone(video.audio)


if __name__ == "__main__":
    unittest.main()
