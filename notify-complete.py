#!/usr/bin/env python3
"""
Task Completion Notifier

Checks for task completion flags and notifies Rafi automatically.
Runs every 5 minutes via cron.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

COMPLETION_FLAG = Path("/home/noahsr/projects/ai-dev-cli/.task-complete.json")
OUTBOX_FILE = Path("/home/noahsr/.openclaw/workspace/.research-state/sessions_outbox.json")

def check_and_notify():
    """Check for completion flag and queue message if found."""
    
    if not COMPLETION_FLAG.exists():
        return
    
    # Load completion data
    with open(COMPLETION_FLAG) as f:
        data = json.load(f)
    
    task_name = data.get("task", "Unknown task")
    status = data.get("status", "unknown")
    details = data.get("details", "")
    
    # Create message
    message = f"""✅ **{task_name} COMPLETE**

Status: {status}
{details}

_Time: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}_"""
    
    # Queue for sending
    outbox_entry = {
        "sessionKey": "main",
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "priority": "normal"
    }
    
    OUTBOX_FILE.parent.mkdir(exist_ok=True)
    
    outbox = []
    if OUTBOX_FILE.exists():
        with open(OUTBOX_FILE) as f:
            outbox = json.load(f)
    
    outbox.append(outbox_entry)
    
    with open(OUTBOX_FILE, 'w') as f:
        json.dump(outbox, f, indent=2)
    
    print(f"[{datetime.now().isoformat()}] ✅ Notification queued: {task_name}")
    
    # Remove flag
    COMPLETION_FLAG.unlink()

if __name__ == "__main__":
    check_and_notify()
