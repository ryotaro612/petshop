resource "runpod_template" "worker" {
  name          = "${var.endpoint_name}-worker"
  image         = var.worker_image
  serverless    = true
  disk          = var.container_disk_gb
  start_ssh     = false
  start_jupyter = false
}

resource "runpod_serverless_endpoint" "petshop" {
  name          = var.endpoint_name
  template_id   = runpod_template.worker.id
  endpoint_type = "QUEUE"
  gpu_pools     = var.gpu_pool_ids
  gpu_count     = var.gpu_count
  scaling_type  = "QUEUE_DELAY"
  scaling_value = 4
  workers_min   = var.workers_min
  workers_max   = var.workers_max
  idle_timeout  = var.idle_timeout_seconds
  timeout       = var.execution_timeout_seconds * 1000
}
