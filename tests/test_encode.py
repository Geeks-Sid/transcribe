import subprocess

import pytest

import transcribe

VIDEO = {"mp4", "mkv", "webm", "mov"}


def make(path, seconds):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
    if path.suffix[1:] in VIDEO:
        cmd += ["-f", "lavfi", "-i", f"color=c=black:s=64x64:d={seconds}"]
    subprocess.run(cmd + [str(path)], check=True)


@pytest.mark.parametrize("ext", ["mp3", "wav", "m4a", "flac", "ogg", "mp4", "mkv", "webm", "mov"])
def test_formats_decode(tmp_path, ext):
    src = tmp_path / f"in.{ext}"
    make(src, 3)
    out = tmp_path / "out"
    out.mkdir()
    assert len(transcribe._encode(src, out)) == 1


def test_long_file_is_chunked_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "SEGMENT_SECONDS", 10)
    src = tmp_path / "in.mp3"
    make(src, 25)
    out = tmp_path / "out"
    out.mkdir()
    assert [p.name for p in transcribe._encode(src, out)] == ["0000.ogg", "0001.ogg", "0002.ogg"]


def test_missing_file_raises(tmp_path):
    with pytest.raises(RuntimeError):
        transcribe._encode(tmp_path / "nope.mp3", tmp_path)
