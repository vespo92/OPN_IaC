#!/usr/bin/env python3
"""
OPNsense Infrastructure as Code CLI

This module provides a command-line interface for the OPNsense IaC tool.
"""

import argparse
import sys
import os
import logging
import yaml
import json
from typing import Dict, List, Optional, Any

from opnsense_iac.config_manager import OPNsenseConfigManager
from opnsense_iac.api.client import OPNsenseAPIClient
from opnsense_iac.models.interface import Interface, VLANInterface
from opnsense_iac.models.vlan import VLAN
from opnsense_iac.models.firewall import FirewallRule, FirewallEndpoint, RuleAction, Protocol, IPProtocol
from opnsense_iac.models.dhcp import DHCPStaticMapping

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        raise


def get_api_client(config: Dict[str, Any]) -> OPNsenseAPIClient:
    """
    Create an API client from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        OPNsenseAPIClient
    """
    api_config = config.get('api', {})
    
    # Check required configuration
    required_fields = ['url', 'key', 'secret']
    for field in required_fields:
        if field not in api_config:
            raise ValueError(f"Missing required API configuration field: {field}")
    
    # Create API client
    client = OPNsenseAPIClient(
        base_url=api_config['url'],
        api_key=api_config['key'],
        api_secret=api_config['secret'],
        verify_ssl=api_config.get('verify_ssl', False)
    )
    
    return client


def get_config_manager(config: Dict[str, Any]) -> OPNsenseConfigManager:
    """
    Create a configuration manager from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        OPNsenseConfigManager
    """
    file_config = config.get('file', {})
    
    # Check required configuration
    if 'path' not in file_config:
        raise ValueError("Missing required file configuration field: path")
    
    # Create configuration manager
    manager = OPNsenseConfigManager(
        config_path=file_config['path'],
        backup_enabled=file_config.get('backup_enabled', True)
    )
    
    return manager


def command_list_interfaces(args, config):
    """List all network interfaces."""
    manager = get_config_manager(config)
    interfaces = manager.get_interfaces()
    
    if args.format == 'json':
        print(json.dumps(interfaces, indent=2))
    else:
        print("Network Interfaces:")
        print("===================")
        for name, iface in interfaces.items():
            if name != 'wan' and name != 'lan':
                # Skip non-user interfaces
                if name.startswith('lo'):
                    continue
                
                enabled = iface.get('enable') == '1'
                status = "ENABLED" if enabled else "DISABLED"
                
                print(f"- {name} ({iface.get('if', 'unknown')}): {iface.get('descr', '')}")
                print(f"  Status: {status}")
                print(f"  IP Address: {iface.get('ipaddr', 'N/A')}")
                if iface.get('subnet'):
                    print(f"  Subnet: /{iface.get('subnet')}")
                print()


def command_list_vlans(args, config):
    """List all VLANs."""
    manager = get_config_manager(config)
    vlans = manager.get_vlans()
    
    if args.format == 'json':
        print(json.dumps(vlans, indent=2))
    else:
        print("VLANs:")
        print("======")
        for vlan in vlans:
            print(f"- VLAN {vlan.get('tag')} on {vlan.get('if')}: {vlan.get('descr', '')}")
            print(f"  Interface: {vlan.get('vlanif')}")
            print()


def command_add_vlan(args, config):
    """Add a new VLAN."""
    manager = get_config_manager(config)
    uuid = manager.add_vlan(
        interface=args.interface,
        tag=args.tag,
        description=args.description
    )
    
    # Save changes
    manager.save_config()
    
    print(f"Added VLAN {args.tag} on {args.interface} with UUID: {uuid}")
    print("Note: You may need to restart OPNsense to apply the changes.")


def command_deploy_container(args, config):
    """Deploy network configuration for a container."""
    manager = get_config_manager(config)
    
    # Deploy container network
    result = manager.deploy_network_for_container(
        container_name=args.name,
        vlan_id=args.vlan_id,
        ip_address=args.ip_address,
        mac_address=args.mac_address,
        parent_interface=args.parent_interface,
        allow_internet=not args.no_internet
    )
    
    # Save changes
    manager.save_config()
    
    print(f"Deployed network configuration for container '{args.name}':")
    print(f"- VLAN UUID: {result['vlan_uuid']}")
    print(f"- DHCP Mapping: {'Added' if result['dhcp_mapping'] else 'Failed'}")
    
    if result['firewall_rules']:
        print(f"- Firewall Rules:")
        for rule_uuid in result['firewall_rules']:
            print(f"  - {rule_uuid}")
    
    print("\nNote: You may need to restart OPNsense to apply the changes.")


def command_generate_config(args, config):
    """Generate a configuration template."""
    template = {
        "api": {
            "url": "https://opnsense.example.com/api",
            "key": "your_api_key",
            "secret": "your_api_secret",
            "verify_ssl": False
        },
        "file": {
            "path": "/path/to/config.xml",
            "backup_enabled": True
        },
        "defaults": {
            "parent_interface": "igc2",
            "allow_internet": True,
            "vlan_base": 100
        }
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
        print(f"Configuration template written to {args.output}")
    else:
        print(yaml.dump(template, default_flow_style=False))


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='OPNsense Infrastructure as Code CLI')
    parser.add_argument('--config', '-c', help='Path to configuration YAML file')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List interfaces command
    parser_list_interfaces = subparsers.add_parser('list-interfaces', help='List network interfaces')
    
    # List VLANs command
    parser_list_vlans = subparsers.add_parser('list-vlans', help='List VLANs')
    
    # Add VLAN command
    parser_add_vlan = subparsers.add_parser('add-vlan', help='Add a new VLAN')
    parser_add_vlan.add_argument('--interface', '-i', required=True, help='Parent interface (e.g., igc0)')
    parser_add_vlan.add_argument('--tag', '-t', type=int, required=True, help='VLAN tag (1-4094)')
    parser_add_vlan.add_argument('--description', '-d', default='', help='Description')
    
    # Deploy container command
    parser_deploy_container = subparsers.add_parser('deploy-container', help='Deploy network configuration for a container')
    parser_deploy_container.add_argument('--name', '-n', required=True, help='Container name')
    parser_deploy_container.add_argument('--vlan-id', '-v', type=int, required=True, help='VLAN ID')
    parser_deploy_container.add_argument('--ip-address', '-i', required=True, help='IP address')
    parser_deploy_container.add_argument('--mac-address', '-m', required=True, help='MAC address')
    parser_deploy_container.add_argument('--parent-interface', '-p', default='igc2', help='Parent interface')
    parser_deploy_container.add_argument('--no-internet', action='store_true', help='Disable internet access')
    
    # Generate config command
    parser_generate_config = subparsers.add_parser('generate-config', help='Generate a configuration template')
    parser_generate_config.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    # Handle generate-config specially (doesn't require config file)
    if args.command == 'generate-config':
        command_generate_config(args, None)
        return 0
    
    # Check if command is provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Load configuration
    if not args.config:
        logger.error("Configuration file is required. Use --config or -c option.")
        return 1
    
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Execute command
    try:
        if args.command == 'list-interfaces':
            command_list_interfaces(args, config)
        elif args.command == 'list-vlans':
            command_list_vlans(args, config)
        elif args.command == 'add-vlan':
            command_add_vlan(args, config)
        elif args.command == 'deploy-container':
            command_deploy_container(args, config)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())