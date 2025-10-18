#!/bin/bash
#
# Run PDF Extraction API Docker container
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="pdf-extraction-api"
CONTAINER_NAME="pdf-extraction-api"
PORT=8000

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Running PDF Extraction API${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if image exists
if ! docker image inspect ${IMAGE_NAME}:latest &> /dev/null; then
    echo -e "${YELLOW}Image not found. Building...${NC}"
    ./docker-build.sh
    echo ""
fi

# Stop and remove existing container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} &> /dev/null || true
    docker rm ${CONTAINER_NAME} &> /dev/null || true
fi

echo -e "${GREEN}Starting container...${NC}"
echo "  Container name: ${CONTAINER_NAME}"
echo "  Port: ${PORT}"
echo ""

# Run the container
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8000 \
    --restart unless-stopped \
    ${IMAGE_NAME}:latest

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Container started successfully!${NC}"
    echo ""
    echo "API is available at:"
    echo -e "  ${YELLOW}http://localhost:${PORT}${NC}"
    echo ""
    echo "Interactive documentation:"
    echo -e "  ${YELLOW}http://localhost:${PORT}/docs${NC}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     docker logs -f ${CONTAINER_NAME}"
    echo "  Stop:          docker stop ${CONTAINER_NAME}"
    echo "  Restart:       docker restart ${CONTAINER_NAME}"
    echo "  Remove:        docker rm -f ${CONTAINER_NAME}"
    echo ""
    echo "Testing the API:"
    echo -e "  ${YELLOW}curl http://localhost:${PORT}/health${NC}"
    echo ""
else
    echo -e "${RED}✗ Failed to start container${NC}"
    exit 1
fi
