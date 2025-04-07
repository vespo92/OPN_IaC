from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, IPvAnyAddress, validator


class RuleAction(str, Enum):
    """Firewall rule action."""
    PASS = "pass"
    BLOCK = "block"
    REJECT = "reject"


class Protocol(str, Enum):
    """Network protocol for firewall rules."""
    ANY = "any"
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ESP = "esp"
    AH = "ah"
    GRE = "gre"


class IPProtocol(str, Enum):
    """IP protocol version."""
    INET = "inet"  # IPv4
    INET6 = "inet6"  # IPv6
    BOTH = "inet46"  # Both IPv4 and IPv6


class FirewallEndpoint(BaseModel):
    """Endpoint (source or destination) for a firewall rule."""
    network: Optional[str] = Field(None, description="Network name or address (e.g., 'lan', '192.168.1.0/24')")
    address: Optional[str] = Field(None, description="IP address or hostname")
    port: Optional[str] = Field(None, description="Port number or range (e.g., '80', '1000:2000')")
    any: bool = Field(False, description="Match any address")
    
    @validator('port')
    def validate_port(cls, v):
        if v is not None:
            if ':' in v:
                start, end = v.split(':')
                if not start.isdigit() or not end.isdigit():
                    raise ValueError('Port range must contain only digits')
                if int(start) < 1 or int(start) > 65535 or int(end) < 1 or int(end) > 65535:
                    raise ValueError('Port numbers must be between 1 and 65535')
                if int(start) > int(end):
                    raise ValueError('Starting port must be less than ending port')
            elif not v.isdigit():
                raise ValueError('Port must be a number')
            elif int(v) < 1 or int(v) > 65535:
                raise ValueError('Port must be between 1 and 65535')
        return v


class FirewallRuleBase(BaseModel):
    """Base model for firewall rules."""
    type: RuleAction = Field(..., description="Rule action (pass, block, reject)")
    interface: str = Field(..., description="Interface name")
    ipprotocol: IPProtocol = Field(IPProtocol.INET, description="IP protocol version")
    protocol: Protocol = Field(Protocol.ANY, description="Network protocol")
    source: FirewallEndpoint = Field(..., description="Source endpoint")
    destination: FirewallEndpoint = Field(..., description="Destination endpoint")
    description: str = Field("", description="Rule description")
    
    # Optional fields
    direction: str = Field("in", description="Traffic direction (in, out)")
    statetype: str = Field("keep state", description="State type")
    gateway: str = Field("", description="Gateway to use")
    quick: bool = Field(True, description="Quick rule processing")
    disabled: bool = Field(False, description="Whether the rule is disabled")


class FirewallRuleCreate(FirewallRuleBase):
    """Model for creating a new firewall rule."""
    pass


class FirewallRuleUpdate(FirewallRuleBase):
    """Model for updating an existing firewall rule."""
    type: Optional[RuleAction] = None
    interface: Optional[str] = None
    ipprotocol: Optional[IPProtocol] = None
    protocol: Optional[Protocol] = None
    source: Optional[FirewallEndpoint] = None
    destination: Optional[FirewallEndpoint] = None
    description: Optional[str] = None
    direction: Optional[str] = None
    statetype: Optional[str] = None
    gateway: Optional[str] = None
    quick: Optional[bool] = None
    disabled: Optional[bool] = None


class FirewallRuleOut(FirewallRuleBase):
    """Model for firewall rule output."""
    uuid: str = Field(..., description="UUID of the rule")


class PortForwardBase(BaseModel):
    """Base model for port forwarding rules."""
    interface: str = Field(..., description="WAN interface name")
    protocol: Protocol = Field(..., description="Network protocol")
    src_port: str = Field(..., description="External port (WAN)")
    dst_ip: str = Field(..., description="Internal IP address (LAN)")
    dst_port: str = Field(..., description="Internal port (LAN)")
    description: str = Field("", description="Rule description")
    
    # Optional fields
    src_ip: Optional[str] = Field(None, description="External IP address restriction")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    
    @validator('src_port', 'dst_port')
    def validate_port(cls, v):
        if ':' in v:
            start, end = v.split(':')
            if not start.isdigit() or not end.isdigit():
                raise ValueError('Port range must contain only digits')
            if int(start) < 1 or int(start) > 65535 or int(end) < 1 or int(end) > 65535:
                raise ValueError('Port numbers must be between 1 and 65535')
            if int(start) > int(end):
                raise ValueError('Starting port must be less than ending port')
        elif not v.isdigit():
            raise ValueError('Port must be a number')
        elif int(v) < 1 or int(v) > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class PortForwardCreate(PortForwardBase):
    """Model for creating a new port forwarding rule."""
    pass


class PortForwardUpdate(PortForwardBase):
    """Model for updating an existing port forwarding rule."""
    interface: Optional[str] = None
    protocol: Optional[Protocol] = None
    src_port: Optional[str] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[str] = None
    description: Optional[str] = None
    src_ip: Optional[str] = None
    enabled: Optional[bool] = None


class PortForwardOut(PortForwardBase):
    """Model for port forwarding rule output."""
    uuid: str = Field(..., description="UUID of the rule")
