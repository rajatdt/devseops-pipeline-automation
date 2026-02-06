# devseops-pipeline-automation

Bond price tracking API deployed to Azure Kubernetes Service using Terraform, Docker, and GitHub Actions.

## What It Does

Fetches the latest government bond yields from the [ECB Data Portal](https://data.ecb.europa.eu/) (no API key needed) and exposes them via a REST API.

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/bonds/yields` | Latest 10Y bond yields for all EU countries |
| `GET /api/v1/bonds/yields/{country_code}` | Bond yield for a specific country (e.g., DE, FR) |
| `GET /api/v1/bonds/benchmarks` | Euro area benchmark yields (2Y, 3Y, 5Y, 7Y, 10Y) |
| `GET /api/v1/bonds/yield-curve` | Euro area yield curve (spot rates) |

## Quick Start

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run locally
uvicorn app.main:app --reload

# Run tests
python -m pytest app/tests/ -v

# Build Docker image
docker build -t fastapi-bonds ./app
docker run -p 8000:8000 fastapi-bonds
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

## Infrastructure

Terraform provisions the following Azure resources:

- **Resource Group** — container for all resources
- **Azure Container Registry (ACR)** — private Docker image registry
- **Virtual Network + Subnet** — network isolation for AKS
- **Azure Kubernetes Service (AKS)** — managed Kubernetes cluster with autoscaling

```bash
cd terraform
terraform init
terraform plan -var-file=environments/dev.tfvars -var="subscription_id=<YOUR_SUB_ID>"
terraform apply -var-file=environments/dev.tfvars -var="subscription_id=<YOUR_SUB_ID>"
```

## CI/CD

Two GitHub Actions workflows:

- **`infra-deploy.yml`** — Runs `terraform plan` and `apply` when `terraform/` changes
- **`app-deploy.yml`** — Tests, builds Docker image, pushes to ACR, and deploys to AKS when `app/` or `k8s/` changes

Both use OIDC authentication (Workload Identity Federation) with Azure.

### Required GitHub Configuration

**Secrets:** `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`

**Variables:** `ACR_NAME`, `AKS_CLUSTER`, `AKS_RESOURCE_GROUP`
