# Shorts Maker

Shorts Maker is a local Python CLI that turns a topic into a narrated, captioned
9:16 video. It generates a five-scene script, scene artwork, and a voice-over
with OpenAI, then renders a 1080x1920 H.264/AAC MP4 using MoviePy and Pillow.
Background music is generated as a quiet original ambient bed by default; you
can instead supply your own licensed music track.

## Requirements

- Python 3.10+
- An OpenAI API key with access to the configured text and image models
- OpenAI TTS access, or Windows built-in speech when `TTS_PROVIDER=windows`
- MoviePy's `imageio-ffmpeg` encoder (installed as a dependency)

## Install

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Never commit `.env` or share your API key.

## Generate a video

```powershell
shorts-maker "Why octopuses are so intelligent"
```

Or run it as a module:

```powershell
python -m shorts_maker "How the Northern Lights form"
```

If no topic argument is supplied, the app prompts for one. Each run creates a
timestamped directory under `output/` containing the final MP4, `story.json`,
five scene images, and the voice-over. Partial assets are retained if generation
fails, which makes the failure easier to diagnose and avoids losing completed
API work.

## Configuration

Copy `.env.example` to `.env`. Settings:

| Variable | Default | Description |
|---|---:|---|
| `OPENAI_API_KEY` | — | Required API key |
| `OPENAI_TEXT_MODEL` | `gpt-4o-mini` | Script model |
| `OPENAI_IMAGE_MODEL` | `gpt-image-1` | Image generation model |
| `OPENAI_TTS_MODEL` | `gpt-4o-mini-tts` | Text-to-speech model |
| `OPENAI_TTS_VOICE` | `alloy` | TTS voice |
| `TTS_PROVIDER` | `openai` | `openai` or Windows built-in speech (`windows`) |
| `VIDEO_DURATION_SECONDS` | `30` | Target video duration |
| `VIDEO_WIDTH` / `VIDEO_HEIGHT` | `1080` / `1920` | Portrait output dimensions |
| `VIDEO_FPS` | `30` | Video frame rate |
| `VIDEO_OUTPUT_DIR` | `output` | Directory for generated assets |
| `VIDEO_FONT_PATH` | platform font | Optional path to a bold TrueType font |
| `BACKGROUND_MUSIC_PATH` | generated ambient music | Optional path to a licensed audio file |
| `BACKGROUND_MUSIC_VOLUME` | `0.12` | Background level from 0.0 to 1.0 |

Voice-over is kept intact when it fits the target duration. If it runs longer,
it is sped up to fit the configured duration; scene timing is weighted by
narration word count. Captions are rendered directly onto each scene image.
On Windows, set `TTS_PROVIDER=windows` to use an installed Windows speech voice
instead of the OpenAI TTS API.

## Development and tests

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

The app uses OpenAI client retries for transient API failures. API costs apply
to text, image, and audio generation. Review `story.json` and generated assets
before publishing, and confirm music and image rights meet your usage needs.
