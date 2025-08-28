#!/usr/bin/env python3
import sys
import json
import datetime

# Log tool usage
with open('/tmp/tool-usage.log', 'a') as f:
    f.write(f"{datetime.datetime.now().isoformat()} - Tool call received\n")

# Always allow the tool to proceed
sys.exit(0)
