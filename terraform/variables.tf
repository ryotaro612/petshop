variable "endpoint_name" {
  description = "Name of the RunPod Serverless endpoint."
  type        = string
  default     = "petshop-comfyui"
}

variable "worker_image" {
  description = "Published image for a RunPod Serverless worker that executes the chosen ComfyUI workflow."
  type        = string
  default     = "CHANGE_ME"
}

variable "gpu_pool_ids" {
  description = "RunPod Serverless GPU pool IDs supported by the selected workflow."
  type        = list(string)
  default     = ["ADA_24"]
}

variable "gpu_count" {
  description = "GPUs per worker. Validate model VRAM requirements before increasing."
  type        = number
  default     = 1
}

variable "workers_min" {
  description = "Minimum warm workers. Zero avoids idle GPU worker compute charges but can increase cold starts."
  type        = number
  default     = 0
}

variable "workers_max" {
  description = "Maximum workers allowed for this endpoint."
  type        = number
  default     = 1
}

variable "idle_timeout_seconds" {
  description = "Seconds before an idle worker is scaled down."
  type        = number
  default     = 5
}

variable "execution_timeout_seconds" {
  description = "Maximum duration for a single generation job."
  type        = number
  default     = 900
}

variable "container_disk_gb" {
  description = "Worker container disk capacity. Model cache/network volume is not configured in this starter."
  type        = number
  default     = 50
}
