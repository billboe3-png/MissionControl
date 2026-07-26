# Kubernetes Deployment Guide

Deploy Mission Control to Kubernetes with production-ready manifests, Helm chart, and scaling configuration.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              Ingress Controller               │   │
│  │              (NGINX Ingress)                   │   │
│  │              Port 80/443                       │   │
│  └────────────────────┬─────────────────────────┘   │
│                       │                              │
│  ┌────────────────────▼─────────────────────────┐   │
│  │           Service: mc-backend                 │   │
│  │           ClusterIP: 8000                     │   │
│  │                                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐   │   │
│  │  │  Pod: backend-1  │  │  Pod: backend-2  │   │   │
│  │  │  (FastAPI)       │  │  (FastAPI)       │   │   │
│  │  └─────────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           Service: mc-frontend                │   │
│  │           ClusterIP: 3000                     │   │
│  │                                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐   │   │
│  │  │  Pod: frontend-1 │  │  Pod: frontend-2 │   │   │
│  │  │  (Vite/Nginx)    │  │  (Vite/Nginx)    │   │   │
│  │  └─────────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────┐  ┌────────────────────────┐   │
│  │  StatefulSet:     │  │  StatefulSet:           │   │
│  │  mc-postgres      │  │  mc-redis               │   │
│  │  (PostgreSQL 16)  │  │  (Redis 7)              │   │
│  └──────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Kubernetes cluster (1.25+)
- `kubectl` configured and connected
- `helm` 3.0+ (for Helm deployment)
- Storage class for persistent volumes

### Verify Cluster

```bash
kubectl cluster-info
kubectl get nodes
kubectl get storageclass
```

---

## Option 1: Helm Chart (Recommended)

### Install via Helm

```bash
# Add repository
helm repo add mission-control https://charts.your-domain.com
helm repo update

# Create namespace
kubectl create namespace mission-control

# Create secrets
kubectl create secret generic mc-secrets \
  --namespace mission-control \
  --from-literal=JWT_SECRET=$(openssl rand -base64 48) \
  --from-literal=DB_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=REDIS_PASSWORD=$(openssl rand -base64 32)

# Install chart
helm install mission-control mission-control/mission-control \
  --namespace mission-control \
  --set ingress.enabled=true \
  --set ingress.hostname=your-domain.com \
  --set backend.replicas=2 \
  --set frontend.replicas=2
```

### Custom Values

```yaml
# values-custom.yaml
backend:
  replicas: 3
  image:
    tag: "latest"
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

frontend:
  replicas: 2
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

postgres:
  enabled: true
  storage: 20Gi
  storageClassName: "fast-ssd"

redis:
  enabled: true
  storage: 5Gi
  storageClassName: "fast-ssd"

ingress:
  enabled: true
  className: nginx
  hostname: your-domain.com
  tls:
    enabled: true
    secretName: mc-tls
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true

webhooks:
  enabled: true
```

### Install with Custom Values

```bash
helm install mission-control mission-control/mission-control \
  --namespace mission-control \
  --values values-custom.yaml
```

### Upgrade

```bash
helm upgrade mission-control mission-control/mission-control \
  --namespace mission-control \
  --values values-custom.yaml
```

### Uninstall

```bash
helm uninstall mission-control --namespace mission-control
kubectl delete namespace mission-control
```

---

## Option 2: Raw Kubernetes Manifests

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mission-control
  labels:
    app.kubernetes.io/name: mission-control
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mc-secrets
  namespace: mission-control
type: Opaque
stringData:
  JWT_SECRET: "your-base64-encoded-jwt-secret"
  DB_PASSWORD: "your-database-password"
  REDIS_PASSWORD: "your-redis-password"
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mc-config
  namespace: mission-control
data:
  DATABASE_URL: "postgresql+asyncpg://mission_control:$(DB_PASSWORD)@mc-postgres:5432/mission_control"
  REDIS_URL: "redis://:$(REDIS_PASSWORD)@mc-redis:6379/0"
  JWT_ALGORITHM: "HS256"
  JWT_ACCESS_TOKEN_EXPIRY: "3600"
  JWT_REFRESH_TOKEN_EXPIRY: "2592000"
  CORS_ORIGINS: "https://your-domain.com"
  LOG_LEVEL: "warning"
  ENVIRONMENT: "production"
  WORKERS: "4"
  API_KEY_PREFIX: "mc_agent_"
```

### PostgreSQL StatefulSet

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mc-postgres
  namespace: mission-control
spec:
  serviceName: mc-postgres
  replicas: 1
  selector:
    matchLabels:
      app: mc-postgres
  template:
    metadata:
      labels:
        app: mc-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              value: "mission_control"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mc-secrets
                  key: DB_PASSWORD
            - name: POSTGRES_DB
              value: "mission_control"
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - mission_control
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - mission_control
            initialDelaySeconds: 5
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "fast-ssd"
        resources:
          requests:
            storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mc-postgres
  namespace: mission-control
spec:
  selector:
    app: mc-postgres
  ports:
    - port: 5432
      targetPort: 5432
  clusterIP: None
```

### Redis StatefulSet

```yaml
# redis.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mc-redis
  namespace: mission-control
spec:
  serviceName: mc-redis
  replicas: 1
  selector:
    matchLabels:
      app: mc-redis
  template:
    metadata:
      labels:
        app: mc-redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command:
            - redis-server
            - --appendonly
            - "yes"
            - --requirepass
            - $(REDIS_PASSWORD)
          ports:
            - containerPort: 6379
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mc-secrets
                  key: REDIS_PASSWORD
          volumeMounts:
            - name: redis-data
              mountPath: /data
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            exec:
              command:
                - redis-cli
                - -a
                - $(REDIS_PASSWORD)
                - ping
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - redis-cli
                - -a
                - $(REDIS_PASSWORD)
                - ping
            initialDelaySeconds: 5
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "fast-ssd"
        resources:
          requests:
            storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mc-redis
  namespace: mission-control
spec:
  selector:
    app: mc-redis
  ports:
    - port: 6379
      targetPort: 6379
  clusterIP: None
```

