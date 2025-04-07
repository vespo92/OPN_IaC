#!/usr/bin/env python3
"""
OPNsense Configuration Manager

This module provides the core functionality for parsing, modifying, and writing
OPNsense XML configurations in an infrastructure-as-code approach.
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

class OPNsenseConfigManager:
    """
    Manager for OPNsense configurations.
    
    This class handles loading, parsing, modifying, and saving OPNsense XML configuration files.
    It provides methods for common operations like adding VLANs, updating firewall rules, etc.
    """
    
    def __init__(self, config_path: Optional[str] = None, backup_enabled: bool = True):
        """
        Initialize the OPNsense configuration manager.
        
        Args:
            config_path: Path to the OPNsense XML configuration file
            backup_enabled: Whether to create backups before making changes
        """
        self.config_path = config_path
        self.backup_enabled = backup_enabled
        self.tree = None
        self.root = None
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """
        Load an OPNsense configuration from a file.
        
        Args:
            config_path: Path to the configuration XML file
        """
        try:
            self.config_path = config_path
            self.tree = ET.parse(config_path)
            self.root = self.tree.getroot()
            logger.info(f"Successfully loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def load_config_from_string(self, xml_content: str) -> None:
        """
        Load an OPNsense configuration from a string.
        
        Args:
            xml_content: XML configuration as a string
        """
        try:
            self.tree = ET.ElementTree(ET.fromstring(xml_content))
            self.root = self.tree.getroot()
            logger.info("Successfully loaded configuration from string")
        except Exception as e:
            logger.error(f"Failed to load configuration from string: {e}")
            raise
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            output_path: Path to save the configuration to. If None, overwrite the original file.
        """
        if not output_path:
            output_path = self.config_path
        
        if not output_path:
            raise ValueError("No output path specified and no original path available")
        
        if self.backup_enabled and os.path.exists(output_path):
            backup_path = f"{output_path}.bak"
            try:
                import shutil
                shutil.copy2(output_path, backup_path)
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        try:
            # Write with proper XML declaration and encoding
            self.tree.write(output_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"Successfully saved configuration to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration to {output_path}: {e}")
            raise
    
    def get_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured interfaces.
        
        Returns:
            Dictionary of interfaces with their properties
        """
        interfaces = {}
        interfaces_elem = self.root.find("interfaces")
        
        if interfaces_elem is not None:
            for iface in interfaces_elem:
                iface_data = {}
                for child in iface:
                    iface_data[child.tag] = child.text
                interfaces[iface.tag] = iface_data
        
        return interfaces
    
    def get_vlans(self) -> List[Dict[str, str]]:
        """
        Get all configured VLANs.
        
        Returns:
            List of VLAN configurations
        """
        vlans = []
        vlans_elem = self.root.find("vlans")
        
        if vlans_elem is not None:
            for vlan in vlans_elem.findall("vlan"):
                vlan_data = {}
                for child in vlan:
                    vlan_data[child.tag] = child.text
                vlans.append(vlan_data)
        
        return vlans
    
    def add_vlan(self, interface: str, tag: int, description: str = "") -> str:
        """
        Add a new VLAN to the configuration.
        
        Args:
            interface: Parent interface name (e.g., 'igc0')
            tag: VLAN tag/ID (1-4094)
            description: Optional description for the VLAN
        
        Returns:
            The UUID of the newly created VLAN
        """
        import uuid
        
        # Generate a UUID for the new VLAN
        vlan_uuid = str(uuid.uuid4())
        
        # Create VLAN element structure
        vlans_elem = self.root.find("vlans")
        if vlans_elem is None:
            # Create the vlans element if it doesn't exist
            vlans_elem = ET.SubElement(self.root, "vlans")
            vlans_elem.set("version", "1.0.0")
        
        # Create new VLAN element
        vlan_elem = ET.SubElement(vlans_elem, "vlan")
        vlan_elem.set("uuid", vlan_uuid)
        
        # Add VLAN properties
        if_elem = ET.SubElement(vlan_elem, "if")
        if_elem.text = interface
        
        tag_elem = ET.SubElement(vlan_elem, "tag")
        tag_elem.text = str(tag)
        
        pcp_elem = ET.SubElement(vlan_elem, "pcp")
        pcp_elem.text = "0"
        
        proto_elem = ET.SubElement(vlan_elem, "proto")
        
        descr_elem = ET.SubElement(vlan_elem, "descr")
        descr_elem.text = description
        
        vlanif_elem = ET.SubElement(vlan_elem, "vlanif")
        vlanif_elem.text = f"{interface}_vlan{tag}"
        
        logger.info(f"Added VLAN {tag} on interface {interface}")
        return vlan_uuid
    
    def add_firewall_rule(self, config: Dict[str, Any]) -> str:
        """
        Add a new firewall rule to the configuration.
        
        Args:
            config: Dictionary containing the firewall rule configuration
        
        Returns:
            The UUID of the newly created firewall rule
        """
        import uuid
        
        # Generate a UUID for the new rule
        rule_uuid = str(uuid.uuid4())
        
        # Find the filter element
        filter_elem = self.root.find("filter")
        if filter_elem is None:
            # Create the filter element if it doesn't exist
            filter_elem = ET.SubElement(self.root, "filter")
        
        # Create new rule element
        rule_elem = ET.SubElement(filter_elem, "rule")
        rule_elem.set("uuid", rule_uuid)
        
        # Add rule properties
        for key, value in config.items():
            if isinstance(value, dict):
                sub_elem = ET.SubElement(rule_elem, key)
                for sub_key, sub_value in value.items():
                    sub_sub_elem = ET.SubElement(sub_elem, sub_key)
                    sub_sub_elem.text = str(sub_value)
            else:
                child_elem = ET.SubElement(rule_elem, key)
                child_elem.text = str(value)
        
        logger.info(f"Added firewall rule with UUID {rule_uuid}")
        return rule_uuid
    
    def add_dhcp_static_mapping(self, interface: str, mac: str, ipaddr: str, hostname: str, description: str = "") -> bool:
        """
        Add a static DHCP mapping.
        
        Args:
            interface: Interface name (e.g., 'lan', 'opt1')
            mac: MAC address of the client
            ipaddr: IP address to assign
            hostname: Hostname for the client
            description: Optional description
        
        Returns:
            True if successful, False otherwise
        """
        # Find the dhcpd element
        dhcpd_elem = self.root.find("dhcpd")
        if dhcpd_elem is None:
            logger.error("DHCP configuration not found")
            return False
        
        # Find the interface's DHCP configuration
        iface_elem = dhcpd_elem.find(interface)
        if iface_elem is None:
            logger.error(f"DHCP configuration for interface {interface} not found")
            return False
        
        # Create the staticmap element
        staticmap_elem = ET.SubElement(iface_elem, "staticmap")
        
        # Add staticmap properties
        mac_elem = ET.SubElement(staticmap_elem, "mac")
        mac_elem.text = mac
        
        ipaddr_elem = ET.SubElement(staticmap_elem, "ipaddr")
        ipaddr_elem.text = ipaddr
        
        hostname_elem = ET.SubElement(staticmap_elem, "hostname")
        hostname_elem.text = hostname
        
        if description:
            descr_elem = ET.SubElement(staticmap_elem, "descr")
            descr_elem.text = description
        
        # Add empty elements that are typically present in static mappings
        for empty_tag in ["winsserver", "dnsserver", "ntpserver"]:
            ET.SubElement(staticmap_elem, empty_tag)
        
        logger.info(f"Added static DHCP mapping for {mac} to {ipaddr} on {interface}")
        return True
    
    def deploy_network_for_container(self, container_name: str, vlan_id: int, ip_address: str, mac_address: str, 
                                    parent_interface: str = "igc2", allow_internet: bool = True) -> Dict[str, Any]:
        """
        Deploy all necessary network configuration for a container.
        
        This is a higher-level method that combines several operations:
        1. Creates a VLAN (if it doesn't exist)
        2. Adds a DHCP static mapping
        3. Creates necessary firewall rules
        
        Args:
            container_name: Name of the container (used for descriptions)
            vlan_id: VLAN ID to use
            ip_address: IP address for the container
            mac_address: MAC address of the container
            parent_interface: Physical interface to use for the VLAN
            allow_internet: Whether to allow internet access
        
        Returns:
            Dictionary with details of the created resources
        """
        result = {
            "vlan_uuid": None,
            "dhcp_mapping": False,
            "firewall_rules": []
        }
        
        # Step 1: Check if VLAN exists, create if not
        vlan_exists = False
        for vlan in self.get_vlans():
            if vlan.get("if") == parent_interface and vlan.get("tag") == str(vlan_id):
                vlan_exists = True
                result["vlan_uuid"] = vlan.get("uuid")
                break
        
        if not vlan_exists:
            result["vlan_uuid"] = self.add_vlan(
                interface=parent_interface,
                tag=vlan_id,
                description=f"Container {container_name}"
            )
        
        # Step 2: Add DHCP static mapping
        # Extract IP details
        ip_parts = ip_address.split('.')
        interface_name = f"opt{vlan_id}"  # This assumes your VLAN interfaces are named this way
        
        # Add static mapping
        result["dhcp_mapping"] = self.add_dhcp_static_mapping(
            interface=interface_name,
            mac=mac_address,
            ipaddr=ip_address,
            hostname=container_name,
            description=f"Container {container_name}"
        )
        
        # Step 3: Create firewall rules if internet access is needed
        if allow_internet:
            # Allow outbound internet access
            internet_rule_uuid = self.add_firewall_rule({
                "type": "pass",
                "interface": interface_name,
                "ipprotocol": "inet",
                "statetype": "keep state",
                "direction": "in",
                "quick": "1",
                "descr": f"Allow {container_name} Internet Access",
                "source": {
                    "network": interface_name
                },
                "destination": {
                    "any": "1"
                }
            })
            result["firewall_rules"].append(internet_rule_uuid)
        
        return result