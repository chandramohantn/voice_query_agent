# Container-Based Deployment Plan

## Overview
Deploy the Voice Query Agent using containerized backend on AWS ECS/Fargate and static frontend on AWS S3 + CloudFront.

---

## Phase 1: Backend Containerization

### Step 1: Create Dockerfile
- Create `backend/Dockerfile` for Python WebSocket server
- Use Python 3.11 slim image
- Copy requirements.txt and main.py
- Expose port 8080
- Set CMD to run main.py

### Step 2: Create .dockerignore
- Exclude `.env`, `__pycache__`, `.venv`, etc.
- Keep only necessary files in container

### Step 3: Update Backend for Production
- Modify `main.py` to read PORT from environment variable (default 8080)
- Add health check endpoint (optional but recommended)
- Ensure proper error handling and logging

### Step 4: Test Docker Build Locally
```bash
cd backend
docker build -t voice-agent-backend .
docker run -p 8080:8080 --env-file ../.env voice-agent-backend
```

---

## Phase 2: AWS Backend Deployment

### Step 5: Create ECR Repository
- Create AWS Elastic Container Registry (ECR) repository
- Name: `voice-agent-backend`
- Get repository URI

### Step 6: Push Docker Image to ECR
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker tag voice-agent-backend:latest <ecr-uri>:latest
docker push <ecr-uri>:latest
```

### Step 7: Create ECS Cluster
- Create new ECS cluster using Fargate
- Name: `voice-agent-cluster`

### Step 8: Create Task Definition
- Container name: `voice-agent-backend`
- Image: ECR URI from Step 6
- Port mapping: 8080
- Environment variables:
  - `GOOGLE_CLOUD_TOKEN` (from Secrets Manager)
  - `GOOGLE_CLOUD_PROJECT_ID` (from Secrets Manager)
  - `GEMINI_MODEL`
  - `API_HOST`
- CPU: 256 (.25 vCPU)
- Memory: 512 MB

### Step 9: Store Secrets in AWS Secrets Manager
- Create secret for `GOOGLE_CLOUD_TOKEN`
- Create secret for `GOOGLE_CLOUD_PROJECT_ID`
- Update task definition to reference secrets

### Step 10: Create Application Load Balancer (ALB)
- Create ALB with HTTPS listener
- Target group: ECS service on port 8080
- Enable WebSocket support (sticky sessions)
- Configure security groups (allow 443, 8080)

### Step 11: Create ECS Service
- Launch type: Fargate
- Desired tasks: 1 (can scale later)
- Attach to ALB
- Enable auto-scaling (optional)

### Step 12: Configure SSL Certificate
- Request certificate in AWS Certificate Manager (ACM)
- Attach to ALB HTTPS listener
- Get ALB DNS name (e.g., `wss://your-alb.region.elb.amazonaws.com`)

---

## Phase 3: Frontend Deployment

### Step 13: Update Frontend Configuration
- Update `frontend/script.js`:
  - Change `PROXY_URL` to ALB WebSocket endpoint (wss://...)
  - Remove hardcoded PROJECT_ID (already handled in backend)

### Step 14: Create S3 Bucket for Frontend
- Bucket name: `voice-agent-frontend-<unique-id>`
- Enable static website hosting
- Block public access: OFF (for website hosting)

### Step 15: Create S3 Bucket Policy
- Allow public read access to objects
- Restrict to CloudFront origin (optional, more secure)

### Step 16: Upload Frontend Files to S3
```bash
aws s3 sync frontend/ s3://voice-agent-frontend-<unique-id>/ --exclude "*.md"
```

### Step 17: Create CloudFront Distribution
- Origin: S3 bucket website endpoint
- Default root object: `index.html`
- Viewer protocol: Redirect HTTP to HTTPS
- Cache behavior: Cache based on query strings
- SSL certificate: Use default CloudFront certificate or custom domain

### Step 18: Configure Custom Domain (Optional)
- Register domain or use existing
- Create Route 53 hosted zone
- Add CNAME/Alias record pointing to CloudFront distribution
- Request SSL certificate for custom domain in ACM

---

## Phase 4: Security & Configuration

### Step 19: Configure CORS on Backend
- Update `main.py` to handle CORS headers
- Allow origin: CloudFront distribution URL
- Allow WebSocket upgrade headers

### Step 20: Set Up IAM Roles
- ECS Task Execution Role: Pull from ECR, read Secrets Manager
- ECS Task Role: Access to required AWS services (if needed)

### Step 21: Configure Security Groups
- ALB Security Group: Allow 443 from 0.0.0.0/0
- ECS Security Group: Allow 8080 from ALB security group only

---

## Phase 5: Testing & Monitoring

### Step 22: Test Deployment
- Access CloudFront URL
- Test WebSocket connection
- Verify audio input/output
- Check browser console for errors

### Step 23: Set Up CloudWatch Logging
- Enable CloudWatch logs for ECS tasks
- Create log group: `/ecs/voice-agent-backend`
- Monitor WebSocket connections and errors

### Step 24: Set Up CloudWatch Alarms (Optional)
- High CPU usage
- High memory usage
- Task failure count
- ALB unhealthy target count

---

## Phase 6: Optimization & Maintenance

### Step 25: Enable Auto-Scaling
- ECS service auto-scaling based on CPU/memory
- ALB target tracking

### Step 26: Implement CI/CD (Optional)
- GitHub Actions or AWS CodePipeline
- Auto-build and push to ECR on commit
- Auto-update ECS service with new image

### Step 27: Cost Optimization
- Use Fargate Spot for non-critical workloads
- Set up CloudFront caching properly
- Monitor AWS Cost Explorer

---

## Estimated Costs (Monthly)

- **ECS Fargate**: ~$15-30 (1 task, 0.25 vCPU, 512 MB)
- **Application Load Balancer**: ~$16-20
- **S3**: ~$1-5 (depending on traffic)
- **CloudFront**: ~$1-10 (depending on traffic)
- **Secrets Manager**: ~$0.40 per secret
- **Total**: ~$35-70/month

---

## Rollback Plan

If deployment fails:
1. Keep old task definition version
2. Update ECS service to use previous task definition
3. Revert frontend changes in S3
4. Invalidate CloudFront cache

---

## Next Steps

1. Review this plan
2. Prepare AWS account and credentials
3. Start with Phase 1: Backend Containerization
4. Test each phase before proceeding to next
