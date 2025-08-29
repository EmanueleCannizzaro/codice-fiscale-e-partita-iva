#!/bin/bash

# Google Cloud Run Deployment Script
# This script deploys the FastAPI app to Google Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="europe-west1"
SERVICE_NAME="codice-fiscale-service"
MEMORY="1Gi"
CPU="1"
MAX_INSTANCES="100"
MIN_INSTANCES="0"
ALLOW_UNAUTHENTICATED="true"

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy FastAPI Fiscal Code API to Google Cloud Run

OPTIONS:
    -p, --project PROJECT_ID     Google Cloud Project ID (required)
    -r, --region REGION         Deployment region (default: europe-west1)
    -n, --name SERVICE_NAME     Service name (default: codice-fiscale-service)
    -m, --memory MEMORY         Memory allocation (default: 1Gi)
    -c, --cpu CPU              CPU allocation (default: 1)
    -i, --max-instances MAX     Max instances (default: 100)
    -a, --auth                  Require authentication (default: allow unauthenticated)
    -h, --help                  Show this help message

EXAMPLES:
    $0 -p my-project-id
    $0 -p my-project-id -r europe-west1 -m 2Gi
    $0 -p my-project-id --auth  # Require authentication

PREREQUISITES:
    - Google Cloud SDK (gcloud) installed and authenticated
    - Google Cloud Run API enabled
    - Docker installed (for building container images)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -n|--name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY="$2"
            shift 2
            ;;
        -c|--cpu)
            CPU="$2"
            shift 2
            ;;
        -i|--max-instances)
            MAX_INSTANCES="$2"
            shift 2
            ;;
        --min-instances)
            MIN_INSTANCES="$2"
            shift 2
            ;;
        -a|--auth)
            ALLOW_UNAUTHENTICATED="false"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required. Use -p or --project to specify it."
    show_usage
    exit 1
fi

# Set the project
print_status "Setting Google Cloud project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Check for requirements.txt
print_status "Checking for requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    print_status "Generating requirements.txt from pyproject.toml..."
    
    if [ -f "scripts/generate_requirements.py" ]; then
        if command -v uv &> /dev/null; then
            uv run python scripts/generate_requirements.py
        elif command -v python3 &> /dev/null; then
            python3 scripts/generate_requirements.py
        else
            print_error "Neither 'uv' nor 'python3' found. Cannot generate requirements.txt"
            exit 1
        fi
        
        if [ -f "requirements.txt" ]; then
            print_success "requirements.txt generated successfully"
        else
            print_error "Failed to generate requirements.txt"
            exit 1
        fi
    else
        print_error "scripts/generate_requirements.py not found. Cannot generate requirements.txt"
        print_error "Please run: uv run python scripts/generate_requirements.py"
        exit 1
    fi
else
    print_success "requirements.txt found"
fi

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create Dockerfile for Cloud Run
print_status "Creating Dockerfile for Cloud Run..."
cat > Dockerfile << 'EOF'
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV GOOGLE_CLOUD_FUNCTION=1
ENV PYTHONPATH=/app

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Start the application
CMD exec uvicorn codicefiscale.app:app --host 0.0.0.0 --port ${PORT:-8080}
EOF

# Show deployment configuration
print_status "Cloud Run deployment configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"
echo "  Max Instances: $MAX_INSTANCES"
echo "  Min Instances: $MIN_INSTANCES"
echo "  Allow Unauthenticated: $ALLOW_UNAUTHENTICATED"
echo

# Confirm deployment
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Deployment cancelled."
    exit 0
fi

# Deploy to Cloud Run
print_status "Deploying to Google Cloud Run..."

DEPLOY_ARGS=(
    "run" "deploy" "$SERVICE_NAME"
    "--source" "."
    "--region" "$REGION"
    "--memory" "$MEMORY"
    "--cpu" "$CPU"
    "--max-instances" "$MAX_INSTANCES"
    "--min-instances" "$MIN_INSTANCES"
    "--set-env-vars" "GOOGLE_CLOUD_FUNCTION=1"
    "--platform" "managed"
)

if [[ "$ALLOW_UNAUTHENTICATED" == "true" ]]; then
    DEPLOY_ARGS+=("--allow-unauthenticated")
fi

if gcloud "${DEPLOY_ARGS[@]}"; then
    print_success "Deployment completed successfully!"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    
    print_success "Service deployed at: $SERVICE_URL"
    print_status "Health check: curl $SERVICE_URL/health"
    
    # Test the deployment 
    print_status "Testing deployment..."
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        print_success "Health check passed!"
    else
        print_warning "Health check failed. The service might still be initializing."
    fi
    
else
    print_error "Deployment failed!"
    exit 1
fi

print_success "Cloud Run deployment completed successfully!"
print_status "API Documentation: $SERVICE_URL/docs"

# Clean up Dockerfile
rm -f Dockerfile