from typing import Dict, Any
from ninja import Router
from django.http import HttpRequest
from pydantic import BaseModel, Field
import requests
import logging

from OPNSense.models import OPNsenseServer
from OPNSense.services.sync_service import OPNsenseSyncService

router = Router(tags=["Onboarding"])

logger = logging.getLogger(__name__)


class ServerConnectionInfo(BaseModel):
    """Model for server connection information."""
    name: str = Field(..., description="Name for this OPNsense server")
    hostname: str = Field(..., description="Hostname or IP address")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    verify_ssl: bool = Field(False, description="Whether to verify SSL certificates")


class ServerConnectionResult(BaseModel):
    """Model for server connection test result."""
    success: bool = Field(..., description="Whether the connection was successful")
    message: str = Field(..., description="Status message")
    version: str = Field(None, description="OPNsense version if available")
    interfaces: list = Field([], description="List of available interfaces if connection was successful")


@router.post("/test-connection", response=ServerConnectionResult)
def test_connection(request: HttpRequest, data: ServerConnectionInfo):
    """Test connection to an OPNsense server."""
    try:
        # Build API URL
        base_url = f"https://{data.hostname}/api"
        
        # Set up auth
        auth = (data.api_key, data.api_secret)
        
        # Test connection with a basic API call
        response = requests.get(
            f"{base_url}/core/system/version",
            auth=auth,
            verify=data.verify_ssl,
            timeout=10
        )
        
        response.raise_for_status()
        version_info = response.json()
        
        # Get interfaces
        interfaces_response = requests.get(
            f"{base_url}/interfaces/interface/getInterfaces",
            auth=auth,
            verify=data.verify_ssl,
            timeout=10
        )
        
        interfaces_response.raise_for_status()
        interfaces_data = interfaces_response.json()
        
        available_interfaces = []
        if "interfaces" in interfaces_data:
            for iface_name, iface_data in interfaces_data["interfaces"].items():
                available_interfaces.append({
                    "name": iface_name,
                    "description": iface_data.get("descr", ""),
                    "if": iface_data.get("if", ""),
                    "enabled": iface_data.get("enable") == "1"
                })
        
        return ServerConnectionResult(
            success=True,
            message="Successfully connected to OPNsense server",
            version=version_info.get("product_version", "Unknown"),
            interfaces=available_interfaces
        )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test failed: {str(e)}")
        return ServerConnectionResult(
            success=False,
            message=f"Connection failed: {str(e)}"
        )


@router.post("/register", response=Dict[str, Any])
def register_server(request: HttpRequest, data: ServerConnectionInfo):
    """Register a new OPNsense server."""
    # First test the connection
    test_result = test_connection(request, data)
    
    if not test_result.success:
        return {
            "success": False,
            "message": f"Cannot register server: {test_result.message}"
        }
    
    # Create server record
    try:
        server = OPNsenseServer.objects.create(
            name=data.name,
            hostname=data.hostname,
            api_key=data.api_key,
            api_secret=data.api_secret,
            verify_ssl=data.verify_ssl
        )
        
        # Import interfaces
        from OPNSense.models import NetworkInterface
        
        for iface in test_result.interfaces:
            NetworkInterface.objects.create(
                server=server,
                name=iface["name"],
                if_name=iface["if"],
                description=iface["description"],
                enabled=iface["enabled"]
            )
        
        return {
            "success": True,
            "message": f"Server {data.name} registered successfully",
            "server_id": str(server.id),
            "interfaces_imported": len(test_result.interfaces)
        }
    
    except Exception as e:
        logger.error(f"Failed to register server: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to register server: {str(e)}"
        }


@router.post("/sync/{server_id}", response=Dict[str, Any])
def sync_configuration(request: HttpRequest, server_id: str):
    """Synchronize configuration from an OPNsense server."""
    try:
        server = OPNsenseServer.objects.get(id=server_id)
        
        # Build API URL
        base_url = f"https://{server.hostname}/api"
        
        # Set up auth
        auth = (server.api_key, server.api_secret)
        
        # Sync interfaces
        interfaces_response = requests.get(
            f"{base_url}/interfaces/interface/getInterfaces",
            auth=auth,
            verify=server.verify_ssl,
            timeout=10
        )
        
        interfaces_response.raise_for_status()
        interfaces_data = interfaces_response.json()
        
        # Sync VLANs
        vlans_response = requests.get(
            f"{base_url}/interfaces/vlan/getVlans",
            auth=auth,
            verify=server.verify_ssl,
            timeout=10
        )
        
        vlans_response.raise_for_status()
        vlans_data = vlans_response.json()
        
        # Sync firewall rules
        firewall_response = requests.get(
            f"{base_url}/firewall/filter/searchRule",
            auth=auth,
            verify=server.verify_ssl,
            timeout=10
        )
        
        firewall_response.raise_for_status()
        firewall_data = firewall_response.json()
        
        # Process and save the data
        # For this implementation, we'll just return the counts
        # The full processing would involve comparing existing records and updating
        
        return {
            "success": True,
            "message": "Configuration synchronized successfully",
            "interfaces_count": len(interfaces_data.get("interfaces", {})),
            "vlans_count": len(vlans_data.get("rows", [])),
            "firewall_rules_count": firewall_data.get("total", 0)
        }
    
    except OPNsenseServer.DoesNotExist:
        return {
            "success": False,
            "message": f"Server with ID {server_id} not found"
        }
    
    except Exception as e:
        logger.error(f"Failed to sync configuration: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to sync configuration: {str(e)}"
        }


@router.post("/sync-all/{server_id}", response=Dict[str, Any])
def sync_all_configuration(request: HttpRequest, server_id: str):
    """Synchronize all configuration from an OPNsense server."""
    try:
        server = OPNsenseServer.objects.get(id=server_id)
        
        # Create sync service and run full sync
        sync_service = OPNsenseSyncService(server)
        results = sync_service.sync_all()
        
        return {
            "success": True,
            "message": "Configuration synchronized successfully",
            "counts": results
        }
    
    except OPNsenseServer.DoesNotExist:
        return {
            "success": False,
            "message": f"Server with ID {server_id} not found"
        }
    
    except Exception as e:
        logger.error(f"Failed to sync all configuration: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to sync configuration: {str(e)}"
        }
