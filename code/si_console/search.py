# This file is Autumn's autumn/search.py, repointed at SI Console task
# notes. What stayed: keyword scoring with stemming, accent folding,
# and IDF reweighting, section excerpts, citations with labels, the
# budgets (6 files, 12000 chars), and the inventory rule. No
# embeddings, no vector store, no rebuild step. That fits a Pi.
# What changed: the Gmail half is dropped. The corpus is task notes
# plus research notes, not mail plus notes. The search answers "what
# did we already do on this task", not "what did my mail say".
# The inventory rule is kept on purpose: "list every task" is not a
# search. It is a directory listing. Running a search for it returns
# the notes that happen to contain the words list, file, or vault,
# which is an arbitrary few. list_tasks in vault.py does that job.
# Citations: every answer must say which note it came from, with a
# label like V1 or V2, the same way Autumn did. An answer with no
# citation is a guess, and the coordinator must not act on it.
"""Vault search. Keyword ranking over task notes, with citations."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from si_console import config
from si_console.errors import SourceError

# Budgets, copied from Autumn search.py. Small on purpose, so six long
# notes cannot blow the context that six short ones fit inside.
MAX_VAULT_FILES = 6
MAX_VAULT_CHARS = 12000
MIN_SCORE = 1.0
RELATIVE_CUTOFF = 0.5

# Small stop word list. These words carry no meaning for ranking.
STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "about",
    "what", "when", "where", "which", "have", "has", "were", "been",
}


def _fold(text: str) -> str:
    """Lowercase and strip accents, so cafe matches cafe. From Autumn."""
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return folded.lower()


def _stem(word: str) -> str:
    """Tiny stemmer. From Autumn. Strips common endings only."""
    for ending in ("ing", "ed", "es", "s"):
        if len(word) > len(ending) + 2 and word.endswith(ending):
            return word[: -len(ending)]
    return word


@dataclass
class Term:
    """One search term, with a weight. Named terms weigh more."""

    stem: str
    weight: float = 1.0


def extract_terms(question: str) -> list[Term]:
    """Split a question into weighted terms. From Autumn search.py."""
    words = re.findall(r"[a-z0-9]+", _fold(question))
    terms: list[Term] = []
    seen: dict[str, Term] = {}
    for word in words:
        if word in STOP_WORDS or len(word) < 3:
            continue
        stem = _stem(word)
        if stem in seen:
            seen[stem].weight += 0.5
        else:
            term = Term(stem=stem, weight=1.0)
            seen[stem] = term
            terms.append(term)
    return terms


def _pattern(term: Term) -> re.Pattern:
    return re.compile(r"\b" + re.escape(term.stem) + r"\w*\b")


@dataclass
class VaultHit:
    """One ranked note, with an excerpt and the terms that matched."""

    path: str
    score: float
    excerpt: str
    matched_terms: set
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "path": self.path,
            "score": round(self.score, 2),
            "excerpt": self.excerpt,
            "matched_terms": sorted(self.matched_terms),
        }


def _excerpt(text: str, terms: list[Term]) -> tuple[str, bool]:
    """One short excerpt around the first matching term. From Autumn."""
    folded = _fold(text)
    best = -1
    for term in terms:
        found = folded.find(term.stem)
        if found >= 0 and (best < 0 or found < best):
            best = found
    if best < 0:
        return text[:200].strip(), False
    start = max(0, best - 80)
    end = min(len(text), best + 220)
    piece = text[start:end].strip()
    if start > 0:
        piece = "..." + piece
    if end < len(text):
        piece = piece + "..."
    return piece, True


def _score_file(path: Path, vault: Path, text: str, terms: list[Term]):
    """Score one note. Title matches weigh more than body matches."""
    folded = _fold(text)
    score = 0.0
    matched: set[str] = set()
    title = text.split("\n", 1)[0]
    for term in terms:
        pattern = _pattern(term)
        hits = len(pattern.findall(folded))
        if hits == 0:
            continue
        matched.add(term.stem)
        # A term in the title is worth three body hits.
        title_hits = len(pattern.findall(_fold(title)))
        score += term.weight * (hits + 2 * title_hits)
    if score < MIN_SCORE:
        return None
    excerpt, _ = _excerpt(text, terms)
    return VaultHit(
        path=str(path.relative_to(vault)),
        score=score,
        excerpt=excerpt,
        matched_terms=matched,
    )


def _iter_markdown(vault: Path) -> Iterable[Path]:
    """Every markdown note in the vault, skipping ignored folders."""
    for path in vault.rglob("*.md"):
        if any(part in config.VAULT_IGNORE_DIRS for part in path.parts):
            continue
        yield path


def _reweight(terms: list[Term], corpus: list[str]) -> list[Term]:
    """IDF reweighting. A term in every note weighs less than a rare one."""
    total = max(1, len(corpus))
    out = []
    for term in terms:
        docs = sum(1 for text in corpus if term.stem in text)
        # A term in all notes adds almost nothing. A term in one note
        # is a strong signal. This is the same shape as Autumn's.
        import math

        idf = math.log((total + 1) / (docs + 1)) + 1
        out.append(Term(stem=term.stem, weight=term.weight * idf))
    return out


def search_vault(
    question: str,
    terms: Optional[list[Term]] = None,
    limit: int = MAX_VAULT_FILES,
) -> list[VaultHit]:
    """Rank every note in the vault against a question. Full text.

    Returns nothing when the question names something specific and
    the vault does not contain that name. Returning nothing is the
    honest answer. The notes that matched on filler words only would
    be a lie. Same rule as Autumn search.py.
    """
    terms = terms if terms is not None else extract_terms(question)
    if not terms:
        return []
    vault = Path(config.VAULT_PATH or "")
    if not vault or not vault.is_dir():
        raise SourceError(
            "obsidian",
            f"Vault path is not a directory: {vault}",
            remedy="Set SI_VAULT_PATH in .env to the vault folder.",
        )
    corpus: list[tuple[Path, str]] = []
    for path in _iter_markdown(vault):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if text.strip():
            corpus.append((path, text))
    weighted = _reweight(terms, [_fold(t) for _, t in corpus])
    hits = [
        hit
        for hit in (_score_file(p, vault, t, weighted) for p, t in corpus)
        if hit and hit.score >= MIN_SCORE
    ]
    named = {t.stem for t in terms if t.weight >= 3.0}
    if named and not any(named & set(h.matched_terms) for h in hits):
        return []
    hits.sort(key=lambda h: (-h.score, h.path))
    if hits:
        floor = hits[0].score * RELATIVE_CUTOFF
        hits = [h for h in hits if h.score >= floor]
    kept: list[VaultHit] = []
    spent = 0
    for i, hit in enumerate(hits[:limit]):
        hit.label = f"V{i + 1}"
        if kept and spent + len(hit.excerpt) > MAX_VAULT_CHARS:
            break
        kept.append(hit)
        spent += len(hit.excerpt)
    return kept


def wants_inventory(question: str) -> bool:
    """True when the question asks for a listing, not a search.

    From Autumn search.py. "List every note" is enumeration, not
    retrieval. The caller must use list_tasks in vault.py instead.
    """
    folded = _fold(question)
    return bool(
        re.search(r"\blist\b.*\b(all|every|tasks|notes|files)\b", folded)
        or re.search(r"\bshow me (all|every)\b", folded)
    )


def build_prompt(question: str, hits: list[VaultHit]) -> str:
    """Build the prompt for a search answer, with citation labels.

    The model must cite by label, like [V1]. A claim with no label
    is a guess. Autumn's ask_vault.py flagged fabricated citations
    the same way. Keep that check in the caller.
    """
    lines = [f"Question: {question}", "", "Sources:"]
    for hit in hits:
        lines.append(f"[{hit.label}] {hit.path}")
        lines.append(hit.excerpt)
        lines.append("")
    lines.append(
        "Answer from the sources above only. Cite each claim as [V1], "
        "[V2], and so on. If the sources do not answer the question, "
        "say so. Do not invent a citation."
    )
    return "\n".join(lines)
