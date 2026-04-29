terraform {
  required_version = ">= 1.6"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1"
    }
  }
}

# ── Security group ────────────────────────────────────────────────────────────

resource "openstack_networking_secgroup_v2" "this" {
  name                 = var.name
  delete_default_rules = true
}

resource "openstack_networking_secgroup_rule_v2" "egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  security_group_id = openstack_networking_secgroup_v2.this.id
}

resource "openstack_networking_secgroup_rule_v2" "talos_api" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.talos_api_port
  port_range_max    = var.talos_api_port
  security_group_id = openstack_networking_secgroup_v2.this.id
}

resource "openstack_networking_secgroup_rule_v2" "kubernetes_api" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 6443
  port_range_max    = 6443
  security_group_id = openstack_networking_secgroup_v2.this.id
}

resource "openstack_networking_secgroup_rule_v2" "extra" {
  for_each = { for r in var.exposed_port_ranges : r.name => r }

  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = each.value.min
  port_range_max    = each.value.max
  security_group_id = openstack_networking_secgroup_v2.this.id
}

# ── Network (created when no pre-existing network is given) ──────────────────

resource "openstack_networking_network_v2" "internal" {
  count          = var.network_id == "" ? 1 : 0
  name           = var.name
  admin_state_up = true
  mtu = var.network_mtu != 0 ? var.network_mtu : null
}

resource "openstack_networking_subnet_v2" "internal" {
  count      = var.network_id == "" ? 1 : 0
  name       = var.name
  network_id = openstack_networking_network_v2.internal[0].id
  cidr       = var.network_cidr
  ip_version = 4
  dns_nameservers = length(var.network_dns_nameservers) > 0 ? var.network_dns_nameservers : null
}

resource "openstack_networking_router_v2" "this" {
  count               = var.network_id == "" ? 1 : 0
  name                = var.name
  admin_state_up      = true
  external_network_id = var.external_network_id
}

resource "openstack_networking_router_interface_v2" "this" {
  count     = var.network_id == "" ? 1 : 0
  router_id = openstack_networking_router_v2.this[0].id
  subnet_id = openstack_networking_subnet_v2.internal[0].id
}

# ── Ports ─────────────────────────────────────────────────────────────────────

resource "openstack_networking_port_v2" "provisioning" {
  count          = var.provisioning_network_id != "" ? 1 : 0
  admin_state_up = true
  network_id     = var.provisioning_network_id
  security_group_ids = [openstack_networking_secgroup_v2.this.id]
}

resource "openstack_networking_port_v2" "internal" {
  admin_state_up     = true
  network_id         = var.network_id != "" ? var.network_id : openstack_networking_network_v2.internal[0].id
  security_group_ids = [openstack_networking_secgroup_v2.this.id]

  dynamic "fixed_ip" {
    for_each = var.network_id == "" ? [1] : []
    content { subnet_id = openstack_networking_subnet_v2.internal[0].id }
  }
}

# ── Compute instance ──────────────────────────────────────────────────────────

resource "openstack_compute_instance_v2" "node" {
  name      = var.machine_name != "" ? var.machine_name : var.name
  flavor_id = var.flavor_id != "" ? var.flavor_id : null
  flavor_name = var.flavor_id == "" ? var.flavor_name : null

  dynamic "block_device" {
    for_each = var.root_volume_enabled ? [1] : []
    content {
      uuid                  = var.image_id
      source_type           = "image"
      volume_size           = var.root_volume_size
      volume_type           = var.root_volume_type != "" ? var.root_volume_type : null
      boot_index            = 0
      destination_type      = "volume"
      delete_on_termination = true
    }
  }

  image_id = var.root_volume_enabled ? null : var.image_id

  # Talos uses its own API — no SSH keypair needed
  user_data = var.user_data

  dynamic "network" {
    for_each = var.provisioning_network_id != "" ? [1] : []
    content { port = openstack_networking_port_v2.provisioning[0].id }
  }

  network {
    port = openstack_networking_port_v2.internal.id
  }

  lifecycle {
    # Talos machine config is injected once at creation; changes require a new VM
    ignore_changes = [user_data]
  }
}

# ── Data volume ───────────────────────────────────────────────────────────────

resource "openstack_blockstorage_volume_v3" "data" {
  name                 = "${var.name}-data"
  size                 = var.data_volume_size
  volume_type          = var.data_volume_type != "" ? var.data_volume_type : null
  enable_online_resize = true
}

resource "openstack_compute_volume_attach_v2" "data" {
  instance_id = openstack_compute_instance_v2.node.id
  volume_id   = openstack_blockstorage_volume_v3.data.id
}

# ── Floating IP ───────────────────────────────────────────────────────────────

data "openstack_networking_network_v2" "external" {
 #count      = var.use_floatingip && var.provisioning_network_id == "" && var.fixed_floatingip == "" && var.floatingip_pool == "" ? 1 : 0
  count = 1
  network_id = var.external_network_id
}

resource "openstack_networking_floatingip_v2" "this" {
  #count = var.use_floatingip && var.provisioning_network_id == "" && var.fixed_floatingip == "" ? 1 : 0
  count = 1
  pool  = var.floatingip_pool != "" ? var.floatingip_pool : data.openstack_networking_network_v2.external[0].name
}

resource "openstack_networking_floatingip_associate_v2" "this" {
  #count       = var.use_floatingip && var.provisioning_network_id == "" ? 1 : 0
  count = 1
  floating_ip = var.fixed_floatingip != "" ? var.fixed_floatingip : openstack_networking_floatingip_v2.this[0].address
  port_id     = openstack_networking_port_v2.internal.id
}
