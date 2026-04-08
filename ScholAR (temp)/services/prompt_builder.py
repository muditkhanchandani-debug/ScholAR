"""
Prompt Builder — Constructs mode-specific prompts.

Combines the base ScholAR system prompt with output format instructions.
Keeps prompt logic centralized and separate from routes.
"""

from prompts.system_prompt import (
    SYSTEM_PROMPT,
    OUTPUT_FORMAT_ANALYSIS,
    OUTPUT_FORMAT_SIMULATION,
    OUTPUT_FORMAT_DECISION,
)


def build_system_prompt(mode: str) -> str:
    """Build complete system prompt for a given mode."""
    format_map = {
        "analysis": OUTPUT_FORMAT_ANALYSIS,
        "simulation": OUTPUT_FORMAT_SIMULATION,
        "decision": OUTPUT_FORMAT_DECISION,
    }
    fmt = format_map.get(mode, OUTPUT_FORMAT_ANALYSIS)
    return f"{SYSTEM_PROMPT}\n\n{fmt}"


def build_analysis_message(topic: str, paper_content: str = None) -> str:
    """Build user message for full analysis."""
    msg = (
        f"Analyze the following research topic with full depth. "
        f"Apply analysis, critique, break, and simulation modes simultaneously.\n\n"
        f"Research Topic: {topic}"
    )
    if paper_content:
        msg += f"\n\nPaper Content / Abstract:\n{paper_content}"
    msg += (
        "\n\nProvide a comprehensive, opinionated analysis. "
        "Be decisive in your trust score and recommendation. Do not hedge."
    )
    return msg


def build_simulation_message(topic: str, noise: int, data_size: int, bias: int) -> str:
    """Build user message for simulation with variable levels."""
    noise_label = "HIGH" if noise > 70 else "MODERATE" if noise > 30 else "LOW"
    data_label = "LARGE" if data_size > 70 else "MODERATE" if data_size > 30 else "SMALL"
    bias_label = "HIGH" if bias > 70 else "MODERATE" if bias > 30 else "LOW"

    return (
        f"Run a heuristic simulation for the following research topic under varying conditions.\n\n"
        f"Research Topic: {topic}\n\n"
        f"Simulation Variables:\n"
        f"- Noise Level: {noise}/100 ({noise_label})\n"
        f"- Data Size: {data_size}/100 ({data_label})\n"
        f"- Bias Level: {bias}/100 ({bias_label})\n\n"
        f"Rules:\n"
        f"- Higher noise → degraded performance. Explain exactly how.\n"
        f"- Smaller data → poor generalization. Explain exactly why.\n"
        f"- Higher bias → skewed results. Explain the mechanism.\n\n"
        f"Simulate under these exact conditions. Be specific about cause-and-effect."
    )


def build_decision_message(topic: str) -> str:
    """Build user message for quick decision."""
    return (
        f"Quick Decision Mode. Should a researcher READ or SKIP this?\n\n"
        f"Research Topic: {topic}\n\n"
        f"Be decisive. Commit to a clear judgment. Don't hedge. "
        f"Provide a confidence level and any important caveats."
    )