### Backend Deployment

```yaml
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mc-backend
  namespace: mission-control
  labels:
    app: mc-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mc-backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: mc-backend
    spec:
      containers:
        - name: backend
          image: your-registry/mission-control-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: mc-config
            - secretRef:
                name: mc-secrets
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://mission_control:$(DB_PASSWORD)@mc-postgres:5432/mission_control"
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@mc-redis:6379/0"
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
          startupProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 30
      imagePullSecrets:
        - name: registry-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: mc-backend
  namespace: mission-control
spec:
  selector:
    app: mc-backend
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

### Frontend Deployment

```yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mc-frontend
  namespace: mission-control
  labels:
    app: mc-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mc-frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: mc-frontend
    spec:
      containers:
        - name: frontend
          image: your-registry/mission-control-frontend:latest
          ports:
            - containerPort: 3000
          env:
            - name: VITE_API_URL
              value: "https://your-domain.com/api/v1"
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
      imagePullSecrets:
        - name: registry-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: mc-frontend
  namespace: mission-control
spec:
  selector:
    app: mc-frontend
  ports:
    - port: 3000
      targetPort: 3000
  type: ClusterIP
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mc-ingress
  namespace: mission-control
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/websocket-services: mc-backend
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - your-domain.com
        - www.your-domain.com
      secretName: mc-tls
  rules:
    - host: your-domain.com
      http:
        paths:
          - path: /api/
            pathType: Prefix
            backend:
              service:
                name: mc-backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: mc-frontend
                port:
                  number: 3000
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mc-backend-hpa
  namespace: mission-control
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mc-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: mc-backend-pdb
  namespace: mission-control
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: mc-backend
```

---

## Apply All Manifests

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
kubectl apply -f pdb.yaml
```

### Verify Deployment

```bash
# Check all resources
kubectl get all -n mission-control

# Check pods
kubectl get pods -n mission-control -w

# Check ingress
kubectl get ingress -n mission-control

# Check logs
kubectl logs -f deployment/mc-backend -n mission-control

# Port forward for testing
kubectl port-forward svc/mc-backend 8000:8000 -n mission-control
kubectl port-forward svc/mc-frontend 3000:3000 -n mission-control
```

---

## Rolling Updates

### Update Backend Image

```bash
kubectl set image deployment/mc-backend \
  backend=your-registry/mission-control-backend:v1.1.0 \
  -n mission-control

# Watch rollout
kubectl rollout status deployment/mc-backend -n mission-control

# Rollback if needed
kubectl rollout undo deployment/mc-backend -n mission-control
```

### Update Frontend Image

```bash
kubectl set image deployment/mc-frontend \
  frontend=your-registry/mission-control-frontend:v1.1.0 \
  -n mission-control
```

### Update Strategy

The backend uses `RollingUpdate` with:
- `maxSurge: 1` — one extra pod during update
- `maxUnavailable: 0` — zero downtime

This ensures at least the current number of replicas are always running.

---

## Persistent Volumes

### Storage Class

```yaml
# storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs  # or your cloud provider
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Expand Volume

```bash
# Edit PVC
kubectl edit pvc postgres-data-mc-postgres-0 -n mission-control

# Change storage: 20Gi → 50Gi
# PVC will expand automatically if StorageClass allows it
```

---

## Database Migrations

### Run Migrations Job

```yaml
# migrate.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: mc-migrate
  namespace: mission-control
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: your-registry/mission-control-backend:latest
          command: ["python", "-m", "alembic", "upgrade", "head"]
          envFrom:
            - configMapRef:
                name: mc-config
            - secretRef:
                name: mc-secrets
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://mission_control:$(DB_PASSWORD)@mc-postgres:5432/mission_control"
      restartPolicy: Never
  backoffLimit: 3
```

```bash
kubectl apply -f migrate.yaml
kubectl wait --for=condition=complete job/mc-migrate -n mission-control --timeout=300s
```

---

## Monitoring

### ServiceMonitor (Prometheus Operator)

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mc-backend
  namespace: mission-control
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: mc-backend
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

### Grafana Dashboard Import

Import the Mission Control dashboard using dashboard ID from Grafana community dashboards or create custom panels for:

- Pod CPU/Memory usage
- Request rate and latency
- Error rate
- Database connections
- Redis memory usage

---

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name> -n mission-control
# Common causes:
# - Insufficient resources → Check node capacity
# - PVC pending → Check storage class
# - Node selectors not matching
```

### Pod CrashLoopBackOff

```bash
kubectl logs <pod-name> -n mission-control --previous
# Common causes:
# - Missing environment variables
# - Database connection refused
# - Invalid JWT_SECRET
```

### Database Connection Issues

```bash
# Test from backend pod
kubectl exec -it deployment/mc-backend -n mission-control -- \
  python -c "import asyncpg; print('OK')"

# Check postgres pod
kubectl logs deployment/mc-postgres -n mission-control
```

### Ingress Not Working

```bash
kubectl describe ingress mc-ingress -n mission-control
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

---

## Related Documentation

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker Compose reference
- [AUTHENTICATION.md](./AUTHENTICATION.md) — JWT and API key setup
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat configuration
- [REST_API.md](./REST_API.md) — API endpoint reference
