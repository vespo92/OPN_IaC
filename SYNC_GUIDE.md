# OPNsense Configuration Synchronization Guide

This guide explains how to use the OPNsense configuration synchronization features to ensure deployments are cognizant of the current running configuration on your OPNsense firewall.

## Understanding Configuration Sync

The OPNsense IaC tool maintains a local database copy of your OPNsense configuration to:

1. Detect conflicts before deployment
2. Ensure changes made outside the system are recognized
3. Provide a history of configuration changes
4. Enable rollback capabilities

## Synchronization Methods

### 1. CLI Sync Command

The most straightforward way to sync configuration is using the CLI:

```bash
# Sync configuration from a specific OPNsense server
opn-cli sync <server-id>
```

This will fetch the current configuration from your OPNsense firewall and update the local database, including:
- Network interfaces
- VLANs
- Firewall rules
- Port forwards
- DHCP configurations
- Static DHCP mappings

### 2. API Endpoint

You can also trigger synchronization via the API:

```bash
curl -X POST http://your-vm-ip:8000/api/onboarding/sync-all/<server-id> \
  -H "X-API-Key: your-api-key"
```

### 3. Utility Script

For automated synchronization, use the included utility script:

```bash
# Direct database access (run on the VM)
python sync_opnsense.py --server-id <server-id>

# Using the REST API (can be run remotely)
python sync_opnsense.py --server-id <server-id> --use-api
```

You can schedule this script to run periodically using cron:

```bash
# Add to crontab to run every hour
0 * * * * /path/to/sync_opnsense.py --server-id <server-id>
```

## Conflict Detection

When deploying new infrastructure, the system automatically checks for potential conflicts with existing configuration:

### Types of Conflicts Detected

1. **VLAN Conflicts**: Attempting to use a VLAN ID that's already in use
2. **IP Address Conflicts**: Assigning an IP address already in use by another interface or container
3. **MAC Address Conflicts**: Using a MAC address already assigned to another container
4. **Port Conflicts**: Forwarding a port that's already in use by another service

### Conflict Resolution

When conflicts are detected, the deployment will fail with detailed information about the conflicts. You can:

1. Modify your deployment configuration to avoid the conflicts
2. Manually resolve the conflicts in OPNsense
3. Use the `--force` option to override (use with caution)

## Best Practices

1. **Sync Before Deployment**: Always sync your configuration before deploying new infrastructure
   ```bash
   opn-cli sync <server-id> && opn-cli deploy my-deployment.yaml
   ```

2. **Regular Synchronization**: Schedule automatic synchronization to run hourly or daily

3. **Post-Change Sync**: After making manual changes in the OPNsense UI, run a sync to update the local database

4. **Validate Deployments**: Use the CLI's validation feature to check for conflicts without actually deploying
   ```bash
   opn-cli validate my-deployment.yaml
   ```

## Troubleshooting

### Sync Failures

If synchronization fails, check:

1. OPNsense API connectivity
2. API credentials validity
3. Network connectivity between the VM and OPNsense
4. OPNsense firewall rules allowing API access

### Conflict Resolution

When encountering conflicts:

1. Review the specific conflicts in the error message
2. Check the current OPNsense configuration to understand what's conflicting
3. Update your deployment configuration accordingly

## Monitoring Sync Status

To monitor the sync status:

```bash
# View sync history
opn-cli sync-status <server-id>

# Check last successful sync time
opn-cli sync-info <server-id>
```

This ensures your deployments are always aware of the current state of your OPNsense firewall.
