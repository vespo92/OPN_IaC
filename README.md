# OPNsense Infrastructure as Code

A Django and Bun-based tool for managing OPNsense firewall configurations as code. This project provides a REST API built with Django Ninja for infrastructure management and a CLI for easy deployment.

## Features

- REST API for OPNsense management (Django Ninja)
- Container deployment with network configuration
- VLAN management
- Firewall rules and port forwarding
- DHCP configuration
- HAProxy setup for web services
- CLI for easy management

## Requirements

- Docker and Docker Compose
- Bun (for frontend and CLI)
- Python 3.11+
- OPNsense firewall with API access

## Getting Started

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd OPN_IaC
   ```

2. Build and start the services:
   ```
   docker-compose up -d
   ```

3. Create a superuser for admin access:
   ```
   docker-compose exec web python OPN_Django/manage.py createsuperuser
   ```

4. Set up the CLI:
   ```
   mv cli-package.json package.json
   bun install
   bun link
   ```

### Usage

#### Web UI

Access the admin interface at http://localhost:8000/admin

API documentation is available at http://localhost:8000/api/docs

#### CLI

The CLI provides several commands for managing infrastructure:

```
# List all containers
opn-cli list-containers

# Deploy a container from a YAML file
opn-cli deploy samples/web-app.yaml

# Create a new VLAN
opn-cli create-vlan --interface igc0 --tag 100 --description "Web Services"

# List all VLANs
opn-cli list-vlans

# Create a port forward
opn-cli create-port-forward --interface wan --protocol tcp --src-port 80 --dst-ip 192.168.100.10 --dst-port 80

# Initialize a new deployment file
opn-cli init-deployment my-deployment.yaml
```

## Configuration

### OPNsense API Configuration

Update the `.env` file or environment variables in the docker-compose.yaml with your OPNsense API details:

```
OPNSENSE_API_URL=https://your-opnsense-firewall/api
OPNSENSE_API_KEY=your_api_key
OPNSENSE_API_SECRET=your_api_secret
OPNSENSE_API_VERIFY_SSL=False
```

### Sample Deployments

The `samples` directory contains example deployment configurations for various services.

## Architecture

This project consists of:

1. **Django Backend**: Provides the REST API using Django Ninja
2. **Bun Server**: Serves the frontend and proxies API requests to Django
3. **Postgres Database**: Stores configuration and deployment history
4. **Docker Proxy**: Allows secure communication with the Docker API

## Deployment Workflow

1. Define your infrastructure as YAML files
2. Use the CLI or API to deploy containers and configure networking
3. The system handles:
   - VLAN creation
   - IP and MAC address assignment
   - Firewall rules
   - Port forwarding
   - HAProxy configuration for web services

## Development

### API Development

The API is built with Django Ninja and follows OpenAPI specifications. Add new endpoints in the `OPN_Django/OPNSense/api/endpoints/` directory.

### Frontend Development

The frontend code is in the `frontend` directory. Use Bun for development:

```
cd frontend
bun install
bun run dev
```

## License

[MIT License](LICENSE)
