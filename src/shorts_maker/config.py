from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    text_model: str = "gpt-4o-mini"
    image_model: str = "gpt-image-1"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"
    tts_provider: str = "openai"
    duration_seconds: int = 30
    width: int = 1080
    height: int = 1920
    fps: int = 30
    output_dir: Path = Path("output")
    font_path: Path | None = None
    music_path: Path | None = None
    music_volume: float = 0.12

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        load_dotenv(dotenv_path=env_file, override=False)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your-api-key":
            raise ConfigurationError(
                "OPENAI_API_KEY is missing. Add your key to .env or set it in the environment."
            )

        try:
            duration = int(os.getenv("VIDEO_DURATION_SECONDS", "30"))
            width = int(os.getenv("VIDEO_WIDTH", "1080"))
            height = int(os.getenv("VIDEO_HEIGHT", "1920"))
            fps = int(os.getenv("VIDEO_FPS", "30"))
            music_volume = float(os.getenv("BACKGROUND_MUSIC_VOLUME", "0.12"))
        except ValueError as exc:
            raise ConfigurationError(
                "Video dimensions, duration, FPS, and music volume must be numeric."
            ) from exc

        if duration <= 0 or width <= 0 or height <= 0 or fps <= 0:
            raise ConfigurationError("Video duration, dimensions, and FPS must be positive.")
        if not 0 <= music_volume <= 1:
            raise ConfigurationError("BACKGROUND_MUSIC_VOLUME must be between 0 and 1.")
        tts_provider = os.getenv("TTS_PROVIDER", "openai").strip().lower()
        if tts_provider not in {"openai", "windows"}:
            raise ConfigurationError("TTS_PROVIDER must be either 'openai' or 'windows'.")

        def optional_path(name: str) -> Path | None:
            value = os.getenv(name, "").strip()
            return Path(value).expanduser() if value else None

        return cls(
            api_key=api_key,
            text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
            image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
            tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
            tts_provider=tts_provider,
            duration_seconds=duration,
            width=width,
            height=height,
            fps=fps,
            output_dir=Path(os.getenv("VIDEO_OUTPUT_DIR", "output")).expanduser(),
            font_path=optional_path("VIDEO_FONT_PATH"),
            music_path=optional_path("BACKGROUND_MUSIC_PATH"),
            music_volume=music_volume,
        )
