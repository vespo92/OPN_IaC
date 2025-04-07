#!/usr/bin/env bun

import { program } from 'commander';
import fetch from 'node-fetch';
import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import yaml from 'js-yaml';
import fs from 'fs';

// Configuration
const API_URL = process.env.API_URL || 'http://localhost:8000/api';
const API_KEY = process.env.API_KEY || 'dev-key';

// Helper function to make API requests
async function apiRequest(endpoint, method = 'GET', data = null) {
  const url = `${API_URL}/${endpoint}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    }
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`API Error (${response.status}): ${JSON.stringify(errorData)}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(chalk.red('Error making API request:'), error.message);
    throw error;
  }
}

// Define the CLI program
program
  .name('opn-cli')
  .description('OPNsense IaC CLI')
  .version('1.0.0');

// Command to list containers
program
  .command('list-containers')
  .description('List all containers')
  .action(async () => {
    const spinner = ora('Fetching containers...').start();
    
    try {
      const containers = await apiRequest('container/');
      spinner.succeed('Containers retrieved successfully');
      
      console.table(containers.map(container => ({
        Name: container.name,
        Image: container.image,
        Status: container.status,
        IP: container.network_config.ip_address,
        VLAN: container.network_config.vlan_id,
        Ports: container.ports.map(p => `${p.host_port}:${p.container_port}/${p.protocol}`).join(', ')
      })));
    } catch (error) {
      spinner.fail(chalk.red('Failed to retrieve containers'));
    }
  });

// Command to deploy a container
program
  .command('deploy')
  .description('Deploy a container from a YAML configuration file')
  .argument('<file>', 'YAML configuration file')
  .action(async (file) => {
    try {
      // Read and parse YAML file
      const config = yaml.load(fs.readFileSync(file, 'utf8'));
      const spinner = ora(`Deploying container ${config.name}...`).start();
      
      // Make API request to deploy container
      await apiRequest('container/deploy', 'POST', config);
      
      spinner.succeed(chalk.green(`Container ${config.name} deployed successfully`));
    } catch (error) {
      console.error(chalk.red('Deployment failed:'), error.message);
    }
  });

// Command to stop a container
program
  .command('stop')
  .description('Stop a container')
  .argument('<name>', 'Container name')
  .action(async (name) => {
    const spinner = ora(`Stopping container ${name}...`).start();
    
    try {
      await apiRequest(`container/${name}/stop`, 'POST');
      spinner.succeed(chalk.green(`Container ${name} stopped successfully`));
    } catch (error) {
      spinner.fail(chalk.red(`Failed to stop container ${name}`));
    }
  });

// Command to start a container
program
  .command('start')
  .description('Start a container')
  .argument('<name>', 'Container name')
  .action(async (name) => {
    const spinner = ora(`Starting container ${name}...`).start();
    
    try {
      await apiRequest(`container/${name}/start`, 'POST');
      spinner.succeed(chalk.green(`Container ${name} started successfully`));
    } catch (error) {
      spinner.fail(chalk.red(`Failed to start container ${name}`));
    }
  });

// Command to create a VLAN
program
  .command('create-vlan')
  .description('Create a new VLAN')
  .requiredOption('-i, --interface <interface>', 'Parent interface (e.g., igc0)')
  .requiredOption('-t, --tag <tag>', 'VLAN tag (1-4094)', parseInt)
  .option('-d, --description <description>', 'Optional description')
  .action(async (options) => {
    const spinner = ora(`Creating VLAN ${options.tag} on ${options.interface}...`).start();
    
    try {
      const data = {
        parent_if: options.interface,
        vlan_tag: options.tag,
        description: options.description || `VLAN ${options.tag}`
      };
      
      await apiRequest('network/vlans', 'POST', data);
      spinner.succeed(chalk.green(`VLAN ${options.tag} created successfully`));
    } catch (error) {
      spinner.fail(chalk.red(`Failed to create VLAN ${options.tag}`));
    }
  });

// Command to list VLANs
program
  .command('list-vlans')
  .description('List all VLANs')
  .action(async () => {
    const spinner = ora('Fetching VLANs...').start();
    
    try {
      const vlans = await apiRequest('network/vlans');
      spinner.succeed('VLANs retrieved successfully');
      
      console.table(vlans.map(vlan => ({
        'Parent IF': vlan.parent_if,
        'VLAN Tag': vlan.vlan_tag,
        'Interface': vlan.vlanif,
        'Description': vlan.description
      })));
    } catch (error) {
      spinner.fail(chalk.red('Failed to retrieve VLANs'));
    }
  });

