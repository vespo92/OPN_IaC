# OPNsense IaC Setup Guide

This guide will help you set up the OPNsense Infrastructure as Code (IaC) tool on a VM that's on the same subnet as your OPNsense host.

## Prerequisites

1. A VM running Linux (Ubuntu 22.04 LTS recommended)
2. Docker and Docker Compose installed
3. Bun runtime installed
4. OPNsense firewall with API access enabled
5. Network connectivity between the VM and the OPNsense host

## Step 1: Configure OPNsense for API Access

Before you can use this tool, you need to enable and configure API access on your OPNsense firewall:

1. Log in to your OPNsense web interface
2. Navigate to **System > Access > Users**
3. Select your admin user or create a dedicated API user
4. Go to the **API Keys** tab
5. Click on the **+** button to generate a new key
6. Note down the **Key** and **Secret** as you'll need them later

## Step 2: Set Up Firewall Rules

Ensure that your OPNsense firewall allows API access from your VM:

1. Navigate to **Firewall > Rules**
2. Select the interface where your VM is connected
3. Add a rule to allow HTTPS traffic (port 443) from your VM to the OPNsense host
4. Apply the changes

## Step 3: Deploy the IaC VM

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/OPN_IaC.git
   cd OPN_IaC
   ```

2. Update environment variables:
   ```bash
   cp .env.example .env
   ```
   
3. Edit the `.env` file with your settings:
   ```
   DEBUG=False
   DJANGO_ALLOWED_HOSTS=your-vm-hostname,your-vm-ip
   SECRET_KEY=generate-a-secure-random-key
   POSTGRES_DB=opn_django
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=choose-a-secure-password
   ```

4. Build and start the services:
   ```bash
   docker-compose up -d
   ```

5. Create a Django admin user:
   ```bash
   docker-compose exec web python OPN_Django/manage.py createsuperuser
   ```

6. Set up the CLI:
   ```bash
   mv cli-package.json package.json
   bun install
   bun link
   ```

## Step 4: Onboard Your OPNsense Host

You can onboard your OPNsense host in one of two ways:

### Option 1: Using the CLI (Recommended)

Use the interactive onboarding process:

```bash
opn-cli onboard -i
```

Follow the prompts to enter your OPNsense host details.

### Option 2: Using the API Directly

1. Test the connection:
   ```bash
   curl -X POST http://localhost:8000/api/onboarding/test-connection \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-key" \
     -d '{
       "name": "My OPNsense",
       "hostname": "your-opnsense-ip",
       "api_key": "your-api-key",
       "api_secret": "your-api-secret",
       "verify_ssl": false
     }'
   ```

2. Register the server:
   ```bash
   curl -X POST http://localhost:8000/api/onboarding/register \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-key" \
     -d '{
       "name": "My OPNsense",
       "hostname": "your-opnsense-ip",
       "api_key": "your-api-key",
       "api_secret": "your-api-secret",
       "verify_ssl": false
     }'
   ```

3. Note the `server_id` returned from the registration and synchronize the configuration:
   ```bash
   curl -X POST http://localhost:8000/api/onboarding/sync/your-server-id \
     -H "X-API-Key: dev-key"
   ```

## Step 5: Verify Deployment

1. Access the admin interface:
   ```
   http://your-vm-ip:8000/admin
   ```

2. Check that your OPNsense server appears in the list
3. Explore the imported network settings, VLANs, etc.
4. Test the API documentation at:
   ```
   http://your-vm-ip:8000/api/docs
   ```

## Network Configuration

For optimal operation, your VM should:

1. Be on the same subnet as your OPNsense host
2. Have a static IP address
3. Have unrestricted access to the OPNsense web interface port (typically 443)

## Security Considerations

1. Use HTTPS with a valid certificate for production deployments
2. Create a dedicated API user on OPNsense with appropriate permissions
3. Limit API access to only the necessary interfaces using firewall rules
4. Regularly rotate API keys
5. Use a strong password for the PostgreSQL database

## Troubleshooting

1. **Connection Issues**:
   - Verify network connectivity with `ping your-opnsense-ip`
   - Check that the API is enabled on OPNsense
   - Ensure firewall rules allow access

2. **API Authentication Errors**:
   - Verify API key and secret
   - Make sure the API user has sufficient permissions

3. **Docker Compose Errors**:
   - Check logs with `docker-compose logs`
   - Ensure all required environment variables are set

## Next Steps

After successful onboarding, you can:

1. Deploy containers with proper network configurations
2. Manage VLANs and firewall rules using the API or CLI
3. Set up automated deployments for your infrastructure

For more information, refer to the main [README.md](README.md) and the API documentation.
