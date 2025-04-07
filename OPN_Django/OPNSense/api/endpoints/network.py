from typing import List, Dict, Any, Optional
from ninja import Router
from ninja.pagination import paginate
from django.http import HttpRequest

from OPNSense.api.models.network import (
    InterfaceCreate, InterfaceUpdate, InterfaceOut,
    VlanCreate, VlanUpdate, VlanOut
)

# Import configuration manager
from OPNSense.services.config_manager import OPNsenseConfigService

# Create router
router = Router(tags=["Network"])

# Initialize service
config_service = OPNsenseConfigService()


# Interface endpoints
@router.get("/interfaces", response=List[InterfaceOut])
def list_interfaces(request: HttpRequest):
    """Get all network interfaces."""
    return config_service.get_interfaces()


@router.get("/interfaces/{name}", response=InterfaceOut)
def get_interface(request: HttpRequest, name: str):
    """Get a specific network interface by name."""
    return config_service.get_interface(name)


@router.post("/interfaces", response=InterfaceOut)
def create_interface(request: HttpRequest, data: InterfaceCreate):
    """Create a new network interface."""
    return config_service.create_interface(data)


@router.put("/interfaces/{name}", response=InterfaceOut)
def update_interface(request: HttpRequest, name: str, data: InterfaceUpdate):
    """Update an existing network interface."""
    return config_service.update_interface(name, data)


@router.delete("/interfaces/{name}", response=Dict[str, bool])
def delete_interface(request: HttpRequest, name: str):
    """Delete a network interface."""
    success = config_service.delete_interface(name)
    return {"success": success}


# VLAN endpoints
@router.get("/vlans", response=List[VlanOut])
def list_vlans(request: HttpRequest):
    """Get all VLANs."""
    return config_service.get_vlans()


@router.get("/vlans/{uuid}", response=VlanOut)
def get_vlan(request: HttpRequest, uuid: str):
    """Get a specific VLAN by UUID."""
    return config_service.get_vlan(uuid)


@router.post("/vlans", response=VlanOut)
def create_vlan(request: HttpRequest, data: VlanCreate):
    """Create a new VLAN."""
    return config_service.create_vlan(data)


@router.put("/vlans/{uuid}", response=VlanOut)
def update_vlan(request: HttpRequest, uuid: str, data: VlanUpdate):
    """Update an existing VLAN."""
    return config_service.update_vlan(uuid, data)


@router.delete("/vlans/{uuid}", response=Dict[str, bool])
def delete_vlan(request: HttpRequest, uuid: str):
    """Delete a VLAN."""
    success = config_service.delete_vlan(uuid)
    return {"success": success}
