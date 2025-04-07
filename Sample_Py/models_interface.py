#!/usr/bin/env python3
"""
OPNsense Interface Models

This module provides data models for OPNsense network interfaces.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid


@dataclass
class Interface:
    """
    Represents an OPNsense network interface.
    """
    name: str  # Interface name like 'lan', 'wan', 'opt1'
    if_name: str  # Physical interface name like 'igc0'
    description: str = ""
    ipaddr: str = "dhcp"  # IP address or "dhcp"
    subnet: Optional[int] = None  # Subnet mask bits (e.g., 24 for /24)
    enabled: bool = True
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Additional fields
    gateway: str = ""
    spoofmac: str = ""
    mtu: Optional[int] = None
    media: str = ""
    mediaopt: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the interface to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of interface properties
        """
        result = {
            "if": self.if_name,
            "descr": self.description,
        }
        
        if self.enabled:
            result["enable"] = "1"
        
        if self.ipaddr:
            result["ipaddr"] = self.ipaddr
            
        if self.subnet is not None:
            result["subnet"] = str(self.subnet)
            
        if self.gateway:
            result["gateway"] = self.gateway
            
        if self.spoofmac:
            result["spoofmac"] = self.spoofmac
            
        if self.mtu is not None:
            result["mtu"] = str(self.mtu)
            
        if self.media:
            result["media"] = self.media
            
        if self.mediaopt:
            result["mediaopt"] = self.mediaopt
            
        return result
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'Interface':
        """
        Create an Interface object from a dictionary.
        
        Args:
            name: The interface name (e.g., 'lan', 'wan', 'opt1')
            data: Dictionary of interface properties
            
        Returns:
            Interface object
        """
        return cls(
            name=name,
            if_name=data.get("if", ""),
            description=data.get("descr", ""),
            ipaddr=data.get("ipaddr", "dhcp"),
            subnet=int(data.get("subnet")) if data.get("subnet") else None,
            enabled=data.get("enable") == "1",
            gateway=data.get("gateway", ""),
            spoofmac=data.get("spoofmac", ""),
            mtu=int(data.get("mtu")) if data.get("mtu") else None,
            media=data.get("media", ""),
            mediaopt=data.get("mediaopt", "")
        )


@dataclass
class VLANInterface:
    """
    Represents a VLAN interface in OPNsense.
    """
    parent_if: str  # Parent interface (e.g., 'igc0')
    vlan_tag: int  # VLAN ID (1-4094)
    description: str = ""
    pcp: int = 0  # Priority Code Point
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def vlanif(self) -> str:
        """
        Get the VLAN interface name.
        
        Returns:
            VLAN interface name (e.g., 'igc0_vlan10')
        """
        return f"{self.parent_if}_vlan{self.vlan_tag}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the VLAN interface to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of VLAN interface properties
        """
        return {
            "if": self.parent_if,
            "tag": str(self.vlan_tag),
            "pcp": str(self.pcp),
            "descr": self.description,
            "vlanif": self.vlanif,
            "proto": ""  # This field is typically empty
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VLANInterface':
        """
        Create a VLANInterface object from a dictionary.
        
        Args:
            data: Dictionary of VLAN interface properties
            
        Returns:
            VLANInterface object
        """
        return cls(
            parent_if=data.get("if", ""),
            vlan_tag=int(data.get("tag", 0)),
            description=data.get("descr", ""),
            pcp=int(data.get("pcp", 0)),
            uuid=data.get("uuid", str(uuid.uuid4()))
        )