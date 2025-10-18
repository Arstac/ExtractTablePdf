#!/bin/bash
#
# Build Docker image for PDF Extraction API
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="pdf-extraction-api"
VERSION="1.1.0"
PLATFORM="linux/amd64"  # For Azure Container Apps

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Building PDF Extraction API Docker Image${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Building image...${NC}"
echo "  Image name: ${IMAGE_NAME}"
echo "  Version: ${VERSION}"
echo "  Platform: ${PLATFORM}"
echo ""

# Build the image
docker build \
    --platform ${PLATFORM} \
    --tag ${IMAGE_NAME}:${VERSION} \
    --tag ${IMAGE_NAME}:latest \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo ""
    echo "Image tags created:"
    echo "  - ${IMAGE_NAME}:${VERSION}"
    echo "  - ${IMAGE_NAME}:latest"
    echo ""
    echo "Image size:"
    docker images ${IMAGE_NAME}:latest --format "  {{.Repository}}:{{.Tag}} - {{.Size}}"
    echo ""
    echo "To run the container:"
    echo -e "  ${YELLOW}docker run -p 8000:8000 ${IMAGE_NAME}:latest${NC}"
    echo ""
    echo "Or use docker-compose:"
    echo -e "  ${YELLOW}docker-compose up${NC}"
    echo ""
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
