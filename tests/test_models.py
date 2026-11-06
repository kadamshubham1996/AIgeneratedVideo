import unittest

from shorts_maker.models import SCENE_COUNT, Scene, Story, StoryValidationError
from shorts_maker.renderer import scene_durations


class StoryTests(unittest.TestCase):
    def make_story_data(self):
        return {
            "title": "A tiny story",
            "scenes": [
                {"narration": f"Scene number {number}.", "image_prompt": f"A scene {number}"}
                for number in range(1, SCENE_COUNT + 1)
            ],
        }

    def test_story_parses_and_combines_narration(self):
        story = Story.from_dict(self.make_story_data())
        self.assertEqual(len(story.scenes), 5)
        self.assertEqual(story.narration, "Scene number 1. Scene number 2. Scene number 3. Scene number 4. Scene number 5.")

    def test_story_rejects_wrong_scene_count(self):
        data = self.make_story_data()
        data["scenes"].pop()
        with self.assertRaises(StoryValidationError):
            Story.from_dict(data)

    def test_scene_rejects_empty_narration(self):
        with self.assertRaises(StoryValidationError):
            Scene.from_dict({"narration": " ", "image_prompt": "A landscape"}, 1)

    def test_scene_durations_are_positive_and_sum_to_target(self):
        story = Story.from_dict(self.make_story_data())
        durations = scene_durations(story, 30)
        self.assertEqual(len(durations), 5)
        self.assertTrue(all(duration > 0 for duration in durations))
        self.assertAlmostEqual(sum(durations), 30)


if __name__ == "__main__":
    unittest.main()
