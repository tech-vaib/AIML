variable "system_pool_machine_type" {
  default = "e2-standard-4"
}

variable "system_pool_size" {
  default = 3
}

variable "cpu_pool_enabled" {
  default = true
}

variable "cpu_machine_type" {
  default = "e2-standard-8"
}

variable "cpu_min_nodes" {
  default = 2
}

variable "cpu_max_nodes" {
  default = 6
}

variable "gpu_driver_version" {
  default = "latest"
}

variable "cuda_version" {
  default = "12.2"
}

variable "max_surge" {
  default = 1
}

variable "max_unavailable" {
  default = 0
}

variable "upgrade_channel" {
  default = "REGULAR"
}

variable "maintenance_window" {
  default = "Sun:02:00"
}

variable "enable_spot_gpu_pool" {
  default = false
}

variable "spot_gpu_max_nodes" {
  default = 3
}
