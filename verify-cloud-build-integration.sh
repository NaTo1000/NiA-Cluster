#!/bin/bash
# Verify Cloud Build Integration Test
# This script verifies that all cloud build components are properly integrated

# Don't exit on first error - we want to run all tests
set +e

echo "================================================"
echo "Cloud Build Integration Verification Test"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
PASSED=0

# Test function
test_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        ((FAILED++))
    fi
}

test_executable() {
    local file=$1
    local description=$2
    
    if [ -x "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file (executable)"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $description: $file (not executable)"
        ((FAILED++))
    fi
}

test_yaml() {
    local file=$1
    local description=$2
    
    if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description: $file (valid YAML)"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $description: $file (invalid YAML)"
        ((FAILED++))
    fi
}

echo "Checking Cloud Build Configuration Files..."
test_file "cloudbuild.yaml" "Root cloud build config"
test_file "nia-enterprise/cloudbuild.yaml" "Enterprise cloud build config"
test_file "nia-enterprise/docker/container-structure-test.yaml" "Container structure test"
test_file ".gcloudignore" "Root gcloud ignore"
test_file "nia-enterprise/.gcloudignore" "Enterprise gcloud ignore"
echo ""

echo "Checking Helper Scripts..."
test_file "submit-cloud-build.sh" "Cloud build submission script"
test_executable "submit-cloud-build.sh" "Submit script executable"
test_file "build-cloud-local.sh" "Local cloud build test script"
test_executable "build-cloud-local.sh" "Local build script executable"
test_file "Makefile" "Makefile for build operations"
echo ""

echo "Checking Documentation..."
test_file "CLOUD_BUILD.md" "Comprehensive cloud build guide"
test_file "CLOUD_BUILD_QUICK_REF.md" "Quick reference guide"
test_file "CLOUD_BUILD_GETTING_STARTED.md" "Getting started guide"
test_file "CLOUD_BUILD_INTEGRATION_SUMMARY.md" "Integration summary"
test_file "cloud-build-triggers.yaml" "Build trigger examples"
echo ""

echo "Checking CI/CD Integration..."
test_file ".github/workflows/cloud-build.yml" "GitHub Actions workflow"
echo ""

echo "Validating YAML Configurations..."
test_yaml "cloudbuild.yaml" "Root cloudbuild.yaml"
test_yaml "nia-enterprise/cloudbuild.yaml" "Enterprise cloudbuild.yaml"
test_yaml "nia-enterprise/docker/container-structure-test.yaml" "Container structure test"
test_yaml ".github/workflows/cloud-build.yml" "GitHub Actions workflow"
echo ""

echo "Testing Makefile Targets..."
if make help &>/dev/null; then
    echo -e "${GREEN}✓${NC} Makefile help target works"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Makefile help target failed"
    ((FAILED++))
fi
echo ""

echo "Testing Docker Build Compatibility..."
if docker build -t test-cloud-integration:latest . &>/dev/null; then
    echo -e "${GREEN}✓${NC} Docker build still works"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Docker build failed"
    ((FAILED++))
fi

if docker run --rm test-cloud-integration:latest --help &>/dev/null; then
    echo -e "${GREEN}✓${NC} Docker image runs correctly"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Docker image execution failed"
    ((FAILED++))
fi
echo ""

echo "Testing Script Help Messages..."
if ./submit-cloud-build.sh 2>&1 | grep -q "Usage"; then
    echo -e "${GREEN}✓${NC} submit-cloud-build.sh has help message"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} submit-cloud-build.sh missing help message"
    ((FAILED++))
fi

if ./build-cloud-local.sh 2>&1 | grep -q "cloud-build-local"; then
    echo -e "${GREEN}✓${NC} build-cloud-local.sh has proper error handling"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} build-cloud-local.sh missing error handling"
    ((FAILED++))
fi
echo ""

echo "================================================"
echo "Test Results"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
echo -e "Tests Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Cloud Build integration is complete.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Setup GCP: make setup-gcp PROJECT_ID=your-project"
    echo "  2. Submit build: ./submit-cloud-build.sh root your-project"
    echo "  3. Read docs: cat CLOUD_BUILD_GETTING_STARTED.md"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
