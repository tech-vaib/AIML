resource "google_container_node_pool" "spot_gpu_pool" {
  count      = var.enable_spot_gpu_pool ? 1 : 0
  name       = "spot-gpu"
  cluster    = var.cluster_name
  location   = var.region

  autoscaling {
    min_node_count = 0
    max_node_count = var.spot_gpu_max_nodes
  }

  node_config {
    preemptible = true
    machine_type = "g2-standard-8"

    labels = {
      role = "spot-gpu"
    }

    taint {
      key    = "spot-gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}
