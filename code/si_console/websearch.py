# Web search for research only. It is never a trading signal, and text
# from the web is data, never instructions, because a web page could try
# to steer the agent.
# Provider order:
#   1. Zhipu (Z.ai) Web Search API on the GLM key (GLM_API_KEY). Works
#      from mainland China; no extra account.
#   2. Bocha, only if BOCHA_API_KEY is set (bocha.web_search).
# Zhipu contract, read from docs.bigmodel.cn (Web Search API reference
# and guide) and docs.z.ai on 2026-11-26 (LIKELY, no live call yet):
#   POST {GLM_BASE_URL}/web_search, Authorization: Bearer <GLM key>
#   mainland body: {"search_query": "<= 70 chars", "search_engine":
#     "search_std", "search_intent": false, "count": 1..50,
#     "search_recency_filter": "oneDay|oneWeek|oneMonth|oneYear|noLimit",
#     "content_size": "medium|high"}
#   Z.ai (api.z.ai) body: search_engine "search-prime"; no search_intent
#     and no content_size.
#   -> {"search_result": [{"title", "content", "link", "media",
#       "publish_date", "refer", "icon"}], ...}
#   errors: mainland {"error": {"code", "message"}}; Z.ai {"code", "message"}.
# Returns the same shape as bocha.web_search: {"results": [...]} or
# {"error": "..."}. A failed search is an error, never an empty result,
# and it never blocks the task.
"""Web search: Zhipu (Z.ai) first, Bocha as an optional fallback."""

from __future__ import annotations

import httpx

from si_console import config

FRESHNESS_VALUES = {"oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"}
MAINLAND_MAX_QUERY_CHARS = 70


def _international() -> bool:
    return "z.ai" in httpx.URL(config.GLM_BASE_URL.rstrip("/")).host


def zhipu_configured() -> bool:
    return bool(config.GLM_API_KEY)


def clip_query(query: str, limit: int = MAINLAND_MAX_QUERY_CHARS) -> str:
    """Mainland Zhipu search takes at most 70 characters. Cut at a word
    boundary when there is one, so the query stays readable."""
    query = " ".join(query.split())
    if len(query) <= limit:
        return query
    cut = query[:limit]
    space = cut.rfind(" ")
    return cut[:space] if space >= limit // 2 else cut


def _error_message(response: httpx.Response) -> str:
    from si_console.chat_client import error_detail

    return error_detail(response, config.GLM_API_KEY).replace(" Provider says: ", ": ")


def zhipu_search(query: str, count: int = 5, freshness: str = "noLimit") -> dict:
    """One Zhipu web search. One retry on a network error, none on an
    HTTP error. Never raises."""
    if not zhipu_configured():
        return {"error": "No GLM key configured. Set GLM_API_KEY in .env."}
    international = _international()
    body = {
        "search_query": query if international else clip_query(query),
        "search_engine": "search-prime" if international else config.ZHIPU_SEARCH_ENGINE,
        "count": count,
        "search_recency_filter": freshness,
    }
    if not international:
        body["search_intent"] = False
        body["content_size"] = "medium"
    url = config.GLM_BASE_URL.rstrip("/") + "/web_search"
    headers = {"Authorization": f"Bearer {config.GLM_API_KEY}",
               "Content-Type": "application/json"}
    for attempt in (1, 2):
        try:
            response = httpx.post(url, headers=headers, json=body,
                                  timeout=config.ZHIPU_SEARCH_TIMEOUT_SECONDS)
        except httpx.HTTPError as exc:
            if attempt == 2:
                return {"error": f"Zhipu search not reachable ({type(exc).__name__}). Search is off."}
            continue
        if response.status_code != 200:
            from si_console.chat_client import _out_of_credit

            message = _error_message(response)
            if response.status_code == 402 or _out_of_credit(message):
                return {"error": f"Zhipu account is out of credit ({response.status_code}){message}. "
                                 "Top up the GLM account; search shares its balance."}
            return {"error": f"Zhipu search error {response.status_code}{message}"}
        try:
            payload = response.json()
        except ValueError:
            return {"error": "Zhipu search returned a reply that was not JSON."}
        if isinstance(payload, dict) and payload.get("error"):
            return {"error": f"Zhipu search error{_error_message(response)}"}
        items = payload.get("search_result") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {"error": "Zhipu search reply has no search_result list."}
        results = []
        for item in items[:count]:
            if not isinstance(item, dict):
                continue
            results.append({
                "title": item.get("title", "") or "",
                "url": item.get("link", "") or "",
                "snippet": item.get("content", "") or "",
                "date": item.get("publish_date", "") or "",
                "source": item.get("media", "") or "",
            })
        return {"results": results, "provider": "zhipu"}
    return {"error": "Zhipu search failed after one retry."}


def web_search(query: str, count: int = 5, freshness: str = "noLimit", lang: str = "en") -> dict:
    """Research search. Zhipu first; Bocha only if its key is set and
    Zhipu failed. Validates input the same way for both."""
    if not query or not query.strip() or len(query) > 200:
        return {"error": "Query must be 1 to 200 characters."}
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10:
        return {"error": "Count must be 1 to 10."}
    if freshness not in FRESHNESS_VALUES:
        return {"error": f"Unknown freshness: {freshness}."}
    errors = []
    if zhipu_configured():
        result = zhipu_search(query, count, freshness)
        if "results" in result:
            return result
        errors.append(result["error"])
    if config.BOCHA_API_KEY:
        from si_console import bocha

        result = bocha.web_search(query, count, freshness, lang)
        if "results" in result:
            result["provider"] = "bocha"
            return result
        errors.append(result["error"])
    if not errors:
        return {"error": "No search configured. Set GLM_API_KEY in .env (Zhipu search)."}
    return {"error": " | ".join(errors)}
