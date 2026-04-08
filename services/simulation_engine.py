"""
Simulation Engine — Lightweight deterministic heuristic logic.

NO ML models. Pure rule-based calculations.
Fast execution, low resource usage, fully interpretable.
"""


def run_heuristic_simulation(
    noise: int = 50,
    data_size: int = 50,
    bias: int = 50,
) -> dict:
    """
    Run a deterministic heuristic simulation using simple rules.

    All inputs are 0-100 scale.
    Returns a dict with computed scores and explanations.
    """
    noise = max(0, min(100, noise))
    data_size = max(0, min(100, data_size))
    bias = max(0, min(100, bias))

    # --- Rule-based impact calculations ---

    # Noise: higher noise → lower accuracy
    # Non-linear: impact grows faster above 60
    noise_impact = min(100, int(noise * 0.6 + (max(0, noise - 60) ** 1.5) * 0.15))
    noise_severity = _severity(noise_impact)

    # Data size: lower data → worse generalization
    # Inverted: low data_size = high impact
    data_impact = max(0, int(100 - data_size * 0.8 - (max(0, data_size - 40) * 0.3)))
    data_severity = _severity(data_impact)

    # Bias: higher bias → worse fairness and validity
    bias_impact = min(100, int(bias * 0.7 + (max(0, bias - 50) ** 1.3) * 0.12))
    bias_severity = _severity(bias_impact)

    # Overall robustness score (0-100, higher = more robust)
    robustness_score = max(0, 100 - int(
        noise_impact * 0.35 + data_impact * 0.35 + bias_impact * 0.30
    ))

    robustness_label = (
        "Strong" if robustness_score >= 70
        else "Moderate" if robustness_score >= 40
        else "Fragile"
    )

    # Real-world reliability
    real_world_score = max(0, robustness_score - int(noise * 0.1) - int(bias * 0.1))
    real_world_label = (
        "Likely reliable" if real_world_score >= 60
        else "Uncertain" if real_world_score >= 35
        else "Unlikely to transfer"
    )

    return {
        "noise": {
            "level": noise,
            "impact": noise_impact,
            "severity": noise_severity,
            "explanation": _noise_explanation(noise, noise_impact),
        },
        "data_size": {
            "level": data_size,
            "impact": data_impact,
            "severity": data_severity,
            "explanation": _data_explanation(data_size, data_impact),
        },
        "bias": {
            "level": bias,
            "impact": bias_impact,
            "severity": bias_severity,
            "explanation": _bias_explanation(bias, bias_impact),
        },
        "robustness": {
            "score": robustness_score,
            "label": robustness_label,
        },
        "real_world": {
            "score": real_world_score,
            "label": real_world_label,
        },
    }


def compute_decision_influence(heuristic_result: dict) -> dict:
    """
    Translate heuristic simulation results into decision influence factors.

    Returns a dict with:
    - recommendation_modifier: "supports_read" | "supports_caution" | "supports_skip"
    - factors: list of string explanations for why the simulation supports this
    - robustness_score: the raw robustness score (0-100)
    - real_world_score: the raw real-world reliability score (0-100)
    """
    robustness = heuristic_result.get("robustness", {})
    real_world = heuristic_result.get("real_world", {})
    noise = heuristic_result.get("noise", {})
    data_size = heuristic_result.get("data_size", {})
    bias = heuristic_result.get("bias", {})

    rob_score = robustness.get("score", 50)
    rob_label = robustness.get("label", "Moderate")
    rw_score = real_world.get("score", 50)
    rw_label = real_world.get("label", "Uncertain")

    factors = []

    # Determine recommendation modifier
    if rob_score >= 70:
        modifier = "supports_read"
        factors.append(f"Simulation robustness is {rob_label} ({rob_score}/100) — findings are likely stable under varying conditions")
    elif rob_score >= 40:
        modifier = "supports_caution"
        factors.append(f"Simulation robustness is {rob_label} ({rob_score}/100) — results hold under controlled conditions but may degrade in real-world settings")
    else:
        modifier = "supports_skip"
        factors.append(f"Simulation robustness is {rob_label} ({rob_score}/100) — findings are likely unreliable under realistic conditions")

    # Real-world reliability factor
    factors.append(f"Real-world reliability: {rw_label} ({rw_score}/100)")

    # Flag critical individual factors
    if noise.get("severity") == "critical":
        factors.append(f"Noise sensitivity is critical (impact: {noise.get('impact', '?')}%) — high risk of performance degradation in noisy environments")
    if data_size.get("severity") == "critical":
        factors.append(f"Data sensitivity is critical (impact: {data_size.get('impact', '?')}%) — poor generalization with limited data")
    if bias.get("severity") == "critical":
        factors.append(f"Bias vulnerability is critical (impact: {bias.get('impact', '?')}%) — systematic errors may compromise validity")

    return {
        "recommendation_modifier": modifier,
        "factors": factors,
        "robustness_score": rob_score,
        "real_world_score": rw_score,
    }


def _severity(impact: int) -> str:
    if impact >= 70:
        return "critical"
    elif impact >= 40:
        return "moderate"
    return "minor"


def _noise_explanation(level: int, impact: int) -> str:
    if level > 70:
        return (
            f"At noise level {level}/100, signal-to-noise ratio is severely degraded. "
            f"Expected accuracy drop: ~{impact}%. Results are likely unreliable in noisy real-world conditions."
        )
    elif level > 30:
        return (
            f"Moderate noise level ({level}/100) introduces measurable error. "
            f"Estimated impact: ~{impact}%. Results may hold but with reduced confidence."
        )
    return (
        f"Low noise level ({level}/100) — minimal impact on results. "
        f"Impact: ~{impact}%. Findings should be stable under clean conditions."
    )


def _data_explanation(level: int, impact: int) -> str:
    if level < 30:
        return (
            f"With only {level}/100 data availability, generalization is severely limited. "
            f"Impact: ~{impact}%. Model likely overfits and fails on unseen distributions."
        )
    elif level < 70:
        return (
            f"Moderate data availability ({level}/100). Generalization is possible "
            f"but not guaranteed. Impact: ~{impact}%. Edge cases may not be covered."
        )
    return (
        f"High data availability ({level}/100) — strong generalization expected. "
        f"Impact: ~{impact}%. Results should transfer well to similar distributions."
    )


def _bias_explanation(level: int, impact: int) -> str:
    if level > 70:
        return (
            f"High systematic bias ({level}/100) fundamentally compromises validity. "
            f"Impact: ~{impact}%. Conclusions may reflect data artifacts rather than true patterns."
        )
    elif level > 30:
        return (
            f"Moderate bias ({level}/100) introduces systematic error. "
            f"Impact: ~{impact}%. Results should be interpreted with caution and cross-validated."
        )
    return (
        f"Low bias ({level}/100) — minimal systematic distortion. "
        f"Impact: ~{impact}%. Findings are likely a fair representation of underlying patterns."
    )
