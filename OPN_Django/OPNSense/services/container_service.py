import os
import uuid
import logging
import requests
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
from django.conf import settings

# Import models
from OPNSense.api.models.container import ContainerCreate, ContainerUpdate, ContainerOut, PortMapping, ContainerNetworkConfig
from OPNSense.api.models.firewall import Protocol

# Import OPNsense config service
from OPNSense.services.config_manager import OPNsenseConfigService

logger = logging.getLogger(__name__)


class ContainerService:
    """Service for managing containers and their network configurations."""
    
    def __init__(self, docker_api_url: Optional[str] = None):
        """
        Initialize the service.
        
        Args:
            docker_api_url: URL for the Docker API
        """
        self.docker_api_url = docker_api_url or os.environ.get('DOCKER_API_URL', 'http://localhost:2375')
        self.config_service = OPNsenseConfigService()
    
    def _docker_api_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make a request to the Docker API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data
        
        Returns:
            API response
        """
        url = f"{self.docker_api_url}/{endpoint}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            if data is not None:
                data_json = json.dumps(data)
            else:
                data_json = None
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data_json
            )
            response.raise_for_status()
            
            if response.text:
                return response.json()
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Docker API request failed: {e}")
            raise
    
    def get_containers(self) -> List[ContainerOut]:
        """Get all containers."""
        try:
            containers_data = self._docker_api_request('GET', 'containers/json?all=true')
            
            containers = []
            for data in containers_data:
                # Get container details
                container_id = data['Id']
                details = self._docker_api_request('GET', f'containers/{container_id}/json')
                
                # Extract network configuration
                network_info = details.get('NetworkSettings', {})
                network_config = self._extract_network_config(network_info)
                
                # Extract port mappings
                port_mappings = self._extract_port_mappings(details)
                
                # Create container model
                container = ContainerOut(
                    id=container_id,
                    name=data['Names'][0].lstrip('/'),
                    image=data['Image'],
                    status=data['State'],
                    created_at=data['Created'],
                    network_config=network_config,
                    ports=port_mappings,
                    environment=self._extract_env_vars(details),
                    volumes=self._extract_volumes(details),
                    restart_policy=details.get('HostConfig', {}).get('RestartPolicy', {}).get('Name', 'no'),
                    network_info=network_info
                )
                containers.append(container)
            
            return containers
        except Exception as e:
            logger.error(f"Failed to get containers: {e}")
            raise
    
    def get_container(self, name: str) -> ContainerOut:
        """Get a specific container by name."""
        containers = self.get_containers()
        for container in containers:
            if container.name == name:
                return container
        raise ValueError(f"Container {name} not found")
    
    def create_container(self, data: ContainerCreate) -> ContainerOut:
        """Create a new container with network configuration."""
        try:
            # Prepare container configuration
            container_config = {
                "Image": data.image,
                "Hostname": data.name,
                "ExposedPorts": {},
                "Env": [f"{key}={value}" for key, value in data.environment.items()],
                "HostConfig": {
                    "RestartPolicy": {
                        "Name": data.restart_policy
                    },
                    "PortBindings": {},
                    "Binds": [f"{host_path}:{container_path}" for host_path, container_path in data.volumes.items()]
                }
            }
            
            # Add port mappings
            for port_mapping in data.ports:
                container_port = f"{port_mapping.container_port}/{port_mapping.protocol}"
                host_port = str(port_mapping.host_port)
                
                container_config["ExposedPorts"][container_port] = {}
                container_config["HostConfig"]["PortBindings"][container_port] = [
                    {"HostPort": host_port}
                ]
            
            # Set network mode to a custom network
            container_config["HostConfig"]["NetworkMode"] = f"vlan{data.network_config.vlan_id}"
            
            # Create the container
            response = self._docker_api_request('POST', 'containers/create', {
                "name": data.name,
                **container_config
            })
            
            container_id = response['Id']
            
            # Start the container
            self._docker_api_request('POST', f'containers/{container_id}/start')
            
            # Get the created container
            return self.get_container(data.name)
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    def update_container(self, name: str, data: ContainerUpdate) -> ContainerOut:
        """Update an existing container."""
        try:
            # Get the existing container
            container = self.get_container(name)
            
            # Stop the container
            self._docker_api_request('POST', f'containers/{container.id}/stop')
            
            # Remove the container
            self._docker_api_request('DELETE', f'containers/{container.id}')
            
            # Create a new container with the updated configuration
            return self.create_container(ContainerCreate(
                name=name,
                image=data.image if data.image is not None else container.image,
                network_config=data.network_config if data.network_config is not None else container.network_config,
                environment=data.environment if data.environment is not None else container.environment,
                ports=data.ports if data.ports is not None else container.ports,
                volumes=data.volumes if data.volumes is not None else container.volumes,
                restart_policy=data.restart_policy if data.restart_policy is not None else container.restart_policy
            ))
        except Exception as e:
            logger.error(f"Failed to update container: {e}")
            raise
    
    def delete_container(self, name: str) -> bool:
        """Delete a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Stop the container
            self._docker_api_request('POST', f'containers/{container.id}/stop')
            
            # Remove the container
            self._docker_api_request('DELETE', f'containers/{container.id}')
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete container: {e}")
            return False
    
    def start_container(self, name: str) -> Dict[str, Any]:
        """Start a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Start the container
            self._docker_api_request('POST', f'containers/{container.id}/start')
            
            return {"success": True, "message": f"Container {name} started"}
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    def stop_container(self, name: str) -> Dict[str, Any]:
        """Stop a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Stop the container
            self._docker_api_request('POST', f'containers/{container.id}/stop')
            
            return {"success": True, "message": f"Container {name} stopped"}
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            raise
    
    def restart_container(self, name: str) -> Dict[str, Any]:
        """Restart a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Restart the container
            self._docker_api_request('POST', f'containers/{container.id}/restart')
            
            return {"success": True, "message": f"Container {name} restarted"}
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            raise
    
    def add_port(self, name: str, port_mapping: PortMapping) -> Dict[str, Any]:
        """Add a port mapping to a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Update the container with the new port mapping
            updated_ports = list(container.ports)
            updated_ports.append(port_mapping)
            
            self.update_container(name, ContainerUpdate(
                name=name,
                ports=updated_ports
            ))
            
            return {"success": True, "message": f"Port mapping added to container {name}"}
        except Exception as e:
            logger.error(f"Failed to add port mapping: {e}")
            raise
    
    def remove_port(self, name: str, host_port: int, protocol: Protocol) -> bool:
        """Remove a port mapping from a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Update the container without the specified port mapping
            updated_ports = [
                p for p in container.ports
                if not (p.host_port == host_port and p.protocol == protocol)
            ]
            
            self.update_container(name, ContainerUpdate(
                name=name,
                ports=updated_ports
            ))
            
            return True
        except Exception as e:
            logger.error(f"Failed to remove port mapping: {e}")
            return False
    
    def update_network_config(self, name: str, network_config: ContainerNetworkConfig) -> Dict[str, Any]:
        """Update the network configuration for a container."""
        try:
            # Get the container
            container = self.get_container(name)
            
            # Update the container with the new network configuration
            self.update_container(name, ContainerUpdate(
                name=name,
                network_config=network_config
            ))
            
            return {
                "success": True,
                "message": f"Network configuration updated for container {name}",
                "network_config": network_config.dict()
            }
        except Exception as e:
            logger.error(f"Failed to update network configuration: {e}")
            raise
    
    def deploy_container(self, data: ContainerCreate) -> ContainerOut:
        """
        Deploy a container with network configuration, firewall rules, and HAProxy configuration if needed.
        
        This is a high-level operation that:
        1. Creates the container
        2. Sets up network (VLAN, IP, etc.)
        3. Configures firewall rules for port mappings
        4. Sets up HAProxy for web services if needed
        """
        try:
            # Step 1: Create the VLAN if it doesn't exist
            network_config = data.network_config
            vlans = self.config_service.get_vlans()
            
            vlan_exists = False
            for vlan in vlans:
                if (vlan.parent_if == network_config.parent_interface and 
                    vlan.vlan_tag == network_config.vlan_id):
                    vlan_exists = True
                    break
            
            if not vlan_exists:
                from OPNSense.api.models.network import VlanCreate
                
                self.config_service.create_vlan(VlanCreate(
                    parent_if=network_config.parent_interface,
                    vlan_tag=network_config.vlan_id,
                    description=f"Container {data.name} VLAN"
                ))
            
            # Step 2: Create DHCP static mapping
            from OPNSense.api.models.dhcp import DHCPStaticMappingCreate
            
            interface_name = f"opt{network_config.vlan_id}"
            
            try:
                self.config_service.create_static_mapping(
                    interface=interface_name,
                    data=DHCPStaticMappingCreate(
                        mac=network_config.mac_address,
                        ipaddr=network_config.ip_address,
                        hostname=data.name,
                        description=f"Container {data.name}"
                    )
                )
            except NotImplementedError:
                # DHCP static mapping not implemented yet, log and continue
                logger.warning("DHCP static mapping not implemented, skipping")
            
            # Step 3: Create firewall rules for port mappings
            if network_config.allow_internet:
                from OPNSense.api.models.firewall import FirewallRuleCreate, FirewallEndpoint, RuleAction, Protocol, IPProtocol
                
                try:
                    # Create a rule to allow internet access
                    self.config_service.create_firewall_rule(FirewallRuleCreate(
                        type=RuleAction.PASS,
                        interface=interface_name,
                        ipprotocol=IPProtocol.INET,
                        protocol=Protocol.ANY,
                        source=FirewallEndpoint(network=interface_name),
                        destination=FirewallEndpoint(any=True),
                        description=f"Allow {data.name} Internet Access"
                    ))
                except NotImplementedError:
                    # Firewall rule not implemented yet, log and continue
                    logger.warning("Firewall rule not implemented, skipping")
            
            # Step 4: Create port forwarding rules
            for port in data.ports:
                from OPNSense.api.models.firewall import PortForwardCreate
                
                try:
                    self.config_service.create_port_forward(PortForwardCreate(
                        interface="wan",  # Assuming WAN interface is named "wan"
                        protocol=port.protocol,
                        src_port=str(port.host_port),
                        dst_ip=network_config.ip_address,
                        dst_port=str(port.container_port),
                        description=f"Container {data.name} Port Forward"
                    ))
                except NotImplementedError:
                    # Port forwarding not implemented yet, log and continue
                    logger.warning("Port forwarding not implemented, skipping")
            
            # Step 5: Set up HAProxy for web services if needed
            http_ports = [p for p in data.ports if p.container_port in (80, 443)]
            if http_ports:
                # This would be implemented to configure HAProxy, but for now we'll just log
                logger.info(f"HTTP port mappings detected for {data.name}, HAProxy configuration required")
            
            # Step 6: Create the container
            container = self.create_container(data)
            
            # Apply all changes in OPNsense
            try:
                self.config_service.apply_firewall_changes()
                self.config_service.apply_dhcp_changes()
            except NotImplementedError:
                # Applying changes not implemented yet, log and continue
                logger.warning("Applying changes not implemented, skipping")
            
            return container
        except Exception as e:
            logger.error(f"Failed to deploy container: {e}")
            raise
    
    def _extract_network_config(self, network_info: Dict[str, Any]) -> ContainerNetworkConfig:
        """Extract network configuration from container network settings."""
        # This is a placeholder implementation
        # In a real implementation, we would extract this from the container's network settings
        # For now, we'll return a default network config
        return ContainerNetworkConfig(
            vlan_id=100,
            ip_address="192.168.100.2",
            mac_address="00:00:00:00:00:00",
            parent_interface="igc2",
            allow_internet=True
        )
    
    def _extract_port_mappings(self, details: Dict[str, Any]) -> List[PortMapping]:
        """Extract port mappings from container details."""
        port_mappings = []
        ports = details.get('NetworkSettings', {}).get('Ports', {})
        
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    # Parse container port and protocol (e.g., "80/tcp")
                    port_str, protocol = container_port.split('/')
                    
                    port_mapping = PortMapping(
                        host_port=int(binding['HostPort']),
                        container_port=int(port_str),
                        protocol=protocol
                    )
                    port_mappings.append(port_mapping)
        
        return port_mappings
    
    def _extract_env_vars(self, details: Dict[str, Any]) -> Dict[str, str]:
        """Extract environment variables from container details."""
        env_vars = {}
        env_list = details.get('Config', {}).get('Env', [])
        
        for env in env_list:
            if '=' in env:
                key, value = env.split('=', 1)
                env_vars[key] = value
        
        return env_vars
    
    def _extract_volumes(self, details: Dict[str, Any]) -> Dict[str, str]:
        """Extract volumes from container details."""
        volumes = {}
        binds = details.get('HostConfig', {}).get('Binds', [])
        
        for bind in binds:
            if ':' in bind:
                host_path, container_path = bind.split(':', 1)
                volumes[host_path] = container_path
        
        return volumes
