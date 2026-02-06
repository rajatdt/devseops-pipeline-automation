variable "name" {
  description = "Cluster name prefix"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for AKS nodes"
  type        = string
}

variable "acr_id" {
  description = "ACR resource ID for AcrPull role assignment"
  type        = string
}

variable "node_vm_size" {
  description = "VM size for the node pool"
  type        = string
  default     = "Standard_D2s_v5"
}

variable "node_count" {
  description = "Initial node count"
  type        = number
  default     = 1
}

variable "min_count" {
  description = "Minimum node count for autoscaler"
  type        = number
  default     = 1
}

variable "max_count" {
  description = "Maximum node count for autoscaler"
  type        = number
  default     = 3
}
