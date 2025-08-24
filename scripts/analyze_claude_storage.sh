#!/bin/bash

# Analyze Claude local storage structure
echo "=== Claude Local Storage Analysis ==="
echo ""

CLAUDE_DIR="/home/jarvis/.claude"

if [ -d "$CLAUDE_DIR" ]; then
    echo "📁 Claude directory found at: $CLAUDE_DIR"
    echo ""
    
    # Count files
    echo "📊 Storage Statistics:"
    echo "  Total files: $(find $CLAUDE_DIR -type f | wc -l)"
    echo "  JSON files: $(find $CLAUDE_DIR -name "*.json" | wc -l)"
    echo "  Directories: $(find $CLAUDE_DIR -type d | wc -l)"
    echo ""
    
    # Show structure
    echo "📂 Directory Structure (top level):"
    ls -la $CLAUDE_DIR/
    echo ""
    
    # Projects info
    if [ -d "$CLAUDE_DIR/projects" ]; then
        echo "📝 Projects found:"
        echo "  Project count: $(ls -1 $CLAUDE_DIR/projects | wc -l)"
        echo "  Total size: $(du -sh $CLAUDE_DIR/projects | cut -f1)"
        echo ""
        
        echo "Recent projects:"
        ls -lt $CLAUDE_DIR/projects | head -10
    fi
    
    # Sample a conversation file
    echo ""
    echo "📄 Sample conversation structure:"
    SAMPLE_FILE=$(find $CLAUDE_DIR -name "*.json" -size +1k | head -1)
    if [ -n "$SAMPLE_FILE" ]; then
        echo "  File: $SAMPLE_FILE"
        echo "  Size: $(ls -lh "$SAMPLE_FILE" | awk '{print $5}')"
        echo "  Preview:"
        head -c 500 "$SAMPLE_FILE" | python3 -m json.tool 2>/dev/null | head -20 || echo "    (Unable to parse as JSON)"
    fi
    
else
    echo "❌ Claude directory not found at $CLAUDE_DIR"
fi