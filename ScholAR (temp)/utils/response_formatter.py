"""
Response Formatter — Validates and normalizes LLM responses.

Ensures the frontend always receives a consistent shape,
even if the LLM omits fields or returns partial data.
"""

ANALYSIS_DEFAULTS = {
    "summary": "Analysis could not be fully generated.",
    "insights": [],
    "critique": [],
    "failure_scenarios": [],
    "simulation": {
        "noise_impact": "",
        "data_sensitivity": "",
        "bias_vulnerability": "",
        "overall_robustness": "Unknown",
    },
    "trust_score": {
        "level": "Low",
        "reason": "Unable to fully assess — insufficient data in response.",
    },
    "recommendation": "Unable to determine — please retry with more specific input.",
}

SIMULATION_DEFAULTS = {
    "baseline": "",
    "scenarios": [],
    "failure_warning": "",
    "key_variables": [],
    "overall_robustness": "Unknown",
    "real_world_reliability": "",
}

DECISION_DEFAULTS = {
    "decision": "SKIP",
    "confidence": "Low",
    "justification": "Unable to determine — please retry.",
    "caveats": [],
    "better_alternatives": "N/A",
}


def format_response(parsed: dict, mode: str) -> dict:
    """Merge parsed LLM output with defaults for the given mode."""
    defaults_map = {
        "analysis": ANALYSIS_DEFAULTS,
        "simulation": SIMULATION_DEFAULTS,
        "decision": DECISION_DEFAULTS,
    }

    defaults = defaults_map.get(mode)
    if not defaults:
        return parsed

    return _deep_merge(defaults, parsed)


def _deep_merge(defaults: dict, source: dict) -> dict:
    """Deep merge source into defaults. Source values win."""
    result = dict(defaults)

    for key, value in source.items():
        if (
            isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = _deep_merge(result[key], value)
        elif value is not None:
            result[key] = value

    return result
