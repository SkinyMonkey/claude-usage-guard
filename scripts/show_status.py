#!/usr/bin/env python3
"""Show current usage-guard status."""
import json
import os
import sys

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.usage_tracker import get_current_usage

usage = get_current_usage()
print(json.dumps(usage, indent=2))
