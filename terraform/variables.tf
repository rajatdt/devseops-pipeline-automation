variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "bondtracker"
}

variable "acr_sku" {
  description = "ACR SKU tier"
  type        = string
  default     = "Basic"
}

variable "node_vm_size" {
  description = "AKS node pool VM size"
  type        = string
  default     = "Standard_D2s_v5"
}

variable "node_count" {
  description = "Initial AKS node count"
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
