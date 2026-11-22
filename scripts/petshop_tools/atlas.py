"""Pack normalized frames into a sprite sheet plus reproducibility metadata."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from . import DEFAULT_CELL, DEFAULT_FRAMES
from .imageio_util import list_frames, save_image, write_json
from .normalize import normalize_image, parse_background


def pack_atlas(
    frames_dir: Path,
    output_path: Path,
    count: int = DEFAULT_FRAMES,
    cell: int = DEFAULT_CELL,
    columns: int | None = None,
    background: str = "transparent",
    normalize: bool = False,
    mode: str = "pad",
    metadata: dict | None = None,
) -> dict:
    frames = list_frames(frames_dir)
    if len(frames) != count:
        raise SystemExit(
            f"expected exactly {count} frames in {frames_dir}, found {len(frames)}. "
            "Select the loop first (petshop select-loop / preview-loop), or pass --count."
        )

    cols = columns or math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    bg = parse_background(background)
    sheet = Image.new("RGBA", (cols * cell, rows * cell), bg)

    for index, path in enumerate(frames):
        with Image.open(path) as im:
            tile = normalize_image(im, cell=cell, mode=mode, background=bg) if normalize else im.convert("RGBA")
        if tile.size != (cell, cell):
            raise SystemExit(
                f"{path.name} is {tile.size[0]}x{tile.size[1]}, expected {cell}x{cell}. "
                "Run `petshop normalize` first or pass --normalize."
            )
        sheet.alpha_composite(tile, ((index % cols) * cell, (index // cols) * cell))

    save_image(sheet, output_path)

    info = {
        "sheet": str(output_path),
        "frame_count": count,
        "cell": cell,
        "columns": cols,
        "rows": rows,
        "sheet_size": [cols * cell, rows * cell],
        "loop": True,
        "frames": [p.name for p in frames],
        "packed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if metadata:
        info["metadata"] = metadata

    meta_path = output_path.with_suffix(".json")
    write_json(info, meta_path)
    info["metadata_file"] = str(meta_path)
    return info
