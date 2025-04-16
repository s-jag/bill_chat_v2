# AWS Deployment Guide

## Prerequisites
- AWS CLI installed and configured
- Docker installed locally
- AWS ECR repository created
- AWS ECS cluster (if using ECS) or Elastic Beanstalk environment

## Option 1: Deploy to AWS ECS

1. Create ECR Repository:
```bash
aws ecr create-repository --repository-name bill-chat-api
```

2. Authenticate Docker to ECR:
```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
```

3. Build and Push Docker Image:
```bash
# Build the image
docker build -t bill-chat-api .

# Tag the image
docker tag bill-chat-api:latest your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest

# Push to ECR
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest
```

4. Create ECS Task Definition:
```json
{
    "family": "bill-chat-api",
    "containerDefinitions": [
        {
            "name": "bill-chat-api",
            "image": "your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest",
            "memory": 2048,
            "cpu": 1024,
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 5000,
                    "hostPort": 5000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "OPENAI_API_KEY",
                    "value": "your-api-key"
                },
                {
                    "name": "QDRANT_URL",
                    "value": "your-qdrant-url"
                },
                {
                    "name": "QDRANT_API_KEY",
                    "value": "your-qdrant-api-key"
                }
            ]
        }
    ],
    "requiresCompatibilities": [
        "FARGATE"
    ],
    "networkMode": "awsvpc",
    "cpu": "1024",
    "memory": "2048"
}
```

5. Create ECS Service:
- Go to AWS Console > ECS
- Create a new service using the task definition
- Configure networking and load balancer

## Option 2: Deploy to Elastic Beanstalk

1. Create Elastic Beanstalk configuration:

Create a file named `.elasticbeanstalk/config.yml`:
```yaml
branch-defaults:
  main:
    environment: bill-chat-prod
environment-defaults:
  bill-chat-prod:
    branch: null
    repository: null
global:
  application_name: bill-chat
  default_ec2_keyname: null
  default_platform: Docker
  default_region: your-region
  include_git_submodules: true
  instance_profile: null
  platform_name: null
  platform_version: null
  profile: null
  sc: null
  workspace_type: Application
```

2. Deploy using EB CLI:
```bash
# Initialize EB (first time only)
eb init

# Create environment (first time only)
eb create bill-chat-prod

# Deploy updates
eb deploy
```

## Environment Variables

For both deployment options, ensure you set these environment variables:
- OPENAI_API_KEY
- OPENAI_MODEL
- QDRANT_URL
- QDRANT_API_KEY

For ECS, set them in the task definition.
For Elastic Beanstalk, set them in the environment configuration.

## Monitoring and Scaling

1. Set up CloudWatch monitoring:
   - CPU utilization
   - Memory utilization
   - Request count
   - Error rates

2. Configure auto-scaling:
   - ECS: Use Service Auto Scaling
   - Elastic Beanstalk: Configure Auto Scaling Group

## Cost Optimization

1. Choose appropriate instance sizes:
   - Start with t3.medium or t3.large
   - Monitor usage and adjust as needed

2. Use spot instances where possible (for non-critical workloads)

3. Set up AWS Budget alerts

## Security Considerations

1. Use AWS Secrets Manager for API keys
2. Configure security groups to restrict access
3. Use HTTPS/SSL for all endpoints
4. Implement AWS WAF if needed

## Troubleshooting

1. Check CloudWatch Logs for application logs
2. Monitor ECS/EB events
3. Use AWS X-Ray for request tracing (optional) 