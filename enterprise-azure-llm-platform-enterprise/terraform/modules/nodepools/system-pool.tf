resource "azurerm_kubernetes_cluster_node_pool" "system_pool" {
  name                  = "system"
  kubernetes_cluster_id = var.cluster_id
  vm_size               = var.system_pool_vm_size
  node_count            = var.system_pool_count
  mode                  = "System"

  upgrade_settings {
    max_surge = var.max_surge
  }

  node_labels = {
    role = "system"
  }
}
