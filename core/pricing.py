"""Calculate cost from usage data using per-model pricing."""


def calculate_cost(usage: dict, model: str, pricing_table: dict) -> float:
    """Calculate USD cost for a single API request's token usage.

    Args:
        usage: Dict with input_tokens, cache_creation_input_tokens,
               cache_read_input_tokens, output_tokens.
        model: Model ID string (e.g. "claude-opus-4-6").
        pricing_table: Model -> pricing dict from config.

    Returns:
        Cost in USD.
    """
    prices = pricing_table.get(model, pricing_table.get("default", {}))

    input_tokens = usage.get("input_tokens", 0)
    cache_create = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    cost = (
        (input_tokens / 1_000_000) * prices.get("input_per_mtok", 15.0)
        + (cache_create / 1_000_000) * prices.get("cache_creation_per_mtok", 18.75)
        + (cache_read / 1_000_000) * prices.get("cache_read_per_mtok", 1.50)
        + (output_tokens / 1_000_000) * prices.get("output_per_mtok", 75.0)
    )

    return cost
