from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from openai import OpenAI

from .config import Settings
from .models import Story, StoryValidationError
from .windows_tts import create_windows_voiceover


class GenerationError(RuntimeError):
    """Raised when the model response cannot be used to build a video."""


class OpenAIGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.api_key, timeout=120.0, max_retries=2)

    def create_story(self, topic: str) -> Story:
        response = self.client.chat.completions.create(
            model=self.settings.text_model,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write engaging, factual, concise scripts for vertical short videos. "
                        "Return JSON only with this shape: "
                        '{"title":"...","scenes":[{"narration":"...","image_prompt":"..."}]}. '
                        "There must be exactly five scenes. The combined narration should be "
                        "about 55-65 spoken words, suitable for a 30-second voice-over. "
                        "Each scene has one natural spoken sentence or two short sentences. "
                        "Each image_prompt must describe a visually clear, cinematic, portrait "
                        "9:16 scene. Keep a consistent visual style and recurring subject where "
                        "appropriate. Do not request text, captions, logos, or watermarks in images. "
                        "Avoid unsupported factual claims and unsafe instructions."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Create a five-scene short video about this topic: {topic}",
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise GenerationError("The text model returned an empty story.")
        try:
            return Story.from_dict(json.loads(content))
        except (json.JSONDecodeError, StoryValidationError) as exc:
            raise GenerationError(f"The text model returned an invalid story: {exc}") from exc

    def create_image(self, prompt: str, destination: Path) -> None:
        response = self.client.images.generate(
            model=self.settings.image_model,
            prompt=(
                f"{prompt}\n\nCreate a polished, photorealistic vertical 9:16 video still. "
                "Keep the main subject centered with safe margins. No text, letters, logos, "
                "subtitles, or watermarks."
            ),
            size="1024x1536",
            quality="medium",
            output_format="png",
        )
        if not response.data or not response.data[0].b64_json:
            raise GenerationError("The image model returned no image data.")
        encoded = response.data[0].b64_json
        destination.write_bytes(base64.b64decode(encoded, validate=True))

    def create_voiceover(self, narration: str, destination: Path) -> None:
        if self.settings.tts_provider == "windows":
            create_windows_voiceover(narration, destination)
            return

        response = self.client.audio.speech.create(
            model=self.settings.tts_model,
            voice=self.settings.tts_voice,
            input=narration,
            instructions="Speak clearly and warmly at a natural, energetic short-video pace.",
            response_format="mp3",
        )
        response.stream_to_file(destination)


def safe_filename(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:60] or "short-video"
