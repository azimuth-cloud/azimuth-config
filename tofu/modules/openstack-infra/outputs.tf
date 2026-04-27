output "node_id" {
  description = "OpenStack instance ID of the node"
  value       = openstack_compute_instance_v2.node.id
}

output "internal_ip" {
  description = "Internal IP address of the node"
  value       = openstack_networking_port_v2.internal.all_fixed_ips[0]
}

output "external_ip" {
  description = "Externally reachable IP (floating IP or provisioning network IP)"
  value = (
    var.provisioning_network_id != "" ? openstack_networking_port_v2.provisioning[0].all_fixed_ips[0] :
    var.use_floatingip && var.fixed_floatingip != "" ? var.fixed_floatingip :
    var.use_floatingip ? openstack_networking_floatingip_v2.this[0].address :
    openstack_networking_port_v2.internal.all_fixed_ips[0]
  )
}

output "network_id" {
  description = "ID of the internal network (created or pre-existing)"
  value       = var.network_id != "" ? var.network_id : openstack_networking_network_v2.internal[0].id
}

output "data_volume_device" {
  description = "Block device path of the attached data volume"
  value       = openstack_compute_volume_attach_v2.data.device
}
