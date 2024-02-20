locals {
  create_vcn      = var.vcn_strategy == "Create New VCN" ? 1 : 0
  vcn_id          = local.create_vcn == 0 ? var.existing_vcn_id : try(oci_core_vcn.vcn[0].id, "VCN_DATA_MISSING")
  create_inet_gw  = (var.vcn_strategy == "Create New VCN" && var.subnet_type == "Public") ? 1 : 0
  create_nat_gw   = (var.vcn_strategy == "Create New VCN" && var.subnet_type == "Private") ? 1 : 0
  create_nsg_rule = (var.vcn_strategy == "Create New VCN" && var.source_cidr != "") ? 1 : 0
}