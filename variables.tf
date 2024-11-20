variable "subnet_id" {
  description = "subnet id"
  type        = string
  sensitive   = false
}

variable "vpc_id" {
  description = "Virtural Private Cloud ID"
  type        = string
  sensitive   = false
  default     = "vpc-00a6f6c0e0afb0484"
}

variable "db_vpc_host" {
  description = "Main Database IP in the VPC"
  type = string
  sensitive = false
}

variable "db_username" {
  description = "Main db username"
  type = string
  sensitive = true
  default = "postgres"
}

variable "db_password" {
  description = "Password of the main database"
  type = string
  sensitive = true
}