// Command to onboard a new OPNsense server
program
  .command('onboard')
  .description('Register a new OPNsense server')
  .option('-n, --name <name>', 'Name for this OPNsense server')
  .option('-h, --hostname <hostname>', 'Hostname or IP address')
  .option('-k, --api-key <apiKey>', 'API key')
  .option('-s, --api-secret <apiSecret>', 'API secret')
  .option('--verify-ssl', 'Verify SSL certificates')
  .option('-i, --interactive', 'Use interactive mode')
  .action(async (options) => {
    // If interactive mode, prompt for information
    if (options.interactive) {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Name for this OPNsense server:',
          validate: input => input.trim() !== '' ? true : 'Name is required'
        },
        {
          type: 'input',
          name: 'hostname',
          message: 'Hostname or IP address:',
          validate: input => input.trim() !== '' ? true : 'Hostname is required'
        },
        {
          type: 'input',
          name: 'api_key',
          message: 'API key:',
          validate: input => input.trim() !== '' ? true : 'API key is required'
        },
        {
          type: 'input',
          name: 'api_secret',
          message: 'API secret:',
          validate: input => input.trim() !== '' ? true : 'API secret is required'
        },
        {
          type: 'confirm',
          name: 'verify_ssl',
          message: 'Verify SSL certificates?',
          default: false
        }
      ]);
      
      // Update options with answers
      options.name = answers.name;
      options.hostname = answers.hostname;
      options.apiKey = answers.api_key;
      options.apiSecret = answers.api_secret;
      options.verifySsl = answers.verify_ssl;
    }
    
    // Validate required options
    if (!options.name || !options.hostname || !options.apiKey || !options.apiSecret) {
      console.error(chalk.red('Missing required options. Use --interactive or provide all required options.'));
      return;
    }
    
    const spinner = ora('Testing connection to OPNsense server...').start();
    
    try {
      // Test connection first
      const testData = {
        name: options.name,
        hostname: options.hostname,
        api_key: options.apiKey,
        api_secret: options.apiSecret,
        verify_ssl: options.verifySsl || false
      };
      
      const testResponse = await apiRequest('onboarding/test-connection', 'POST', testData);
      
      if (!testResponse.success) {
        spinner.fail(chalk.red(`Connection test failed: ${testResponse.message}`));
        return;
      }
      
      spinner.succeed(chalk.green(`Successfully connected to ${options.hostname} (OPNsense ${testResponse.version})`));
      spinner.text = 'Registering server...';
      spinner.start();
      
      // Register the server
      const registerResponse = await apiRequest('onboarding/register', 'POST', testData);
      
      if (!registerResponse.success) {
        spinner.fail(chalk.red(`Registration failed: ${registerResponse.message}`));
        return;
      }
      
      spinner.succeed(chalk.green('Configuration synchronized successfully'));
      console.log(chalk.cyan(`Imported ${registerResponse.interfaces_imported} interfaces`));
      
      // Sync configuration
      spinner.text = 'Synchronizing configuration...';
      spinner.start();
      
      const syncResponse = await apiRequest(`onboarding/sync/${registerResponse.server_id}`, 'POST');
      
      if (!syncResponse.success) {
        spinner.fail(chalk.red(`Sync failed: ${syncResponse.message}`));
        return;
      }
      
      spinner.succeed(chalk.green('Configuration synchronized successfully'));
      console.log(chalk.cyan(`Imported:
- ${syncResponse.counts.interfaces || 0} interfaces
- ${syncResponse.counts.vlans || 0} VLANs
- ${syncResponse.counts.firewall_rules || 0} firewall rules
- ${syncResponse.counts.port_forwards || 0} port forwards
- ${syncResponse.counts.dhcp_servers || 0} DHCP servers
- ${syncResponse.counts.dhcp_static_mappings || 0} DHCP static mappings`));
    } catch (error) {
      spinner.fail(chalk.red('Onboarding failed'));
      console.error(error.message);
    }
  });

// Command to synchronize configuration
program
  .command('sync')
  .description('Synchronize configuration from OPNsense server')
  .argument('<server_id>', 'Server ID')
  .action(async (serverId) => {
    const spinner = ora('Synchronizing configuration...').start();
    
    try {
      const response = await apiRequest(`onboarding/sync-all/${serverId}`, 'POST');
      
      if (!response.success) {
        spinner.fail(chalk.red(`Sync failed: ${response.message}`));
        return;
      }
      
      spinner.succeed(chalk.green('Configuration synchronized successfully'));
      
      const counts = response.counts;
      console.log(chalk.cyan(`Synchronized:
- ${counts.interfaces || 0} interfaces
- ${counts.vlans || 0} VLANs
- ${counts.firewall_rules || 0} firewall rules
- ${counts.port_forwards || 0} port forwards
- ${counts.dhcp_servers || 0} DHCP servers
- ${counts.dhcp_static_mappings || 0} DHCP static mappings`));
    } catch (error) {
      spinner.fail(chalk.red('Synchronization failed'));
      console.error(error.message);
    }
  });

