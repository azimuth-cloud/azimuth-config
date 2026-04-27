variable "name" {
  description = "Name prefix for all provisioned resources"
  type        = string
}

variable "external_network_id" {
  description = "ID of the OpenStack external network used for the router and floating IPs"
  type        = string
  default     = ""
}

variable "network_id" {
  description = "ID of a pre-existing internal network. If empty, a new network is created."
  type        = string
  default     = ""
}

variable "network_cidr" {
  description = "CIDR for the internal subnet (used only when network_id is empty)"
  type        = string
  default     = "192.168.100.0/24"
}

variable "network_mtu" {
  description = "MTU for the internal network. 0 means use cloud default."
  type        = number
  default     = 0
}

variable "network_dns_nameservers" {
  description = "DNS nameservers for the internal subnet"
  type        = list(string)
  default     = []
}

variable "provisioning_network_id" {
  description = "ID of an optional provisioning network (adds a second NIC)"
  type        = string
  default     = ""
}

variable "use_floatingip" {
  description = "Whether to allocate a floating IP for the node"
  type        = bool
  default     = true
}

variable "fixed_floatingip" {
  description = "A pre-allocated floating IP to associate. If empty, one is created."
  type        = string
  default     = ""
}

variable "floatingip_pool" {
  description = "Name of the floating IP pool. If empty, the external network name is used."
  type        = string
  default     = ""
}

variable "image_id" {
  description = "ID of the image to use for the node"
  type        = string
}

variable "flavor_id" {
  description = "ID of the OpenStack flavor to use"
  type        = string
  default     = ""
}

variable "flavor_name" {
  description = "Name of the OpenStack flavor (used when flavor_id is empty)"
  type        = string
  default     = ""
}

variable "root_volume_enabled" {
  description = "Boot from a Cinder volume instead of ephemeral disk"
  type        = bool
  default     = false
}

variable "root_volume_size" {
  description = "Size in GB of the root Cinder volume"
  type        = number
  default     = 40
}

variable "root_volume_type" {
  description = "Volume type for the root volume. Empty means default."
  type        = string
  default     = ""
}

variable "data_volume_size" {
  description = "Size in GB of the data volume attached to the node"
  type        = number
  default     = 100
}

variable "data_volume_type" {
  description = "Volume type for the data volume. Empty means default."
  type        = string
  default     = ""
}

variable "exposed_port_ranges" {
  description = "Extra ingress TCP port ranges to open in the security group"
  type = list(object({
    name = string
    min  = number
    max  = number
  }))
  default = []
}

variable "talos_api_port" {
  description = "Talos API port to allow in the security group"
  type        = number
  default     = 50000
}

variable "user_data" {
  description = "User data to pass to the compute instance (Talos machine config)"
  type        = string
  default     = null
}
