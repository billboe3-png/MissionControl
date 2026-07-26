# Azure Deployment Guide

Deploy Mission Control to Microsoft Azure using Virtual Machines, Azure Database for PostgreSQL, Azure Cache for Redis, and Azure Load Balancer.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Azure Region                      │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         Azure Load Balancer                   │   │
│  │         (Port 80/443)                         │   │
│  └────────────────────┬─────────────────────────┘   │
│                       │                              │
│  ┌────────────────────▼─────────────────────────┐   │
│  │        Azure VM (Standard_D4s_v3)             │   │
│  │        Ubuntu 22.04                           │   │
│  │                                               │   │
│  │  ┌──────────┐  ┌────────────────────────┐   │   │
│  │  │  Nginx   │  │  Docker Compose         │   │   │
│  │  │  :80/443 │──│  Backend :8000          │   │   │
│  │  └──────────┘  │  Frontend :3000         │   │   │
│  │                └────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────┐  ┌────────────────────────┐   │
│  │  Azure Database   │  │  Azure Cache for       │   │
│  │  for PostgreSQL   │  │  Redis                 │   │
│  │  (Standard_D2s)  │  │  (Basic C1)            │   │
│  └──────────────────┘  └────────────────────────┘   │
│                                                      │
│  ┌──────────────────┐  ┌────────────────────────┐   │
│  │  Azure Blob      │  │  Azure Monitor         │   │
│  │  Storage         │  │  (Logs + Metrics)      │   │
│  └──────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and authenticated
- Domain name (optional, for SSL)

### Install Azure CLI

```bash
# Linux/macOS
curl -sL https://aka.ms/InstallAzureCLI | bash

# Windows
winget install Microsoft.AzureCLI
```

### Authenticate

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

---

## Step 1: Create Resource Group

```bash
az group create \
  --name mission-control-rg \
  --location southafricanorth
```

---

## Step 2: Create Virtual Network

```bash
# Create VNet
az network vnet create \
  --resource-group mission-control-rg \
  --name mc-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name mc-subnet \
  --subnet-prefixes 10.0.1.0/24

# Create NSG
az network nsg create \
  --resource-group mission-control-rg \
  --name mc-nsg

# Allow HTTP
az network nsg rule create \
  --resource-group mission-control-rg \
  --nsg-name mc-nsg \
  --name allow-http \
  --protocol tcp \
  --priority 100 \
  --destination-port-ranges 80 \
  --access allow \
  --direction Inbound

# Allow HTTPS
az network nsg rule create \
  --resource-group mission-control-rg \
  --nsg-name mc-nsg \
  --name allow-https \
  --protocol tcp \
  --priority 101 \
  --destination-port-ranges 443 \
  --access allow \
  --direction Inbound

# Allow SSH
az network nsg rule create \
  --resource-group mission-control-rg \
  --nsg-name mc-nsg \
  --name allow-ssh \
  --protocol tcp \
  --priority 102 \
  --destination-port-ranges 22 \
  --source-address-prefixes YOUR_IP/32 \
  --access allow \
  --direction Inbound

# Allow agent API
az network nsg rule create \
  --resource-group mission-control-rg \
  --nsg-name mc-nsg \
  --name allow-agent-api \
  --protocol tcp \
  --priority 103 \
  --destination-port-ranges 8000 \
  --access allow \
  --direction Inbound

# Associate NSG with subnet
az network vnet subnet update \
  --resource-group mission-control-rg \
  --vnet-name mc-vnet \
  --name mc-subnet \
  --network-security-group mc-nsg
```

---

## Step 3: Create Azure Database for PostgreSQL

```bash
# Generate password
DB_PASSWORD=$(openssl rand -base64 32)

# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group mission-control-rg \
  --name mc-postgres \
  --location southafricanorth \
  --admin-user mission_control \
  --admin-password "$DB_PASSWORD" \
  --sku-name Standard_D2s \
  --tier GeneralPurpose \
  --storage-size 32 \
  --backup-retention 7 \
  --high-availability ZoneRedundant \
  --version 16

# Create database
az postgres flexible-server db create \
  --resource-group mission-control-rg \
  --server-name mc-postgres \
  --database-name mission_control

# Get connection string
az postgres flexible-server show \
  --resource-group mission-control-rg \
  --name mc-postgres \
  --query 'fullyQualifiedDomainName' \
  --output text
```

---

## Step 4: Create Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --resource-group mission-control-rg \
  --name mc-redis \
  --location southafricanorth \
  --sku Basic \
  --vm-size C1

