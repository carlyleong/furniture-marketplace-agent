#!/bin/bash

# 🛋️ Furniture Classifier - Docker Startup Script
# This script helps you manage your Docker containers easily

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛋️  Furniture Classifier - Docker Management${NC}"
echo "=================================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop and try again.${NC}"
        exit 1
    fi
}

# Function to check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating a basic one...${NC}"
        cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
OPENAI_API_KEY=your_openai_key_here
EOF
        echo -e "${YELLOW}📝 Please edit .env file with your OpenAI API key if you want AI features${NC}"
    fi
}

# Function to start services
start_services() {
    echo -e "${BLUE}🚀 Starting Furniture Classifier...${NC}"
    
    if [ "$1" = "full" ]; then
        echo -e "${BLUE}🔄 Starting both backend and frontend...${NC}"
        docker-compose --profile full up --build
    else
        echo -e "${BLUE}🔄 Starting backend only...${NC}"
        docker-compose up --build backend
    fi
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    docker-compose down
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Showing logs...${NC}"
    docker-compose logs -f
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    docker-compose down
    docker system prune -f
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo "📱 Frontend: http://localhost:3000 (if running full profile)"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📋 API Docs: http://localhost:8000/docs"
    echo "❤️  Health Check: http://localhost:8000/api/health"
}

# Main menu
case "${1:-help}" in
    "start")
        check_docker
        check_env
        start_services
        ;;
    "start-full")
        check_docker
        check_env
        start_services full
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        check_docker
        check_env
        start_services
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "clean")
        cleanup
        ;;
    "help"|*)
        echo -e "${GREEN}📖 Available commands:${NC}"
        echo ""
        echo -e "${YELLOW}./docker-start.sh start${NC}      - Start backend only"
        echo -e "${YELLOW}./docker-start.sh start-full${NC} - Start backend + frontend"
        echo -e "${YELLOW}./docker-start.sh stop${NC}       - Stop all services"
        echo -e "${YELLOW}./docker-start.sh restart${NC}    - Restart backend"
        echo -e "${YELLOW}./docker-start.sh logs${NC}       - Show container logs"
        echo -e "${YELLOW}./docker-start.sh status${NC}     - Show service status"
        echo -e "${YELLOW}./docker-start.sh clean${NC}      - Clean up Docker resources"
        echo ""
        echo -e "${BLUE}💡 Quick Start:${NC}"
        echo "1. Run: ./docker-start.sh start"
        echo "2. Open: http://localhost:8000"
        echo "3. Upload furniture photos and classify!"
        ;;
esac
