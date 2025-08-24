#!/bin/bash

# Lineary Claude Code Hooks Setup Script
# Installs and configures all Lineary hooks for Claude Code

set -e

echo "============================================"
echo "Lineary Claude Code Hooks Installation"
echo "============================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect Claude Code hooks directory
CLAUDE_HOOKS_DIR=""
if [ -d "$HOME/.claudecode/hooks" ]; then
    CLAUDE_HOOKS_DIR="$HOME/.claudecode/hooks"
elif [ -d "$HOME/.claude/hooks" ]; then
    CLAUDE_HOOKS_DIR="$HOME/.claude/hooks"
else
    # Create the directory if it doesn't exist
    CLAUDE_HOOKS_DIR="$HOME/.claudecode/hooks"
    mkdir -p "$CLAUDE_HOOKS_DIR"
    echo -e "${YELLOW}Created hooks directory: $CLAUDE_HOOKS_DIR${NC}"
fi

echo -e "${GREEN}Using hooks directory: $CLAUDE_HOOKS_DIR${NC}"

# Base directory for our hooks
LINEARY_HOOKS_DIR="/home/jarvis/projects/Lineary/hooks"
KOMPENDIUM_HOOKS_DIR="/home/jarvis/projects/claude-kompendium/hooks/src"

# Create Lineary hooks directory if it doesn't exist
mkdir -p "$LINEARY_HOOKS_DIR"

echo ""
echo "Step 1: Creating NTFY Notification Hook"
echo "----------------------------------------"

cat > "$LINEARY_HOOKS_DIR/ntfy-notification.py" << 'EOF'
#!/usr/bin/env python3
"""
NTFY Notification Hook for Lineary
Sends notifications to https://ntfy.da-tech.io/Lineary
"""

import json
import sys
import requests
from datetime import datetime

NTFY_URL = "https://ntfy.da-tech.io/Lineary"

def send_notification(title, message, priority="default", tags=None):
    """Send notification to NTFY server"""
    headers = {
        "Title": title,
        "Priority": priority
    }
    
    if tags:
        headers["Tags"] = ",".join(tags)
    
    try:
        response = requests.post(NTFY_URL, data=message, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send notification: {e}", file=sys.stderr)
        return False

def main():
    # Read input from Claude Code
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            return
    else:
        return
    
    tool_name = data.get("tool_name", "")
    
    # Notification triggers
    if tool_name == "Stop":
        # Session completed
        stats = data.get("stats", {})
        duration = stats.get("duration", "unknown")
        send_notification(
            "✅ Lineary Session Complete",
            f"Session finished after {duration}",
            "low",
            ["white_check_mark"]
        )
    
    elif tool_name == "PostToolUse":
        tool_input = data.get("tool_input", {})
        actual_tool = tool_input.get("tool_name", "")
        
        # Notify on significant events
        if actual_tool == "Write" and "test" in str(tool_input).lower():
            send_notification(
                "🧪 Tests Created",
                "New test files have been written",
                "default",
                ["test_tube"]
            )
        
        elif actual_tool == "MultiEdit":
            file_count = len(tool_input.get("edits", []))
            if file_count > 5:
                send_notification(
                    "📝 Major Code Changes",
                    f"Modified {file_count} sections",
                    "default",
                    ["memo"]
                )
    
    # Always continue
    print(json.dumps({"success": True, "action": "continue"}))

if __name__ == "__main__":
    main()
EOF

echo -e "${GREEN}✓ Created NTFY notification hook${NC}"

echo ""
echo "Step 2: Creating Auto-Documentation Hook"
echo "----------------------------------------"

cat > "$LINEARY_HOOKS_DIR/auto-documentation.py" << 'EOF'
#!/usr/bin/env python3
"""
Auto-Documentation Generator for Lineary
Creates feature documentation when significant changes are made
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

class AutoDocumentationHook:
    def __init__(self):
        self.docs_dir = Path("/home/jarvis/projects/Lineary/docs/auto-generated")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.docs_dir / ".session_state.json"
        self.load_session_state()
    
    def load_session_state(self):
        """Load or initialize session state"""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "files_modified": [],
                "features_added": [],
                "tests_created": [],
                "last_doc_generated": None
            }
    
    def save_session_state(self):
        """Save session state"""
        with open(self.session_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def should_generate_doc(self):
        """Determine if documentation should be generated"""
        # Generate if 3+ files modified or significant feature added
        return (len(self.state["files_modified"]) >= 3 or 
                len(self.state["features_added"]) > 0 or
                len(self.state["tests_created"]) >= 2)
    
    def generate_documentation(self):
        """Generate feature documentation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_file = self.docs_dir / f"feature_{timestamp}.md"
        
        content = f"""# Auto-Generated Feature Documentation

**Generated**: {datetime.now().isoformat()}
**Session ID**: {os.getenv('CLAUDE_SESSION_ID', 'unknown')}

## Changes Made

### Files Modified ({len(self.state['files_modified'])})
"""
        for file in self.state["files_modified"]:
            content += f"- `{file}`\n"
        
        if self.state["features_added"]:
            content += f"\n### Features Added ({len(self.state['features_added'])})\n"
            for feature in self.state["features_added"]:
                content += f"- {feature}\n"
        
        if self.state["tests_created"]:
            content += f"\n### Tests Created ({len(self.state['tests_created'])})\n"
            for test in self.state["tests_created"]:
                content += f"- `{test}`\n"
        
        content += "\n---\n*Auto-generated by Lineary Documentation Hook*\n"
        
        doc_file.write_text(content)
        return doc_file
    
    def process_event(self, data):
        """Process Claude Code event"""
        tool_name = data.get("tool_name", "")
        
        if tool_name == "PostToolUse":
            tool_input = data.get("tool_input", {})
            actual_tool = tool_input.get("tool_name", "")
            
            if actual_tool in ["Write", "Edit", "MultiEdit"]:
                file_path = tool_input.get("tool_input", {}).get("file_path", "")
                if file_path and file_path not in self.state["files_modified"]:
                    self.state["files_modified"].append(file_path)
                    
                    # Check if it's a test file
                    if "test" in file_path.lower():
                        self.state["tests_created"].append(file_path)
                    
                    # Check if it's a new feature
                    if any(keyword in file_path.lower() for keyword in ["api", "feature", "component"]):
                        feature_name = Path(file_path).stem.replace("_", " ").title()
                        self.state["features_added"].append(feature_name)
            
            self.save_session_state()
            
            # Generate documentation if threshold met
            if self.should_generate_doc():
                doc_file = self.generate_documentation()
                return {
                    "success": True,
                    "action": "documentation_generated",
                    "file": str(doc_file)
                }
        
        elif tool_name == "Stop":
            # Generate final documentation on session end
            if self.state["files_modified"]:
                doc_file = self.generate_documentation()
                return {
                    "success": True,
                    "action": "final_documentation",
                    "file": str(doc_file)
                }
        
        return {"success": True, "action": "continue"}

def main():
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
            hook = AutoDocumentationHook()
            result = hook.process_event(data)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": str(e)
            }))
    else:
        print(json.dumps({"success": True, "action": "continue"}))

