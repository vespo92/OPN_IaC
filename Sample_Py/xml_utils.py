#!/usr/bin/env python3
"""
OPNsense XML Utilities

This module provides utility functions for working with OPNsense XML configurations.
"""

import xml.etree.ElementTree as ET
import uuid
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)


def find_element_by_name(root: ET.Element, path: str, name_tag: str, name_value: str) -> Optional[ET.Element]:
    """
    Find an element by its name within a specified path.
    
    Args:
        root: Root element to search from
        path: Path to the parent element (e.g., 'vlans')
        name_tag: Tag name containing the name (e.g., 'descr')
        name_value: Value to search for (e.g., 'MyVLAN')
        
    Returns:
        Element if found, None otherwise
    """
    parent = root.find(path)
    if parent is None:
        return None
    
    for child in parent:
        name_elem = child.find(name_tag)
        if name_elem is not None and name_elem.text == name_value:
            return child
    
    return None


def find_element_by_attribute(root: ET.Element, path: str, attr_name: str, attr_value: str) -> Optional[ET.Element]:
    """
    Find an element by its attribute within a specified path.
    
    Args:
        root: Root element to search from
        path: Path to the parent element (e.g., 'vlans/vlan')
        attr_name: Attribute name (e.g., 'uuid')
        attr_value: Attribute value to search for
        
    Returns:
        Element if found, None otherwise
    """
    for elem in root.findall(path):
        if elem.get(attr_name) == attr_value:
            return elem
    
    return None


def element_to_dict(element: ET.Element, skip_tags: List[str] = None) -> Dict[str, Any]:
    """
    Convert an XML element to a dictionary.
    
    Args:
        element: XML element to convert
        skip_tags: Optional list of child tags to skip
        
    Returns:
        Dictionary representation of the element
    """
    if skip_tags is None:
        skip_tags = []
    
    result = {}
    
    # Add attributes
    for key, value in element.attrib.items():
        result[f"@{key}"] = value
    
    # Add child elements
    for child in element:
        if child.tag in skip_tags:
            continue
        
        # Handle lists (multiple elements with the same tag)
        if child.tag in result:
            if isinstance(result[child.tag], list):
                result[child.tag].append(element_to_dict(child, skip_tags))
            else:
                result[child.tag] = [result[child.tag], element_to_dict(child, skip_tags)]
        else:
            if len(child) > 0:
                # Element has children
                result[child.tag] = element_to_dict(child, skip_tags)
            else:
                # Leaf element
                result[child.tag] = child.text
    
    return result


def dict_to_element(tag: str, data: Dict[str, Any]) -> ET.Element:
    """
    Convert a dictionary to an XML element.
    
    Args:
        tag: Tag name for the element
        data: Dictionary of element data
        
    Returns:
        XML element
    """
    element = ET.Element(tag)
    
    for key, value in data.items():
        if key.startswith('@'):
            # Attribute
            element.set(key[1:], str(value))
        elif isinstance(value, dict):
            # Nested element
            child = dict_to_element(key, value)
            element.append(child)
        elif isinstance(value, list):
            # Multiple elements with the same tag
            for item in value:
                if isinstance(item, dict):
                    child = dict_to_element(key, item)
                    element.append(child)
                else:
                    child = ET.SubElement(element, key)
                    child.text = str(item)
        else:
            # Simple element
            child = ET.SubElement(element, key)
            if value is not None:
                child.text = str(value)
    
    return element


def generate_uuid() -> str:
    """
    Generate a UUID for use in OPNsense configurations.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_next_interface_id(root: ET.Element, prefix: str = 'opt') -> int:
    """
    Get the next available interface ID.
    
    Args:
        root: Root element of the configuration
        prefix: Interface prefix (e.g., 'opt')
        
    Returns:
        Next available ID
    """
    interfaces = root.find('interfaces')
    if interfaces is None:
        return 1
    
    # Find the highest existing ID
    pattern = re.compile(rf'^{prefix}(\d+)$')
    max_id = 0
    
    for iface in interfaces:
        match = pattern.match(iface.tag)
        if match:
            id_num = int(match.group(1))
            max_id = max(max_id, id_num)
    
    return max_id + 1


def get_ip_network_parts(ip_cidr: str) -> Tuple[str, int]:
    """
    Split an IP address in CIDR notation into address and prefix length.
    
    Args:
        ip_cidr: IP address in CIDR notation (e.g., '192.168.1.0/24')
        
    Returns:
        Tuple of (IP address, prefix length)
    """
    if '/' in ip_cidr:
        ip, prefix = ip_cidr.split('/')
        return ip, int(prefix)
    else:
        return ip_cidr, 32  # Default to /32 for single IP addresses


def check_ip_in_network(ip: str, network_cidr: str) -> bool:
    """
    Check if an IP address is within a network.
    
    Args:
        ip: IP address to check
        network_cidr: Network in CIDR notation (e.g., '192.168.1.0/24')
        
    Returns:
        True if the IP is in the network, False otherwise
    """
    # Simple implementation for IPv4 only
    try:
        # Convert IP to integer
        ip_parts = ip.split('.')
        ip_int = (int(ip_parts[0]) << 24) + (int(ip_parts[1]) << 16) + (int(ip_parts[2]) << 8) + int(ip_parts[3])
        
        # Convert network to integer and calculate mask
        network, prefix = get_ip_network_parts(network_cidr)
        network_parts = network.split('.')
        network_int = (int(network_parts[0]) << 24) + (int(network_parts[1]) << 16) + (int(network_parts[2]) << 8) + int(network_parts[3])
        mask = (1 << 32) - (1 << (32 - prefix))
        
        # Check if IP is in network
        return (ip_int & mask) == (network_int & mask)
    except Exception:
        logger.warning(f"Failed to check if {ip} is in {network_cidr}")
        return False


def validate_mac_address(mac: str) -> bool:
    """
    Validate a MAC address.
    
    Args:
        mac: MAC address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))


def normalize_mac_address(mac: str) -> str:
    """
    Normalize a MAC address to lowercase with colons.
    
    Args:
        mac: MAC address to normalize
        
    Returns:
        Normalized MAC address
    """
    # Remove all separators and convert to lowercase
    mac_clean = re.sub(r'[^0-9a-fA-F]', '', mac).lower()
    
    # Insert colons
    return ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))


def get_interface_by_network(root: ET.Element, network: str) -> Optional[str]:
    """
    Find an interface that matches a network.
    
    Args:
        root: Root element of the configuration
        network: Network in CIDR notation
        
    Returns:
        Interface name if found, None otherwise
    """
    interfaces = root.find('interfaces')
    if interfaces is None:
        return None
    
    network_ip, network_prefix = get_ip_network_parts(network)
    
    for iface_name, iface in interfaces.items():
        iface_ip = iface.findtext('ipaddr')
        iface_subnet = iface.findtext('subnet')
        
        if iface_ip and iface_subnet:
            iface_network = f"{iface_ip}/{iface_subnet}"
            if check_ip_in_network(network_ip, iface_network):
                return iface_name
    
    return None