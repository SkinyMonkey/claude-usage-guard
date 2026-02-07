#!/usr/bin/env python3
"""PreToolUse hook: Block tool calls when usage budget is exhausted."""
import json
import os
import sys

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)


def main():
    try:
        # Consume stdin (required by hook protocol)
        json.load(sys.stdin)

        from core.usage_tracker import get_current_usage

        usage = get_current_usage()

        if usage["status"] == "blocked":
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                },
                "systemMessage": usage["message"],
            }
            print(json.dumps(result))

        elif usage["status"] == "warning":
            print(json.dumps({"systemMessage": usage["message"]}))

        else:
            print("{}")

    except Exception as e:
        # Fail open — never block on errors
        sys.stderr.write(f"usage-guard error: {e}\n")
        print("{}")

    sys.exit(0)


if __name__ == "__main__":
    main()
