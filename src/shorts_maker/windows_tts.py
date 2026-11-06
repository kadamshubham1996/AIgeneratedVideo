from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


class WindowsSpeechError(RuntimeError):
    """Raised when Windows built-in speech synthesis cannot create narration."""


def create_windows_voiceover(narration: str, destination: Path) -> None:
    if os.name != "nt":
        raise WindowsSpeechError("TTS_PROVIDER=windows is only supported on Windows.")

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise WindowsSpeechError("Windows PowerShell is required for Windows speech synthesis.")

    script = r"""
$ErrorActionPreference = 'Stop'
try {
    $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $synth.SetOutputToWaveFile([string]$request.destination)
        $synth.Speak([string]$request.text)
    } finally {
        $synth.Dispose()
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
"""
    try:
        result = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
            input=json.dumps(
                {"text": narration, "destination": str(destination.resolve())},
                ensure_ascii=True,
            ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise WindowsSpeechError("Windows speech synthesis timed out after 180 seconds.") from exc
    except OSError as exc:
        raise WindowsSpeechError(f"Could not start Windows PowerShell: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or "Windows speech synthesis failed."
        raise WindowsSpeechError(detail)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise WindowsSpeechError("Windows speech synthesis did not produce an audio file.")
