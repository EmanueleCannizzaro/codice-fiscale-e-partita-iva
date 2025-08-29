#!/bin/bash

# Google Cloud Function Deployment Script for Italian Fiscal Code API
# This script deploys the FastAPI application as a Google Cloud Function

set -e  # Exit on any error

# Configuration
FUNCTION_NAME="fiscal-code-api"
REGION="europe-west1"  # Choose your preferred region
RUNTIME="python311"    # Python 3.11 runtime
SOURCE_DIR="."
ENTRY_POINT="fiscal_code_api"
MEMORY="1024MB"
TIMEOUT="540s"  # 9 minutes max for Cloud Functions
MAX_INSTANCES="100"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    log_info "Checking deployment requirements..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI (gcloud) is not installed!"
        log_error "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed!"
        exit 1
    fi
    
    log_success "All required tools are available"
}

# Check if user is authenticated
check_auth() {
    log_info "Checking Google Cloud authentication..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "You are not authenticated with Google Cloud!"
        log_error "Please run: gcloud auth login"
        exit 1
    fi
    
    local active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log_success "Authenticated as: $active_account"
}

# Check if project is set
check_project() {
    log_info "Checking Google Cloud project configuration..."
    
    local project_id=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$project_id" ]; then
        log_error "No Google Cloud project is set!"
        log_error "Please run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    log_success "Using project: $project_id"
    
    # Verify project exists and we have access
    if ! gcloud projects describe "$project_id" &> /dev/null; then
        log_error "Cannot access project '$project_id' or it doesn't exist!"
        exit 1
    fi
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    local apis=(
        "cloudfunctions.googleapis.com"
        "cloudbuild.googleapis.com"
        "artifactregistry.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            log_info "API $api is already enabled"
        else
            log_warning "Enabling API: $api"
            if ! gcloud services enable "$api"; then
                log_error "Failed to enable API: $api"
                exit 1
            fi
        fi
    done
    
    log_success "All required APIs are enabled"
}

# Validate source files
validate_source() {
    log_info "Validating source files..."
    
    # Check main entry point
    if [ ! -f "main.py" ]; then
        log_error "main.py not found! This file is required for Cloud Functions."
        exit 1
    fi
    
    # Check requirements file
    if [ ! -f "requirements-cloudfunction.txt" ]; then
        log_error "requirements-cloudfunction.txt not found!"
        exit 1
    fi
    
    # Check if codicefiscale module exists
    if [ ! -d "codicefiscale" ]; then
        log_error "codicefiscale module directory not found!"
        exit 1
    fi
    
    # Test import in a temporary Python environment
    log_info "Testing main.py syntax..."
    if ! python3 -m py_compile main.py; then
        log_error "main.py has syntax errors!"
        exit 1
    fi
    
    log_success "Source files validation passed"
}

# Create .gcloudignore file
create_gcloudignore() {
    log_info "Creating .gcloudignore file..."
    
    cat > .gcloudignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# Development files
.env
.env.*
*.log
.DS_Store
.vscode/
.idea/
*.swp
*.swo
*~

# Git
.git/
.gitignore

# Documentation and examples
README.md
CHANGELOG.md
AUTHENTICATION.md
QUICK_AUTH_SETUP.md
docs/
images/
*.md

# Testing
tests/
test_*.py
*_test.py
tox.ini
.pytest.ini

# Build and distribution
build/
dist/
*.egg-info/
.eggs/

# Node.js (if present)
node_modules/
package*.json

# UV and pip
uv.lock
requirements.txt
requirements-test.txt
requirements-data.txt

# Cloud Function specific - keep only what we need
src/
.github/
scripts/
python_codicefiscale.egg-info/
setup.py
MANIFEST.in
EOF
    
    log_success ".gcloudignore file created"
}

# Prepare deployment files
prepare_deployment() {
    log_info "Preparing deployment files..."
    
    # Copy requirements-cloudfunction.txt to requirements.txt (Cloud Functions expects this name)
    cp requirements-cloudfunction.txt requirements.txt
    log_info "Copied requirements-cloudfunction.txt to requirements.txt"
    
    # Create runtime.txt if Python version is specific
    echo "python-3.11" > runtime.txt
    log_info "Created runtime.txt specifying Python 3.11"
    
    log_success "Deployment files prepared"
}

# Deploy the function
deploy_function() {
    log_info "Deploying Cloud Function: $FUNCTION_NAME"
    log_info "This may take several minutes..."
    
    # Prepare deployment command
    local deploy_cmd="gcloud functions deploy $FUNCTION_NAME"
    deploy_cmd+=" --gen2"  # Use 2nd generation Cloud Functions
    deploy_cmd+=" --runtime=$RUNTIME"
    deploy_cmd+=" --region=$REGION"
    deploy_cmd+=" --source=$SOURCE_DIR"
    deploy_cmd+=" --entry-point=$ENTRY_POINT"
    deploy_cmd+=" --trigger=http"
    deploy_cmd+=" --allow-unauthenticated"  # Make publicly accessible
    deploy_cmd+=" --memory=$MEMORY"
    deploy_cmd+=" --timeout=$TIMEOUT"
    deploy_cmd+=" --max-instances=$MAX_INSTANCES"
    deploy_cmd+=" --set-env-vars=GOOGLE_CLOUD_FUNCTION=1"
    
    # Add Clerk environment variables if they exist
    if [ -n "$CLERK_PUBLISHABLE_KEY" ]; then
        deploy_cmd+=" --set-env-vars=CLERK_PUBLISHABLE_KEY=$CLERK_PUBLISHABLE_KEY"
        log_info "Using CLERK_PUBLISHABLE_KEY from environment"
    fi
    
    if [ -n "$CLERK_SECRET_KEY" ]; then
        deploy_cmd+=" --set-env-vars=CLERK_SECRET_KEY=$CLERK_SECRET_KEY"
        log_info "Using CLERK_SECRET_KEY from environment"
    fi
    
    if [ -n "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" ]; then
        deploy_cmd+=" --set-env-vars=NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
        log_info "Using NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY from environment"
    fi
    
    log_info "Executing: $deploy_cmd"
    
    # Execute deployment
    if eval $deploy_cmd; then
        log_success "Cloud Function deployed successfully!"
    else
        log_error "Cloud Function deployment failed!"
        exit 1
    fi
}

# Get function URL
get_function_url() {
    log_info "Retrieving function URL..."
    
    local function_url=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.uri)" 2>/dev/null)
    
    if [ -n "$function_url" ]; then
        log_success "Function deployed at: $function_url"
        log_success "API Documentation: $function_url/docs"
        log_success "Health Check: $function_url/health"
        
        # Save URL to file for reference
        echo "$function_url" > .function-url
        log_info "Function URL saved to .function-url"
    else
        log_warning "Could not retrieve function URL"
    fi
}

