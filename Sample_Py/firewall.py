#!/usr/bin/env python3
"""
OPNsense Firewall Models

This module provides data models for OPNsense firewall rules and related configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import uuid


class RuleAction(Enum):
    """Firewall rule action types."""
    PASS = "pass"
    BLOCK = "block"
    REJECT = "reject"


class Protocol(Enum):
    """Network protocols for firewall rules."""
    ANY = "any"
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ESP = "esp"
    AH = "ah"
    GRE = "gre"


class IPProtocol(Enum):
    """IP protocol versions."""
    IPv4 = "inet"
    IPv6 = "inet6"
    BOTH = "inet46"


@dataclass
class FirewallEndpoint:
    """
    Represents a source or destination endpoint in a firewall rule.
    """
    # Only one of the following should be set
    any: bool = False
    network: Optional[str] = None  # Interface name or network in CIDR notation
    address: Optional[str] = None  # Single IP address or alias
    port: Optional[str] = None  # Port number, range, or alias
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the endpoint to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of endpoint properties
        """
        result = {}
        
        if self.any:
            result["any"] = "1"
        elif self.network:
            result["network"] = self.network
        elif self.address:
            result["address"] = self.address
            
        if self.port:
            result["port"] = self.port
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirewallEndpoint':
        """
        Create a FirewallEndpoint object from a dictionary.
        
        Args:
            data: Dictionary of endpoint properties
            
        Returns:
            FirewallEndpoint object
        """
        return cls(
            any=data.get("any") == "1",
            network=data.get("network"),
            address=data.get("address"),
            port=data.get("port")
        )


@dataclass
class FirewallRule:
    """
    Represents an OPNsense firewall rule.
    """
    # Required fields
    interface: str  # Interface name (e.g., 'lan', 'wan', 'opt1')
    action: RuleAction  # pass, block, reject
    protocol: Protocol = Protocol.ANY
    
    # Source and destination
    source: FirewallEndpoint = field(default_factory=FirewallEndpoint)
    destination: FirewallEndpoint = field(default_factory=FirewallEndpoint)
    
    # Optional fields
    description: str = ""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    ip_protocol: IPProtocol = IPProtocol.IPv4
    direction: str = "in"
    statetype: str = "keep state"
    quick: bool = True
    
    # Additional fields
    category: str = ""
    disabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the firewall rule to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of firewall rule properties
        """
        result = {
            "type": self.action.value,
            "interface": self.interface,
            "ipprotocol": self.ip_protocol.value,
            "protocol": self.protocol.value if self.protocol != Protocol.ANY else None,
            "source": self.source.to_dict(),
            "destination": self.destination.to_dict(),
            "description": self.description,
            "direction": self.direction,
            "statetype": self.statetype
        }
        
        if self.quick:
            result["quick"] = "1"
            
        if self.category:
            result["category"] = self.category
            
        if self.disabled:
            result["disabled"] = "1"
            
        # Clean up empty values
        return {k: v for k, v in result.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirewallRule':
        """
        Create a FirewallRule object from a dictionary.
        
        Args:
            data: Dictionary of firewall rule properties
            
        Returns:
            FirewallRule object
        """
        # Parse action
        action = RuleAction.PASS
        if data.get("type") == "block":
            action = RuleAction.BLOCK
        elif data.get("type") == "reject":
            action = RuleAction.REJECT
        
        # Parse protocol
        protocol = Protocol.ANY
        if data.get("protocol") in [p.value for p in Protocol]:
            protocol = Protocol(data.get("protocol"))
        
        # Parse IP protocol
        ip_protocol = IPProtocol.IPv4
        if data.get("ipprotocol") in [p.value for p in IPProtocol]:
            ip_protocol = IPProtocol(data.get("ipprotocol"))
        
        # Parse source and destination
        source_data = data.get("source", {})
        destination_data = data.get("destination", {})
        
        if not isinstance(source_data, dict):
            source_data = {}
        if not isinstance(destination_data, dict):
            destination_data = {}
        
        source = FirewallEndpoint.from_dict(source_data)
        destination = FirewallEndpoint.from_dict(destination_data)
        
        return cls(
            interface=data.get("interface", ""),
            action=action,
            protocol=protocol,
            source=source,
            destination=destination,
            description=data.get("description", ""),
            uuid=data.get("uuid", str(uuid.uuid4())),
            ip_protocol=ip_protocol,
            direction=data.get("direction", "in"),
            statetype=data.get("statetype", "keep state"),
            quick=data.get("quick") == "1",
            category=data.get("category", ""),
            disabled=data.get("disabled") == "1"
        )


@dataclass
class FirewallRuleSet:
    """
    Represents a collection of firewall rules.
    """
    rules: List[FirewallRule] = field(default_factory=list)
    
    def add_rule(self, rule: FirewallRule) -> None:
        """
        Add a rule to the ruleset.
        
        Args:
            rule: FirewallRule to add
        """
        self.rules.append(rule)
    
    def get_rules_by_interface(self, interface: str) -> List[FirewallRule]:
        """
        Get all rules for a specific interface.
        
        Args:
            interface: Interface name
            
        Returns:
            List of FirewallRule objects
        """
        return [rule for rule in self.rules if rule.interface == interface]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert all rules to a list of dictionaries.
        
        Returns:
            List of rule dictionaries
        """
        return [rule.to_dict() for rule in self.rules]


@dataclass
class NATRule:
    """
    Represents an OPNsense NAT (Port Forward) rule.
    """
    interface: str  # Interface name (e.g., 'wan')
    protocol: Protocol  # Protocol (tcp, udp, tcp/udp)
    target: str  # Target IP address
    local_port: str  # Destination port on the target
    
    # Source and destination
    source: FirewallEndpoint = field(default_factory=lambda: FirewallEndpoint(any=True))
    destination: FirewallEndpoint = field(default_factory=FirewallEndpoint)
    
    # Optional fields
    description: str = ""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the NAT rule to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of NAT rule properties
        """
        # Configure destination if not set
        if not self.destination.network and not self.destination.address:
            dest = FirewallEndpoint(network="wanip", port=self.local_port)
        else:
            dest = self.destination
            
        result = {
            "interface": self.interface,
            "protocol": self.protocol.value,
            "target": self.target,
            "local-port": self.local_port,
            "source": self.source.to_dict(),
            "destination": dest.to_dict(),
            "descr": self.description
        }
        
        return result