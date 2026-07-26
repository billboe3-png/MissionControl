# AWS Deployment Guide

Deploy Mission Control to Amazon Web Services using EC2, RDS, ElastiCache, and Application Load Balancer.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      AWS Region                      │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              Application Load Balancer        │   │
│  │              (Port 80/443)                    │   │
│  └────────────────────┬─────────────────────────┘   │
│                       │                              │
│  ┌────────────────────▼─────────────────────────┐   │
│  │          EC2 Instance (Auto Scaling)          │   │
│  │          t3.xlarge - Ubuntu 22.04             │   │
│  │                                               │   │
│  │  ┌──────────┐  ┌────────────────────────┐   │   │
│  │  │  Nginx   │  │  Docker Compose         │   │   │
│  │  │  :80/443 │──│  Backend :8000          │   │   │
│  │  └──────────┘  │  Frontend :3000         │   │   │
│  │                └────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────┐  ┌────────────────────────┐   │
│  │   RDS PostgreSQL  │  │  ElastiCache Redis     │   │
│  │   (db.t3.medium)  │  │  (cache.t3.micro)      │   │
│  │   Port 5432       │  │  Port 6379             │   │
│  └──────────────────┘  └────────────────────────┘   │
│                                                      │
│  ┌──────────────────┐  ┌────────────────────────┐   │
│  │   S3 Bucket      │  │  CloudWatch            │   │
│  │   (Backups)      │  │  (Monitoring)          │   │
│  └──────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Prerequisites

- AWS account with appropriate IAM permissions
- AWS CLI installed and configured
- Domain name (optional, for SSL)

### Configure AWS CLI

```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: af-south-1
# Default output format: json
```

---

## Step 1: Create VPC and Networking

### Create VPC

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text)

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames

# Create public subnet
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone af-south-1a \
  --query 'Subnet.SubnetId' \
  --output text)

# Create internet gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

# Create route table and associate
RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route \
  --route-table-id $RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

aws ec2 associate-route-table \
  --route-table-id $RT_ID \
  --subnet-id $SUBNET_ID
```

---

## Step 2: Create Security Groups

```bash
# Create ALB security group
ALB_SG=$(aws ec2 create-security-group \
  --group-name mc-alb-sg \
  --description "Mission Control ALB Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Create EC2 security group
EC2_SG=$(aws ec2 create-security-group \
  --group-name mc-ec2-sg \
  --description "Mission Control EC2 Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG \
  --protocol tcp \
  --port 8000 \
  --source-group $ALB_SG

aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG \
  --protocol tcp \
  --port 3000 \
  --source-group $ALB_SG

aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Create RDS security group
RDS_SG=$(aws ec2 create-security-group \
  --group-name mc-rds-sg \
  --description "Mission Control RDS Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --source-group $EC2_SG

# Create ElastiCache security group
REDIS_SG=$(aws ec2 create-security-group \
  --group-name mc-redis-sg \
  --description "Mission Control Redis Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG \
  --protocol tcp \
  --port 6379 \
  --source-group $EC2_SG
```

---

## Step 3: Create RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name mc-db-subnet \
  --db-subnet-group-description "Mission Control DB Subnet" \
  --subnet-ids $SUBNET_ID

# Generate password
DB_PASSWORD=$(openssl rand -base64 32)

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier mission-control-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16 \
  --master-username mission_control \
  --master-user-password "$DB_PASSWORD" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids $RDS_SG \
  --db-subnet-group-name mc-db-subnet \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted \
  --no-publicly-accessible \
  --tags Key=Project,Value=MissionControl
```

---

## Step 4: Create ElastiCache Redis

```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name mc-redis-subnet \
  --cache-subnet-group-description "Mission Control Redis Subnet" \
  --subnet-ids $SUBNET_ID

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id mission-control-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --vpc-security-group-ids $REDIS_SG \
  --cache-subnet-group-name mc-redis-subnet
```

---

## Step 5: Create EC2 Instance

```bash
# Get latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text)

# Create key pair
aws ec2 create-key-pair \
  --key-name mc-prod-key \
  --query 'KeyMaterial' \
  --output text > mc-prod-key.pem

chmod 400 mc-prod-key.pem

# Create EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.xlarge \
  --key-name mc-prod-key \
  --security-group-ids $EC2_SG \
  --subnet-id $SUBNET_ID \
  --associate-public-ip-address \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mission-control-prod},{Key=Project,Value=MissionControl}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

# Allocate and associate Elastic IP
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $EIP_ALLOC

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance IP: $PUBLIC_IP"
```

---

## Step 6: Deploy Mission Control

### SSH into Instance

```bash
ssh -i mc-prod-key.pem ubuntu@$PUBLIC_IP
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
cd /home/ubuntu
git clone https://github.com/your-org/mission-control.git
cd mission-control

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier mission-control-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id mission-control-redis \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

# Create .env
cat > .env << EOF
DB_USER=mission_control
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=mission_control
DB_HOST=${RDS_ENDPOINT}
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://mission_control:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/mission_control

REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_ENDPOINT}:6379/0

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

# Start services (without local postgres/redis)
docker compose -f docker-compose.prod.yml up -d backend frontend nginx
```

---

## Step 7: Application Load Balancer

### Create Target Group

```bash
TG_ARN=$(aws elbv2 create-target-group \
  --name mc-targets \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --health-check-path /api/v1/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 3 \
  --unhealthy-threshold-count 3 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)
```

### Register Target

```bash
aws elbv2 register-targets \
  --target-group-arn $TG_ARN \
  --targets Id=$INSTANCE_ID
```

### Create ALB

```bash
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name mc-alb \
  --subnets $SUBNET_ID \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)
```

### Create Listener

```bash
# HTTPS listener (after obtaining SSL certificate)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:af-south-1:ACCOUNT:certificate/CERT_ID \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN

# HTTP redirect to HTTPS
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

### Get ALB DNS Name

```bash
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "ALB DNS: $ALB_DNS"
```

---

## Step 8: SSL with AWS Certificate Manager

```bash
# Request certificate
CERT_ARN=$(aws acm request-certificate \
  --domain-name your-domain.com \
  --subject-alternative-names www.your-domain.com \
  --validation-method DNS \
  --query 'CertificateArn' \
  --output text)

# Get validation records
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# Create DNS records (if using Route53)
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "_acme-challenge.your-domain.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"validation-value\""}]
      }
    }]
  }'
