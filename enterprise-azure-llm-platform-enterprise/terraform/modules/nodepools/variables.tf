variable "system_pool_vm_size" {
  default = "Standard_D4s_v5"
}

variable "system_pool_count" {
  default = 3
}

variable "cpu_pool_enabled" {
  default = true
}

variable "cpu_pool_vm_size" {
  default = "Standard_D8s_v5"
}

variable "cpu_min_nodes" {
  default = 2
}

variable "cpu_max_nodes" {
  default = 6
}

variable "enable_spot_gpu_pool" {
  default = false
}

variable "spot_gpu_max_nodes" {
  default = 3
}

variable "max_surge" {
  default = "33%"
}

variable "gpu_driver_version" {
  default = "latest"
}

variable "cuda_version" {
  default = "12.2"
}
