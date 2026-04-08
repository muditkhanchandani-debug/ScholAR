"""
/simulate route — Combines heuristic simulation with LLM-based simulation.

Returns both deterministic computed results and AI-generated scenario analysis.
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_simulation_message
from services.simulation_engine import run_heuristic_simulation
from utils.response_formatter import format_response

logger = logging.getLogger("scholar.simulate")
router = APIRouter()


class SimulateRequest(BaseModel):
    topic: str
    noise: int = 50
    data_size: int = 50
    bias: int = 50


@router.post("/simulate")
async def simulate(req: SimulateRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    start = time.time()
    noise = max(0, min(100, req.noise))
    data_size = max(0, min(100, req.data_size))
    bias = max(0, min(100, req.bias))

    logger.info(
        f'[SIMULATE] "{req.topic[:60]}" | N={noise} D={data_size} B={bias}'
    )

    try:
        # 1. Run deterministic heuristic simulation (instant)
        heuristic = run_heuristic_simulation(noise, data_size, bias)

        # 2. Run LLM-based simulation for richer context
        system_prompt = build_system_prompt("simulation")
        user_message = build_simulation_message(req.topic, noise, data_size, bias)

        llm_result = await call_llm_json(system_prompt, user_message)
        llm_formatted = format_response(llm_result, "simulation")

        # 3. Merge: heuristic provides numbers, LLM provides explanations
        combined = {
            "heuristic": heuristic,
            "ai_analysis": llm_formatted,
        }

        duration = time.time() - start
        logger.info(f"[SIMULATE] Done in {duration:.1f}s | Robustness: {heuristic['robustness']['label']}")

        return combined

    except ValueError as e:
        logger.error(f"[SIMULATE] Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[SIMULATE] LLM error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"[SIMULATE] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
