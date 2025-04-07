from typing import Optional, List
from pydantic import BaseModel, Field, IPvAnyAddress, constr, validator
import re


class InterfaceBase(BaseModel):
    """Base model for OPNsense network interfaces."""
    name: str = Field(..., description="Interface name like 'lan', 'wan', 'opt1'")
    if_name: str = Field(..., description="Physical interface name like 'igc0'")
    description: str = Field("", description="Description of the interface")
    ipaddr: str = Field("dhcp", description="IP address or 'dhcp'")
    subnet: Optional[int] = Field(None, description="Subnet mask bits (e.g., 24 for /24)")
    enabled: bool = Field(True, description="Whether the interface is enabled")
    
    # Additional fields
    gateway: str = Field("", description="Gateway for the interface")
    spoofmac: str = Field("", description="MAC address to spoof")
    mtu: Optional[int] = Field(None, description="MTU for the interface")
    media: str = Field("", description="Media type for the interface")
    mediaopt: str = Field("", description="Media options for the interface")
    
    @validator('subnet')
    def validate_subnet(cls, v):
        if v is not None and (v < 0 or v > 32):
            raise ValueError('Subnet must be between 0 and 32')
        return v
    
    @validator('ipaddr')
    def validate_ipaddr(cls, v):
        if v != "dhcp" and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            raise ValueError('IP address must be in format x.x.x.x or "dhcp"')
        return v


class InterfaceCreate(InterfaceBase):
    """Model for creating a new interface."""
    pass


class InterfaceUpdate(InterfaceBase):
    """Model for updating an existing interface."""
    name: Optional[str] = None
    if_name: Optional[str] = None
    ipaddr: Optional[str] = None


class InterfaceOut(InterfaceBase):
    """Model for interface output."""
    uuid: str = Field(..., description="UUID of the interface")


class VlanBase(BaseModel):
    """Base model for VLAN interfaces."""
    parent_if: str = Field(..., description="Parent interface (e.g., 'igc0')")
    vlan_tag: int = Field(..., description="VLAN ID (1-4094)")
    description: str = Field("", description="Description of the VLAN")
    pcp: int = Field(0, description="Priority Code Point")
    
    @validator('vlan_tag')
    def validate_vlan_tag(cls, v):
        if v < 1 or v > 4094:
            raise ValueError('VLAN tag must be between 1 and 4094')
        return v
    
    @validator('pcp')
    def validate_pcp(cls, v):
        if v < 0 or v > 7:
            raise ValueError('PCP must be between 0 and 7')
        return v


class VlanCreate(VlanBase):
    """Model for creating a new VLAN."""
    pass


class VlanUpdate(VlanBase):
    """Model for updating an existing VLAN."""
    parent_if: Optional[str] = None
    vlan_tag: Optional[int] = None
    description: Optional[str] = None
    pcp: Optional[int] = None


class VlanOut(VlanBase):
    """Model for VLAN output."""
    uuid: str = Field(..., description="UUID of the VLAN")
    vlanif: str = Field(..., description="VLAN interface name (e.g., 'igc0_vlan10')")
