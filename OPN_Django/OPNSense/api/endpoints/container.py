from typing import List, Dict, Any, Optional
from ninja import Router
from django.http import HttpRequest
import logging

from OPNSense.api.models.container import (
    ContainerCreate, ContainerUpdate, ContainerOut,
    PortMapping, ContainerNetworkConfig
)
from OPNSense.api.models.firewall import Protocol

# Import services
from OPNSense.services.container_service import ContainerService
from OPNSense.services.deployment_service import DeploymentService

# Create router
router = Router(tags=["Containers"])

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize service
container_service = ContainerService()


# Container endpoints
@router.get("/", response=List[ContainerOut])
def list_containers(request: HttpRequest):
    """Get all containers."""
    return container_service.get_containers()


@router.get("/{name}", response=ContainerOut)
def get_container(request: HttpRequest, name: str):
    """Get a specific container by name."""
    return container_service.get_container(name)


@router.post("/", response=ContainerOut)
def create_container(request: HttpRequest, data: ContainerCreate):
    """Create a new container with network configuration."""
    return container_service.create_container(data)


@router.put("/{name}", response=ContainerOut)
def update_container(request: HttpRequest, name: str, data: ContainerUpdate):
    """Update an existing container."""
    return container_service.update_container(name, data)


@router.delete("/{name}", response=Dict[str, bool])
def delete_container(request: HttpRequest, name: str):
    """Delete a container."""
    success = container_service.delete_container(name)
    return {"success": success}


# Container actions
@router.post("/{name}/start", response=Dict[str, Any])
def start_container(request: HttpRequest, name: str):
    """Start a container."""
    return container_service.start_container(name)


@router.post("/{name}/stop", response=Dict[str, Any])
def stop_container(request: HttpRequest, name: str):
    """Stop a container."""
    return container_service.stop_container(name)


@router.post("/{name}/restart", response=Dict[str, Any])
def restart_container(request: HttpRequest, name: str):
    """Restart a container."""
    return container_service.restart_container(name)


# Port management
@router.post("/{name}/ports", response=Dict[str, Any])
def add_port(request: HttpRequest, name: str, port_mapping: PortMapping):
    """Add a port mapping to a container."""
    return container_service.add_port(name, port_mapping)


@router.delete("/{name}/ports/{host_port}/{protocol}", response=Dict[str, bool])
def remove_port(request: HttpRequest, name: str, host_port: int, protocol: Protocol):
    """Remove a port mapping from a container."""
    success = container_service.remove_port(name, host_port, protocol)
    return {"success": success}


# Network configuration
@router.put("/{name}/network", response=Dict[str, Any])
def update_network_config(request: HttpRequest, name: str, network_config: ContainerNetworkConfig):
    """Update the network configuration for a container."""
    return container_service.update_network_config(name, network_config)


# Deployment with everything
@router.post("/deploy", response=Dict[str, Any])
def deploy_container(request: HttpRequest, data: ContainerCreate):
    """
    Deploy a container with network configuration, firewall rules, and HAProxy configuration if needed.
    
    This is a high-level operation that:
    1. Creates the container
    2. Sets up network (VLAN, IP, etc.)
    3. Configures firewall rules for port mappings
    4. Sets up HAProxy for web services if needed
    """
    # Validate deployment first
    validation = DeploymentService.validate_deployment(data.dict())
    
    if not validation["valid"]:
        return {
            "success": False,
            "message": validation["message"],
            "conflicts": validation["conflicts"]
        }
    
    # Proceed with deployment
    try:
        container = container_service.deploy_container(data)
        return {
            "success": True,
            "message": f"Container {data.name} deployed successfully",
            "container": container
        }
    except Exception as e:
        logger.error(f"Failed to deploy container: {e}")
        return {
            "success": False,
            "message": f"Failed to deploy container: {str(e)}"
        }
