"""Transcribe any audio/video file with Whisper large-v3-turbo (DeepInfra) or whisper-1 (OpenAI)."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI, OpenAIError

# Short chunks keep every upload far below the 25 MB API limit and let long files transcribe in parallel.
# shortcut: fixed-length cuts can split a word at a chunk boundary, upgrade to silence-aware splitting if that matters.
SEGMENT_SECONDS = 600


def _client():
    load_dotenv(find_dotenv(usecwd=True))  # usecwd: look in the user's directory, not site-packages
    if key := os.getenv("DEEPINFRA_API_KEY"):
        return OpenAI(api_key=key, base_url="https://api.deepinfra.com/v1/openai"), "openai/whisper-large-v3-turbo"
    if key := os.getenv("OPENAI_API_KEY"):
        return OpenAI(api_key=key), "whisper-1"  # OpenAI's API does not serve large-v3-turbo
    raise RuntimeError("set DEEPINFRA_API_KEY or OPENAI_API_KEY in .env (see .env.example)")


def _encode(path, out_dir):
    """Let ffmpeg decode anything (mp4, mp3, m4a, wav, mkv, ...) into small mono 16 kHz opus chunks."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found; install it (e.g. `brew install ffmpeg`)")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "libopus", "-b:a", "24k",
         "-f", "segment", "-segment_time", str(SEGMENT_SECONDS), f"{out_dir}/%04d.ogg"],
        capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    return sorted(Path(out_dir).glob("*.ogg"))


def transcribe(path):
    """Return the transcript of an audio/video file."""
    client, model = _client()
    with tempfile.TemporaryDirectory() as tmp:
        def one(chunk):
            with chunk.open("rb") as f:
                return client.audio.transcriptions.create(model=model, file=f).text.strip()

        with ThreadPoolExecutor(8) as pool:
            return " ".join(pool.map(one, _encode(path, tmp)))


def main():
    ap = argparse.ArgumentParser(prog="transcribe", description=__doc__)
    ap.add_argument("file", help="audio or video file")
    try:
        print(transcribe(ap.parse_args().file))
    except (RuntimeError, OpenAIError) as e:
        sys.exit(f"transcribe: {e}")
