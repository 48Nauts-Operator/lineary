#!/bin/bash
# Lineary MCP Server Persistent Launcher

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MCP_DIR="/home/jarvis/projects/Lineary/mcp-server"
LOG_DIR="/home/jarvis/projects/Lineary/logs"
LOG_FILE="$LOG_DIR/mcp-server.log"
PID_FILE="$MCP_DIR/mcp-server.pid"
API_URL="https://ai-linear.blockonauts.io/api"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the server
start_server() {
    if is_running; then
        echo -e "${YELLOW}MCP Server is already running (PID: $(cat $PID_FILE))${NC}"
        return 0
    fi

    echo -e "${GREEN}Starting Lineary MCP Server...${NC}"
    
    cd "$MCP_DIR"
    
    # Export environment variables
    export LINEARY_API_URL="$API_URL"
    export NODE_ENV="production"
    
    # Start the server in background with nohup
    nohup node index.js >> "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Save PID
    echo $PID > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✓ MCP Server started successfully (PID: $PID)${NC}"
        echo -e "${GREEN}✓ Logs: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start MCP Server${NC}"
        echo -e "${RED}Check logs at: $LOG_FILE${NC}"
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if ! is_running; then
        echo -e "${YELLOW}MCP Server is not running${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping MCP Server (PID: $PID)...${NC}"
    
    kill "$PID"
    sleep 2
    
    if is_running; then
        echo -e "${YELLOW}Server didn't stop gracefully, forcing...${NC}"
        kill -9 "$PID"
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ MCP Server stopped${NC}"
}

# Function to restart the server
restart_server() {
    stop_server
    sleep 1
    start_server
}

# Function to show status
show_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}● MCP Server is running (PID: $PID)${NC}"
        echo -e "  API URL: $API_URL"
        echo -e "  Log file: $LOG_FILE"
        
        # Show last few log lines
        if [ -f "$LOG_FILE" ]; then
            echo -e "\nRecent logs:"
            tail -5 "$LOG_FILE"
        fi
    else
        echo -e "${RED}● MCP Server is not running${NC}"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start the MCP server"
        echo "  stop    - Stop the MCP server"
        echo "  restart - Restart the MCP server"
        echo "  status  - Show server status"
        exit 1
        ;;
esac

exit $?