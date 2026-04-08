"""
/decision route — Quick READ/SKIP decision endpoint.
"""

import logging
import time
from fastapi import APIRouter
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_decision_message
from utils.response_formatter import format_response, DECISION_DEFAULTS

logger = logging.getLogger("scholar.decision")
router = APIRouter()


class DecisionRequest(BaseModel):
    topic: str


@router.post("/decision")
async def decision(req: DecisionRequest):
    topic = (req.topic or "").strip()
    if not topic:
        return {**DECISION_DEFAULTS, "justification": "No topic provided."}

    start = time.time()
    logger.info(f'[DECISION] Processing: "{topic[:80]}"')

    try:
        system_prompt = build_system_prompt("decision")
        user_message = build_decision_message(topic)

        parsed = await call_llm_json(system_prompt, user_message)
        result = format_response(parsed, "decision")

        duration = time.time() - start
        logger.info(f"[DECISION] Done in {duration:.1f}s | Decision: {result.get('decision', '?')}")

        return result

    except Exception as e:
        logger.error(f"[DECISION] Failed: {e}", exc_info=True)
        return {**DECISION_DEFAULTS, "justification": f"Could not determine. {str(e)}"}