# Test the deployed function
test_function() {
    log_info "Testing deployed function..."
    
    local function_url=$(cat .function-url 2>/dev/null)
    if [ -z "$function_url" ]; then
        log_warning "Function URL not found, skipping test"
        return
    fi
    
    # Test health endpoint
    if curl -s "$function_url/health" | grep -q "healthy"; then
        log_success "Health check passed"
    else
        log_warning "Health check failed"
    fi
    
    # Test API info endpoint  
    if curl -s "$function_url/api" | grep -q "Italian Fiscal Code"; then
        log_success "API endpoint test passed"
    else
        log_warning "API endpoint test failed"
    fi
    
    # Test a simple validation
    local test_response=$(curl -s -X POST "$function_url/fiscal-code/validate" \
        -H "Content-Type: application/json" \
        -d '{"code": "CCCFBA85D03L219P"}')
    
    if echo "$test_response" | grep -q '"valid"'; then
        log_success "Fiscal code validation test passed"
    else
        log_warning "Fiscal code validation test failed"
        log_warning "Response: $test_response"
    fi
}

# Cleanup temporary files
cleanup() {
    log_info "Cleaning up temporary files..."
    
    rm -f requirements.txt runtime.txt
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting Google Cloud Function deployment for Italian Fiscal Code API"
    log_info "============================================================="
    
    # Pre-deployment checks
    check_requirements
    check_auth
    check_project
    enable_apis
    validate_source
    
    # Prepare and deploy
    create_gcloudignore
    prepare_deployment
    
    log_warning "About to deploy to Google Cloud Functions"
    log_warning "This will create/update function: $FUNCTION_NAME in region: $REGION"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_function
        get_function_url
        
        # Test if requested
        read -p "Test the deployed function? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            test_function
        fi
        
        cleanup
        
        log_success "============================================================="
        log_success "Deployment completed successfully!"
        log_success "Your Italian Fiscal Code API is now live on Google Cloud Functions"
        
        if [ -f ".function-url" ]; then
            local url=$(cat .function-url)
            echo ""
            log_info "📋 Quick Reference:"
            log_info "   Function URL: $url"
            log_info "   API Docs: $url/docs"
            log_info "   Health Check: $url/health"
            log_info "   Web Interface: $url"
            echo ""
            log_info "🔧 Example API Call:"
            echo "   curl -X POST '$url/fiscal-code/validate' \\"
            echo "        -H 'Content-Type: application/json' \\"
            echo "        -d '{\"code\": \"CCCFBA85D03L219P\"}'"
        fi
        
    else
        log_info "Deployment cancelled"
        cleanup
        exit 0
    fi
}

# Handle script interruption
trap cleanup EXIT

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Google Cloud Function Deployment Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --function-name     Set function name (default: $FUNCTION_NAME)"
        echo "  --region           Set deployment region (default: $REGION)"
        echo "  --memory           Set memory limit (default: $MEMORY)"
        echo ""
        echo "Environment Variables:"
        echo "  CLERK_PUBLISHABLE_KEY      Optional Clerk authentication key"
        echo "  CLERK_SECRET_KEY           Optional Clerk secret key"
        echo "  GOOGLE_CLOUD_PROJECT       Google Cloud project ID"
        echo ""
        echo "Prerequisites:"
        echo "  - Google Cloud CLI installed and authenticated"
        echo "  - Google Cloud project configured"
        echo "  - Billing enabled on the project"
        echo ""
        exit 0
        ;;
    --function-name)
        FUNCTION_NAME="$2"
        shift 2
        ;;
    --region)
        REGION="$2"
        shift 2
        ;;
    --memory)
        MEMORY="$2"
        shift 2
        ;;
    "")
        # No arguments, proceed with deployment
        main
        ;;
    *)
        log_error "Unknown option: $1"
        log_error "Use --help for usage information"
        exit 1
        ;;
esac