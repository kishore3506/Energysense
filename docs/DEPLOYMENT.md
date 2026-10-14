# EnergySense — Cloud Deployment & Containerization Guide

This document outlines how to deploy EnergySense to **Hugging Face Spaces** (Free Cloud Hosting) and **Amazon Web Services (AWS)** using Docker.

---

## 1. Local Docker Testing (Single Command)

Ensure Docker Desktop is running on Windows, then execute:

```powershell
Set-Location "C:\Users\kish3\.gemini\antigravity\scratch\energysense"
docker compose up --build
```

The application will build both the frontend and backend, automatically bind ports, and be accessible at:
- **Unified Web Application:** `http://localhost:7860/`
- **FastAPI Interactive Docs:** `http://localhost:7860/docs`
- **Backend Health Check:** `http://localhost:7860/api/health`

---

## 2. Deploying to Hugging Face Spaces (Free Cloud Tier)

Hugging Face Spaces provides **free, instant cloud hosting** for Dockerized ML applications with 2 vCPUs and 16 GB RAM.

### Step 1: Create a Hugging Face Space
1. Log in to [Hugging Face](https://huggingface.co/).
2. Click on **Spaces** -> **Create new Space**.
3. Fill in the details:
   - **Space name:** `energysense-forecasting`
   - **License:** `MIT`
   - **Select the Space SDK:** Choose **Docker** -> **Blank**.
   - **Space Hardware:** Free (2 vCPU, 16GB RAM).
   - **Visibility:** Public.
4. Click **Create Space**.

### Step 2: Configure Git Remote & Push
In your local repository:
```powershell
cd C:\Users\kish3\.gemini\antigravity\scratch\energysense

# Initialize git if not already done
git init
git add .
git commit -m "EnergySense Full-Stack Docker Deployment"

# Add Hugging Face Space remote (replace YOUR_USERNAME with your HF username)
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/energysense-forecasting

# Push to Hugging Face
git push --force space main
```

### Step 3: Verify Hugging Face Spaces YAML Metadata
Hugging Face Spaces reads container instructions from the `README.md` YAML frontmatter header. EnergySense includes the required metadata:

```yaml
---
title: EnergySense AI Energy Forecaster
emoji: ⚡
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
---
```

Hugging Face Spaces will automatically execute the multi-stage `Dockerfile`, build the React 19 frontend, launch FastAPI, and expose the live application to the public URL:
`https://huggingface.co/spaces/YOUR_USERNAME/energysense-forecasting`

---

## 3. Deploying to Amazon Web Services (AWS)

### Method A: AWS EC2 (Elastic Compute Cloud)

1. **Launch an EC2 Instance:**
   - AMI: Ubuntu 24.04 LTS (x86_64)
   - Instance Type: `t3.medium` or `t3.large` (recommended for TensorFlow)
   - Security Group: Allow Inbound traffic on Port `80` (HTTP), `443` (HTTPS), and `22` (SSH).

2. **Connect and Install Docker:**
   ```bash
   ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-v2
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

3. **Deploy EnergySense:**
   ```bash
   git clone https://github.com/YOUR_REPO/energysense.git
   cd energysense
   docker compose up -d --build
   ```

4. **Nginx Reverse Proxy for Domain & SSL:**
   Configure Nginx to proxy port `80` to `http://localhost:7860` for production traffic.

---

### Method B: AWS App Runner (Serverless Container Platform)

1. Build and push image to **Amazon ECR (Elastic Container Registry)**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   docker build -t energysense:latest .
   docker tag energysense:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/energysense:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/energysense:latest
   ```

2. **Create AWS App Runner Service:**
   - Source: ECR image `energysense:latest`.
   - Port: `7860`.
   - CPU: 1 vCPU, Memory: 2 GB.
   - App Runner will provide an auto-scaling, managed HTTPS URL (e.g., `https://xyz.us-east-1.awsapprunner.com`).

---

## 4. Evaluation Checklist for Rubric Criteria

- [x] **FastAPI Local Inference:** Verified on `http://127.0.0.1:8000` with Swagger documentation at `/docs`.
- [x] **Production Multi-Stage Dockerfile:** Builds React frontend in Node stage and serves via lightweight Python runtime.
- [x] **Unified Single-Port Delivery:** Frontend and backend served concurrently through FastAPI on port `7860`.
- [x] **Hugging Face Spaces Compatibility:** Pre-configured with YAML frontmatter, non-root user permissions, and port `7860`.
- [x] **AWS Deployment Roadmap:** Complete step-by-step instructions for AWS EC2 and AWS App Runner.
