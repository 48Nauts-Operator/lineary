#!/bin/bash
# Monitor for deployment marker files

echo "Monitoring for PostTool hook activity..."
echo "Watching for marker files:"
echo "  - .frontend-needs-deploy"
echo "  - .backend-needs-deploy"  
echo "  - .docker-needs-rebuild"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "============================================"

while true; do
    # Check for frontend marker
    if [ -f "/home/jarvis/projects/Lineary/.frontend-needs-deploy" ]; then
        echo "[$(date '+%H:%M:%S')] 🚨 FRONTEND needs deployment!"
        cat /home/jarvis/projects/Lineary/.frontend-needs-deploy
        echo "---"
    fi
    
    # Check for backend marker
    if [ -f "/home/jarvis/projects/Lineary/.backend-needs-deploy" ]; then
        echo "[$(date '+%H:%M:%S')] 🚨 BACKEND needs deployment!"
        cat /home/jarvis/projects/Lineary/.backend-needs-deploy
        echo "---"
    fi
    
    # Check for docker marker
    if [ -f "/home/jarvis/projects/Lineary/.docker-needs-rebuild" ]; then
        echo "[$(date '+%H:%M:%S')] 🚨 DOCKER needs rebuild!"
        cat /home/jarvis/projects/Lineary/.docker-needs-rebuild
        echo "---"
    fi
    
    sleep 2
done