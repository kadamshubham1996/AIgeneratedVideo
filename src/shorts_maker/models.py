from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCENE_COUNT = 5


class StoryValidationError(ValueError):
    """Raised when generated story data does not match the application contract."""


@dataclass(frozen=True)
class Scene:
    narration: str
    image_prompt: str

    @classmethod
    def from_dict(cls, value: Any, index: int) -> Scene:
        if not isinstance(value, dict):
            raise StoryValidationError(f"Scene {index} must be a JSON object.")
        narration = value.get("narration")
        image_prompt = value.get("image_prompt")
        if not isinstance(narration, str) or not narration.strip():
            raise StoryValidationError(f"Scene {index} must have non-empty narration.")
        if not isinstance(image_prompt, str) or not image_prompt.strip():
            raise StoryValidationError(f"Scene {index} must have a non-empty image_prompt.")
        return cls(narration=narration.strip(), image_prompt=image_prompt.strip())


@dataclass(frozen=True)
class Story:
    title: str
    scenes: tuple[Scene, ...]

    @classmethod
    def from_dict(cls, value: Any) -> Story:
        if not isinstance(value, dict):
            raise StoryValidationError("Generated story must be a JSON object.")
        title = value.get("title")
        scenes = value.get("scenes")
        if not isinstance(title, str) or not title.strip():
            raise StoryValidationError("Generated story must have a non-empty title.")
        if not isinstance(scenes, list) or len(scenes) != SCENE_COUNT:
            raise StoryValidationError(f"Generated story must contain exactly {SCENE_COUNT} scenes.")
        return cls(
            title=title.strip(),
            scenes=tuple(Scene.from_dict(scene, i + 1) for i, scene in enumerate(scenes)),
        )

    @property
    def narration(self) -> str:
        return " ".join(scene.narration for scene in self.scenes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "scenes": [
                {"narration": scene.narration, "image_prompt": scene.image_prompt}
                for scene in self.scenes
            ],
        }
