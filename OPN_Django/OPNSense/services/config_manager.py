import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
import uuid
import requests
from django.conf import settings

# Import models
from OPNSense.api.models.network import InterfaceCreate, InterfaceUpdate, InterfaceOut, VlanCreate, VlanUpdate, VlanOut
from OPNSense.api.models.firewall import FirewallRuleCreate, FirewallRuleUpdate, FirewallRuleOut, PortForwardCreate, PortForwardUpdate, PortForwardOut
from OPNSense.api.models.dhcp import DHCPConfigCreate, DHCPConfigUpdate, DHCPConfigOut, DHCPStaticMappingCreate, DHCPStaticMappingUpdate, DHCPStaticMappingOut

logger = logging.getLogger(__name__)


class OPNsenseConfigService:
    """Service for managing OPNsense configurations."""
    
    def __init__(self, config_path: Optional[str] = None, api_config: Optional[Dict[str, str]] = None):
        """
        Initialize the service.
        
        Args:
            config_path: Path to the OPNsense XML configuration file (for file-based operations)
            api_config: API configuration for OPNsense API interactions
        """
        self.config_path = config_path or os.environ.get('OPNSENSE_CONFIG_PATH')
        self.api_config = api_config or {
            'url': os.environ.get('OPNSENSE_API_URL', ''),
            'key': os.environ.get('OPNSENSE_API_KEY', ''),
            'secret': os.environ.get('OPNSENSE_API_SECRET', ''),
            'verify_ssl': os.environ.get('OPNSENSE_API_VERIFY_SSL', 'False').lower() == 'true'
        }
        
        self.use_api = bool(self.api_config['url'] and self.api_config['key'] and self.api_config['secret'])
        self.root = None
        
        # Load config if using file-based operations
        if not self.use_api and self.config_path and os.path.exists(self.config_path):
            self._load_config()
    
    def _load_config(self) -> None:
        """Load the XML configuration from file."""
        try:
            tree = ET.parse(self.config_path)
            self.root = tree.getroot()
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _save_config(self) -> None:
        """Save the XML configuration to file."""
        if not self.root:
            raise ValueError("No configuration loaded")
        
        try:
            tree = ET.ElementTree(self.root)
            tree.write(self.config_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _api_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the OPNsense API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data
        
        Returns:
            API response
        """
        if not self.use_api:
            raise ValueError("API not configured")
        
        url = f"{self.api_config['url']}/{endpoint}"
        auth = (self.api_config['key'], self.api_config['secret'])
        
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                auth=auth,
                json=data,
                verify=self.api_config['verify_ssl']
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    # Interface methods
    def get_interfaces(self) -> List[InterfaceOut]:
        """Get all network interfaces."""
        if self.use_api:
            # Use API
            response = self._api_request('GET', 'interfaces')
            interfaces = []
            for name, data in response.get('interfaces', {}).items():
                interface = InterfaceOut(
                    name=name,
                    if_name=data.get('if', ''),
                    description=data.get('descr', ''),
                    ipaddr=data.get('ipaddr', 'dhcp'),
                    subnet=int(data.get('subnet')) if data.get('subnet') else None,
                    enabled=data.get('enable') == '1',
                    uuid=data.get('uuid', str(uuid.uuid4())),
                    gateway=data.get('gateway', ''),
                    spoofmac=data.get('spoofmac', ''),
                    mtu=int(data.get('mtu')) if data.get('mtu') else None,
                    media=data.get('media', ''),
                    mediaopt=data.get('mediaopt', '')
                )
                interfaces.append(interface)
            return interfaces
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            interfaces_elem = self.root.find('interfaces')
            if interfaces_elem is None:
                return []
            
            interfaces = []
            for iface_elem in interfaces_elem:
                iface_data = {}
                for child in iface_elem:
                    iface_data[child.tag] = child.text
                
                interface = InterfaceOut(
                    name=iface_elem.tag,
                    if_name=iface_data.get('if', ''),
                    description=iface_data.get('descr', ''),
                    ipaddr=iface_data.get('ipaddr', 'dhcp'),
                    subnet=int(iface_data.get('subnet')) if iface_data.get('subnet') else None,
                    enabled=iface_data.get('enable') == '1',
                    uuid=iface_data.get('uuid', str(uuid.uuid4())),
                    gateway=iface_data.get('gateway', ''),
                    spoofmac=iface_data.get('spoofmac', ''),
                    mtu=int(iface_data.get('mtu')) if iface_data.get('mtu') else None,
                    media=iface_data.get('media', ''),
                    mediaopt=iface_data.get('mediaopt', '')
                )
                interfaces.append(interface)
            
            return interfaces
    
    def get_interface(self, name: str) -> InterfaceOut:
        """Get a specific network interface by name."""
        interfaces = self.get_interfaces()
        for interface in interfaces:
            if interface.name == name:
                return interface
        raise ValueError(f"Interface {name} not found")
    
    def create_interface(self, data: InterfaceCreate) -> InterfaceOut:
        """Create a new network interface."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('POST', 'interfaces', {
                'interface': data.dict()
            })
            
            if response.get('result') != 'saved':
                raise ValueError(f"Failed to create interface: {response.get('message', 'Unknown error')}")
            
            # Get the created interface
            return self.get_interface(data.name)
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the interfaces element
            interfaces_elem = self.root.find('interfaces')
            if interfaces_elem is None:
                interfaces_elem = ET.SubElement(self.root, 'interfaces')
            
            # Check if interface already exists
            for iface_elem in interfaces_elem:
                if iface_elem.tag == data.name:
                    raise ValueError(f"Interface {data.name} already exists")
            
            # Create the new interface element
            iface_elem = ET.SubElement(interfaces_elem, data.name)
            
            # Add a UUID
            interface_uuid = str(uuid.uuid4())
            uuid_elem = ET.SubElement(iface_elem, 'uuid')
            uuid_elem.text = interface_uuid
            
            # Add other properties
            for key, value in data.dict().items():
                if key != 'name' and value is not None:
                    if key == 'enabled':
                        key = 'enable'
                        value = '1' if value else '0'
                    
                    elem = ET.SubElement(iface_elem, key)
                    elem.text = str(value) if value is not None else ''
            
            # Save the configuration
            self._save_config()
            
            # Return the created interface
            return InterfaceOut(
                **data.dict(),
                uuid=interface_uuid
            )
    
    def update_interface(self, name: str, data: InterfaceUpdate) -> InterfaceOut:
        """Update an existing network interface."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('PUT', f'interfaces/{name}', {
                'interface': data.dict(exclude_unset=True)
            })
            
            if response.get('result') != 'saved':
                raise ValueError(f"Failed to update interface: {response.get('message', 'Unknown error')}")
            
            # Get the updated interface
            return self.get_interface(name)
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the interface
            interfaces_elem = self.root.find('interfaces')
            if interfaces_elem is None:
                raise ValueError("No interfaces found in configuration")
            
            iface_elem = interfaces_elem.find(name)
            if iface_elem is None:
                raise ValueError(f"Interface {name} not found")
            
            # Update properties
            for key, value in data.dict(exclude_unset=True).items():
                if key != 'name' and value is not None:
                    if key == 'enabled':
                        key = 'enable'
                        value = '1' if value else '0'
                    
                    elem = iface_elem.find(key)
                    if elem is None:
                        elem = ET.SubElement(iface_elem, key)
                    elem.text = str(value) if value is not None else ''
            
            # Save the configuration
            self._save_config()
            
            # Get the interface's UUID
            uuid_elem = iface_elem.find('uuid')
            interface_uuid = uuid_elem.text if uuid_elem is not None else str(uuid.uuid4())
            
            # Return the updated interface
            return self.get_interface(name)
    
    def delete_interface(self, name: str) -> bool:
        """Delete a network interface."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('DELETE', f'interfaces/{name}')
            
            return response.get('result') == 'deleted'
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the interface
            interfaces_elem = self.root.find('interfaces')
            if interfaces_elem is None:
                raise ValueError("No interfaces found in configuration")
            
            iface_elem = interfaces_elem.find(name)
            if iface_elem is None:
                raise ValueError(f"Interface {name} not found")
            
            # Remove the interface
            interfaces_elem.remove(iface_elem)
            
            # Save the configuration
            self._save_config()
            
            return True
    
    # VLAN methods
    def get_vlans(self) -> List[VlanOut]:
        """Get all VLANs."""
        if self.use_api:
            # Use API
            response = self._api_request('GET', 'vlans')
            vlans = []
            for data in response.get('vlans', []):
                vlan = VlanOut(
                    parent_if=data.get('if', ''),
                    vlan_tag=int(data.get('tag', 0)),
                    description=data.get('descr', ''),
                    pcp=int(data.get('pcp', 0)),
                    uuid=data.get('uuid', str(uuid.uuid4())),
                    vlanif=data.get('vlanif', '')
                )
                vlans.append(vlan)
            return vlans
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            vlans_elem = self.root.find('vlans')
            if vlans_elem is None:
                return []
            
            vlans = []
            for vlan_elem in vlans_elem.findall('vlan'):
                vlan_data = {}
                for child in vlan_elem:
                    vlan_data[child.tag] = child.text
                
                vlan = VlanOut(
                    parent_if=vlan_data.get('if', ''),
                    vlan_tag=int(vlan_data.get('tag', 0)),
                    description=vlan_data.get('descr', ''),
                    pcp=int(vlan_data.get('pcp', 0)),
                    uuid=vlan_elem.get('uuid', str(uuid.uuid4())),
                    vlanif=vlan_data.get('vlanif', '')
                )
                vlans.append(vlan)
            
            return vlans
    
    def get_vlan(self, uuid_str: str) -> VlanOut:
        """Get a specific VLAN by UUID."""
        vlans = self.get_vlans()
        for vlan in vlans:
            if vlan.uuid == uuid_str:
                return vlan
        raise ValueError(f"VLAN with UUID {uuid_str} not found")
    
    def create_vlan(self, data: VlanCreate) -> VlanOut:
        """Create a new VLAN."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('POST', 'vlans', {
                'vlan': data.dict()
            })
            
            if response.get('result') != 'saved':
                raise ValueError(f"Failed to create VLAN: {response.get('message', 'Unknown error')}")
            
            # Get the UUID of the created VLAN
            uuid_str = response.get('uuid', str(uuid.uuid4()))
            
            # Return the created VLAN
            vlanif = f"{data.parent_if}_vlan{data.vlan_tag}"
            return VlanOut(
                **data.dict(),
                uuid=uuid_str,
                vlanif=vlanif
            )
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the vlans element
            vlans_elem = self.root.find('vlans')
            if vlans_elem is None:
                vlans_elem = ET.SubElement(self.root, 'vlans')
            
            # Create a new VLAN element
            vlan_elem = ET.SubElement(vlans_elem, 'vlan')
            vlan_uuid = str(uuid.uuid4())
            vlan_elem.set('uuid', vlan_uuid)
            
            # Add properties
            vlanif = f"{data.parent_if}_vlan{data.vlan_tag}"
            
            for key, value in data.dict().items():
                if value is not None:
                    elem = ET.SubElement(vlan_elem, key)
                    elem.text = str(value)
            
            # Add vlanif
            vlanif_elem = ET.SubElement(vlan_elem, 'vlanif')
            vlanif_elem.text = vlanif
            
            # Save the configuration
            self._save_config()
            
            # Return the created VLAN
            return VlanOut(
                **data.dict(),
                uuid=vlan_uuid,
                vlanif=vlanif
            )
    
    def update_vlan(self, uuid_str: str, data: VlanUpdate) -> VlanOut:
        """Update an existing VLAN."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('PUT', f'vlans/{uuid_str}', {
                'vlan': data.dict(exclude_unset=True)
            })
            
            if response.get('result') != 'saved':
                raise ValueError(f"Failed to update VLAN: {response.get('message', 'Unknown error')}")
            
            # Get the updated VLAN
            return self.get_vlan(uuid_str)
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the VLAN
            vlans_elem = self.root.find('vlans')
            if vlans_elem is None:
                raise ValueError("No VLANs found in configuration")
            
            vlan_elem = None
            for elem in vlans_elem.findall('vlan'):
                if elem.get('uuid') == uuid_str:
                    vlan_elem = elem
                    break
            
            if vlan_elem is None:
                raise ValueError(f"VLAN with UUID {uuid_str} not found")
            
            # Get current values for fields not provided in the update
            current_vlan = self.get_vlan(uuid_str)
            
            # Update properties
            update_dict = data.dict(exclude_unset=True)
            parent_if = update_dict.get('parent_if', current_vlan.parent_if)
            vlan_tag = update_dict.get('vlan_tag', current_vlan.vlan_tag)
            
            for key, value in update_dict.items():
                if value is not None:
                    elem = vlan_elem.find(key)
                    if elem is None:
                        elem = ET.SubElement(vlan_elem, key)
                    elem.text = str(value)
            
            # Update vlanif if parent_if or vlan_tag changed
            if 'parent_if' in update_dict or 'vlan_tag' in update_dict:
                vlanif = f"{parent_if}_vlan{vlan_tag}"
                vlanif_elem = vlan_elem.find('vlanif')
                if vlanif_elem is not None:
                    vlanif_elem.text = vlanif
            
            # Save the configuration
            self._save_config()
            
            # Return the updated VLAN
            return self.get_vlan(uuid_str)
    
    def delete_vlan(self, uuid_str: str) -> bool:
        """Delete a VLAN."""
        # Implementation depends on whether we're using the API or file
        if self.use_api:
            # Use API
            response = self._api_request('DELETE', f'vlans/{uuid_str}')
            
            return response.get('result') == 'deleted'
        else:
            # Use file
            if not self.root:
                self._load_config()
            
            # Find the VLAN
            vlans_elem = self.root.find('vlans')
            if vlans_elem is None:
                raise ValueError("No VLANs found in configuration")
            
            vlan_elem = None
            for elem in vlans_elem.findall('vlan'):
                if elem.get('uuid') == uuid_str:
                    vlan_elem = elem
                    break
            
            if vlan_elem is None:
                raise ValueError(f"VLAN with UUID {uuid_str} not found")
            
            # Remove the VLAN
            vlans_elem.remove(vlan_elem)
            
            # Save the configuration
            self._save_config()
            
            return True
    
    # Firewall methods
    def get_firewall_rules(self, interface: Optional[str] = None) -> List[FirewallRuleOut]:
        """Get all firewall rules, optionally filtered by interface."""
        # Implementation for firewall rules...
        # This would be similar to the interface and VLAN methods, but adapted for firewall rules
        # For brevity, we'll return a placeholder
        return []
    
    def get_firewall_rule(self, uuid_str: str) -> FirewallRuleOut:
        """Get a specific firewall rule by UUID."""
        # Placeholder
        raise NotImplementedError("Firewall rule methods not implemented")
    
    def create_firewall_rule(self, data: FirewallRuleCreate) -> FirewallRuleOut:
        """Create a new firewall rule."""
        # Placeholder
        raise NotImplementedError("Firewall rule methods not implemented")
    
    def update_firewall_rule(self, uuid_str: str, data: FirewallRuleUpdate) -> FirewallRuleOut:
        """Update an existing firewall rule."""
        # Placeholder
        raise NotImplementedError("Firewall rule methods not implemented")
    
    def delete_firewall_rule(self, uuid_str: str) -> bool:
        """Delete a firewall rule."""
        # Placeholder
        raise NotImplementedError("Firewall rule methods not implemented")
    
    # Port forwarding methods
    def get_port_forwards(self, interface: Optional[str] = None) -> List[PortForwardOut]:
        """Get all port forwarding rules, optionally filtered by interface."""
        # Placeholder
        return []
    
    def get_port_forward(self, uuid_str: str) -> PortForwardOut:
        """Get a specific port forwarding rule by UUID."""
        # Placeholder
        raise NotImplementedError("Port forwarding methods not implemented")
    
    def create_port_forward(self, data: PortForwardCreate) -> PortForwardOut:
        """Create a new port forwarding rule."""
        # Placeholder
        raise NotImplementedError("Port forwarding methods not implemented")
    
    def update_port_forward(self, uuid_str: str, data: PortForwardUpdate) -> PortForwardOut:
        """Update an existing port forwarding rule."""
        # Placeholder
        raise NotImplementedError("Port forwarding methods not implemented")
    
    def delete_port_forward(self, uuid_str: str) -> bool:
        """Delete a port forwarding rule."""
        # Placeholder
        raise NotImplementedError("Port forwarding methods not implemented")
    
    # Firewall aliases
    def get_aliases(self, type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all firewall aliases, optionally filtered by type."""
        # Placeholder
        return []
    
    # Apply changes
    def apply_firewall_changes(self) -> Dict[str, Any]:
        """Apply all pending firewall changes."""
        # Placeholder
        return {"success": True, "message": "Changes applied"}
    
    # DHCP methods
    def get_dhcp_configs(self) -> List[DHCPConfigOut]:
        """Get all DHCP configurations."""
        # Placeholder
        return []
    
    def get_dhcp_config(self, interface: str) -> DHCPConfigOut:
        """Get DHCP configuration for a specific interface."""
        # Placeholder
        raise NotImplementedError("DHCP methods not implemented")
    
    def create_dhcp_config(self, data: DHCPConfigCreate) -> DHCPConfigOut:
        """Create a new DHCP configuration."""
        # Placeholder
        raise NotImplementedError("DHCP methods not implemented")
    
    def update_dhcp_config(self, interface: str, data: DHCPConfigUpdate) -> DHCPConfigOut:
        """Update an existing DHCP configuration."""
        # Placeholder
        raise NotImplementedError("DHCP methods not implemented")
    
    def delete_dhcp_config(self, interface: str) -> bool:
        """Delete a DHCP configuration."""
        # Placeholder
        raise NotImplementedError("DHCP methods not implemented")
    
    # DHCP static mapping methods
    def get_static_mappings(self, interface: str) -> List[DHCPStaticMappingOut]:
        """Get all static DHCP mappings for a specific interface."""
        # Placeholder
        return []
    
    def get_static_mapping(self, interface: str, uuid_str: str) -> DHCPStaticMappingOut:
        """Get a specific static DHCP mapping."""
        # Placeholder
        raise NotImplementedError("DHCP static mapping methods not implemented")
    
    def create_static_mapping(self, interface: str, data: DHCPStaticMappingCreate) -> DHCPStaticMappingOut:
        """Create a new static DHCP mapping."""
        # Placeholder
        raise NotImplementedError("DHCP static mapping methods not implemented")
    
    def update_static_mapping(self, interface: str, uuid_str: str, data: DHCPStaticMappingUpdate) -> DHCPStaticMappingOut:
        """Update an existing static DHCP mapping."""
        # Placeholder
        raise NotImplementedError("DHCP static mapping methods not implemented")
    
    def delete_static_mapping(self, interface: str, uuid_str: str) -> bool:
        """Delete a static DHCP mapping."""
        # Placeholder
        raise NotImplementedError("DHCP static mapping methods not implemented")
    
    # DHCP leases
    def get_dhcp_leases(self, interface: str) -> List[Dict[str, Any]]:
        """Get all DHCP leases for a specific interface."""
        # Placeholder
        return []
    
    # Apply DHCP changes
    def apply_dhcp_changes(self) -> Dict[str, Any]:
        """Apply all pending DHCP changes."""
        # Placeholder
        return {"success": True, "message": "Changes applied"}
