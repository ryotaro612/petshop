# Petshop project memory

This file captures project decisions and requirements from the conversation so future Codex sessions opened in this directory can continue without asking the user to repeat them. Read `AGENTS.md` and this file before making product or architecture decisions. Keep it updated when the user makes a new durable decision.

## Product goal

Create a local-first tool for turning an existing 2D anime-style character illustration into an editable short animation and a loopable sprite sheet. The user has an existing PNG drawn by someone else, cannot draw the art themself, and prioritizes image quality. They want to iterate by changing prompts and previewing results without waiting through long full-resolution generations for every attempt.

## Requirements from the conversation

- Edit the input image either as a whole using a prompt or only within a user-painted/masked region.
- For masked edits, preserve pixels outside the selected region by compositing the generated edit through the mask.
- Prepare or revise key poses from a single source illustration, including desired start/end poses where possible.
- Generate a short video (roughly 2-3 seconds) as an intermediate when useful; video is a means to create the animation, not the final goal.
- Convert generated video to a loopable sprite sheet with 56 frames, each frame 780x780 pixels. Include a way to preview the loop and adjust frame selection/boundaries before packing.
- Desired motion includes changing expression, bending/stretching, stepping, and taking off/putting on a hat. Text prompting alone may not reliably control a precise prop transition or exact pose; test reference/pose controls and plan for manual selection/compositing where needed.
- Iteration speed matters. Use low-cost/fast previews or intermediate resolutions before a final render where the selected workflow supports them.
- Local repeatability matters. The user wants to move away from hosted sprite-sheet generators such as AutoSprite and run the editing/management process locally as much as practical.

## Architecture decisions

- Use ComfyUI locally on the Mac first as the UI for image input, mask drawing, prompt/workflow experimentation, and preview. ComfyUI is an orchestration/UI tool, not itself a model.
- Run local ComfyUI in Docker; use CPU mode for UI/workflow authoring and keep model inference on RunPod. Do not rely on local GPU availability.
- Keep heavyweight model inference on RunPod Serverless GPU workers. The local Mac is not assumed to have a suitable GPU.
- Use Terraform to manage RunPod endpoint/template configuration so infrastructure changes are reviewable.
- Prototype workflows in ComfyUI first. Add a dedicated thin local UI only after the useful interaction pattern is known (canvas/mask, prompts, before/after comparison, job status, video/loop/sprite preview). Avoid building a complete UI before validating model workflows.
- Keep credentials in local/server-side environment variables or secret storage; never put RunPod API keys in browser JavaScript, workflow JSON, source control, or chat logs.
- RunPod was selected partly for payment/security reasons. Keep worker minimum at zero by default and be explicit about cold-start delays and storage/endpoint charges. Never run `terraform apply` without an explicit request for that apply operation.
- The current Terraform and workflow files are starter scaffolding only. The exact model, worker Docker image, API payload/storage transport, mask-aware image edit graph, and video graph still need selection and implementation. Do not present placeholders as a working generation setup.

## Workflow intent

1. Load the source illustration locally.
2. Edit the full image by prompt or paint a mask and edit only the requested area.
3. Optionally composite an edit or create/revise key poses; preserve unmasked pixels for local edits.
4. Submit only inference work to RunPod, preferably async for longer video jobs; poll for status and retrieve outputs.
5. Preview generated image/video locally and compare iterations.
6. Extract 56 frames, select/adjust a loopable interval, preview seam behavior, normalize each cell to 780x780 (preserving aspect ratio with padding/cropping as configured), and pack the atlas.
7. Save prompt, seed, workflow/version, and chosen frame metadata alongside outputs to make iterations reproducible.

## Local post-processing decisions

- Local post-processing lives in `scripts/` as a `petshop` CLI (package `petshop_tools`), run with `uv run --project scripts petshop <command>`. `uv` manages the interpreter and dependencies so the Mac needs no global Python packages.
- Depend on `imageio-ffmpeg` rather than a system ffmpeg, so video decoding works on a clean Mac; a system ffmpeg is used when present.
- Masked-edit safety is enforced locally in `composite`, not trusted to the model: the result is recomposited through the mask and the original alpha channel is restored. With the default `--feather 0` the pixels outside the mask are bit-identical to the original.
- Loop selection is a ranking aid, not a decision: `select-loop` scores the wrap seam on downscaled grayscale frames and also reports `mean_motion`, because a nearly static window scores well for the wrong reason. The user confirms with `preview-loop`.
- Sprite sheet defaults: 56 frames, 780x780 cells, 8 columns x 7 rows (6240x5460), transparent background, with a sidecar `<sheet>.json` recording frame order, layout, and any `--meta key=value` (prompt, seed, workflow) for reproducibility.
- Frame normalization defaults to `pad` (preserve aspect ratio, pad to square); `cover` (center crop) and `stretch` are available.

## Current repository state

The repository was initially empty except for `.git`. A starter README, agent instructions, Terraform endpoint/template configuration, a Docker ComfyUI setup, and workflow notes were created. No RunPod resources have been deployed.

Implemented and verified: the `scripts/` local post-processing CLI (inspect, composite, extract-frames, select-loop, preview-loop, normalize, pack-atlas), exercised end to end on synthetic fixtures.

Still unimplemented, because each depends on a model/worker choice the user has not made: the worker Docker image (Terraform `worker_image` is deliberately a placeholder), the RunPod request/response payload schema, image and mask upload transport, the ComfyUI custom node / client that calls RunPod, and the workflow JSON graphs under `comfyui/workflows/`. Do not present these placeholders as a working generation setup.
