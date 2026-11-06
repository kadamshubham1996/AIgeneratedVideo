from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import Settings
from .models import Story
from .openai_service import OpenAIGenerator, safe_filename
from .renderer import render_video


def generate_video(topic: str, settings: Settings) -> Path:
    topic = topic.strip()
    if not topic:
        raise ValueError("Topic must not be empty.")
    if len(topic) > 300:
        raise ValueError("Topic must be 300 characters or fewer.")

    run_name = f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}-{safe_filename(topic)}"
    run_dir = settings.output_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=False)

    generator = OpenAIGenerator(settings)
    print("Creating a five-scene script...")
    story = generator.create_story(topic)
    (run_dir / "story.json").write_text(
        json.dumps(story.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    image_paths: list[Path] = []
    for index, scene in enumerate(story.scenes, start=1):
        image_path = run_dir / f"scene-{index:02}.png"
        print(f"Generating image {index}/{len(story.scenes)}...")
        generator.create_image(scene.image_prompt, image_path)
        image_paths.append(image_path)

    voiceover_path = run_dir / ("voiceover.wav" if settings.tts_provider == "windows" else "voiceover.mp3")
    print("Generating voice-over...")
    generator.create_voiceover(story.narration, voiceover_path)

    video_path = run_dir / f"{safe_filename(story.title)}.mp4"
    print("Rendering vertical video...")
    render_video(story, image_paths, voiceover_path, video_path, settings)
    return video_path
