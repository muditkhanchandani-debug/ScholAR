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
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file to enable analysis."
        )

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

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        logger.error("[LLM] Request timed out after 60 seconds")
        raise RuntimeError(
            "The AI service took too long to respond. Please try again."
        )
    except httpx.ConnectError:
        logger.error("[LLM] Could not connect to Groq API")
        raise RuntimeError(
            "Could not connect to the AI service. Check your internet connection."
        )
    except httpx.HTTPError as e:
        logger.error(f"[LLM] HTTP error: {e}")
        raise RuntimeError(
            f"Network error communicating with AI service: {type(e).__name__}"
        )

    if response.status_code != 200:
        error_detail = response.text[:300]
        logger.error(f"[LLM] API error {response.status_code}: {error_detail}")

        if response.status_code == 401:
            raise RuntimeError("Invalid API key. Check your GROQ_API_KEY in .env.")
        elif response.status_code == 429:
            raise RuntimeError("Rate limit exceeded. Please wait a moment and try again.")
        elif response.status_code == 503:
            raise RuntimeError("AI service is temporarily unavailable. Try again shortly.")
        else:
            raise RuntimeError(
                f"AI service returned error {response.status_code}. Please try again."
            )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"[LLM] Malformed API response: {e}")
        raise RuntimeError(
            "AI service returned an unexpected response format. Please try again."
        )

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
    Returns a fallback dict if all attempts fail (never raises).
    """
    from utils.response_formatter import FALLBACK_RESPONSE

    try:
        raw = await call_llm(system_prompt, user_message, **kwargs)
    except (ValueError, RuntimeError) as e:
        logger.error(f"[LLM] Call failed: {e}")
        return {**FALLBACK_RESPONSE, "summary": str(e)}

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
    except (json.JSONDecodeError, ValueError, RuntimeError) as e:
        logger.error(f"[LLM] Retry failed: {e}")

    # Last resort: extract JSON from original response
    extracted = extract_json(raw)
    if extracted:
        logger.info("[LLM] Extracted JSON from messy response")
        return extracted

    # Final fallback — never crash
    logger.error("[LLM] All parse attempts failed. Returning fallback response.")
    return {**FALLBACK_RESPONSE, "summary": "AI returned an unparseable response. Please try again."}