# Get Redis connection info
az redis show \
  --resource-group mission-control-rg \
  --name mc-redis \
  --query '{host:hostName,port:sslPort,primaryKey:primaryKey}' \
  --output json
```

---

## Step 5: Create Virtual Machine

```bash
# Create public IP
az network public-ip create \
  --resource-group mission-control-rg \
  --name mc-public-ip \
  --sku Standard \
  --allocation-method Static

# Create NIC
az network nic create \
  --resource-group mission-control-rg \
  --name mc-nic \
  --vnet-name mc-vnet \
  --subnet mc-subnet \
  --network-security-group mc-nsg \
  --public-ip-address mc-public-ip

# Create VM
az vm create \
  --resource-group mission-control-rg \
  --name mission-control-vm \
  --nics mc-nic \
  --image Ubuntu2204 \
  --size Standard_D4s_v3 \
  --admin-username azureuser \
  --ssh-key-value ~/.ssh/id_rsa.pub \
  --storage-sku Premium_LRS \
  --os-disk-size-gb 50 \
  --tags Project=MissionControl Environment=Production

# Get public IP
PUBLIC_IP=$(az vm show \
  --resource-group mission-control-rg \
  --name mission-control-vm \
  --query publicIps \
  --output tsv)

echo "Public IP: $PUBLIC_IP"
```

---

## Step 6: Deploy Mission Control

### SSH into VM

```bash
ssh azureuser@$PUBLIC_IP
```

### Install Docker

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker
```

### Deploy Application

```bash
cd /home/azureuser
git clone https://github.com/your-org/mission-control.git
cd mission-control

# Get Azure PostgreSQL FQDN
PG_HOST=$(az postgres flexible-server show \
  --resource-group mission-control-rg \
  --name mc-postgres \
  --query 'fullyQualifiedDomainName' \
  --output tsv)

# Get Redis connection info
REDIS_HOST=$(az redis show \
  --resource-group mission-control-rg \
  --name mc-redis \
  --query 'hostName' \
  --output tsv)

REDIS_KEY=$(az redis list-keys \
  --resource-group mission-control-rg \
  --name mc-redis \
  --query 'primaryKey' \
  --output tsv)

# Create .env
cat > .env << EOF
DB_USER=mission_control
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=mission_control
DB_HOST=${PG_HOST}
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://mission_control:${DB_PASSWORD}@${PG_HOST}:5432/mission_control

REDIS_HOST=${REDIS_HOST}
REDIS_PORT=6380
REDIS_PASSWORD=${REDIS_KEY}
REDIS_URL=rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/0

JWT_SECRET=$(openssl rand -base64 48)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY=3600
JWT_REFRESH_TOKEN_EXPIRY=2592000

CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=warning
ENVIRONMENT=production
WORKERS=4

VITE_API_URL=https://your-domain.com/api/v1
API_KEY_PREFIX=mc_agent_
EOF

# Start services
docker compose -f docker-compose.prod.yml up -d backend frontend nginx
```

---

## Step 7: Azure Load Balancer

### Create Load Balancer

```bash
# Create backend pool
az network lb address-pool create \
  --resource-group mission-control-rg \
  --lb-name mc-lb \
  --name mc-backend-pool

# Get NIC ID
NIC_ID=$(az network nic show \
  --resource-group mission-control-rg \
  --name mc-nic \
  --query id \
  --output tsv)

# Add NIC to backend pool
az network lb address-pool update \
  --resource-group mission-control-rg \
  --lb-name mc-lb \
  --name mc-backend-pool \
  --nic $NIC_ID

# Create load balancer
az network lb create \
  --resource-group mission-control-rg \
  --name mc-lb \
  --sku Standard \
  --frontend-ip-configurations mc-frontend-ip \
  --backend-pool-names mc-backend-pool \
  --public-ip-addresses mc-public-ip

# Create health probe
az network lb probe create \
  --resource-group mission-control-rg \
  --lb-name mc-lb \
  --name mc-health-probe \
  --protocol tcp \
  --port 80 \
  --interval 15 \
  --threshold 5

# Create load balancing rules
az network lb rule create \
  --resource-group mission-control-rg \
  --lb-name mc-lb \
  --name mc-http-rule \
  --protocol tcp \
  --frontend-port 80 \
  --backend-port 80 \
  --frontend-ip-configurations mc-frontend-ip \
  --backend-address-pools mc-backend-pool \
  --probe mc-health-probe

az network lb rule create \
  --resource-group mission-control-rg \
  --lb-name mc-lb \
  --name mc-https-rule \
  --protocol tcp \
  --frontend-port 443 \
  --backend-port 443 \
  --frontend-ip-configurations mc-frontend-ip \
  --backend-address-pools mc-backend-pool \
  --probe mc-health-probe
```