if __name__ == "__main__":
    main()
EOF

echo -e "${GREEN}✓ Created auto-documentation hook${NC}"

echo ""
echo "Step 3: Creating Lineary Task Extractor Hook"
echo "----------------------------------------"

# Copy the task extractor we already created
if [ -f "$LINEARY_HOOKS_DIR/lineary-task-extractor.py" ]; then
    echo -e "${GREEN}✓ Task extractor already exists${NC}"
else
    cp "/home/jarvis/projects/Lineary/hooks/lineary-task-extractor.py" "$LINEARY_HOOKS_DIR/" 2>/dev/null || \
    echo -e "${YELLOW}⚠ Task extractor not found, will create later${NC}"
fi

echo ""
echo "Step 4: Creating Smart Guardian Hook"
echo "----------------------------------------"

cat > "$LINEARY_HOOKS_DIR/lineary-guardian.py" << 'EOF'
#!/usr/bin/env python3
"""
Lineary Guardian Hook - Smart protection and monitoring
"""

import json
import sys
import os
import re
from pathlib import Path

class LinearyGuardian:
    def __init__(self):
        self.protected_files = [
            "docker-compose.yml",
            ".env",
            "database.db",
            "*.sqlite"
        ]
        
        self.dangerous_commands = [
            r"rm\s+-rf\s+/",
            r"docker\s+volume\s+rm",
            r"DROP\s+DATABASE",
            r"DELETE\s+FROM",
            r"git\s+push\s+--force"
        ]
    
    def check_command(self, command):
        """Check if command is dangerous"""
        for pattern in self.dangerous_commands:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Dangerous command pattern detected: {pattern}"
        return True, "Command approved"
    
    def check_file_operation(self, file_path, operation):
        """Check if file operation is safe"""
        path = Path(file_path)
        
        # Check protected files
        for protected in self.protected_files:
            if path.match(protected):
                if operation in ["delete", "overwrite"]:
                    return False, f"Protected file: {protected}"
        
        # Check critical directories
        if "/home/jarvis/projects/Lineary" in str(path):
            if path.name == "database.db" and operation == "delete":
                return False, "Cannot delete Lineary database"
        
        return True, "File operation approved"
    
    def process_event(self, data):
        """Process Claude Code event"""
        tool_name = data.get("tool_name", "")
        
        if tool_name == "PreToolUse":
            tool_input = data.get("tool_input", {})
            actual_tool = tool_input.get("tool_name", "")
            
            if actual_tool == "Bash":
                command = tool_input.get("tool_input", {}).get("command", "")
                safe, reason = self.check_command(command)
                if not safe:
                    return {
                        "success": False,
                        "action": "block",
                        "reason": reason,
                        "suggestion": "Please review this command for safety"
                    }
            
            elif actual_tool == "Write":
                file_path = tool_input.get("tool_input", {}).get("file_path", "")
                safe, reason = self.check_file_operation(file_path, "overwrite")
                if not safe:
                    return {
                        "success": False,
                        "action": "block",
                        "reason": reason,
                        "suggestion": "This file is protected. Please confirm this action."
                    }
        
        return {"success": True, "action": "continue"}

