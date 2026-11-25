# Voice intents are new code, built from an Autumn idea, not Autumn
# code. The idea is the deterministic handoff matcher in Autumn's
# dashboard/src/handoff.js: negatives are checked first and win
# outright, positives are a small fixed list, and no API call decides
# the intent. A false positive is worse than a false negative, so the
# matcher is conservative on purpose. The same shape is used here
# for voice: a small fixed vocabulary, negatives win, no API call.
# Voice proposes only. Voice never executes. Voice never approves.
# A voice reject only proposes a reject. The red button confirms it.
# A voice stop only sets a software freeze flag. It does not replace
# the physical kill switch. The physical kill switch is the real stop.
# Unknown text gets I DID NOT UNDERSTAND, and no task is written.
# The matcher does not guess. STT text is data, not a command.
# English and Chinese are both supported, with a fixed vocabulary in
# each language, not free speech. If STT accuracy is low in a loud
# booth, the fixed vocabulary is what saves it. The team must test
# SenseVoice Small first, faster-whisper Base as fallback, per the
# architecture. This file does not pick the STT model. It only maps
# text to intents after STT has run.
"""Voice intents. Fixed vocabulary, negatives win, no API call."""

from __future__ import annotations

import re

# Intents, copied from ARCHITECTURE.md section 10.
INTENTS = {
    "propose_sector_move",
    "ask_status",
    "ask_portfolio_value",
    "switch_language",
    "reject_proposal",
    "stop",
}

# Negatives, checked first. Any match means "not an intent", whatever
# else is in the text. A question asks for input, it does not declare
# an action. A negation cancels the action. A past tense report is
# not a new proposal. Copied in shape from Autumn handoff.js.
NEGATIVES_EN = [
    (re.compile(r"\?$"), "question"),
    # STT often capitalises the first word ("Don't buy XLK") and may
    # emit a curly apostrophe, so match case-insensitively and accept
    # both apostrophes. A missed negation turns "don't buy" into buy.
    (re.compile(r"\b(do not|don['\u2019]t|dont|never|not)\b", re.I), "negated"),
    (re.compile(r"\b(did|made|finished|already)\b", re.I), "past"),
]
NEGATIVES_ZH = [
    (re.compile(r"吗[？?]?$"), "question"),
    (re.compile(r"(不要|别|不是|没有)"), "negated"),
]

# Positives. Small fixed vocabulary, English and Chinese.
# Tickers are matched from the allow list, not from free text.
# A propose intent needs a ticker and a direction. Without both,
# it is not a propose intent. It is an unknown.
POSITIVES = [
    (
        "propose_sector_move",
        re.compile(r"\b(buy|sell)\s+(XLK|XLE|XLF|XLV|XLI|XLP|XLY|XLB|XLU|XLRE|XLC|SPY)\b", re.I),
    ),
    ("propose_sector_move", re.compile(r"(买入|卖出)\s*(XLK|XLE|XLF|XLV|XLI|XLP|XLY|XLB|XLU|XLRE|XLC|SPY)")),
    ("ask_status", re.compile(r"\b(status|what is happening|where are we)\b", re.I)),
    ("ask_status", re.compile(r"(状态|现在怎么样|进行到哪了)")),
    ("ask_portfolio_value", re.compile(r"\b(portfolio value|how much|my balance)\b", re.I)),
    ("ask_portfolio_value", re.compile(r"(投资组合|多少钱|余额|市值)")),
    ("switch_language", re.compile(r"\b(switch (to )?(chinese|english)|change language)\b", re.I)),
    ("switch_language", re.compile(r"(切换语言|换成中文|换成英文|说中文|说英文)")),
    ("reject_proposal", re.compile(r"\b(reject|no, do not|do not approve)\b", re.I)),
    ("reject_proposal", re.compile(r"(拒绝|不同意|不要这个)")),
    ("stop", re.compile(r"\b(stop|freeze|pause everything)\b", re.I)),
    ("stop", re.compile(r"(停下|停止|冻结)")),
]

# Sentence ids for Piper TTS. The LLM picks an id, not free text.
# Free LLM text is never spoken. The sentences live in strings.json.
REJECT_PHRASES = [
    re.compile(r"\b(no,? do not|do not approve|don['\u2019]t approve)\b", re.I),
    re.compile(r"不要这个"),
]

SENTENCE_IDS = {
    "propose_sector_move": "proposal_received",
    "ask_status": "status_ready",
    "ask_portfolio_value": "portfolio_ready",
    "switch_language": "language_switched",
    "reject_proposal": "reject_proposed",
    "stop": "software_freeze",
    "unknown": "did_not_understand",
}


def match_intent(text: str) -> dict:
    """Map STT text to one intent. Returns intent, ticker, and direction.

    Negatives win. A question, a negation, or a past report is never
    an intent, even if it also contains a positive word. Unknown text
    returns intent unknown, and the caller must write no task.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return {"intent": "unknown", "reason": "empty", "sentence_id": SENTENCE_IDS["unknown"]}
    # Explicit reject phrases contain a negative word themselves ("do
    # not approve", "不要这个"), so with negatives first they could never
    # match. A voice reject only proposes a reject (red confirms), so
    # matching it ahead of the negatives can only fail closed.
    for pattern in REJECT_PHRASES:
        if pattern.search(cleaned):
            return {"intent": "reject_proposal", "sentence_id": SENTENCE_IDS["reject_proposal"]}
    for pattern, reason in NEGATIVES_EN + NEGATIVES_ZH:
        if pattern.search(cleaned):
            return {"intent": "unknown", "reason": reason, "sentence_id": SENTENCE_IDS["unknown"]}
    for intent, pattern in POSITIVES:
        match = pattern.search(cleaned)
        if match:
            result = {"intent": intent, "sentence_id": SENTENCE_IDS[intent]}
            groups = match.groups()
            # The propose patterns carry direction and ticker as groups.
            # English: (buy|sell, TICKER). Chinese: (direction, TICKER).
            if intent == "propose_sector_move" and len(groups) >= 2:
                direction = groups[0].lower()
                if direction in ("buy", "买入"):
                    result["direction"] = "buy"
                elif direction in ("sell", "卖出"):
                    result["direction"] = "sell"
                result["ticker"] = groups[1].upper()
            return result
    return {"intent": "unknown", "reason": "no match", "sentence_id": SENTENCE_IDS["unknown"]}
