# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Python FastAPI application that tracks bond prices from the ECB Data Portal API, deployed to Azure using Terraform (AKS + ACR), Docker, Kubernetes (Kustomize), and GitHub Actions CI/CD.

## Project Structure

- **`app/`** — FastAPI application fetching bond yields from ECB's IRS, FM, and YC datasets
- **`terraform/`** — Modular Terraform config: resource_group, acr, networking, aks modules
- **`k8s/`** — Kustomize-based Kubernetes manifests with base + dev/prod overlays
- **`.github/workflows/`** — CI/CD: `infra-deploy.yml` (Terraform) and `app-deploy.yml` (test/build/deploy)

## Common Commands

### Python App
```bash
cd app
pip install -r requirements.txt
uvicorn app.main:app --reload                  # Run locally (http://localhost:8000/docs)
python -m pytest app/tests/ -v                 # Run tests
```

### Docker
```bash
docker build -t fastapi-bonds ./app
docker run -p 8000:8000 fastapi-bonds
```

### Terraform (from terraform/)
```bash
terraform init
terraform plan -var-file=environments/dev.tfvars -var="subscription_id=<YOUR_SUB_ID>"
terraform apply -var-file=environments/dev.tfvars -var="subscription_id=<YOUR_SUB_ID>"
```

### Kubernetes
```bash
kubectl apply -k k8s/overlays/dev --dry-run=client    # Validate
kubectl apply -k k8s/overlays/dev                      # Deploy
```

## Architecture Notes

- **ECB API** requires no authentication. Data is fetched as CSV (`?format=csvdata`) and parsed with pandas.
- **ECB datasets:** IRS (country-level 10Y bond yields), FM (benchmark yields at multiple maturities), YC (daily yield curves)
- **ECBClient** in `app/services/ecb_client.py` uses in-memory TTL cache (default 5 min) to avoid excessive API calls
- **Config** uses `pydantic-settings` with `BOND_` env prefix (e.g., `BOND_CACHE_TTL_SECONDS`)
- **ACR-AKS auth** uses AcrPull role on kubelet managed identity — no imagePullSecrets needed
- **CI/CD auth** uses OIDC (Workload Identity Federation) — no stored Azure credentials
- **Kustomize overlays** control replica count per environment (dev=1, prod=3)
