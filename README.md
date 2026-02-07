# usage-guard

A Claude Code plugin that monitors token usage per 5-hour billing window and pauses sessions when approaching the limit.

## What it does

- Tracks estimated token cost across all Claude Code sessions in the current 5-hour billing window
- **Blocks all tool calls** when spend reaches 95% of your configured budget
- **Warns** at 80% with a system message
- Integrates with Ralph Loop to prevent infinite loops from burning through limits
- Uses an incremental cache so it doesn't re-parse all session files on every check (~10ms warm path)

## Installation

```bash
claude plugin add /path/to/usage-guard
```

Or clone and register:

```bash
git clone git@github.com:SkinyMonkey/claude-usage-guard.git
claude plugin add ./claude-usage-guard
```

## Configuration

Default budget is $8.00 per 5-hour window (at API pricing rates). Adjust based on when you actually get rate-limited on your plan:

```
/usage-configure 12.00
```

Or edit `~/.claude/usage-guard-config.json` directly:

```json
{
  "max_cost_per_window_usd": 12.00,
  "warning_threshold_pct": 80,
  "block_threshold_pct": 95
}
```

## Slash Commands

- `/usage-status` — show current window spend, remaining time, and status
- `/usage-configure <amount>` — set the max cost per window

## How it works

1. **PreToolUse hook** runs before every tool call, checks cached usage stats
2. If over budget, returns `permissionDecision: deny` which blocks the tool call
3. **Stop hook** prevents Ralph Loop from continuing when budget is exhausted
4. Session JSONL files in `~/.claude/projects/` are parsed incrementally using byte offsets
5. Cache stored at `~/.claude/usage-guard-cache.json`, resets when the 5h window expires

## Calibration

The plugin estimates cost using published Anthropic API pricing. Since Max/Pro plans have different internal accounting, the dollar amounts won't match your actual plan limits. Use them as a relative measure:

1. Start with the default ($8.00)
2. If you get rate-limited before the guard triggers, lower the threshold
3. If the guard triggers but you've never been rate-limited, raise it

## Requirements

- Python 3.8+
- Claude Code with plugin support
