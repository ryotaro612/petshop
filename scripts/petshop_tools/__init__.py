"""Local CPU post-processing tools for the petshop pipeline.

Nothing in this package talks to RunPod or loads a generative model. It only
handles work that stays on the Mac: validating images, compositing masked
edits, turning generated video into frames, choosing a loop, normalizing each
cell to a fixed size, and packing a sprite atlas.
"""

__all__ = ["DEFAULT_CELL", "DEFAULT_FRAMES"]

DEFAULT_CELL = 780
DEFAULT_FRAMES = 56