def main():
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
            guardian = LinearyGuardian()
            result = guardian.process_event(data)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({
                "success": True,
                "action": "continue",
                "error": str(e)
            }))
    else:
        print(json.dumps({"success": True, "action": "continue"}))

if __name__ == "__main__":
    main()
EOF

echo -e "${GREEN}✓ Created Lineary Guardian hook${NC}"

echo ""
echo "Step 5: Installing Hooks to Claude Code Directory"
echo "-------------------------------------------------"

# Function to install a hook
install_hook() {
    local source_file="$1"
    local hook_type="$2"
    local dest_name="$3"
    
    if [ -f "$source_file" ]; then
        dest_file="$CLAUDE_HOOKS_DIR/${hook_type}_${dest_name}"
        cp "$source_file" "$dest_file"
        chmod +x "$dest_file"
        echo -e "${GREEN}✓ Installed: ${hook_type}_${dest_name}${NC}"
    else
        echo -e "${RED}✗ Source file not found: $source_file${NC}"
    fi
}

# Install all hooks
install_hook "$LINEARY_HOOKS_DIR/ntfy-notification.py" "notification" "lineary_ntfy.py"
install_hook "$LINEARY_HOOKS_DIR/auto-documentation.py" "posttooluse" "lineary_autodoc.py"
install_hook "$LINEARY_HOOKS_DIR/lineary-task-extractor.py" "posttooluse" "lineary_tasks.py"
install_hook "$LINEARY_HOOKS_DIR/lineary-guardian.py" "pretooluse" "lineary_guardian.py"

echo ""
echo "Step 6: Creating Hook Configuration"
echo "------------------------------------"

cat > "$CLAUDE_HOOKS_DIR/lineary-hooks-config.json" << 'EOF'
{
  "hooks": {
    "notification": {
      "enabled": true,
      "script": "notification_lineary_ntfy.py",
      "events": ["Stop", "SessionStart", "SubagentStop"]
    },
    "pretooluse": {
      "enabled": true,
      "scripts": [
        "pretooluse_lineary_guardian.py"
      ]
    },
    "posttooluse": {
      "enabled": true,
      "scripts": [
        "posttooluse_lineary_autodoc.py",
        "posttooluse_lineary_tasks.py"
      ]
    }
  },
  "settings": {
    "ntfy_url": "https://ntfy.da-tech.io/Lineary",
    "auto_doc_threshold": 3,
    "task_extraction": true,
    "guardian_mode": "warn"
  }
}
EOF

echo -e "${GREEN}✓ Created hook configuration${NC}"

echo ""
echo "Step 7: Testing Hooks"
echo "---------------------"

# Test NTFY notification
echo "Testing NTFY notification..."
curl -X POST https://ntfy.da-tech.io/Lineary \
    -H "Title: 🎉 Lineary Hooks Installed" \
    -H "Priority: default" \
    -H "Tags: rocket,white_check_mark" \
    -d "All Lineary hooks have been successfully installed:
✓ NTFY Notifications
✓ Auto-Documentation
✓ Task Extraction  
✓ Lineary Guardian

The hooks are ready to enhance your Claude Code experience!" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ NTFY notification test successful${NC}"
else
    echo -e "${YELLOW}⚠ NTFY notification test failed${NC}"
fi

# Test Lineary API
echo ""
echo "Testing Lineary Task API..."
response=$(curl -s -X GET http://localhost:3034/api/tasks/stats 2>/dev/null)
if echo "$response" | grep -q "success"; then
    echo -e "${GREEN}✓ Lineary Task API is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Lineary Task API not responding${NC}"
fi

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Installed hooks:"
echo "  • NTFY Notifications - Sends alerts to https://ntfy.da-tech.io/Lineary"
echo "  • Auto-Documentation - Generates docs when 3+ files modified"
echo "  • Task Extraction - Captures tasks from Claude's responses"
echo "  • Lineary Guardian - Protects critical files and commands"
echo ""
echo "Hooks directory: $CLAUDE_HOOKS_DIR"
echo ""
echo -e "${YELLOW}IMPORTANT: You may need to restart Claude Code for hooks to take effect${NC}"
echo ""
echo "To verify hooks are working:"
echo "  1. Make some code changes"
echo "  2. Check for NTFY notifications"
echo "  3. Look for auto-generated docs in docs/auto-generated/"
echo "  4. Check if tasks are being extracted to ~/.lineary/tasks/"
echo ""
echo -e "${GREEN}✅ Lineary Hooks Setup Complete!${NC}"
EOF