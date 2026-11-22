"""Shared image / path helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_SUFFIXES = (".png", ".webp", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")

_NUM_RE = re.compile(r"(\d+)")


def natural_key(path: Path) -> tuple:
    """Sort frame_2.png before frame_10.png."""
    parts = _NUM_RE.split(path.name)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def list_frames(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise SystemExit(f"not a directory: {directory}")
    frames = [p for p in directory.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
    if not frames:
        raise SystemExit(f"no image files in {directory}")
    return sorted(frames, key=natural_key)


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return im.convert("RGBA")


def load_mask(path: Path, size: tuple[int, int], invert: bool = False) -> Image.Image:
    """Load a black/white mask as single-channel L, white = area to edit."""
    with Image.open(path) as im:
        mask = im.convert("L")
    if mask.size != size:
        mask = mask.resize(size, Image.Resampling.LANCZOS)
    if invert:
        mask = Image.eval(mask, lambda v: 255 - v)
    return mask


def save_image(image: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def write_json(data: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def to_gray_array(path: Path, size: int = 96) -> np.ndarray:
    """Small grayscale array used for cheap frame-to-frame distances."""
    with Image.open(path) as im:
        small = im.convert("L").resize((size, size), Image.Resampling.BILINEAR)
    return np.asarray(small, dtype=np.float32) / 255.0


def parse_meta(pairs: list[str] | None) -> dict:
    """Parse repeated --meta key=value options."""
    meta: dict[str, str] = {}
    for item in pairs or []:
        if "=" not in item:
            raise SystemExit(f"--meta expects key=value, got: {item}")
        key, value = item.split("=", 1)
        meta[key.strip()] = value.strip()
    return meta
