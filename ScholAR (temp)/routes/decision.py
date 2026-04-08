"""
/decision route — Quick READ/SKIP decision endpoint.
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_decision_message
from utils.response_formatter import format_response

logger = logging.getLogger("scholar.decision")
router = APIRouter()


class DecisionRequest(BaseModel):
    topic: str


@router.post("/decision")
async def decision(req: DecisionRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    start = time.time()
    logger.info(f'[DECISION] Processing: "{req.topic[:80]}"')

    try:
        system_prompt = build_system_prompt("decision")
        user_message = build_decision_message(req.topic)

        parsed = await call_llm_json(system_prompt, user_message)
        result = format_response(parsed, "decision")

        duration = time.time() - start
        logger.info(f"[DECISION] Done in {duration:.1f}s | Decision: {result.get('decision', '?')}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"[DECISION] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Decision failed: {str(e)}")
