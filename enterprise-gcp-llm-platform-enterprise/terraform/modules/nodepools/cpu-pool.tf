resource "google_container_node_pool" "cpu_pool" {
  count      = var.cpu_pool_enabled ? 1 : 0
  name       = "cpu-pool"
  cluster    = var.cluster_name
  location   = var.region

  autoscaling {
    min_node_count = var.cpu_min_nodes
    max_node_count = var.cpu_max_nodes
  }

  node_config {
    machine_type = var.cpu_machine_type

    labels = {
      role = "cpu-apps"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
