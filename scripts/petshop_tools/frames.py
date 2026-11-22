"""Extract frames from a generated video without requiring a system ffmpeg.

imageio-ffmpeg ships an ffmpeg binary, so `uv run` works on a clean Mac. A
system ffmpeg is used when present.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from .imageio_util import save_image


def _ffmpeg_exe() -> str:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise SystemExit(
            "no ffmpeg found; install ffmpeg or run via `uv run --project scripts`"
        ) from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def read_video(path: Path) -> tuple[dict, list[np.ndarray]]:
    """Decode a video to a list of HxWx3 uint8 arrays plus its metadata."""
    import imageio_ffmpeg

    reader = imageio_ffmpeg.read_frames(str(path), bits_per_pixel=24)
    meta = next(reader)
    width, height = meta["size"]
    frames = [
        np.frombuffer(chunk, dtype=np.uint8).reshape(height, width, 3) for chunk in reader
    ]
    return meta, frames


def pick_indices(total: int, count: int | None) -> list[int]:
    """Evenly spaced indices, used to hit an exact frame budget (e.g. 56)."""
    if count is None or count >= total:
        return list(range(total))
    if count <= 0:
        raise SystemExit("--count must be positive")
    step = total / count
    return [min(total - 1, int(i * step)) for i in range(count)]


def extract_frames(
    video_path: Path,
    output_dir: Path,
    count: int | None = None,
    prefix: str = "frame",
) -> dict:
    _ffmpeg_exe()  # fail early with a clear message if no binary is reachable
    meta, frames = read_video(video_path)
    if not frames:
        raise SystemExit(f"decoded no frames from {video_path}")

    indices = pick_indices(len(frames), count)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for out_i, src_i in enumerate(indices):
        image = Image.fromarray(frames[src_i], mode="RGB")
        path = output_dir / f"{prefix}_{out_i:04d}.png"
        save_image(image, path)
        written.append(path.name)

    return {
        "video": str(video_path),
        "output_dir": str(output_dir),
        "source_frames": len(frames),
        "written_frames": len(written),
        "source_indices": indices,
        "fps": meta.get("fps"),
        "duration": meta.get("duration"),
        "size": list(meta.get("size", ())),
    }
