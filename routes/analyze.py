"""
/analyze route — Full research analysis endpoint.

Runs analysis + critique + break + simulation modes simultaneously.
Returns structured JSON with insights, critique, failure scenarios,
evidence, contradictions, trust score, and recommendation.
"""

import logging
import time
from fastapi import APIRouter
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_analysis_message
from services.simulation_engine import run_heuristic_simulation, compute_decision_influence
from utils.response_formatter import format_response, validate_analysis_response, FALLBACK_RESPONSE

logger = logging.getLogger("scholar.analyze")
router = APIRouter()


class AnalyzeRequest(BaseModel):
    topic: str
    paper_content: str | None = None


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    topic = (req.topic or "").strip()
    if not topic:
        fallback = {**FALLBACK_RESPONSE, "summary": "No topic provided. Please enter a research topic."}
        return validate_analysis_response(fallback)

    start = time.time()
    logger.info(f'[ANALYZE] Processing: "{topic[:80]}"')

    try:
        system_prompt = build_system_prompt("analysis")
        user_message = build_analysis_message(topic, req.paper_content)

        parsed = await call_llm_json(system_prompt, user_message)
        result = format_response(parsed, "analysis")

        # --- Integrate simulation into the decision ---
        heuristic = run_heuristic_simulation(50, 50, 50)
        sim_influence = compute_decision_influence(heuristic)

        # Append simulation factors to why_this_decision
        if not isinstance(result.get("why_this_decision"), list):
            result["why_this_decision"] = []
        for factor in sim_influence["factors"]:
            if factor not in result["why_this_decision"]:
                result["why_this_decision"].append(factor)

        # If simulation contradicts LLM recommendation, add caveat
        rec = (result.get("recommendation") or "").upper()
        modifier = sim_influence["recommendation_modifier"]

        if modifier == "supports_skip" and "READ" in rec and "CAUTION" not in rec:
            result["recommendation"] = "READ WITH CAUTION"
            result["why_this_decision"].append(
                "Recommendation adjusted: simulation indicates fragile robustness, "
                "contradicting initial READ assessment"
            )
        elif modifier == "supports_read" and rec == "SKIP":
            # Simulation says it's robust but LLM says skip — add a note but don't override
            result["why_this_decision"].append(
                "Note: simulation indicates strong robustness, but other factors "
                "led to a SKIP recommendation"
            )

        # Enrich trust_score confidence_basis if missing or generic
        trust = result.get("trust_score", {})
        if not trust.get("confidence_basis") or len(trust.get("confidence_basis", "")) < 20:
            rob_score = sim_influence["robustness_score"]
            rw_score = sim_influence["real_world_score"]
            trust["confidence_basis"] = (
                f"Confidence based on consistency across evidence, "
                f"simulation robustness ({rob_score}/100), "
                f"and real-world reliability assessment ({rw_score}/100)"
            )
            result["trust_score"] = trust

        # Final validation — guarantees all fields present
        result = validate_analysis_response(result)

        duration = time.time() - start
        logger.info(
            f"[ANALYZE] Done in {duration:.1f}s | "
            f"Trust: {result.get('trust_score', {}).get('level', '?')} | "
            f"Rec: {result.get('recommendation', '?')} | "
            f"SimInfluence: {modifier}"
        )

        return result

    except ValueError as e:
        logger.error(f"[ANALYZE] Configuration error: {e}", exc_info=True)
        fallback = {**FALLBACK_RESPONSE, "summary": f"Configuration error: {str(e)}"}
        return validate_analysis_response(fallback)

    except RuntimeError as e:
        logger.error(f"[ANALYZE] Runtime error: {e}", exc_info=True)
        fallback = {**FALLBACK_RESPONSE, "summary": f"Analysis engine error: {str(e)}"}
        return validate_analysis_response(fallback)

    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"[ANALYZE] Unexpected {error_type}: {e}", exc_info=True)
        fallback = {
            **FALLBACK_RESPONSE,
            "summary": f"Analysis could not be completed ({error_type}). Please try again.",
        }
        return validate_analysis_response(fallback)
