# Instructions for Claude

Read `AGENTS.md` first and follow it. This project uses ComfyUI locally for UI/workflow authoring and RunPod Serverless for GPU inference, with Terraform-managed infrastructure.

Preserve the product requirements in `README.md`: whole-image prompt editing, masked local edits with outside-mask preservation, image-to-video, loop preview, and a 56-frame sprite sheet with 780x780 cells. Do not assume local GPU inference. Do not expose credentials or apply Terraform without an explicit user request for that deployment.

Read `MEMORY.md` for the conversation-derived product requirements and architecture choices. Keep it current when durable decisions change.
