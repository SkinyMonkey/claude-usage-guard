---
name: usage-status
description: "Show current 5-hour window usage stats and budget status"
allowed-tools: ["Bash(python3:*)"]
---

# Usage Status

Run this command to check current usage:

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" python3 "${CLAUDE_PLUGIN_ROOT}/scripts/show_status.py"
```

Report the output to the user in a clear, formatted way showing:
- Current spend vs budget
- Percentage used
- Time remaining in window
- Status (ok / warning / blocked)
