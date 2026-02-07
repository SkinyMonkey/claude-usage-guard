#!/usr/bin/env python3
"""Stop hook: Block Ralph Loop continuation when usage budget is exhausted.

Runs alongside Ralph Loop's stop hook. When budget is exhausted:
- Injects a system message telling Claude to stop working
- Combined with PreToolUse denying every tool call, this freezes the session
"""
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
        json.load(sys.stdin)

        from core.usage_tracker import get_current_usage

        usage = get_current_usage()

        if usage["status"] == "blocked":
            remaining_min = usage["window_remaining_seconds"] // 60
            result = {
                "decision": "block",
                "reason": (
                    f"USAGE GUARD: 5-hour window budget exhausted "
                    f"({usage['threshold_pct']:.0f}% of ${usage['max_cost']:.2f}). "
                    f"Resets in {remaining_min} minutes "
                    f"(at {usage['window_end'][:16]}Z). "
                    f"STOP working. Do NOT attempt further tool calls."
                ),
            }
            print(json.dumps(result))

        elif usage["status"] == "warning":
            print(
                json.dumps(
                    {
                        "systemMessage": (
                            f"USAGE GUARD WARNING: {usage['threshold_pct']:.0f}% "
                            f"of budget used. Consider wrapping up soon."
                        )
                    }
                )
            )

        else:
            print("{}")

    except Exception as e:
        sys.stderr.write(f"usage-guard stop error: {e}\n")
        print("{}")

    sys.exit(0)


if __name__ == "__main__":
    main()