// Command to create a port forward
program
  .command('create-port-forward')
  .description('Create a new port forwarding rule')
  .requiredOption('-i, --interface <interface>', 'WAN interface name')
  .requiredOption('-p, --protocol <protocol>', 'Network protocol (tcp, udp)')
  .requiredOption('-s, --src-port <srcPort>', 'External port (WAN)')
  .requiredOption('-d, --dst-ip <dstIp>', 'Internal IP address (LAN)')
  .requiredOption('-t, --dst-port <dstPort>', 'Internal port (LAN)')
  .option('--description <description>', 'Optional description')
  .action(async (options) => {
    const spinner = ora(`Creating port forward ${options.srcPort} -> ${options.dstIp}:${options.dstPort}...`).start();
    
    try {
      const data = {
        interface: options.interface,
        protocol: options.protocol,
        src_port: options.srcPort,
        dst_ip: options.dstIp,
        dst_port: options.dstPort,
        description: options.description || `Forward ${options.srcPort} to ${options.dstIp}:${options.dstPort}`
      };
      
      await apiRequest('firewall/port-forwards', 'POST', data);
      spinner.succeed(chalk.green('Port forward created successfully'));
    } catch (error) {
      spinner.fail(chalk.red('Failed to create port forward'));
    }
  });

// Command to list port forwards
program
  .command('list-port-forwards')
  .description('List all port forwarding rules')
  .action(async () => {
    const spinner = ora('Fetching port forwards...').start();
    
    try {
      const portForwards = await apiRequest('firewall/port-forwards');
      spinner.succeed('Port forwards retrieved successfully');
      
      console.table(portForwards.map(pf => ({
        'Interface': pf.interface,
        'Protocol': pf.protocol,
        'Source Port': pf.src_port,
        'Destination IP': pf.dst_ip,
        'Destination Port': pf.dst_port,
        'Description': pf.description,
        'Enabled': pf.enabled ? 'Yes' : 'No'
      })));
    } catch (error) {
      spinner.fail(chalk.red('Failed to retrieve port forwards'));
    }
  });

// Interactive command to create a container deployment file
program
  .command('init-deployment')
  .description('Create a new container deployment YAML file')
  .argument('[file]', 'Output YAML file (default: deployment.yaml)')
  .action(async (file = 'deployment.yaml') => {
    try {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Container name:',
          validate: input => input.trim() !== '' ? true : 'Name is required'
        },
        {
          type: 'input',
          name: 'image',
          message: 'Docker image:',
          validate: input => input.trim() !== '' ? true : 'Image is required'
        },
        {
          type: 'input',
          name: 'vlan_id',
          message: 'VLAN ID:',
          default: '100',
          validate: input => !isNaN(parseInt(input)) ? true : 'VLAN ID must be a number'
        },
        {
          type: 'input',
          name: 'ip_address',
          message: 'IP address:',
          default: '192.168.100.2',
          validate: input => /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(input) ? true : 'Invalid IP address'
        },
        {
          type: 'input',
          name: 'mac_address',
          message: 'MAC address:',
          default: '00:00:00:00:00:01',
          validate: input => /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/.test(input) ? true : 'Invalid MAC address'
        },
        {
          type: 'confirm',
          name: 'allow_internet',
          message: 'Allow internet access?',
          default: true
        },
        {
          type: 'input',
          name: 'ports',
          message: 'Port mappings (host:container/protocol, comma separated):',
          default: '8080:80/tcp',
          filter: input => {
            if (!input) return [];
            
            return input.split(',').map(port => {
              const [mapping, protocol = 'tcp'] = port.split('/');
              const [host, container] = mapping.split(':');
              
              return {
                host_port: parseInt(host),
                container_port: parseInt(container),
                protocol
              };
            });
          }
        }
      ]);
      
      // Create deployment config
      const config = {
        name: answers.name,
        image: answers.image,
        network_config: {
          vlan_id: parseInt(answers.vlan_id),
          ip_address: answers.ip_address,
          mac_address: answers.mac_address,
          parent_interface: 'igc2',
          allow_internet: answers.allow_internet
        },
        ports: answers.ports,
        environment: {},
        volumes: {},
        restart_policy: 'unless-stopped'
      };
      
      // Write to file
      fs.writeFileSync(file, yaml.dump(config));
      console.log(chalk.green(`Deployment file created successfully: ${file}`));
      
    } catch (error) {
      console.error(chalk.red('Failed to create deployment file:'), error.message);
    }
  });

// Parse command line arguments
program.parse();
