#!/usr/bin/env python3
"""
OPNsense VLAN Models

This module provides data models for OPNsense VLAN configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid


@dataclass
class VLAN:
    """
    Represents an OPNsense VLAN.
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
        Convert the VLAN to a dictionary suitable for XML creation.
        
        Returns:
            Dictionary of VLAN properties
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
    def from_dict(cls, data: Dict[str, Any]) -> 'VLAN':
        """
        Create a VLAN object from a dictionary.
        
        Args:
            data: Dictionary of VLAN properties
            
        Returns:
            VLAN object
        """
        return cls(
            parent_if=data.get("if", ""),
            vlan_tag=int(data.get("tag", 0)),
            description=data.get("descr", ""),
            pcp=int(data.get("pcp", 0)),
            uuid=data.get("uuid", str(uuid.uuid4()))
        )


@dataclass
class VLANGroup:
    """
    Represents a group of VLANs in OPNsense.
    """
    vlans: List[VLAN] = field(default_factory=list)
    
    def add_vlan(self, vlan: VLAN) -> None:
        """
        Add a VLAN to the group.
        
        Args:
            vlan: VLAN to add
        """
        self.vlans.append(vlan)
    
    def get_vlan_by_tag(self, tag: int) -> Optional[VLAN]:
        """
        Get a VLAN by its tag.
        
        Args:
            tag: VLAN tag to search for
            
        Returns:
            VLAN object if found, None otherwise
        """
        for vlan in self.vlans:
            if vlan.vlan_tag == tag:
                return vlan
        return None
    
    def get_vlan_by_interface(self, interface: str) -> List[VLAN]:
        """
        Get all VLANs for a specific parent interface.
        
        Args:
            interface: Parent interface name
            
        Returns:
            List of VLAN objects
        """
        return [vlan for vlan in self.vlans if vlan.parent_if == interface]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert all VLANs to a list of dictionaries.
        
        Returns:
            List of VLAN dictionaries
        """
        return [vlan.to_dict() for vlan in self.vlans]