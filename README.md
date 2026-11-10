# transcribe

Speech-to-text CLI using Whisper large-v3-turbo. Accepts anything ffmpeg can read: mp4, mp3, m4a, wav, flac, ogg, webm, mkv, mov, ...

## Install

Needs Python 3.9+ and [ffmpeg](https://ffmpeg.org) (`brew install ffmpeg` / `apt install ffmpeg`).

```bash
uv tool install .      # or: pip install .
cp .env.example .env   # then fill in a key
```

## Use

```bash
transcribe meeting.mp4 > meeting.txt
```

```python
from transcribe import transcribe
text = transcribe("podcast.mp3")
```

## Keys

Read from `.env` in the current directory (or any parent); real environment variables also work.

| Variable | Model used |
|---|---|
| `DEEPINFRA_API_KEY` (preferred) | `openai/whisper-large-v3-turbo` |
| `OPENAI_API_KEY` | `whisper-1` (OpenAI's API does not offer large-v3-turbo) |

Installed globally (`uv tool install .`), the command only finds `.env` in the directory you run it from (or a parent). From anywhere else, export the variable in your shell profile instead.

## How it works

ffmpeg strips video and re-encodes to mono 16 kHz opus (~24 kbps), cut into 10-minute chunks. Chunks are transcribed in parallel (8 at a time) and joined in order. A chunk boundary can split a word.

## Test

```bash
uv run pytest
```
