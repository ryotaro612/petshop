"""Composite a masked edit back over the original, preserving outside-mask pixels.

This is the guarantee the product requires: whatever the model returns, only
pixels inside the mask may change. Even a model that rewrites the whole canvas
is corrected here.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

from .imageio_util import load_mask, load_rgba, save_image


def composite_masked_edit(
    original_path: Path,
    edited_path: Path,
    mask_path: Path,
    output_path: Path,
    feather: float = 0.0,
    invert_mask: bool = False,
) -> dict:
    original = load_rgba(original_path)
    edited = load_rgba(edited_path)

    resized = False
    if edited.size != original.size:
        edited = edited.resize(original.size, Image.Resampling.LANCZOS)
        resized = True

    mask = load_mask(mask_path, original.size, invert=invert_mask)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))

    # Composite RGB through the mask, then restore the original alpha so a
    # model that flattens or clips transparency cannot damage the cutout.
    merged = Image.composite(edited.convert("RGB"), original.convert("RGB"), mask)
    merged = merged.convert("RGBA")
    merged.putalpha(original.getchannel("A"))

    save_image(merged, output_path)
    return {
        "output": str(output_path),
        "size": list(original.size),
        "edited_resized_to_original": resized,
        "feather": feather,
        "mask_inverted": invert_mask,
    }
