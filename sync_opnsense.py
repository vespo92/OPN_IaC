#!/usr/bin/env python3
"""
OPNsense Configuration Sync Utility

This script helps synchronize the configuration from an OPNsense server to the local database.
"""

import os
import sys
import logging
import argparse
import json
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_django_env():
    """Setup Django environment."""
    # Add Django project path to sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    django_project_path = os.path.join(script_dir, 'OPN_Django')
    sys.path.append(django_project_path)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OPN_Django.settings')
    
    # Import Django and setup
    import django
    django.setup()

def get_opnsense_servers():
    """Get all OPNsense servers from the database."""
    from OPNSense.models import OPNsenseServer
    return OPNsenseServer.objects.filter(is_active=True)

def sync_server(server_id=None):
    """
    Synchronize configuration from an OPNsense server.
    
    Args:
        server_id: Optional server ID to sync. If None, sync all servers.
    """
    from OPNSense.models import OPNsenseServer
    from OPNSense.services.sync_service import OPNsenseSyncService
    
    servers = []
    if server_id:
        try:
            servers = [OPNsenseServer.objects.get(id=server_id)]
        except OPNsenseServer.DoesNotExist:
            logger.error(f"Server with ID {server_id} not found")
            return False
    else:
        servers = get_opnsense_servers()
        if not servers:
            logger.error("No active OPNsense servers found")
            return False
    
    success = True
    for server in servers:
        logger.info(f"Synchronizing configuration from {server.name} ({server.hostname})...")
        
        try:
            # Create sync service
            sync_service = OPNsenseSyncService(server)
            
            # Run full sync
            start_time = datetime.now()
            results = sync_service.sync_all()
            end_time = datetime.now()
            
            # Log results
            logger.info(f"Sync completed in {(end_time - start_time).total_seconds():.2f} seconds")
            logger.info(f"Synchronized: "
                      f"{results.get('interfaces', 0)} interfaces, "
                      f"{results.get('vlans', 0)} VLANs, "
                      f"{results.get('firewall_rules', 0)} firewall rules, "
                      f"{results.get('port_forwards', 0)} port forwards, "
                      f"{results.get('dhcp_servers', 0)} DHCP servers, "
                      f"{results.get('dhcp_static_mappings', 0)} DHCP static mappings")
            
        except Exception as e:
            logger.error(f"Error synchronizing {server.name}: {e}")
            success = False
    
    return success

def rest_api_sync(server_id=None):
    """
    Synchronize configuration from an OPNsense server using the REST API.
    
    Args:
        server_id: Optional server ID to sync. If None, sync all servers.
    """
    api_url = os.environ.get('API_URL', 'http://localhost:8000/api')
    api_key = os.environ.get('API_KEY', 'dev-key')
    
    # Prepare request headers
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }
    
    if server_id:
        # Sync specific server
        url = f"{api_url}/onboarding/sync-all/{server_id}"
        
        logger.info(f"Synchronizing server {server_id} using REST API...")
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                counts = data.get('counts', {})
                logger.info(f"Sync completed successfully")
                logger.info(f"Synchronized: "
                          f"{counts.get('interfaces', 0)} interfaces, "
                          f"{counts.get('vlans', 0)} VLANs, "
                          f"{counts.get('firewall_rules', 0)} firewall rules, "
                          f"{counts.get('port_forwards', 0)} port forwards, "
                          f"{counts.get('dhcp_servers', 0)} DHCP servers, "
                          f"{counts.get('dhcp_static_mappings', 0)} DHCP static mappings")
                return True
            else:
                logger.error(f"Sync failed: {data.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Error synchronizing server {server_id}: {e}")
            return False
    else:
        # Get all servers
        try:
            # First, we need to get a list of servers
            url = f"{api_url}/servers"
            
            logger.info("Getting list of OPNsense servers...")
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            servers = response.json()
            
            if not servers:
                logger.error("No OPNsense servers found")
                return False
            
            success = True
            for server in servers:
                server_id = server.get('id')
                if not rest_api_sync(server_id):
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Error getting server list: {e}")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Synchronize OPNsense configuration')
    parser.add_argument('--server-id', help='ID of the server to synchronize')
    parser.add_argument('--use-api', action='store_true', help='Use REST API instead of direct database access')
    
    args = parser.parse_args()
    
    if args.use_api:
        # Use REST API
        if rest_api_sync(args.server_id):
            logger.info("Synchronization completed successfully")
            return 0
        else:
            logger.error("Synchronization failed")
            return 1
    else:
        # Use direct database access
        setup_django_env()
        
        if sync_server(args.server_id):
            logger.info("Synchronization completed successfully")
            return 0
        else:
            logger.error("Synchronization failed")
            return 1

if __name__ == '__main__':
    sys.exit(main())
