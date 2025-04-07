from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class PortMapping(BaseModel):
    """Port mapping for a container."""
    host_port: int = Field(..., description="Host port")
    container_port: int = Field(..., description="Container port")
    protocol: str = Field("tcp", description="Protocol (tcp, udp)")
    
    @validator('host_port', 'container_port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('protocol')
    def validate_protocol(cls, v):
        if v not in ['tcp', 'udp', 'both']:
            raise ValueError('Protocol must be tcp, udp, or both')
        return v


class ContainerNetworkConfig(BaseModel):
    """Network configuration for a container."""
    vlan_id: int = Field(..., description="VLAN ID")
    ip_address: str = Field(..., description="IP address for the container")
    mac_address: str = Field(..., description="MAC address for the container")
    parent_interface: str = Field("igc2", description="Parent interface")
    allow_internet: bool = Field(True, description="Whether to allow internet access")
    
    @validator('vlan_id')
    def validate_vlan_id(cls, v):
        if v < 1 or v > 4094:
            raise ValueError('VLAN ID must be between 1 and 4094')
        return v
    
    @validator('ip_address')
    def validate_ip(cls, v):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            raise ValueError('IP address must be in format x.x.x.x')
        return v
    
    @validator('mac_address')
    def validate_mac(cls, v):
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
            raise ValueError('MAC address must be in format xx:xx:xx:xx:xx:xx')
        return v.lower()


class ContainerBase(BaseModel):
    """Base model for containers."""
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Docker image")
    network_config: ContainerNetworkConfig = Field(..., description="Network configuration")
    
    # Optional fields
    environment: Dict[str, str] = Field({}, description="Environment variables")
    ports: List[PortMapping] = Field([], description="Port mappings")
    volumes: Dict[str, str] = Field({}, description="Volume mappings (host_path:container_path)")
    restart_policy: str = Field("unless-stopped", description="Container restart policy")
    
    @validator('restart_policy')
    def validate_restart_policy(cls, v):
        valid_policies = ['no', 'always', 'on-failure', 'unless-stopped']
        if v not in valid_policies:
            raise ValueError(f'Restart policy must be one of: {", ".join(valid_policies)}')
        return v


class ContainerCreate(ContainerBase):
    """Model for creating a new container."""
    pass


class ContainerUpdate(ContainerBase):
    """Model for updating an existing container."""
    name: Optional[str] = None
    image: Optional[str] = None
    network_config: Optional[ContainerNetworkConfig] = None
    environment: Optional[Dict[str, str]] = None
    ports: Optional[List[PortMapping]] = None
    volumes: Optional[Dict[str, str]] = None
    restart_policy: Optional[str] = None


class ContainerOut(ContainerBase):
    """Model for container output."""
    id: str = Field(..., description="Container ID")
    status: str = Field(..., description="Container status")
    created_at: str = Field(..., description="Creation timestamp")
    network_info: Dict[str, Any] = Field(..., description="Network information")
