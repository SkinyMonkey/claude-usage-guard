"""Load and merge configuration from defaults + user overrides."""
import json
import os

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
DEFAULT_CONFIG_PATH = os.path.join(PLUGIN_ROOT, "config.default.json")


def load_config() -> dict:
    """Load config, merging defaults with user overrides."""
    with open(DEFAULT_CONFIG_PATH) as f:
        config = json.load(f)

    user_config_path = os.path.expanduser(
        config.get("config_file", "~/.claude/usage-guard-config.json")
    )
    if os.path.exists(user_config_path):
        with open(user_config_path) as f:
            user_config = json.load(f)
        if "pricing" in user_config:
            config["pricing"].update(user_config.pop("pricing"))
        config.update(user_config)

    return config
