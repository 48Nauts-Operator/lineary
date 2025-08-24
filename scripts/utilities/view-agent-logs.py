#!/usr/bin/env python3
"""
Agent Activity Log Viewer
Provides formatted view of agent activities for debugging
"""

import json
import datetime
from pathlib import Path

def format_timestamp(ts_str):
    """Format timestamp for display"""
    dt = datetime.datetime.fromisoformat(ts_str)
    return dt.strftime("%H:%M:%S")

def view_logs(log_file="/home/jarvis/projects/nautBrain/agent-activity.log", last_n=50):
    """View and format agent activity logs"""
    
    if not Path(log_file).exists():
        print("❌ No agent activity log found")
        return
        
    print("🤖 AGENT ACTIVITY LOG")
    print("=" * 80)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        
    # Get last N lines
    recent_lines = lines[-last_n:] if len(lines) > last_n else lines
    
    current_session = None
    
    for line in recent_lines:
        try:
            entry = json.loads(line.strip())
            entry_type = entry['type']
            data = entry['data']
            timestamp = format_timestamp(entry['timestamp'])
            
            if entry_type == "SESSION_START":
                current_session = data['session_id']
                print(f"\n🚀 [{timestamp}] AGENT STARTED: {data['agent_type']}")
                print(f"   Session: {data['session_id']}")
                print(f"   Environment: {data['environment']}")
                print(f"   Task: {data['task_description']}")
                print(f"   Prompt: {data['prompt'][:100]}...")
                
            elif entry_type == "COMMAND":
                status = "✅" if data['success'] else "❌"
                print(f"   {status} [{timestamp}] CMD: {data['command']}")
                print(f"      Description: {data['description']}")
                if data['error']:
                    print(f"      ❌ Error: {data['error']}")
                    
            elif entry_type == "FILE_CHANGE":
                print(f"   📝 [{timestamp}] FILE: {data['change_type']} {data['file_path']}")
                if data['lines_changed']:
                    changes = data['lines_changed']
                    print(f"      +{changes['added']} -{changes['removed']} lines")
                    
            elif entry_type == "SESSION_END":
                duration = data['duration_seconds']
                status_emoji = "✅" if data['status'] == "COMPLETED" else "❌" if data['status'] == "FAILED" else "⚠️"
                print(f"   {status_emoji} [{timestamp}] AGENT FINISHED: {data['agent_type']}")
                print(f"      Status: {data['status']}")
                print(f"      Duration: {duration:.1f}s")
                if data['summary']:
                    print(f"      Summary: {data['summary']}")
                if data['errors']:
                    print(f"      Errors: {data['errors']}")
                print("-" * 60)
                
        except Exception as e:
            print(f"❌ Error parsing log entry: {e}")
            
def get_session_summary():
    """Get summary of all agent sessions"""
    log_file = "/home/jarvis/projects/nautBrain/agent-activity.log"
    
    if not Path(log_file).exists():
        return "No agent sessions found"
        
    sessions = {}
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry['type'] == "SESSION_START":
                    session_id = entry['data']['session_id']
                    sessions[session_id] = {
                        'agent_type': entry['data']['agent_type'],
                        'start_time': entry['data']['start_time'],
                        'task': entry['data']['task_description'],
                        'environment': entry['data']['environment'],
                        'commands': 0,
                        'file_changes': 0,
                        'status': 'RUNNING'
                    }
                elif entry['type'] == "COMMAND":
                    session_id = entry['data']['session_id']
                    if session_id in sessions:
                        sessions[session_id]['commands'] += 1
                elif entry['type'] == "FILE_CHANGE":
                    session_id = entry['data']['session_id']
                    if session_id in sessions:
                        sessions[session_id]['file_changes'] += 1
                elif entry['type'] == "SESSION_END":
                    session_id = entry['data']['session_id']
                    if session_id in sessions:
                        sessions[session_id]['status'] = entry['data']['status']
                        sessions[session_id]['duration'] = entry['data']['duration_seconds']
                        
            except Exception as e:
                continue
                
    print("\n📊 AGENT SESSION SUMMARY")
    print("=" * 80)
    
    for session_id, info in sessions.items():
        status_emoji = "✅" if info['status'] == "COMPLETED" else "❌" if info['status'] == "FAILED" else "🔄"
        duration = f"{info.get('duration', 0):.1f}s" if 'duration' in info else "Running"
        
        print(f"{status_emoji} {info['agent_type']} ({session_id[:8]})")
        print(f"    Task: {info['task'][:60]}...")
        print(f"    Environment: {info['environment']}")
        print(f"    Commands: {info['commands']}, Files: {info['file_changes']}, Duration: {duration}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        get_session_summary()
    else:
        view_logs()