```

---

## Step 9: S3 Backup Bucket

```bash
# Create S3 bucket
aws s3 mb s3://mission-control-backups-$(aws sts get-caller-identity --query Account --output text) \
  --region af-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket mission-control-backups \
  --versioning-configuration Status=Enabled

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket mission-control-backups \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "ExpireOldBackups",
      "Status": "Enabled",
      "Expiration": {"Days": 30},
      "Transitions": [{
        "Days": 7,
        "StorageClass": "STANDARD_IA"
      }]
    }]
  }'
```

### Backup Script

```bash
sudo tee /opt/mission-control/backup.sh << 'SCRIPT'
#!/bin/bash
set -e

BACKUP_DIR="/tmp/mission-control-backups"
DATE=$(date +%Y%m%d_%H%M%S)
BUCKET="mission-control-backups-$(aws sts get-caller-identity --query Account --output text)"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec mc-postgres pg_dump -U mission_control mission_control | \
  gzip > $BACKUP_DIR/db_${DATE}.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db_${DATE}.sql.gz s3://$BUCKET/db/

# Cleanup
rm -rf $BACKUP_DIR

echo "Backup completed: $DATE"
SCRIPT

sudo chmod +x /opt/mission-control/backup.sh

# Schedule backups
sudo crontab -l | { cat; echo "0 2 * * * /opt/mission-control/backup.sh >> /var/log/mission-control-backup.log 2>&1"; } | crontab -
```

---

## Step 10: CloudWatch Monitoring

### Install CloudWatch Agent

```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### Configure CloudWatch

```bash
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/config.json << 'EOF'
{
  "metrics": {
    "namespace": "MissionControl",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "resources": ["*"],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "mission-control-nginx",
            "log_stream_name": "access"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "mission-control-nginx",
            "log_stream_name": "error"
          }
        ]
      }
    }
  }
}
EOF

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

---

## Cost Estimation

| Resource | Specification | Monthly Cost (approx) |
|----------|---------------|----------------------|
| EC2 t3.xlarge | 4 vCPU, 16 GB RAM | ~$140 |
| RDS db.t3.medium | 2 vCPU, 4 GB RAM, Multi-AZ | ~$130 |
| ElastiCache cache.t3.micro | 1 GB | ~$15 |
| ALB | Application Load Balancer | ~$22 |
| S3 | 50 GB backups | ~$2 |
| Data Transfer | 100 GB egress | ~$9 |
| **Total** | | **~$318/month** |

---

## Related Documentation

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker Compose reference
- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat configuration
- [REST_API.md](./REST_API.md) — API endpoint reference
