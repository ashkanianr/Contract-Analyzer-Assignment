"""LLM client: Primary Gemini (google-genai), backup OpenRouter. Abstracted behind generate()."""
import json
import logging
from typing import Any, Optional

from backend.config import (
    GOOGLE_API_KEY,
    LLM_MODEL_GOOGLE,
    LLM_MODEL_OPENROUTER,
    LLM_PRIMARY,
    OPENROUTER_API_KEY,
)

logger = logging.getLogger(__name__)


def _strip_json_block(text: str) -> str:
    """Remove markdown code fence around JSON if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _call_google(prompt: str, system: str, json_mode: bool) -> str:
    """Call Google Gemini via google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    model = LLM_MODEL_GOOGLE
    contents = [types.Content(role="user", parts=[types.Part(text=system + "\n\n" + prompt)])]
    gen_config = types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json" if json_mode else None,
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=gen_config,
    )
    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("Empty response from Google")
    return response.candidates[0].content.parts[0].text


def _call_google_chat(messages: list[dict], system: str) -> str:
    """Multi-turn chat via Google Gemini. messages: [{"role":"user"|"assistant","content":str}, ...]."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    contents = []
    for i, m in enumerate(messages):
        role = "user" if m.get("role") == "user" else "model"
        text = m.get("content", "")
        if not text:
            continue
        if system and i == 0 and role == "user":
            text = system + "\n\n" + text
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    if not contents:
        raise ValueError("No messages to send")
    gen_config = types.GenerateContentConfig(temperature=0.1)
    response = client.models.generate_content(
        model=LLM_MODEL_GOOGLE,
        contents=contents,
        config=gen_config,
    )
    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("Empty response from Google")
    return response.candidates[0].content.parts[0].text


def _call_openrouter_chat(messages: list[dict], system: str) -> str:
    """Multi-turn chat via OpenRouter. messages: [{"role":"user"|"assistant","content":str}, ...]."""
    import httpx

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
    }
    api_messages = [{"role": "system", "content": system}] if system else []
    for m in messages:
        role = m.get("role", "user")
        if role == "model":
            role = "assistant"
        api_messages.append({"role": role, "content": m.get("content", "")})
    body = {
        "model": LLM_MODEL_OPENROUTER,
        "messages": api_messages,
        "temperature": 0.1,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    return choice.get("message", {}).get("content", "")


def generate_chat(messages: list[dict], system: str = "") -> str:
    """
    Multi-turn chat. messages: [{"role":"user"|"assistant","content":str}, ...].
    On Google/OpenRouter failure, retries with the other provider.
    """
    used = "google"
    try:
        if LLM_PRIMARY == "openrouter" or not GOOGLE_API_KEY:
            result = _call_openrouter_chat(messages, system)
            used = "openrouter"
        else:
            result = _call_google_chat(messages, system)
    except Exception as e:
        err_str = str(e).lower()
        is_retryable = (
            "429" in err_str or "503" in err_str or "quota" in err_str
            or "resource" in err_str or "unavailable" in err_str
            or "high demand" in err_str or "overloaded" in err_str
        )
        if is_retryable and OPENROUTER_API_KEY and LLM_PRIMARY != "openrouter":
            logger.warning("Primary LLM unavailable, using OpenRouter: %s", e)
            result = _call_openrouter_chat(messages, system)
            used = "openrouter"
        else:
            raise
    if used == "openrouter":
        logger.info("Used OpenRouter for chat")
    return result


def _call_openrouter(prompt: str, system: str, json_mode: bool) -> str:
    """Call OpenRouter (OpenAI-compatible API) with same model family."""
    import httpx

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
    }
    body = {
        "model": LLM_MODEL_OPENROUTER,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    return message.get("content", "")


def generate(prompt: str, system: str = "", json_mode: bool = True) -> str:
    """
    Generate completion. Primary: Google Gemini. On 429/quota, retry with OpenRouter.
    Returns raw response text (caller parses JSON if needed).
    """
    used = "google"
    try:
        if LLM_PRIMARY == "openrouter" or not GOOGLE_API_KEY:
            result = _call_openrouter(prompt, system, json_mode)
            used = "openrouter"
        else:
            result = _call_google(prompt, system, json_mode)
    except Exception as e:
        err_str = str(e).lower()
        # Retry with OpenRouter on rate limit, quota, overload (503), or temporary unavailability
        is_retryable = (
            "429" in err_str
            or "503" in err_str
            or "quota" in err_str
            or "resource" in err_str
            or "unavailable" in err_str
            or "high demand" in err_str
            or "overloaded" in err_str
        )
        if is_retryable and OPENROUTER_API_KEY and LLM_PRIMARY != "openrouter":
            logger.warning("Primary LLM unavailable (retryable), using OpenRouter: %s", e)
            result = _call_openrouter(prompt, system, json_mode)
            used = "openrouter"
        else:
            raise
    if used == "openrouter":
        logger.info("Used OpenRouter for this request (fallback or primary)")
    if json_mode and result:
        result = _strip_json_block(result)
    return result
