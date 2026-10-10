# Kubernetes Deployment Guide

## Prerequisites

- Docker installed
- kubectl installed
- kind installed (for local testing)
- Python 3.13+
- uv installed

## Build Docker Image

```bash
# Build the image
docker build -t orquestra:latest .

# Or use the CI/CD built image from GHCR
docker pull ghcr.io/<username>/orquestra:latest
```

## Local Deployment with Kind

### Create Kind Cluster

```bash
# Create cluster
uv run poe k8s-kind-create

# Verify cluster
kubectl cluster-info --context kind-orquestra
```

### Deploy Application

```bash
# Apply manifests
uv run poe k8s-apply

# Check pods
kubectl get pods -n orquestra

# Check services
kubectl get svc -n orquestra
```

### Access Application

```bash
# Port-forward if needed
kubectl port-forward -n orquestra svc/orquestra-api 8000:80

# Access at http://localhost:8000
```

### Cleanup

```bash
# Delete resources
uv run poe k8s-delete

# Delete cluster
uv run poe k8s-kind-delete
```

## Production Deployment

### Build and Push Image

```bash
# Tag image
docker tag orquestra:latest ghcr.io/<username>/orquestra:latest

# Push to GHCR
docker push ghcr.io/<username>/orquestra:latest
```

### Update Secret

Edit `deploy/k8s/base/secret.yaml` with production values:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: orquestra-secret
type: Opaque
stringData:
  db-user: "production-db-user"
  db-password: "production-db-password"
  secret-key: "production-secret-key"
```

### Update ConfigMap (Optional)

Edit `deploy/k8s/base/configmap.yaml` for different service names:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orquestra-config
data:
  db-host: "postgres-service"
  db-port: "5432"
  db-name: "orquestra"
  redis-host: "redis-service"
  redis-port: "6379"
  rabbitmq-host: "rabbitmq-service"
  rabbitmq-port: "5672"
```

### Deploy to Production

```bash
# Apply with production context
kubectl apply -k deploy/k8s/base -n production

# Or use overlay
kubectl apply -k deploy/k8s/overlays/production -n production
```

## Scaling

### Scale API

```bash
kubectl scale deployment orquestra-api -n orquestra --replicas=3
```

### Scale Workers

```bash
kubectl scale deployment orquestra-worker -n orquestra --replicas=4
```

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -n orquestra deployment/orquestra-api -f

# Worker logs
kubectl logs -n orquestra deployment/orquestra-worker -f

# Relay logs
kubectl logs -n orquestra deployment/orquestra-relay -f
```

### View Pod Status

```bash
kubectl get pods -n orquestra -w
```

### Describe Pod

```bash
kubectl describe pod -n orquestra <pod-name>
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl get events -n orquestra --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -n orquestra <pod-name>

# Check pod status
kubectl describe pod -n orquestra <pod-name>
```

### Database Connection Issues

1. Verify ConfigMap values
2. Verify Secret values
3. Check if database service is accessible
4. Check network policies

### RabbitMQ Connection Issues

1. Verify RabbitMQ is running
2. Check if RabbitMQ service is accessible
3. Verify credentials in Secret

## Rollback

```bash
# Rollback to previous revision
kubectl rollout undo deployment/orquestra-api -n orquestra

# View rollout history
kubectl rollout history deployment/orquestra-api -n orquestra
```

## Health Checks

The application includes health checks at:
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/health/detailed` - Detailed health status

These are configured in the deployment manifests with appropriate delays and periods.
