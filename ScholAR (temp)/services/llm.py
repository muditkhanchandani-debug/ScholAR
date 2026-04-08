"""
LLM Service — Groq API integration via OpenAI-compatible format.

Uses httpx for direct HTTP calls. No SDK dependency.
Easy to swap providers by changing the base URL and key.
"""

import os
import json
import httpx
import logging

logger = logging.getLogger("scholar.llm")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_api_key() -> str:
    """Read API key at call time, not import time."""
    return os.getenv("GROQ_API_KEY", "")


def _get_model() -> str:
    """Read model at call time, not import time."""
    return os.getenv("GROQ_MODEL", "llama3-70b-8192")


async def call_llm(
    system_prompt: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_mode: bool = True,
) -> str:
    """
    Call the Groq LLM API.
    Returns raw response content string.
    """
    api_key = _get_api_key()
    model = model or _get_model()

    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    logger.info(f"[LLM] Calling {model} | msg_len={len(user_message)}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            error_detail = response.text[:300]
            logger.error(f"[LLM] API error {response.status_code}: {error_detail}")
            raise RuntimeError(
                f"Groq API returned status {response.status_code}: {error_detail}"
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        logger.info(f"[LLM] Response received | len={len(content)}")
        return content


def clean_json_response(raw: str) -> str:
    """Strip markdown fences and extra whitespace from LLM output."""
    if not raw:
        return "{}"

    cleaned = raw.strip()

    # Remove markdown code fences
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def extract_json(text: str) -> dict | None:
    """Last-resort: try to find a JSON object in messy text."""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


async def call_llm_json(
    system_prompt: str,
    user_message: str,
    **kwargs,
) -> dict:
    """
    Call LLM and parse the response as JSON.
    Retries once with a correction prompt if parsing fails.
    """
    raw = await call_llm(system_prompt, user_message, **kwargs)
    cleaned = clean_json_response(raw)

    # First attempt
    try:
        result = json.loads(cleaned)
        logger.info("[LLM] JSON parsed on first attempt")
        return result
    except json.JSONDecodeError:
        logger.warning(f"[LLM] Invalid JSON, retrying... preview: {cleaned[:150]}")

    # Retry with correction prompt
    correction = (
        "Your previous response was not valid JSON. "
        "Return ONLY a valid JSON object. No markdown, no code fences, no explanation. "
        f"Previous broken response:\n{cleaned[:500]}\n\nFix it and return ONLY valid JSON."
    )

    try:
        retry_raw = await call_llm(system_prompt, correction, **kwargs)
        retry_cleaned = clean_json_response(retry_raw)
        result = json.loads(retry_cleaned)
        logger.info("[LLM] JSON parsed on retry")
        return result
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"[LLM] Retry failed: {e}")

    # Last resort: extract JSON from original response
    extracted = extract_json(raw)
    if extracted:
        logger.info("[LLM] Extracted JSON from messy response")
        return extracted

    raise RuntimeError("AI returned an invalid response format. Please try again.")
