"""petshop local post-processing CLI.

Pipeline order:
    inspect -> composite -> extract-frames -> select-loop -> preview-loop
            -> normalize -> pack-atlas

None of these commands contact RunPod or read credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import DEFAULT_CELL, DEFAULT_FRAMES
from .atlas import pack_atlas
from .composite import composite_masked_edit
from .frames import extract_frames
from .imageio_util import IMAGE_SUFFIXES, list_frames, parse_meta
from .loop import analyze_loop, write_preview
from .normalize import normalize_frames


def _emit(result: dict) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_inspect(args: argparse.Namespace) -> dict:
    from PIL import Image

    target = Path(args.path)
    paths = list_frames(target) if target.is_dir() else [target]
    if not target.is_dir() and target.suffix.lower() not in IMAGE_SUFFIXES:
        raise SystemExit(f"not a supported image: {target}")

    items = []
    for path in paths:
        with Image.open(path) as im:
            items.append(
                {
                    "file": path.name,
                    "size": list(im.size),
                    "mode": im.mode,
                    "has_alpha": im.mode in ("RGBA", "LA") or "transparency" in im.info,
                }
            )
    distinct = sorted({tuple(i["size"]) for i in items})
    return {
        "path": str(target),
        "count": len(items),
        "distinct_sizes": [list(s) for s in distinct],
        "uniform": len(distinct) == 1,
        "items": items if args.verbose else items[:5],
    }


def cmd_composite(args: argparse.Namespace) -> dict:
    return composite_masked_edit(
        Path(args.original),
        Path(args.edited),
        Path(args.mask),
        Path(args.output),
        feather=args.feather,
        invert_mask=args.invert_mask,
    )


def cmd_extract(args: argparse.Namespace) -> dict:
    return extract_frames(
        Path(args.video), Path(args.output_dir), count=args.count, prefix=args.prefix
    )


def cmd_select_loop(args: argparse.Namespace) -> dict:
    return analyze_loop(
        Path(args.frames_dir),
        length=args.length,
        top=args.top,
        report_path=Path(args.report) if args.report else None,
    )


def cmd_preview_loop(args: argparse.Namespace) -> dict:
    return write_preview(
        Path(args.frames_dir),
        Path(args.output),
        start=args.start,
        length=args.length,
        fps=args.fps,
        max_size=args.max_size,
    )


def cmd_normalize(args: argparse.Namespace) -> dict:
    return normalize_frames(
        Path(args.frames_dir),
        Path(args.output_dir),
        cell=args.cell,
        mode=args.mode,
        background=args.background,
        prefix=args.prefix,
        start=args.start,
        length=args.length,
    )


def cmd_pack(args: argparse.Namespace) -> dict:
    metadata = parse_meta(args.meta)
    if args.meta_json:
        metadata.update(json.loads(Path(args.meta_json).read_text(encoding="utf-8")))
    return pack_atlas(
        Path(args.frames_dir),
        Path(args.output),
        count=args.count,
        cell=args.cell,
        columns=args.columns,
        background=args.background,
        normalize=args.normalize,
        mode=args.mode,
        metadata=metadata or None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="petshop", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect", help="report size/mode/alpha for an image or a frame directory")
    p.add_argument("path")
    p.add_argument("--verbose", action="store_true", help="list every file, not just the first 5")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser(
        "composite",
        help="merge a masked edit over the original so pixels outside the mask are preserved",
    )
    p.add_argument("--original", required=True)
    p.add_argument("--edited", required=True, help="model output for the masked region")
    p.add_argument("--mask", required=True, help="black/white mask; white = edited area")
    p.add_argument("--output", required=True)
    p.add_argument("--feather", type=float, default=0.0, help="gaussian blur radius on mask edges")
    p.add_argument("--invert-mask", action="store_true", help="use if white marks the keep area")
    p.set_defaults(func=cmd_composite)

    p = sub.add_parser("extract-frames", help="decode a generated video into PNG frames")
    p.add_argument("--video", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--count", type=int, default=None, help="evenly sample this many frames")
    p.add_argument("--prefix", default="frame")
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("select-loop", help="rank loop start points by wrap-seam difference")
    p.add_argument("frames_dir")
    p.add_argument("--length", type=int, default=DEFAULT_FRAMES)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--report", default=None, help="write the ranking to this JSON file")
    p.set_defaults(func=cmd_select_loop)

    p = sub.add_parser("preview-loop", help="write an animated preview of a chosen frame range")
    p.add_argument("frames_dir")
    p.add_argument("--output", required=True, help=".webp or .gif")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--length", type=int, default=DEFAULT_FRAMES)
    p.add_argument("--fps", type=float, default=12.0)
    p.add_argument("--max-size", type=int, default=480)
    p.set_defaults(func=cmd_preview_loop)

    p = sub.add_parser("normalize", help=f"resize/pad frames to a square cell ({DEFAULT_CELL}px)")
    p.add_argument("frames_dir")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--cell", type=int, default=DEFAULT_CELL)
    p.add_argument("--mode", default="pad", choices=("pad", "cover", "stretch"))
    p.add_argument("--background", default="transparent")
    p.add_argument("--prefix", default="cell")
    p.add_argument("--start", type=int, default=0, help="first frame of the loop chosen by select-loop")
    p.add_argument("--length", type=int, default=None, help=f"frames to keep (e.g. {DEFAULT_FRAMES})")
    p.set_defaults(func=cmd_normalize)

    p = sub.add_parser("pack-atlas", help=f"pack {DEFAULT_FRAMES} cells into a sprite sheet")
    p.add_argument("frames_dir")
    p.add_argument("--output", required=True)
    p.add_argument("--count", type=int, default=DEFAULT_FRAMES)
    p.add_argument("--cell", type=int, default=DEFAULT_CELL)
    p.add_argument("--columns", type=int, default=None, help="default: ceil(sqrt(count))")
    p.add_argument("--background", default="transparent")
    p.add_argument("--normalize", action="store_true", help="normalize cells while packing")
    p.add_argument("--mode", default="pad", choices=("pad", "cover", "stretch"))
    p.add_argument("--meta", action="append", help="key=value recorded in the sheet JSON")
    p.add_argument("--meta-json", default=None, help="JSON file merged into the sheet metadata")
    p.set_defaults(func=cmd_pack)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _emit(args.func(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