---

## Step 8: SSL with Azure Key Vault + Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain Certificate

```bash
sudo certbot --nginx \
  -d your-domain.com \
  -d www.your-domain.com \
  --non-interactive \
  --agree-tos \
  --email admin@your-domain.com
```

### Auto-Renew

```bash
sudo crontab -l | { cat; echo "0 0 1 * * certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | crontab -
```

---

## Step 9: Azure Blob Storage Backup

### Create Storage Account

```bash
az storage account create \
  --resource-group mission-control-rg \
  --name mcbackups$(date +%s) \
  --location southafricanorth \
  --sku Standard_LRS \
  --kind StorageV2

STORAGE_ACCOUNT=$(az storage account list \
  --resource-group mission-control-rg \
  --query '[0].name' \
  --output tsv)

az storage container create \
  --account-name $STORAGE_ACCOUNT \
  --name mission-control-backups
```

### Backup Script

```bash
sudo tee /opt/mission-control/backup.sh << 'SCRIPT'
#!/bin/bash
set -e

BACKUP_DIR="/tmp/mission-control-backups"
DATE=$(date +%Y%m%d_%H%M%S)
STORAGE_ACCOUNT=$(az storage account list \
  --resource-group mission-control-rg \
  --query '[0].name' \
  --output tsv)
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec mc-postgres pg_dump -U mission_control mission_control | \
  gzip > $BACKUP_DIR/db_${DATE}.sql.gz

# Upload to Blob Storage
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --container-name mission-control-backups \
  --name db/db_${DATE}.sql.gz \
  --file $BACKUP_DIR/db_${DATE}.sql.gz

# Cleanup
rm -rf $BACKUP_DIR

echo "Backup completed: $DATE"
SCRIPT

sudo chmod +x /opt/mission-control/backup.sh

# Schedule backups
sudo crontab -l | { cat; echo "0 2 * * * /opt/mission-control/backup.sh >> /var/log/mission-control-backup.log 2>&1"; } | crontab -
```

---

## Step 10: Azure Monitor

### Enable Monitoring

```bash
# Install Azure Monitor Agent
wget https://packages.microsoft.com/repos/azurecore/azurecore.asc | sudo tee /etc/apt/trusted.gpg.d/azurecore.asc

echo "deb [arch=amd64] https://packages.microsoft.com/repos/azurecore/ jammy main" | \
  sudo tee /etc/apt/sources.list.d/azure-core.list

sudo apt update
sudo apt install -y azure-monitor-agent
```

### Create Log Analytics Workspace

```bash
az monitor log-analytics workspace create \
  --resource-group mission-control-rg \
  --workspace-name mc-workspace \
  --location southafricanorth
```

### Create Alerts

```bash
# CPU alert
az monitor metrics alert create \
  --resource-group mission-control-rg \
  --name "MC High CPU" \
  --scopes /subscriptions/SUB_ID/resourceGroups/mission-control-rg/providers/Microsoft.Compute/virtualMachines/mission-control-vm \
  --condition "avg percentage cpu > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2

# Memory alert
az monitor metrics alert create \
  --resource-group mission-control-rg \
  --name "MC High Memory" \
  --scopes /subscriptions/SUB_ID/resourceGroups/mission-control-rg/providers/Microsoft.Compute/virtualMachines/mission-control-vm \
  --condition "avg Available Memory Bytes < 1073741824" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2
```

---

## Cost Estimation

| Resource | Specification | Monthly Cost (approx) |
|----------|---------------|----------------------|
| VM Standard_D4s_v3 | 4 vCPU, 16 GB RAM | ~$140 |
| Azure Database PostgreSQL | Standard_D2s, 2 vCPU | ~$120 |
| Azure Cache for Redis | Basic C1 | ~$45 |
| Load Balancer | Standard SKU | ~$20 |
| Storage | 50 GB managed disk | ~$8 |
| Blob Storage | 50 GB backups | ~$2 |
| **Total** | | **~$335/month** |

---

## Related Documentation

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker Compose reference
- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat configuration
- [REST_API.md](./REST_API.md) — API endpoint reference
