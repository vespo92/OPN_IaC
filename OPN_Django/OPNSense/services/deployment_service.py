import logging
from typing import Dict, Any, List, Optional
from ..models import Container, VLAN, NetworkInterface, PortForward

logger = logging.getLogger(__name__)

class DeploymentService:
    """Service for handling deployments with conflict detection."""
    
    @staticmethod
    def detect_conflicts(deployment: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Detect potential conflicts between a deployment and existing configuration.
        
        Args:
            deployment: Deployment configuration
            
        Returns:
            Dictionary with conflict types and descriptions
        """
        conflicts = {
            "vlan": [],
            "ip": [],
            "mac": [],
            "port": [],
        }
        
        # Extract network config
        network_config = deployment.get("network_config", {})
        vlan_id = network_config.get("vlan_id")
        ip_address = network_config.get("ip_address")
        mac_address = network_config.get("mac_address")
        ports = deployment.get("ports", [])
        
        # Check VLAN conflicts
        existing_vlan = VLAN.objects.filter(vlan_tag=vlan_id).first()
        if existing_vlan and existing_vlan.description != f"Container {deployment.get('name')} VLAN":
            conflicts["vlan"].append(
                f"VLAN {vlan_id} is already in use by '{existing_vlan.description}'"
            )
        
        # Check IP address conflicts
        existing_iface = NetworkInterface.objects.filter(ipaddr=ip_address).first()
        if existing_iface:
            conflicts["ip"].append(
                f"IP address {ip_address} is already assigned to interface '{existing_iface.name}'"
            )
            
        existing_container = Container.objects.filter(ip_address=ip_address).exclude(name=deployment.get("name")).first()
        if existing_container:
            conflicts["ip"].append(
                f"IP address {ip_address} is already assigned to container '{existing_container.name}'"
            )
        
        # Check MAC address conflicts
        existing_mac_container = Container.objects.filter(mac_address=mac_address).exclude(name=deployment.get("name")).first()
        if existing_mac_container:
            conflicts["mac"].append(
                f"MAC address {mac_address} is already assigned to container '{existing_mac_container.name}'"
            )
        
        # Check port conflicts
        for port in ports:
            host_port = port.get("host_port")
            protocol = port.get("protocol", "tcp")
            
            existing_port = PortForward.objects.filter(
                src_port=str(host_port),
                protocol=protocol
            ).first()
            
            if existing_port:
                conflicts["port"].append(
                    f"Port {host_port}/{protocol} is already forwarded to {existing_port.dst_ip}:{existing_port.dst_port}"
                )
                
            existing_container_port = Container.objects.filter(
                ports__contains=[{"host_port": host_port, "protocol": protocol}]
            ).exclude(name=deployment.get("name")).first()
            
            if existing_container_port:
                conflicts["port"].append(
                    f"Port {host_port}/{protocol} is already used by container '{existing_container_port.name}'"
                )
        
        # Remove empty conflict categories
        return {k: v for k, v in conflicts.items() if v}
    
    @staticmethod
    def validate_deployment(deployment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a deployment by checking for conflicts and other issues.
        
        Args:
            deployment: Deployment configuration
            
        Returns:
            Validation result with status and messages
        """
        # Check for conflicts
        conflicts = DeploymentService.detect_conflicts(deployment)
        
        if conflicts:
            return {
                "valid": False,
                "conflicts": conflicts,
                "message": "Deployment would conflict with existing configuration"
            }
        
        # All checks passed
        return {
            "valid": True,
            "message": "Deployment validation successful"
        }
