#!/usr/bin/env python3
"""Configure usage-guard thresholds."""
import json
import os
import sys

CONFIG_PATH = os.path.expanduser("~/.claude/usage-guard-config.json")


def main():
    if len(sys.argv) < 2:
        print("Usage: configure.py <max-cost-usd> [--warn-pct N] [--block-pct N]")
        sys.exit(1)

    # Load existing config
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--warn-pct" and i + 1 < len(args):
            config["warning_threshold_pct"] = int(args[i + 1])
            i += 2
        elif args[i] == "--block-pct" and i + 1 < len(args):
            config["block_threshold_pct"] = int(args[i + 1])
            i += 2
        else:
            try:
                config["max_cost_per_window_usd"] = float(args[i])
            except ValueError:
                print(f"Invalid value: {args[i]}")
                sys.exit(1)
            i += 1

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Configuration saved to {CONFIG_PATH}:")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
