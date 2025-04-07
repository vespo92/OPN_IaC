from typing import List, Dict, Any, Optional
from ninja import Router
from django.http import HttpRequest

from OPNSense.api.models.dhcp import (
    DHCPConfigCreate, DHCPConfigUpdate, DHCPConfigOut,
    DHCPStaticMappingCreate, DHCPStaticMappingUpdate, DHCPStaticMappingOut
)

# Import configuration manager
from OPNSense.services.config_manager import OPNsenseConfigService

# Create router
router = Router(tags=["DHCP"])

# Initialize service
config_service = OPNsenseConfigService()


# DHCP configuration endpoints
@router.get("/configs", response=List[DHCPConfigOut])
def list_dhcp_configs(request: HttpRequest):
    """Get all DHCP configurations."""
    return config_service.get_dhcp_configs()


@router.get("/configs/{interface}", response=DHCPConfigOut)
def get_dhcp_config(request: HttpRequest, interface: str):
    """Get DHCP configuration for a specific interface."""
    return config_service.get_dhcp_config(interface)


@router.post("/configs", response=DHCPConfigOut)
def create_dhcp_config(request: HttpRequest, data: DHCPConfigCreate):
    """Create a new DHCP configuration."""
    return config_service.create_dhcp_config(data)


@router.put("/configs/{interface}", response=DHCPConfigOut)
def update_dhcp_config(request: HttpRequest, interface: str, data: DHCPConfigUpdate):
    """Update an existing DHCP configuration."""
    return config_service.update_dhcp_config(interface, data)


@router.delete("/configs/{interface}", response=Dict[str, bool])
def delete_dhcp_config(request: HttpRequest, interface: str):
    """Delete a DHCP configuration."""
    success = config_service.delete_dhcp_config(interface)
    return {"success": success}


# DHCP static mapping endpoints
@router.get("/static-mappings/{interface}", response=List[DHCPStaticMappingOut])
def list_static_mappings(request: HttpRequest, interface: str):
    """Get all static DHCP mappings for a specific interface."""
    return config_service.get_static_mappings(interface)


@router.get("/static-mappings/{interface}/{uuid}", response=DHCPStaticMappingOut)
def get_static_mapping(request: HttpRequest, interface: str, uuid: str):
    """Get a specific static DHCP mapping."""
    return config_service.get_static_mapping(interface, uuid)


@router.post("/static-mappings/{interface}", response=DHCPStaticMappingOut)
def create_static_mapping(request: HttpRequest, interface: str, data: DHCPStaticMappingCreate):
    """Create a new static DHCP mapping."""
    return config_service.create_static_mapping(interface, data)


@router.put("/static-mappings/{interface}/{uuid}", response=DHCPStaticMappingOut)
def update_static_mapping(request: HttpRequest, interface: str, uuid: str, data: DHCPStaticMappingUpdate):
    """Update an existing static DHCP mapping."""
    return config_service.update_static_mapping(interface, uuid, data)


@router.delete("/static-mappings/{interface}/{uuid}", response=Dict[str, bool])
def delete_static_mapping(request: HttpRequest, interface: str, uuid: str):
    """Delete a static DHCP mapping."""
    success = config_service.delete_static_mapping(interface, uuid)
    return {"success": success}


# DHCP leases
@router.get("/leases/{interface}", response=List[Dict[str, Any]])
def list_dhcp_leases(request: HttpRequest, interface: str):
    """Get all DHCP leases for a specific interface."""
    return config_service.get_dhcp_leases(interface)


# Apply changes endpoint
@router.post("/apply", response=Dict[str, Any])
def apply_dhcp_changes(request: HttpRequest):
    """Apply all pending DHCP changes."""
    return config_service.apply_dhcp_changes()
