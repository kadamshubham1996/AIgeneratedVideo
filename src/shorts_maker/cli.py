from __future__ import annotations

import argparse
import sys

from openai import OpenAIError

from .config import ConfigurationError, Settings
from .pipeline import generate_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shorts-maker",
        description="Generate a narrated, subtitled vertical video from a topic.",
    )
    parser.add_argument("topic", nargs="?", help="Topic for the short video.")
    parser.add_argument(
        "--env-file",
        help="Path to a .env file (defaults to .env in the current directory).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    topic = args.topic or input("Enter a topic for your short video: ").strip()
    try:
        settings = Settings.from_env(env_file=args.env_file)
        video_path = generate_video(topic, settings)
    except (ConfigurationError, OpenAIError, OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"Video ready: {video_path.resolve()}")


if __name__ == "__main__":
    main()
