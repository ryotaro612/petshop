output "serverless_endpoint_id" {
  description = "RunPod endpoint ID."
  value       = runpod_serverless_endpoint.petshop.id
}

output "serverless_run_url" {
  description = "Queue endpoint URL for asynchronous jobs. Keep the API key on the local server side."
  value       = runpod_serverless_endpoint.petshop.request_urls.run
}
