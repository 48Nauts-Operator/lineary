#!/bin/bash
set -e  # Exit on any error

# BETTY Analytics Dashboard - Build and Test Script
# This script builds the entire system and runs comprehensive tests

set -e  # Exit on any error

echo "🚀 BETTY Analytics Dashboard - Build & Test"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
print_status "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker is running"

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose down -v || true

# Build all services
print_status "Building all services..."
docker-compose build --no-cache

# Start all services
print_status "Starting all services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check Neo4j
print_status "Checking Neo4j..."
if docker-compose exec neo4j cypher-shell -u neo4j -p bettypassword "RETURN 1" > /dev/null 2>&1; then
    print_success "Neo4j is healthy"
else
    print_warning "Neo4j might not be ready yet"
fi

# Check Qdrant
print_status "Checking Qdrant..."
if curl -f http://localhost:6335/collections > /dev/null 2>&1; then
    print_success "Qdrant is healthy"
else
    print_warning "Qdrant might not be ready yet"
fi

# Check PostgreSQL
print_status "Checking PostgreSQL..."
if docker-compose exec postgres pg_isready -U betty -d betty_memory > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy"
else
    print_warning "PostgreSQL might not be ready yet"
fi

# Check Redis
print_status "Checking Redis..."
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_warning "Redis might not be ready yet"
fi

# Check Memory API
print_status "Checking BETTY Memory API..."
sleep 10  # Give the API more time to start
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "BETTY Memory API is healthy"
else
    print_error "BETTY Memory API is not responding"
    print_status "Checking API logs..."
    docker-compose logs --tail=20 memory-api
fi

# Check Frontend
print_status "Checking Frontend..."
sleep 5
if curl -f http://localhost:3377 > /dev/null 2>&1; then
    print_success "Frontend is healthy"
else
    print_error "Frontend is not responding"
    print_status "Checking frontend logs..."
    docker-compose logs --tail=20 frontend
fi

# Test Analytics Endpoints
print_status "Testing Analytics Endpoints..."

test_endpoint() {
    local endpoint=$1
    local name=$2
    
    if curl -f "http://localhost:8001/api/analytics/${endpoint}" > /dev/null 2>&1; then
        print_success "✓ ${name} endpoint working"
    else
        print_warning "✗ ${name} endpoint not responding"
    fi
}

test_endpoint "dashboard-summary" "Dashboard Summary"
test_endpoint "knowledge-growth?days=7" "Knowledge Growth"
test_endpoint "cross-project-connections" "Cross-Project Connections"
test_endpoint "pattern-usage?limit=10" "Pattern Usage"
test_endpoint "real-time-activity?limit=20" "Real-Time Activity"
test_endpoint "intelligence-metrics" "Intelligence Metrics"
test_endpoint "system-performance?hours=24" "System Performance"

# Show service status
print_status "Service Status:"
docker-compose ps

# Show service logs (last 10 lines each)
print_status "Recent logs from each service:"
echo "--- Memory API ---"
docker-compose logs --tail=10 memory-api

echo "--- Frontend ---"
docker-compose logs --tail=10 frontend

# Performance test
print_status "Running performance test..."
if command -v ab > /dev/null 2>&1; then
    print_status "Testing API performance with Apache Bench..."
    ab -n 10 -c 2 http://localhost:8001/health || print_warning "Apache Bench not available"
else
    print_warning "Apache Bench (ab) not available for performance testing"
fi

# Final summary
echo ""
echo "=========================================="
print_success "🎉 BETTY Analytics Dashboard Build Complete!"
echo "=========================================="
echo ""
print_status "Access Points:"
echo "  🎨 Analytics Dashboard: http://localhost:3377"
echo "  🔧 API Documentation:   http://localhost:8001/docs"
echo "  💾 Neo4j Browser:       http://localhost:7475"
echo "  📊 Qdrant Dashboard:    http://localhost:6335/dashboard"
echo ""
print_status "Quick Commands:"
echo "  📋 View logs:           docker-compose logs -f [service]"
echo "  🔄 Restart service:     docker-compose restart [service]"
echo "  ⏹️  Stop all:            docker-compose down"
echo "  🧹 Clean rebuild:       docker-compose down -v && docker-compose up -d --build"
echo ""

# Check if everything is working
if curl -f http://localhost:3377 > /dev/null 2>&1 && curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "✅ All systems operational! Visit http://localhost:3377 to see your analytics dashboard!"
else
    print_error "❌ Some services may not be fully ready. Check the logs above for details."
    echo ""
    print_status "Troubleshooting tips:"
    echo "  1. Wait a few more minutes for services to fully initialize"
    echo "  2. Check logs: docker-compose logs [service_name]"
    echo "  3. Restart problematic services: docker-compose restart [service_name]"
    echo "  4. For a clean restart: docker-compose down -v && docker-compose up -d"
fi

echo ""
print_status "Build and test script completed."