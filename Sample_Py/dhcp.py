#!/usr/bin/env python3
"""
OPNsense DHCP Models

This module provides data models for OPNsense DHCP configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid


@dataclass
class DHCPStaticMapping:
    """
    Represents a static DHCP mapping in OPNsense.
    """
    mac: str  # MAC address of the client
    ipaddr: str  # Static IP address to assign
    hostname: str  # Hostname for the client
    description: str = ""  # Optional description
    
    # Optional fields
    winsserver: str = ""
    dnsserver: str = ""
    ntpserver: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the static mapping to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of static mapping properties
        """
        result = {
            "mac": self.mac,
            "ipaddr": self.ipaddr,
            "hostname": self.hostname,
            "winsserver": self.winsserver,
            "dnsserver": self.dnsserver,
            "ntpserver": self.ntpserver
        }
        
        if self.description:
            result["descr"] = self.description
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DHCPStaticMapping':
        """
        Create a DHCPStaticMapping object from a dictionary.
        
        Args:
            data: Dictionary of static mapping properties
            
        Returns:
            DHCPStaticMapping object
        """
        return cls(
            mac=data.get("mac", ""),
            ipaddr=data.get("ipaddr", ""),
            hostname=data.get("hostname", ""),
            description=data.get("descr", ""),
            winsserver=data.get("winsserver", ""),
            dnsserver=data.get("dnsserver", ""),
            ntpserver=data.get("ntpserver", "")
        )


@dataclass
class DHCPRange:
    """
    Represents a DHCP range in OPNsense.
    """
    from_addr: str  # Starting IP address
    to_addr: str  # Ending IP address
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DHCP range to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of DHCP range properties
        """
        return {
            "from": self.from_addr,
            "to": self.to_addr
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DHCPRange':
        """
        Create a DHCPRange object from a dictionary.
        
        Args:
            data: Dictionary of DHCP range properties
            
        Returns:
            DHCPRange object
        """
        return cls(
            from_addr=data.get("from", ""),
            to_addr=data.get("to", "")
        )


@dataclass
class DHCPConfiguration:
    """
    Represents a DHCP configuration for an interface in OPNsense.
    """
    interface: str  # Interface name (e.g., 'lan', 'opt1')
    enabled: bool = True
    
    # DHCP range
    range: Optional[DHCPRange] = None
    
    # Static mappings
    staticmaps: List[DHCPStaticMapping] = field(default_factory=list)
    
    # Optional fields
    gateway: str = ""
    dnsserver: str = ""
    domain: str = ""
    
    def add_static_mapping(self, mapping: DHCPStaticMapping) -> None:
        """
        Add a static DHCP mapping.
        
        Args:
            mapping: Static mapping to add
        """
        self.staticmaps.append(mapping)
    
    def find_static_mapping_by_mac(self, mac: str) -> Optional[DHCPStaticMapping]:
        """
        Find a static mapping by MAC address.
        
        Args:
            mac: MAC address to search for
            
        Returns:
            DHCPStaticMapping if found, None otherwise
        """
        for mapping in self.staticmaps:
            if mapping.mac.lower() == mac.lower():
                return mapping
        return None
    
    def find_static_mapping_by_ip(self, ip: str) -> Optional[DHCPStaticMapping]:
        """
        Find a static mapping by IP address.
        
        Args:
            ip: IP address to search for
            
        Returns:
            DHCPStaticMapping if found, None otherwise
        """
        for mapping in self.staticmaps:
            if mapping.ipaddr == ip:
                return mapping
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DHCP configuration to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of DHCP configuration properties
        """
        result = {
            "enable": "1" if self.enabled else "0"
        }
        
        if self.range:
            result["range"] = self.range.to_dict()
            
        if self.gateway:
            result["gateway"] = self.gateway
            
        if self.dnsserver:
            result["dnsserver"] = self.dnsserver
            
        if self.domain:
            result["domain"] = self.domain
            
        # Static mappings are added separately in the XML
        
        return result
    
    @classmethod
    def from_dict(cls, interface: str, data: Dict[str, Any]) -> 'DHCPConfiguration':
        """
        Create a DHCPConfiguration object from a dictionary.
        
        Args:
            interface: Interface name
            data: Dictionary of DHCP configuration properties
            
        Returns:
            DHCPConfiguration object
        """
        # Parse DHCP range if present
        range_data = data.get("range")
        dhcp_range = None
        if range_data and isinstance(range_data, dict):
            dhcp_range = DHCPRange.from_dict(range_data)
        
        # Parse static mappings if present
        staticmaps = []
        for mapping_data in data.get("staticmap", []):
            if isinstance(mapping_data, dict):
                staticmaps.append(DHCPStaticMapping.from_dict(mapping_data))
        
        return cls(
            interface=interface,
            enabled=data.get("enable") == "1",
            range=dhcp_range,
            staticmaps=staticmaps,
            gateway=data.get("gateway", ""),
            dnsserver=data.get("dnsserver", ""),
            domain=data.get("domain", "")
        )


@dataclass
class DHCPServer:
    """
    Represents the overall DHCP server configuration in OPNsense.
    """
    configurations: Dict[str, DHCPConfiguration] = field(default_factory=dict)
    
    def add_configuration(self, config: DHCPConfiguration) -> None:
        """
        Add a DHCP configuration for an interface.
        
        Args:
            config: DHCP configuration to add
        """
        self.configurations[config.interface] = config
    
    def get_configuration(self, interface: str) -> Optional[DHCPConfiguration]:
        """
        Get the DHCP configuration for an interface.
        
        Args:
            interface: Interface name
            
        Returns:
            DHCPConfiguration if found, None otherwise
        """
        return self.configurations.get(interface)
    
    def add_static_mapping(self, interface: str, mapping: DHCPStaticMapping) -> bool:
        """
        Add a static mapping to a DHCP configuration.
        
        Args:
            interface: Interface name
            mapping: Static mapping to add
            
        Returns:
            True if successful, False if the interface configuration doesn't exist
        """
        config = self.get_configuration(interface)
        if config:
            config.add_static_mapping(mapping)
            return True
        return False