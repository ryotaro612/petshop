"""Normalize frames to a fixed square cell (780x780 by default)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from . import DEFAULT_CELL
from .imageio_util import list_frames, save_image

MODES = ("pad", "cover", "stretch")


def parse_background(value: str) -> tuple[int, int, int, int]:
    if value.lower() in ("transparent", "none"):
        return (0, 0, 0, 0)
    from PIL import ImageColor

    rgba = ImageColor.getcolor(value, "RGBA")
    return rgba  # type: ignore[return-value]


def normalize_image(
    image: Image.Image,
    cell: int = DEFAULT_CELL,
    mode: str = "pad",
    background: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    if mode not in MODES:
        raise SystemExit(f"--mode must be one of {', '.join(MODES)}")
    image = image.convert("RGBA")

    if mode == "stretch":
        return image.resize((cell, cell), Image.Resampling.LANCZOS)

    width, height = image.size
    scale = min(cell / width, cell / height) if mode == "pad" else max(cell / width, cell / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    scaled = image.resize(new_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (cell, cell), background)
    offset = ((cell - new_size[0]) // 2, (cell - new_size[1]) // 2)
    if mode == "pad":
        canvas.alpha_composite(scaled, offset)
        return canvas
    # cover: center-crop the overflow
    left = (new_size[0] - cell) // 2
    top = (new_size[1] - cell) // 2
    return scaled.crop((left, top, left + cell, top + cell))


def normalize_frames(
    frames_dir: Path,
    output_dir: Path,
    cell: int = DEFAULT_CELL,
    mode: str = "pad",
    background: str = "transparent",
    prefix: str = "cell",
    start: int = 0,
    length: int | None = None,
) -> dict:
    frames = list_frames(frames_dir)
    total = len(frames)
    if length is not None:
        if start < 0 or start + length > total:
            raise SystemExit(
                f"range {start}..{start + length - 1} is outside the {total} available frames"
            )
        frames = frames[start : start + length]
    elif start:
        if start >= total:
            raise SystemExit(f"--start {start} is outside the {total} available frames")
        frames = frames[start:]
    bg = parse_background(background)
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes: set[tuple[int, int]] = set()
    for index, path in enumerate(frames):
        with Image.open(path) as im:
            sizes.add(im.size)
            normalized = normalize_image(im, cell=cell, mode=mode, background=bg)
        save_image(normalized, output_dir / f"{prefix}_{index:04d}.png")

    return {
        "frames_dir": str(frames_dir),
        "output_dir": str(output_dir),
        "count": len(frames),
        "selected_range": [start, start + len(frames) - 1],
        "cell": cell,
        "mode": mode,
        "background": background,
        "source_sizes": sorted(list(s) for s in sizes),
    }
