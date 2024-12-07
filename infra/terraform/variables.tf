variable "subnet_id" {
  description = "subnet id"
  type        = string
  sensitive   = false
  default = "subnet-096406ee88a1e2d2e"
}

variable "vpc_id" {
  description = "Virtural Private Cloud ID"
  type        = string
  sensitive   = false
  default     = "vpc-00a6f6c0e0afb0484"
}