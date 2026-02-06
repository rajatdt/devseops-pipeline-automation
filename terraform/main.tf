locals {
  resource_prefix = "${var.prefix}-${var.environment}"
}

module "resource_group" {
  source   = "./modules/resource_group"
  name     = "${local.resource_prefix}-rg"
  location = var.location
}

module "networking" {
  source              = "./modules/networking"
  name                = local.resource_prefix
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
}

module "acr" {
  source              = "./modules/acr"
  name                = replace(var.prefix, "-", "")
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  sku                 = var.acr_sku
}

module "aks" {
  source              = "./modules/aks"
  name                = local.resource_prefix
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  subnet_id           = module.networking.subnet_id
  acr_id              = module.acr.id
  node_vm_size        = var.node_vm_size
  node_count          = var.node_count
  min_count           = var.min_count
  max_count           = var.max_count
}
