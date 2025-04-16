# AWS App Runner Deployment Guide

## Prerequisites
- AWS CLI installed and configured
- Docker installed locally
- AWS ECR repository (we'll create one)
- AWS App Runner access

## Step 1: Set Up AWS Environment

1. First, install and configure AWS CLI if you haven't:
```bash
# Install AWS CLI (macOS)
brew install awscli

# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your output format (json)
```

2. Create an ECR repository:
```bash
aws ecr create-repository \
    --repository-name bill-chat-api \
    --image-scanning-configuration scanOnPush=true
```

3. Get the ECR login command:
```bash
aws ecr get-login-password --region your-region | \
    docker login --username AWS --password-stdin \
    your-account-id.dkr.ecr.your-region.amazonaws.com
```

## Step 2: Build and Push Docker Image

1. Build the Docker image:
```bash
docker build -t bill-chat-api .
```

2. Tag the image for ECR:
```bash
docker tag bill-chat-api:latest \
    your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest
```

3. Push to ECR:
```bash
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest
```

## Step 3: Set Up AWS App Runner

1. Go to AWS Console > App Runner

2. Click "Create service"

3. Source and deployment settings:
   - Choose "Container registry"
   - Select "Amazon ECR"
   - Choose your repository and image tag
   - Select "Automatic" for deployment trigger if you want automatic deployments

4. Service settings:
   - Service name: bill-chat-api
   - Port: 8080 (matches Dockerfile)
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Environment variables:
     ```
     OPENAI_API_KEY=your_openai_api_key
     QDRANT_URL=your_qdrant_url
     QDRANT_API_KEY=your_qdrant_api_key
     ```

5. Security settings:
   - Create a new service role or use existing
   - Enable auto-scaling if needed (e.g., 1-10 instances)

6. Click "Create & deploy"

## Step 4: Monitoring and Management

1. View logs in CloudWatch:
```bash
aws logs get-log-events \
    --log-group-name /aws/apprunner/bill-chat-api \
    --log-stream-name app
```

2. Set up CloudWatch alarms:
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name bill-chat-api-errors \
    --metric-name Errors \
    --namespace AWS/AppRunner \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --alarm-actions your-sns-topic-arn
```

## Step 5: Updating the Application

1. Make changes to your code

2. Build and push new image:
```bash
docker build -t bill-chat-api .
docker tag bill-chat-api:latest your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/bill-chat-api:latest
```

3. App Runner will automatically deploy if automatic deployments are enabled

## Cost Optimization

1. Use the auto-scaling features to scale down during low-traffic periods

2. Monitor CloudWatch metrics to adjust resources as needed

3. Consider using the AWS Cost Explorer to track expenses

## Security Best Practices

1. Store sensitive environment variables using AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
    --name bill-chat-api-secrets \
    --secret-string '{"OPENAI_API_KEY":"your-key","QDRANT_API_KEY":"your-key"}'
```

2. Update App Runner configuration to use secrets from Secrets Manager

3. Regularly update dependencies and scan for vulnerabilities:
```bash
aws ecr start-image-scan --repository-name bill-chat-api --image-id imageTag=latest
```

## Troubleshooting

1. Check application logs in CloudWatch

2. Common issues and solutions:
   - If the app doesn't start: Check environment variables and port configuration
   - If memory issues occur: Adjust memory allocation in App Runner configuration
   - If cold starts are slow: Consider using provisioned concurrency

## Useful Commands

```bash
# View service status
aws apprunner list-services

# View service logs
aws apprunner list-operations --service-arn your-service-arn

# Update service
aws apprunner update-service --service-arn your-service-arn --source-configuration ...
``` 