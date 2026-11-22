"""Pick and preview a loopable interval inside an extracted frame sequence.

Scoring is deliberately simple and local: downscale every frame to grayscale
and measure the mean absolute difference across the wrap seam. The point is to
rank candidates for the user to eyeball, not to decide for them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .imageio_util import list_frames, to_gray_array, write_json


def _seam_scores(arrays: list[np.ndarray], length: int) -> list[tuple[int, float, float]]:
    """For each start index, score the wrap seam and the local motion."""
    total = len(arrays)
    results: list[tuple[int, float, float]] = []
    for start in range(total - length + 1):
        first = arrays[start]
        last = arrays[start + length - 1]
        seam = float(np.mean(np.abs(last - first)))
        window = arrays[start : start + length]
        motion = float(
            np.mean([np.mean(np.abs(window[i + 1] - window[i])) for i in range(length - 1)])
        ) if length > 1 else 0.0
        results.append((start, seam, motion))
    return results


def analyze_loop(
    frames_dir: Path,
    length: int,
    top: int = 5,
    report_path: Path | None = None,
) -> dict:
    frames = list_frames(frames_dir)
    if len(frames) < length:
        raise SystemExit(
            f"need at least {length} frames to pick a {length}-frame loop, found {len(frames)}"
        )

    arrays = [to_gray_array(p) for p in frames]
    scored = _seam_scores(arrays, length)
    ranked = sorted(scored, key=lambda item: item[1])[:top]

    candidates = [
        {
            "start": start,
            "end": start + length - 1,
            "seam_distance": round(seam, 6),
            "mean_motion": round(motion, 6),
            "start_file": frames[start].name,
            "end_file": frames[start + length - 1].name,
        }
        for start, seam, motion in ranked
    ]
    result = {
        "frames_dir": str(frames_dir),
        "available_frames": len(frames),
        "loop_length": length,
        "candidates": candidates,
        "note": "seam_distance is the wrap-around difference; lower is a smoother loop. "
        "A near-zero mean_motion means the window barely moves, so check the preview.",
    }
    if report_path:
        write_json(result, report_path)
        result["report"] = str(report_path)
    return result


def write_preview(
    frames_dir: Path,
    output_path: Path,
    start: int,
    length: int,
    fps: float = 12.0,
    max_size: int = 480,
) -> dict:
    frames = list_frames(frames_dir)
    if start < 0 or start + length > len(frames):
        raise SystemExit(
            f"range {start}..{start + length - 1} is outside the {len(frames)} available frames"
        )

    selected = frames[start : start + length]
    images: list[Image.Image] = []
    for path in selected:
        with Image.open(path) as im:
            image = im.convert("RGBA")
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        images.append(image)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(1, round(1000.0 / fps))
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        format="WEBP" if output_path.suffix.lower() == ".webp" else None,
    )
    return {
        "preview": str(output_path),
        "start": start,
        "end": start + length - 1,
        "frames": len(images),
        "fps": fps,
        "size": list(images[0].size),
    }
