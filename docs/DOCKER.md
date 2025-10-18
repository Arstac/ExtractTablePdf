# Docker Deployment Guide

This guide covers how to build, run, and deploy the PDF Extraction API using Docker.

## Quick Start

### Using Helper Scripts (Recommended)

```bash
# Build the Docker image
./docker-build.sh

# Run the container
./docker-run.sh
```

### Using Docker Compose (Alternative)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Manual Docker Commands

### Build the Image

```bash
docker build -t pdf-extraction-api:latest .
```

**For Azure Container Apps (linux/amd64):**
```bash
docker build --platform linux/amd64 -t pdf-extraction-api:latest .
```

### Run the Container

```bash
docker run -d \
  --name pdf-extraction-api \
  -p 8000:8000 \
  pdf-extraction-api:latest
```

### Test the Container

```bash
# Health check
curl http://localhost:8000/health

# Upload a PDF
curl -X POST "http://localhost:8000/extract" \
  -F "file=@data/documento.pdf"
```

---

## Azure Container Apps Deployment

### Prerequisites

1. Install Azure CLI:
```bash
# macOS
brew install azure-cli

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

2. Login to Azure:
```bash
az login
```

### Option 1: Deploy from Local Image

#### Step 1: Create Azure Container Registry (ACR)

```bash
# Set variables
RESOURCE_GROUP="pdf-extraction-rg"
LOCATION="westeurope"
ACR_NAME="pdfextractionacr"  # Must be globally unique
APP_NAME="pdf-extraction-api"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create container registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

#### Step 2: Build and Push Image to ACR

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
az acr build \
  --registry $ACR_NAME \
  --image pdf-extraction-api:latest \
  --platform linux/amd64 \
  .
```

#### Step 3: Create Container Apps Environment

```bash
# Install Container Apps extension
az extension add --name containerapp --upgrade

# Register providers
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

# Create Container Apps environment
az containerapp env create \
  --name pdf-extraction-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

#### Step 4: Deploy Container App

```bash
# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Create container app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment pdf-extraction-env \
  --image ${ACR_LOGIN_SERVER}/pdf-extraction-api:latest \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --cpu 2.0 \
  --memory 4.0Gi \
  --min-replicas 1 \
  --max-replicas 5 \
  --env-vars PYTHONUNBUFFERED=1

# Get app URL
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

### Option 2: Deploy from Docker Hub

```bash
# Tag and push to Docker Hub
docker tag pdf-extraction-api:latest yourusername/pdf-extraction-api:latest
docker push yourusername/pdf-extraction-api:latest

# Create container app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment pdf-extraction-env \
  --image yourusername/pdf-extraction-api:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2.0 \
  --memory 4.0Gi \
  --min-replicas 1 \
  --max-replicas 5
```

### Update Existing Container App

```bash
# Build and push new version
az acr build \
  --registry $ACR_NAME \
  --image pdf-extraction-api:v2 \
  --platform linux/amd64 \
  .

# Update container app
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_LOGIN_SERVER}/pdf-extraction-api:v2
```

---

## Configuration

### Environment Variables

Set environment variables in the container:

**Docker:**
```bash
docker run -d \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=info \
  -p 8000:8000 \
  pdf-extraction-api:latest
```

**Azure Container Apps:**
```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info
```

### Resource Limits

**Docker Compose:**
Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

**Azure Container Apps:**
```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --cpu 2.0 \
  --memory 4.0Gi
```

### Scaling

**Azure Container Apps:**
```bash
# Configure autoscaling
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 1 \
  --max-replicas 10

# Scale based on HTTP requests
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 10
```

---

## Monitoring and Logs

### Docker Logs

```bash
# View logs
docker logs -f pdf-extraction-api

# Last 100 lines
docker logs --tail 100 pdf-extraction-api

# Since timestamp
docker logs --since 2024-01-01T00:00:00 pdf-extraction-api
```

### Azure Container Apps Logs

```bash
# View logs
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# View specific revision
az containerapp revision list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table

az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --revision <revision-name>
```

### Application Insights (Optional)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app pdf-extraction-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app pdf-extraction-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)

# Add to container app
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=${INSTRUMENTATION_KEY}"
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs pdf-extraction-api

# Inspect container
docker inspect pdf-extraction-api

# Run interactively for debugging
docker run -it --rm pdf-extraction-api:latest /bin/bash
```

### Health check fails

```bash
# Test health endpoint
curl http://localhost:8000/health

# Check if Tesseract is installed
docker exec pdf-extraction-api tesseract --version

# Check Python dependencies
docker exec pdf-extraction-api pip list
```

### Out of memory

Increase memory limits:

```bash
docker run -d \
  --name pdf-extraction-api \
  --memory 4g \
  --memory-swap 8g \
  -p 8000:8000 \
  pdf-extraction-api:latest
```

### Slow PDF processing

- Increase CPU allocation
- Use multiple workers (modify CMD in Dockerfile)
- Enable caching if processing same PDFs

---

## Performance Optimization

### Multi-worker Setup

Edit Dockerfile CMD:
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Gunicorn with Uvicorn Workers

Edit Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "app:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300"]
```

Add to requirements.txt:
```
gunicorn==21.2.0
```

---

## Security Best Practices

1. **Use non-root user** ✓ (Already configured in Dockerfile)
2. **Minimal base image** ✓ (Using python:3.10-slim)
3. **No secrets in image** ✓ (Use environment variables)
4. **Regular updates:**
   ```bash
   # Update base image
   docker build --pull -t pdf-extraction-api:latest .
   ```
5. **Scan for vulnerabilities:**
   ```bash
   docker scan pdf-extraction-api:latest
   ```

---

## Cost Optimization (Azure)

### Use Consumption Plan

```bash
# Create with consumption plan (pay-per-use)
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment pdf-extraction-env \
  --image ${ACR_LOGIN_SERVER}/pdf-extraction-api:latest \
  --ingress external \
  --target-port 8000 \
  --min-replicas 0 \
  --max-replicas 3
```

### Set Scale-to-Zero

```bash
# Scale to 0 when no requests
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 0
```

---

## Cleanup

### Docker

```bash
# Stop and remove container
docker stop pdf-extraction-api
docker rm pdf-extraction-api

# Remove image
docker rmi pdf-extraction-api:latest

# Prune unused resources
docker system prune -a
```

### Azure

```bash
# Delete container app
az containerapp delete \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --yes

# Delete entire resource group
az group delete \
  --name $RESOURCE_GROUP \
  --yes
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)
