from typing import List, Dict, Any, Optional
from ninja import Router
from ninja.pagination import paginate
from django.http import HttpRequest

from OPNSense.api.models.firewall import (
    FirewallRuleCreate, FirewallRuleUpdate, FirewallRuleOut,
    PortForwardCreate, PortForwardUpdate, PortForwardOut
)

# Import configuration manager
from OPNSense.services.config_manager import OPNsenseConfigService

# Create router
router = Router(tags=["Firewall"])

# Initialize service
config_service = OPNsenseConfigService()


# Firewall rule endpoints
@router.get("/rules", response=List[FirewallRuleOut])
def list_firewall_rules(request: HttpRequest, interface: Optional[str] = None):
    """Get all firewall rules, optionally filtered by interface."""
    return config_service.get_firewall_rules(interface)


@router.get("/rules/{uuid}", response=FirewallRuleOut)
def get_firewall_rule(request: HttpRequest, uuid: str):
    """Get a specific firewall rule by UUID."""
    return config_service.get_firewall_rule(uuid)


@router.post("/rules", response=FirewallRuleOut)
def create_firewall_rule(request: HttpRequest, data: FirewallRuleCreate):
    """Create a new firewall rule."""
    return config_service.create_firewall_rule(data)


@router.put("/rules/{uuid}", response=FirewallRuleOut)
def update_firewall_rule(request: HttpRequest, uuid: str, data: FirewallRuleUpdate):
    """Update an existing firewall rule."""
    return config_service.update_firewall_rule(uuid, data)


@router.delete("/rules/{uuid}", response=Dict[str, bool])
def delete_firewall_rule(request: HttpRequest, uuid: str):
    """Delete a firewall rule."""
    success = config_service.delete_firewall_rule(uuid)
    return {"success": success}


# Port forwarding endpoints
@router.get("/port-forwards", response=List[PortForwardOut])
def list_port_forwards(request: HttpRequest, interface: Optional[str] = None):
    """Get all port forwarding rules, optionally filtered by interface."""
    return config_service.get_port_forwards(interface)


@router.get("/port-forwards/{uuid}", response=PortForwardOut)
def get_port_forward(request: HttpRequest, uuid: str):
    """Get a specific port forwarding rule by UUID."""
    return config_service.get_port_forward(uuid)


@router.post("/port-forwards", response=PortForwardOut)
def create_port_forward(request: HttpRequest, data: PortForwardCreate):
    """Create a new port forwarding rule."""
    return config_service.create_port_forward(data)


@router.put("/port-forwards/{uuid}", response=PortForwardOut)
def update_port_forward(request: HttpRequest, uuid: str, data: PortForwardUpdate):
    """Update an existing port forwarding rule."""
    return config_service.update_port_forward(uuid, data)


@router.delete("/port-forwards/{uuid}", response=Dict[str, bool])
def delete_port_forward(request: HttpRequest, uuid: str):
    """Delete a port forwarding rule."""
    success = config_service.delete_port_forward(uuid)
    return {"success": success}


# Firewall aliases
@router.get("/aliases", response=List[Dict[str, Any]])
def list_aliases(request: HttpRequest, type: Optional[str] = None):
    """Get all firewall aliases, optionally filtered by type."""
    return config_service.get_aliases(type)


# Apply changes endpoint
@router.post("/apply", response=Dict[str, Any])
def apply_firewall_changes(request: HttpRequest):
    """Apply all pending firewall changes."""
    return config_service.apply_firewall_changes()
