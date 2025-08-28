#!/usr/bin/env python3
import sys
import json
import requests

# Send notification for important tool results
try:
    # Read tool result from stdin if available
    if not sys.stdin.isatty():
        result = json.load(sys.stdin)
        # Process result if needed
except:
    pass

# Always exit successfully
sys.exit(0)
