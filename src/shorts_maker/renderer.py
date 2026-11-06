from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

import numpy as np
from moviepy import (
    AudioArrayClip,
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import Settings
from .models import Story


def scene_durations(story: Story, total_seconds: float) -> tuple[float, ...]:
    word_counts = [max(1, len(scene.narration.split())) for scene in story.scenes]
    total_words = sum(word_counts)
    durations = [total_seconds * count / total_words for count in word_counts]
    durations[-1] += total_seconds - sum(durations)
    return tuple(durations)


def _font(settings: Settings, size: int) -> ImageFont.ImageFont:
    candidates = [settings.font_path] if settings.font_path else []
    candidates.extend(
        [
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
    )
    for candidate in candidates:
        if candidate and candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _wrapped_lines(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font, stroke_width=1)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _captioned_frame(image_path: Path, caption: str, settings: Settings) -> np.ndarray:
    with Image.open(image_path) as source:
        frame = ImageOps.fit(
            source.convert("RGB"),
            (settings.width, settings.height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.45),
        )

    draw = ImageDraw.Draw(frame)
    font_size = max(28, int(settings.width * 0.052))
    font = _font(settings, font_size)
    max_width = int(settings.width * 0.84)
    lines = _wrapped_lines(caption, draw, font, max_width)
    line_height = int(font_size * 1.3)
    block_height = line_height * len(lines)
    margin_x = int(settings.width * 0.06)
    padding_y = int(settings.height * 0.025)
    box_top = int(settings.height * 0.77)
    box_bottom = min(settings.height - int(settings.height * 0.06), box_top + block_height + 2 * padding_y)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        (margin_x, box_top, settings.width - margin_x, box_bottom),
        radius=max(12, int(settings.width * 0.015)),
        fill=(0, 0, 0, 190),
    )
    frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(frame)
    text_y = box_top + padding_y
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        text_width = bounds[2] - bounds[0]
        text_x = (settings.width - text_width) // 2
        draw.text(
            (text_x, text_y),
            line,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill="black",
        )
        text_y += line_height
    return np.asarray(frame)


def _ambient_music(duration: float, fps: int, volume: float) -> AudioArrayClip:
    sample_count = int(duration * fps)
    time = np.arange(sample_count, dtype=np.float32) / fps
    fade = np.minimum(1.0, time / 1.5) * np.minimum(1.0, (duration - time) / 2.0)
    chord = (
        np.sin(2 * np.pi * 110.0 * time)
        + 0.62 * np.sin(2 * np.pi * 164.81 * time)
        + 0.42 * np.sin(2 * np.pi * 220.0 * time)
        + 0.24 * np.sin(2 * np.pi * 261.63 * time)
    ) / 2.28
    pulse = 0.72 + 0.28 * np.sin(2 * np.pi * time / 8.0) ** 2
    signal = (chord * fade * pulse * volume).astype(np.float32)
    stereo = np.column_stack((signal, signal))
    return AudioArrayClip(stereo, fps=fps)


def render_video(
    story: Story,
    image_paths: list[Path],
    voiceover_path: Path,
    destination: Path,
    settings: Settings,
) -> None:
    if len(image_paths) != len(story.scenes):
        raise ValueError("An image is required for every story scene.")
    if settings.music_path and not settings.music_path.is_file():
        raise FileNotFoundError(f"Background music file not found: {settings.music_path}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    target_duration = float(settings.duration_seconds)
    durations = scene_durations(story, target_duration)
    clips = []
    with ExitStack() as stack:
        voice = stack.enter_context(AudioFileClip(str(voiceover_path)))
        if voice.duration > target_duration:
            voice = voice.with_speed_scaled(factor=voice.duration / target_duration)

        for scene, image_path, duration in zip(story.scenes, image_paths, durations, strict=True):
            frame = _captioned_frame(image_path, scene.narration, settings)
            clip = ImageClip(frame).with_duration(duration)
            clips.append(clip)
            stack.callback(clip.close)

        video = concatenate_videoclips(clips, method="compose")
        stack.callback(video.close)
        if settings.music_path:
            source_music = stack.enter_context(AudioFileClip(str(settings.music_path)))
            repetitions = max(1, int(np.ceil(target_duration / source_music.duration)))
            music = concatenate_audioclips([source_music] * repetitions).with_duration(target_duration)
            music = music.with_volume_scaled(settings.music_volume)
            stack.callback(music.close)
        else:
            music = _ambient_music(target_duration, 44100, settings.music_volume)
            stack.callback(music.close)

        soundtrack = CompositeAudioClip([voice, music]).with_duration(target_duration)
        stack.callback(soundtrack.close)
        final_video = video.with_audio(soundtrack).with_duration(target_duration)
        stack.callback(final_video.close)
        final_video.write_videofile(
            str(destination),
            fps=settings.fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None,
        )
