---
name: usage-configure
description: "Configure usage-guard thresholds (max cost per window)"
argument-hint: "[max-cost-usd]"
allowed-tools: ["Bash(python3:*)"]
---

# Configure Usage Guard

Set the maximum cost per 5-hour window. The argument should be a dollar amount (e.g. `8.00`).

```bash
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" $ARGUMENTS
```

Report the updated configuration to the user.
