"""
Response Formatter — Validates and normalizes LLM responses.

Ensures the frontend always receives a consistent shape,
even if the LLM omits fields or returns partial data.
"""


ANALYSIS_DEFAULTS = {
    "summary": "No summary could be generated.",
    "insights": [],
    "critique": [],
    "failure_scenarios": [],
    "simulation": {
        "variables": {},
        "outcome": "Unknown",
        "explanation": "No simulation data available.",
    },
    "evidence_sources": [],
    "contradictions": [],
    "trust_score": {
        "level": "Low",
        "reason": "Unable to assess — insufficient data.",
        "confidence_basis": "Insufficient data to determine confidence.",
    },
    "recommendation": "Unable to determine — please retry.",
    "why_this_decision": [],
    "decision_highlights": {
        "strengths": [],
        "risks": [],
        "uncertainties": [],
    },
    "related_topics": [],
    "global_research_context": {
        "active_regions": [],
        "summary": "",
    },
    "internal_debate": {
        "argument_for": "",
        "argument_against": "",
        "conclusion": "",
    },
    "future_relevance": {
        "level": "Unknown",
        "reasoning": "",
    },
    "visual_indicators": {
        "reliability": 0,
        "novelty": 0,
        "impact": 0,
        "reproducibility": 0,
        "risk": 0,
    },
    "researcher_focus": "",
    "new_research_idea": {
        "title": "",
        "explanation": "",
    },
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

# Returned when the entire pipeline fails
FALLBACK_RESPONSE = {
    "summary": "Analysis could not be completed. Please try again with a different or more specific query.",
    "insights": ["Insufficient data to extract insights."],
    "critique": [{"issue": "Analysis incomplete.", "severity": "minor", "explanation": "The system could not fully process this query."}],
    "failure_scenarios": [{"scenario": "Analysis pipeline did not complete.", "likelihood": "low", "impact": "No results to evaluate."}],
    "simulation": {
        "variables": {},
        "outcome": "Unknown",
        "explanation": "Simulation could not be run.",
    },
    "evidence_sources": [{"claim": "No evidence could be retrieved for this query.", "basis": "N/A", "relevance": "N/A"}],
    "contradictions": [{"finding_a": "N/A", "finding_b": "N/A", "reason": "Analysis incomplete — no contradictions could be assessed."}],
    "trust_score": {
        "level": "Low",
        "reason": "Analysis was incomplete.",
        "confidence_basis": "Confidence cannot be assessed due to incomplete analysis.",
    },
    "recommendation": "SKIP",
    "why_this_decision": ["Analysis could not be completed — defaulting to SKIP for safety."],
    "decision_highlights": {
        "strengths": ["N/A"],
        "risks": ["Incomplete analysis — results may be unreliable."],
        "uncertainties": ["Full assessment could not be performed."],
    },
    "related_topics": [],
    "global_research_context": {
        "active_regions": [],
        "summary": "Unable to determine research geography.",
    },
    "internal_debate": {
        "argument_for": "N/A",
        "argument_against": "N/A",
        "conclusion": "Debate could not be generated — analysis incomplete.",
    },
    "future_relevance": {
        "level": "Unknown",
        "reasoning": "Unable to assess future relevance.",
    },
    "visual_indicators": {
        "reliability": 0,
        "novelty": 0,
        "impact": 0,
        "reproducibility": 0,
        "risk": 0,
    },
    "researcher_focus": "",
    "new_research_idea": {
        "title": "",
        "explanation": "",
    },
}


def normalize_simulation(parsed: dict) -> dict:
    """Convert old-style simulation fields to the variables/outcome/explanation format."""
    sim = parsed.get("simulation", {})

    # Already in correct format
    if "variables" in sim and "outcome" in sim:
        return parsed

    # Old format: noise_impact, data_sensitivity, bias_vulnerability, overall_robustness
    if any(k in sim for k in ("noise_impact", "data_sensitivity", "bias_vulnerability")):
        parsed["simulation"] = {
            "variables": {
                "noise": sim.get("noise_impact", "No data"),
                "data_size": sim.get("data_sensitivity", "No data"),
                "bias": sim.get("bias_vulnerability", "No data"),
            },
            "outcome": sim.get("overall_robustness", "Unknown"),
            "explanation": (
                f"Noise: {sim.get('noise_impact', 'N/A')}. "
                f"Data: {sim.get('data_sensitivity', 'N/A')}. "
                f"Bias: {sim.get('bias_vulnerability', 'N/A')}."
            ),
        }

    return parsed


def _fill_empty_lists(result: dict) -> dict:
    """Ensure list fields always have at least one item so sections never show blank."""
    if not result.get("insights"):
        result["insights"] = ["No strong signal found."]
    if not result.get("critique"):
        result["critique"] = [{"issue": "No significant weaknesses identified.", "severity": "minor", "explanation": ""}]
    if not result.get("failure_scenarios"):
        result["failure_scenarios"] = [{"scenario": "No critical failure scenarios identified.", "likelihood": "low", "impact": ""}]
    if not result.get("evidence_sources"):
        result["evidence_sources"] = [{"claim": "No specific evidence could be identified for this topic.", "basis": "N/A", "relevance": "N/A"}]
    if not result.get("contradictions"):
        result["contradictions"] = [{"finding_a": "N/A", "finding_b": "N/A", "reason": "No contradictions identified — the field may have general consensus on this topic."}]
    if not result.get("why_this_decision"):
        result["why_this_decision"] = ["Decision based on overall assessment of available evidence and methodology."]

    # Ensure decision_highlights always has content
    highlights = result.get("decision_highlights", {})
    if not isinstance(highlights, dict):
        highlights = {}
    if not highlights.get("strengths"):
        highlights["strengths"] = ["No specific strengths identified."]
    if not highlights.get("risks"):
        highlights["risks"] = ["No specific risks identified."]
    if not highlights.get("uncertainties"):
        highlights["uncertainties"] = ["Uncertainty level not assessed."]
    result["decision_highlights"] = highlights

    # New intelligence fields — safe defaults
    if not isinstance(result.get("related_topics"), list):
        result["related_topics"] = []
    if not isinstance(result.get("researcher_focus"), str):
        result["researcher_focus"] = ""

    return result


def validate_analysis_response(result: dict) -> dict:
    """
    Final validation gate. Ensures every required field exists with correct types.
    Called as the last step before returning to the frontend.
    """
    # String fields
    for key in ("summary", "recommendation"):
        if not isinstance(result.get(key), str) or not result[key].strip():
            result[key] = ANALYSIS_DEFAULTS[key]

    # List fields
    for key in ("insights", "critique", "failure_scenarios", "evidence_sources", "contradictions", "why_this_decision"):
        if not isinstance(result.get(key), list):
            result[key] = ANALYSIS_DEFAULTS[key]

    # Dict fields
    if not isinstance(result.get("simulation"), dict):
        result["simulation"] = ANALYSIS_DEFAULTS["simulation"]
    else:
        sim = result["simulation"]
        if "variables" not in sim:
            sim["variables"] = {}
        if "outcome" not in sim:
            sim["outcome"] = "Unknown"
        if "explanation" not in sim:
            sim["explanation"] = "No simulation data available."

    if not isinstance(result.get("trust_score"), dict):
        result["trust_score"] = ANALYSIS_DEFAULTS["trust_score"]
    else:
        ts = result["trust_score"]
        if "level" not in ts:
            ts["level"] = "Low"
        if "reason" not in ts:
            ts["reason"] = "Unable to assess."
        if "confidence_basis" not in ts:
            ts["confidence_basis"] = f"Confidence based on overall assessment — trust level: {ts['level']}."

    if not isinstance(result.get("decision_highlights"), dict):
        result["decision_highlights"] = ANALYSIS_DEFAULTS["decision_highlights"]

    # New intelligence dict fields
    for key in ("global_research_context", "internal_debate", "future_relevance", "visual_indicators", "new_research_idea"):
        if not isinstance(result.get(key), dict):
            result[key] = ANALYSIS_DEFAULTS[key]

    # New intelligence simple fields
    if not isinstance(result.get("related_topics"), list):
        result["related_topics"] = ANALYSIS_DEFAULTS["related_topics"]
    if not isinstance(result.get("researcher_focus"), str):
        result["researcher_focus"] = ANALYSIS_DEFAULTS.get("researcher_focus", "")

    # Fill any empty lists
    result = _fill_empty_lists(result)

    return result


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

    # Normalize simulation to consistent shape
    if mode == "analysis":
        parsed = normalize_simulation(parsed)

    result = _deep_merge(defaults, parsed)

    # Ensure no blank sections for analysis
    if mode == "analysis":
        result = _fill_empty_lists(result)

    return result


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
