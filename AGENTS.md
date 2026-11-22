# Agent instructions

## Project intent
Build a local-first illustration editing and sprite production tool. ComfyUI is initially the local workflow/UI surface; RunPod Serverless performs GPU inference; Terraform manages RunPod resources. The user prioritizes visual quality and iterative prompt edits.

## Requirements
- Support both whole-image prompt edits and mask-scoped edits.
- Preserve pixels outside a partial-edit mask by compositing the generated result over the original with the mask.
- Support image-to-video generation and later video-to-sprite-sheet processing.
- Target a loopable 56-frame sheet with 780x780 pixels per frame; allow preview and loop adjustment before packing.
- Keep the local Mac free of heavyweight model inference; do not assume a local GPU.
- Keep API credentials out of browser code, workflows, README examples, and git. Use local environment variables/secrets.
- Do not silently deploy or incur RunPod charges. Terraform `apply` requires the user's explicit request for that apply action.

## Implementation
- Keep model-specific workflow details configurable; do not claim a model supports masks or pose control until verified.
- Store portable ComfyUI workflows under `comfyui/workflows/`.
- Prefer clear stages: input validation/upload, RunPod job submission, result retrieval, local post-processing, preview/export.
- Document any temporary limitation in README.
- Do not commit images, videos, masks, model weights, `.env`, Terraform state, or `terraform.tfvars`.

## Conversation continuity
- Read `MEMORY.md` at the start of work. It records durable requirements and decisions from earlier discussion so the user does not need to repeat them.
- If the user gives a durable new preference or changes a project decision, update `MEMORY.md` and the relevant implementation docs.
