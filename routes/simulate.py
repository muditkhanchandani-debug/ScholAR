"""
/simulate route — Combines heuristic simulation with LLM-based simulation.

Returns both deterministic computed results and AI-generated scenario analysis.
"""

import logging
import time
from fastapi import APIRouter
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_simulation_message
from services.simulation_engine import run_heuristic_simulation
from utils.response_formatter import format_response, SIMULATION_DEFAULTS

logger = logging.getLogger("scholar.simulate")
router = APIRouter()

SIMULATION_FALLBACK = {
    "heuristic": None,
    "ai_analysis": SIMULATION_DEFAULTS,
}


class SimulateRequest(BaseModel):
    topic: str
    noise: int = 50
    data_size: int = 50
    bias: int = 50


@router.post("/simulate")
async def simulate(req: SimulateRequest):
    topic = (req.topic or "").strip()
    if not topic:
        return {**SIMULATION_FALLBACK, "ai_analysis": {**SIMULATION_DEFAULTS, "overall_robustness": "No topic provided."}}

    start = time.time()
    noise = max(0, min(100, req.noise))
    data_size = max(0, min(100, req.data_size))
    bias = max(0, min(100, req.bias))

    logger.info(f'[SIMULATE] "{topic[:60]}" | N={noise} D={data_size} B={bias}')

    # Always run heuristic (instant, can't fail)
    heuristic = run_heuristic_simulation(noise, data_size, bias)

    try:
        system_prompt = build_system_prompt("simulation")
        user_message = build_simulation_message(topic, noise, data_size, bias)

        llm_result = await call_llm_json(system_prompt, user_message)
        llm_formatted = format_response(llm_result, "simulation")

        duration = time.time() - start
        logger.info(f"[SIMULATE] Done in {duration:.1f}s | Robustness: {heuristic['robustness']['label']}")

        return {"heuristic": heuristic, "ai_analysis": llm_formatted}

    except Exception as e:
        logger.error(f"[SIMULATE] LLM failed, returning heuristic only: {e}")
        # LLM failed but heuristic always works — return heuristic with fallback AI text
        return {"heuristic": heuristic, "ai_analysis": {**SIMULATION_DEFAULTS, "overall_robustness": f"LLM unavailable — heuristic only. {str(e)}"}}
