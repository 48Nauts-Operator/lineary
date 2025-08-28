#!/bin/bash

# Tmux-based Claude Code session keeper
# Maintains a persistent session that survives client disconnections

SESSION_NAME="claude-betty"
WINDOW_NAME="claude-betty-work"

# Function to check if session exists
session_exists() {
    tmux has-session -t $SESSION_NAME 2>/dev/null
}

# Function to create new session
create_session() {
    echo "🚀 Creating new tmux session: $SESSION_NAME"
    
    # Create new session in detached mode
    tmux new-session -d -s $SESSION_NAME -n $WINDOW_NAME
    
    # Set up the environment
    tmux send-keys -t $SESSION_NAME:$WINDOW_NAME "cd /home/jarvis/projects/Betty" C-m
    tmux send-keys -t $SESSION_NAME:$WINDOW_NAME "echo '✅ Persistent Claude session started'" C-m
    
    # Could launch a browser here if needed
    # tmux send-keys -t $SESSION_NAME:$WINDOW_NAME "firefox https://claude.ai/code" C-m
    
    echo "✅ Session created successfully"
}

# Function to attach to existing session
attach_session() {
    echo "🔗 Attaching to existing session: $SESSION_NAME"
    tmux attach-session -t $SESSION_NAME
}

# Function to show session status
show_status() {
    echo "📊 Session Status:"
    if session_exists; then
        echo "✅ Session '$SESSION_NAME' is running"
        tmux list-sessions | grep $SESSION_NAME
        echo ""
        echo "Windows in session:"
        tmux list-windows -t $SESSION_NAME
    else
        echo "❌ Session '$SESSION_NAME' is not running"
    fi
}

# Function to send commands to session
send_command() {
    if session_exists; then
        echo "📤 Sending command to session: $1"
        tmux send-keys -t $SESSION_NAME:$WINDOW_NAME "$1" C-m
    else
        echo "❌ Session not running. Create it first with: $0 start"
        exit 1
    fi
}

# Function to kill session
kill_session() {
    if session_exists; then
        echo "🛑 Killing session: $SESSION_NAME"
        tmux kill-session -t $SESSION_NAME
        echo "✅ Session killed"
    else
        echo "❌ Session '$SESSION_NAME' is not running"
    fi
}

# Main script logic
case "$1" in
    "start")
        if session_exists; then
            echo "⚠️  Session already exists"
            show_status
            echo ""
            echo "Attach with: $0 attach"
        else
            create_session
        fi
        ;;
    "attach")
        if session_exists; then
            attach_session
        else
            echo "❌ Session doesn't exist. Create it first with: $0 start"
            exit 1
        fi
        ;;
    "status")
        show_status
        ;;
    "send")
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 send 'command'"
            exit 1
        fi
        send_command "$2"
        ;;
    "kill")
        kill_session
        ;;
    "restart")
        kill_session
        sleep 1
        create_session
        ;;
    *)
        echo "🔧 Claude Code Persistent Session Manager"
        echo ""
        echo "Usage: $0 {start|attach|status|send|kill|restart}"
        echo ""
        echo "Commands:"
        echo "  start    - Create new persistent session"
        echo "  attach   - Attach to existing session"
        echo "  status   - Show session status"
        echo "  send     - Send command to session"
        echo "  kill     - Terminate session"
        echo "  restart  - Kill and recreate session"
        echo ""
        echo "Example workflow:"
        echo "  $0 start              # Create session"
        echo "  $0 status             # Check status"
        echo "  $0 send 'ls -la'      # Send command"
        echo "  $0 attach             # Attach to see output"
        exit 1
        ;;
esac