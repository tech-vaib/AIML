resource "azurerm_kubernetes_cluster_node_pool" "cpu_pool" {
  count                 = var.cpu_pool_enabled ? 1 : 0
  name                  = "cpuapps"
  kubernetes_cluster_id = var.cluster_id
  vm_size               = var.cpu_pool_vm_size
  auto_scaling_enabled  = true
  min_count             = var.cpu_min_nodes
  max_count             = var.cpu_max_nodes
  mode                  = "User"

  node_labels = {
    role = "cpu-apps"
  }

  upgrade_settings {
    max_surge = var.max_surge
  }
}
