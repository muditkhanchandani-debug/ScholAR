"""
/analyze route — Full research analysis endpoint.

Runs analysis + critique + break + simulation modes simultaneously.
Returns structured JSON with insights, critique, failure scenarios, trust score, recommendation.
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.llm import call_llm_json
from services.prompt_builder import build_system_prompt, build_analysis_message
from utils.response_formatter import format_response

logger = logging.getLogger("scholar.analyze")
router = APIRouter()


class AnalyzeRequest(BaseModel):
    topic: str
    paper_content: str | None = None


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    start = time.time()
    logger.info(f'[ANALYZE] Processing: "{req.topic[:80]}"')

    try:
        system_prompt = build_system_prompt("analysis")
        user_message = build_analysis_message(req.topic, req.paper_content)

        parsed = await call_llm_json(system_prompt, user_message)
        result = format_response(parsed, "analysis")

        duration = time.time() - start
        logger.info(
            f"[ANALYZE] Done in {duration:.1f}s | "
            f"Trust: {result.get('trust_score', {}).get('level', '?')}"
        )

        return result

    except ValueError as e:
        logger.error(f"[ANALYZE] Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[ANALYZE] LLM error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"[ANALYZE] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
