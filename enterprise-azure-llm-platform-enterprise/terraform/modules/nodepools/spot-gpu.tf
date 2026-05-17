resource "azurerm_kubernetes_cluster_node_pool" "spot_gpu" {
  count                 = var.enable_spot_gpu_pool ? 1 : 0
  name                  = "spotgpu"
  kubernetes_cluster_id = var.cluster_id
  vm_size               = "Standard_NC24ads_A100_v4"

  auto_scaling_enabled = true
  min_count            = 0
  max_count            = var.spot_gpu_max_nodes

  priority        = "Spot"
  eviction_policy = "Delete"

  node_labels = {
    role = "spot-gpu"
  }

  node_taints = [
    "spot-gpu=true:NoSchedule"
  ]
}
