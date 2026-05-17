resource "google_container_node_pool" "system_pool" {
  name       = "system-pool"
  cluster    = var.cluster_name
  location   = var.region

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = var.max_surge
    max_unavailable = var.max_unavailable
  }

  node_config {
    machine_type = var.system_pool_machine_type

    labels = {
      role = "system"
    }

    taint {
      key    = "system"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }

  node_count = var.system_pool_size
}
