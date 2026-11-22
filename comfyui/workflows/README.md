# ComfyUI workflows

Place exported API/UI workflow JSON files in this directory. Initial intended flows:

1. Whole-image edit: image + prompt -> RunPod job -> preview.
2. Mask edit: image + mask + prompt -> RunPod inpaint job -> composite outside mask from original -> preview.
3. Image-to-video: source/keyframe image(s) + motion prompt -> RunPod job -> video preview.

These are workflow goals, not yet executable graphs. Add a workflow JSON only after matching it to a selected worker image, model, and request schema. Never store credentials in workflow JSON.
