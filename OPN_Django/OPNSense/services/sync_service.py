import logging
import requests
from typing import Dict, Any, List
from django.db import transaction
from ..models import (
    OPNsenseServer, NetworkInterface, VLAN, FirewallRule, 
    PortForward, DHCPServer, DHCPStaticMapping
)

logger = logging.getLogger(__name__)

class OPNsenseSyncService:
    """Service for synchronizing OPNsense configurations."""
    
    def __init__(self, server: OPNsenseServer):
        self.server = server
        self.base_url = f"https://{server.hostname}/api"
        self.auth = (server.api_key, server.api_secret)
        self.verify_ssl = server.verify_ssl
    
    def _api_request(self, endpoint: str) -> Dict[str, Any]:
        """Make an API request to OPNsense."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(
                url, 
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    @transaction.atomic
    def sync_all(self) -> Dict[str, int]:
        """Synchronize all configurations from OPNsense."""
        results = {}
        
        # Sync interfaces
        results['interfaces'] = self.sync_interfaces()
        
        # Sync VLANs
        results['vlans'] = self.sync_vlans()
        
        # Sync firewall rules
        results['firewall_rules'] = self.sync_firewall_rules()
        
        # Sync port forwards
        results['port_forwards'] = self.sync_port_forwards()
        
        # Sync DHCP server configs
        results['dhcp_servers'] = self.sync_dhcp_servers()
        
        # Sync DHCP static mappings
        results['dhcp_static_mappings'] = self.sync_dhcp_static_mappings()
        
        return results
    
    def sync_interfaces(self) -> int:
        """Synchronize network interfaces."""
        try:
            # Get interfaces from OPNsense
            response = self._api_request("interfaces/interface/getInterfaces")
            
            if "interfaces" not in response:
                logger.warning("No interfaces found in API response")
                return 0
            
            # Clear existing interfaces for this server
            NetworkInterface.objects.filter(server=self.server).delete()
            
            # Create new interface records
            count = 0
            for name, data in response["interfaces"].items():
                NetworkInterface.objects.create(
                    server=self.server,
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
                    mediaopt=data.get("mediaopt", ""),
                    opnsense_uuid=data.get("uuid", "")
                )
                count += 1
            
            logger.info(f"Synchronized {count} interfaces for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync interfaces: {e}")
            return 0
    
    def sync_vlans(self) -> int:
        """Synchronize VLANs."""
        try:
            # Get VLANs from OPNsense
            response = self._api_request("interfaces/vlan/getVlans")
            
            # Clear existing VLANs for this server
            VLAN.objects.filter(server=self.server).delete()
            
            # Create new VLAN records
            count = 0
            for item in response.get("rows", []):
                VLAN.objects.create(
                    server=self.server,
                    parent_if=item.get("if", ""),
                    vlan_tag=int(item.get("tag", 0)),
                    description=item.get("descr", ""),
                    pcp=int(item.get("pcp", 0)),
                    vlanif=item.get("vlanif", ""),
                    opnsense_uuid=item.get("uuid", "")
                )
                count += 1
            
            logger.info(f"Synchronized {count} VLANs for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync VLANs: {e}")
            return 0
    
    def sync_firewall_rules(self) -> int:
        """Synchronize firewall rules."""
        try:
            # Get firewall rules from OPNsense
            response = self._api_request("firewall/filter/searchRule")
            
            # Clear existing firewall rules for this server
            FirewallRule.objects.filter(server=self.server).delete()
            
            # Create new firewall rule records
            count = 0
            for item in response.get("rows", []):
                FirewallRule.objects.create(
                    server=self.server,
                    interface=item.get("interface", ""),
                    protocol=item.get("protocol", "any"),
                    src_address=item.get("source", ""),
                    src_port=item.get("source_port", ""),
                    dst_address=item.get("destination", ""),
                    dst_port=item.get("destination_port", ""),
                    action=item.get("action", "pass"),
                    description=item.get("description", ""),
                    enabled=not item.get("disabled", False),
                    direction=item.get("direction", "in"),
                    ipprotocol=item.get("ipprotocol", "inet"),
                    opnsense_uuid=item.get("uuid", "")
                )
                count += 1
            
            logger.info(f"Synchronized {count} firewall rules for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync firewall rules: {e}")
            return 0
    
    def sync_port_forwards(self) -> int:
        """Synchronize port forwarding rules."""
        try:
            # Get port forwarding rules from OPNsense
            response = self._api_request("firewall/nat/searchRule")
            
            # Clear existing port forwards for this server
            PortForward.objects.filter(server=self.server).delete()
            
            # Create new port forward records
            count = 0
            for item in response.get("rows", []):
                # Only process port forwarding rules
                if item.get("type") != "port_forward":
                    continue
                
                PortForward.objects.create(
                    server=self.server,
                    interface=item.get("interface", ""),
                    protocol=item.get("protocol", "tcp"),
                    src_port=item.get("source_port", ""),
                    dst_ip=item.get("target", ""),
                    dst_port=item.get("target_port", ""),
                    description=item.get("description", ""),
                    src_ip=item.get("source_subnet", ""),
                    enabled=not item.get("disabled", False),
                    opnsense_uuid=item.get("uuid", "")
                )
                count += 1
            
            logger.info(f"Synchronized {count} port forwards for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync port forwards: {e}")
            return 0
    
    def sync_dhcp_servers(self) -> int:
        """Synchronize DHCP server configurations."""
        try:
            # Get DHCP server configurations from OPNsense
            response = self._api_request("dhcp/service/get")
            
            # Clear existing DHCP servers for this server
            DHCPServer.objects.filter(server=self.server).delete()
            
            # Create new DHCP server records
            count = 0
            dhcp_config = response.get("dhcp", {})
            
            for interface, config in dhcp_config.items():
                # Skip non-interface configs
                if interface in ["registration", "netflow", "ntpd"]:
                    continue
                
                DHCPServer.objects.create(
                    server=self.server,
                    interface=interface,
                    enabled=config.get("enable") == "1",
                    range_from=config.get("range", {}).get("from", ""),
                    range_to=config.get("range", {}).get("to", ""),
                    gateway=config.get("gateway", ""),
                    dnsserver=config.get("dnsserver", ""),
                    domain=config.get("domain", "")
                )
                count += 1
            
            logger.info(f"Synchronized {count} DHCP servers for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync DHCP servers: {e}")
            return 0
    
    def sync_dhcp_static_mappings(self) -> int:
        """Synchronize DHCP static mappings."""
        try:
            # Get DHCP server configurations from OPNsense
            response = self._api_request("dhcp/service/get")
            
            # Clear existing DHCP static mappings
            DHCPStaticMapping.objects.filter(
                dhcp_server__server=self.server
            ).delete()
            
            # Create new DHCP static mapping records
            count = 0
            dhcp_config = response.get("dhcp", {})
            
            for interface, config in dhcp_config.items():
                # Skip non-interface configs
                if interface in ["registration", "netflow", "ntpd"]:
                    continue
                
                # Get the DHCP server
                try:
                    dhcp_server = DHCPServer.objects.get(
                        server=self.server,
                        interface=interface
                    )
                except DHCPServer.DoesNotExist:
                    logger.warning(f"DHCP server for interface {interface} not found")
                    continue
                
                # Process static mappings
                for mapping in config.get("staticmap", []):
                    DHCPStaticMapping.objects.create(
                        dhcp_server=dhcp_server,
                        mac=mapping.get("mac", ""),
                        ipaddr=mapping.get("ipaddr", ""),
                        hostname=mapping.get("hostname", ""),
                        description=mapping.get("descr", ""),
                        winsserver=mapping.get("winsserver", ""),
                        dnsserver=mapping.get("dnsserver", ""),
                        ntpserver=mapping.get("ntpserver", ""),
                        opnsense_uuid=mapping.get("uuid", "")
                    )
                    count += 1
            
            logger.info(f"Synchronized {count} DHCP static mappings for server {self.server.name}")
            return count
        except Exception as e:
            logger.error(f"Failed to sync DHCP static mappings: {e}")
            return 0
