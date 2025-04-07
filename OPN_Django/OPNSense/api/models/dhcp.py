from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class DHCPRangeBase(BaseModel):
    """Base model for DHCP ranges."""
    from_addr: str = Field(..., description="Starting IP address")
    to_addr: str = Field(..., description="Ending IP address")
    
    @validator('from_addr', 'to_addr')
    def validate_ip(cls, v):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            raise ValueError('IP address must be in format x.x.x.x')
        return v


class DHCPRangeCreate(DHCPRangeBase):
    """Model for creating a new DHCP range."""
    pass


class DHCPRangeOut(DHCPRangeBase):
    """Model for DHCP range output."""
    pass


class DHCPStaticMappingBase(BaseModel):
    """Base model for static DHCP mappings."""
    mac: str = Field(..., description="MAC address of the client")
    ipaddr: str = Field(..., description="Static IP address to assign")
    hostname: str = Field(..., description="Hostname for the client")
    description: str = Field("", description="Optional description")
    
    # Optional fields
    winsserver: str = Field("", description="WINS server")
    dnsserver: str = Field("", description="DNS server")
    ntpserver: str = Field("", description="NTP server")
    
    @validator('mac')
    def validate_mac(cls, v):
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
            raise ValueError('MAC address must be in format xx:xx:xx:xx:xx:xx')
        return v.lower()
    
    @validator('ipaddr')
    def validate_ip(cls, v):
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            raise ValueError('IP address must be in format x.x.x.x')
        return v


class DHCPStaticMappingCreate(DHCPStaticMappingBase):
    """Model for creating a new static DHCP mapping."""
    pass


class DHCPStaticMappingUpdate(DHCPStaticMappingBase):
    """Model for updating an existing static DHCP mapping."""
    mac: Optional[str] = None
    ipaddr: Optional[str] = None
    hostname: Optional[str] = None
    description: Optional[str] = None
    winsserver: Optional[str] = None
    dnsserver: Optional[str] = None
    ntpserver: Optional[str] = None


class DHCPStaticMappingOut(DHCPStaticMappingBase):
    """Model for static DHCP mapping output."""
    uuid: str = Field(..., description="UUID of the mapping")


class DHCPConfigBase(BaseModel):
    """Base model for DHCP configurations."""
    interface: str = Field(..., description="Interface name (e.g., 'lan', 'opt1')")
    enabled: bool = Field(True, description="Whether DHCP is enabled")
    
    # Optional fields
    range: Optional[DHCPRangeBase] = Field(None, description="DHCP range")
    gateway: str = Field("", description="Gateway")
    dnsserver: str = Field("", description="DNS server")
    domain: str = Field("", description="Domain name")


class DHCPConfigCreate(DHCPConfigBase):
    """Model for creating a new DHCP configuration."""
    pass


class DHCPConfigUpdate(DHCPConfigBase):
    """Model for updating an existing DHCP configuration."""
    interface: Optional[str] = None
    enabled: Optional[bool] = None
    range: Optional[DHCPRangeBase] = None
    gateway: Optional[str] = None
    dnsserver: Optional[str] = None
    domain: Optional[str] = None


class DHCPConfigOut(DHCPConfigBase):
    """Model for DHCP configuration output."""
    static_mappings: List[DHCPStaticMappingOut] = Field([], description="Static DHCP mappings")
