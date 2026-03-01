variable "env" {
  description = "Environment name"
  type        = string
}

variable "app_image" {
  description = "Docker image for app"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
}
