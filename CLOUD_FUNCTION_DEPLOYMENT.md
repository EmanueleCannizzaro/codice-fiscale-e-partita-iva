# Google Cloud Function Deployment Guide

This guide explains how to deploy the Italian Fiscal Code & VAT Validation API as a Google Cloud Function (serverless).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Authentication Setup](#authentication-setup)
- [Testing](#testing)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cost Management](#cost-management)

## Prerequisites

### 1. Google Cloud Account & Project
- Google Cloud account with billing enabled
- A Google Cloud project
- Cloud Functions API enabled

### 2. Local Development Environment
- Google Cloud CLI installed: [Installation Guide](https://cloud.google.com/sdk/docs/install)
- Python 3.11 or later
- Git (for cloning the repository)

### 3. Authentication & Permissions
- Authenticated with Google Cloud: `gcloud auth login`
- Required IAM roles:
  - `Cloud Functions Developer`
  - `Cloud Build Service Account` 
  - `Storage Admin` (for deployment artifacts)

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd python-codicefiscale
git checkout deploy/google-cloud-function
```

### 2. Configure Google Cloud
```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Set default region (optional)
gcloud config set functions/region europe-west1
```

### 3. Deploy with Script
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

The script will:
- ✅ Check all requirements
- ✅ Enable necessary APIs
- ✅ Deploy the function
- ✅ Provide the function URL
- ✅ Test the deployment

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Required
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional - Clerk Authentication
CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_secret_here

# Optional - Function Configuration  
FUNCTION_NAME=fiscal-code-api
FUNCTION_MEMORY=1024MB
FUNCTION_TIMEOUT=540s
```

### Function Configuration

Edit `function-config.yaml` to customize:

```yaml
name: fiscal-code-api
runtime: python311
region: europe-west1
memory: 1024MB
timeout: 540s
max_instances: 100
```

## Deployment

### Automated Deployment (Recommended)

Use the provided deployment script:

```bash
./deploy.sh
```

**Script Options:**
```bash
./deploy.sh --help                    # Show help
./deploy.sh --function-name my-api    # Custom function name
./deploy.sh --region us-central1      # Custom region
./deploy.sh --memory 2048MB           # Custom memory
```

### Manual Deployment

If you prefer manual deployment:

```bash
# 1. Prepare requirements file
cp requirements-cloudfunction.txt requirements.txt

# 2. Deploy function
gcloud functions deploy fiscal-code-api \
  --gen2 \
  --runtime=python311 \
  --region=europe-west1 \
  --source=. \
  --entry-point=fiscal_code_api \
  --trigger=http \
  --allow-unauthenticated \
  --memory=1024MB \
  --timeout=540s \
  --set-env-vars=GOOGLE_CLOUD_FUNCTION=1

# 3. Get function URL
gcloud functions describe fiscal-code-api \
  --region=europe-west1 \
  --format="value(serviceConfig.uri)"
```

### Deployment with Authentication

If using Clerk authentication:

```bash
./deploy.sh
# The script will automatically detect and use these environment variables:
# - CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY  
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
```

Or manually:
```bash
gcloud functions deploy fiscal-code-api \
  --gen2 \
  --runtime=python311 \
  --region=europe-west1 \
  --source=. \
  --entry-point=fiscal_code_api \
  --trigger=http \
  --allow-unauthenticated \
  --memory=1024MB \
  --timeout=540s \
  --set-env-vars=GOOGLE_CLOUD_FUNCTION=1,CLERK_PUBLISHABLE_KEY=pk_test_xxx,CLERK_SECRET_KEY=sk_test_xxx
```

## Authentication Setup

### Without Authentication (Public API)
Deploy without setting Clerk environment variables. All endpoints will be publicly accessible.

### With Clerk Authentication
1. **Create Clerk Application**:
   - Sign up at [clerk.com](https://clerk.com)
   - Create new application
   - Get your API keys from the dashboard

2. **Set Environment Variables**:
   ```bash
   export CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
   export CLERK_SECRET_KEY=sk_test_your_secret_here
   ```

3. **Deploy with Authentication**:
   ```bash
   ./deploy.sh
   ```

4. **Using Authenticated Endpoints**:
   ```bash
   # Get JWT token from your Clerk application
   curl -X POST "https://YOUR_FUNCTION_URL/fiscal-code/validate" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"code": "CCCFBA85D03L219P"}'
   ```

## Testing

### Automated Testing
The deployment script includes basic testing:
```bash
./deploy.sh
# Select "y" when prompted to test
```

### Manual Testing

1. **Health Check**:
   ```bash
   curl https://YOUR_FUNCTION_URL/health
   ```

2. **API Information**:
   ```bash
   curl https://YOUR_FUNCTION_URL/api
   ```

3. **Fiscal Code Validation**:
   ```bash
   # Without authentication
   curl -X POST "https://YOUR_FUNCTION_URL/fiscal-code/validate" \
     -H "Content-Type: application/json" \
     -d '{"code": "CCCFBA85D03L219P"}'

   # With authentication
   curl -X POST "https://YOUR_FUNCTION_URL/fiscal-code/validate" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"code": "CCCFBA85D03L219P"}'
   ```

4. **VAT Number Validation**:
   ```bash
   curl -X POST "https://YOUR_FUNCTION_URL/vat/validate" \
     -H "Content-Type: application/json" \
     -d '{"partita_iva": "01234567890"}'
   ```

### Interactive Testing

Visit your function URL in a browser to use the web interface:
- **Main Interface**: `https://YOUR_FUNCTION_URL/`
- **API Documentation**: `https://YOUR_FUNCTION_URL/docs`
- **Health Check**: `https://YOUR_FUNCTION_URL/health`

## Monitoring & Troubleshooting

### View Logs
```bash
# Real-time logs
gcloud functions logs tail fiscal-code-api --region=europe-west1

# Recent logs
gcloud functions logs read fiscal-code-api --region=europe-west1 --limit=50
```

### Function Status
```bash
# Get function details
gcloud functions describe fiscal-code-api --region=europe-west1

# List all functions
gcloud functions list
```

### Common Issues

#### 1. **Deployment Fails - API Not Enabled**
```bash
# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

#### 2. **Import Errors in Logs**
- Check that all dependencies are in `requirements-cloudfunction.txt`
- Verify the module structure is correct
- Check Python version compatibility

#### 3. **Timeout Issues**
```bash
# Increase timeout (max 540s for HTTP functions)
gcloud functions deploy fiscal-code-api \
  --timeout=540s \
  --update-env-vars=GOOGLE_CLOUD_FUNCTION=1
```

#### 4. **Memory Issues**
```bash
# Increase memory allocation
gcloud functions deploy fiscal-code-api \
  --memory=2048MB \
  --update-env-vars=GOOGLE_CLOUD_FUNCTION=1
```

#### 5. **Authentication Issues**
- Verify Clerk environment variables are set correctly
- Check JWT token format and expiration
- Ensure instance ID matches in JWT issuer claim

### Performance Monitoring

1. **Cloud Console**: Visit [Google Cloud Functions Console](https://console.cloud.google.com/functions)
2. **Metrics**: Monitor invocations, duration, memory usage
3. **Alerts**: Set up alerts for errors or high latency

## Cost Management

### Understanding Costs

Google Cloud Functions pricing includes:
- **Invocations**: Number of times function is called
- **Compute time**: CPU and memory usage duration
- **Network**: Data transfer (usually minimal for API responses)

### Cost Optimization

1. **Right-size Memory**: 
   - Start with 512MB, increase if needed
   - Monitor memory usage in Cloud Console

2. **Optimize Cold Starts**:
   - Keep functions warm with minimal traffic
   - Use global variables for reusable connections
   - Consider min instances for high-traffic APIs

3. **Monitor Usage**:
   ```bash
   # Get function statistics
   gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=fiscal-code-api" \
     --limit=10 --format="table(timestamp,severity,textPayload)"
   ```

### Free Tier Limits
- **2 million invocations** per month (free)
- **400,000 GB-seconds** of compute time (free)
- **200,000 GHz-seconds** of compute time (free)

## Updating the Function

### Update Code
```bash
# Make your changes, then redeploy
./deploy.sh

# Or manually
gcloud functions deploy fiscal-code-api \
  --source=. \
  --region=europe-west1
```

### Update Environment Variables
```bash
gcloud functions deploy fiscal-code-api \
  --update-env-vars=NEW_VAR=value \
  --region=europe-west1
```

### Update Configuration
```bash
gcloud functions deploy fiscal-code-api \
  --memory=2048MB \
  --timeout=300s \
  --region=europe-west1
```

## Deleting the Function

```bash
# Delete function
gcloud functions delete fiscal-code-api --region=europe-west1

# Verify deletion
gcloud functions list
```

## Advanced Configuration

### Custom Domain
1. Set up Cloud Load Balancer
2. Configure SSL certificate
3. Map custom domain to function URL

### VPC Integration
```bash
gcloud functions deploy fiscal-code-api \
  --vpc-connector=projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME \
  --region=europe-west1
```

### Service Account
```bash
# Create service account
gcloud iam service-accounts create fiscal-code-api-sa

# Deploy with custom service account
gcloud functions deploy fiscal-code-api \
  --service-account=fiscal-code-api-sa@PROJECT_ID.iam.gserviceaccount.com \
  --region=europe-west1
```

## Support & Resources

- **Google Cloud Functions Documentation**: [https://cloud.google.com/functions/docs](https://cloud.google.com/functions/docs)
- **FastAPI Documentation**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Clerk Authentication**: [https://clerk.com/docs](https://clerk.com/docs)
- **Project Issues**: [GitHub Issues](https://github.com/fabiocaccamo/python-codicefiscale/issues)

---

**Note**: This deployment creates a public API. For production use with sensitive data, implement proper authentication and consider additional security measures like API keys, rate limiting, and WAF protection.