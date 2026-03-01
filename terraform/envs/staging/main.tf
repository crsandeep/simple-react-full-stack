provider "aws" {
  region = "us-east-1"
}

module "network" {
  source = "../../modules/network"
  env    = var.env
}

module "ecs" {
  source     = "../../modules/ecs"
  env        = var.env
  app_image  = var.app_image
  vpc_id     = module.network.vpc_id
  subnet_ids = module.network.subnet_ids
}
