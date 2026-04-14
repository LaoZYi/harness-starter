"""BM25 fallback search over lessons.md + task-log.md (Issue #29).

Pure-stdlib implementation inspired by mksglu/context-mode's FTS5/BM25
philosophy, but without the MCP server or SQLite dependency — we run
ranking on-the-fly over <1 MB of markdown per query.

Tokenizer: Mixed Chinese + Western. CJK chars become 1-gram tokens; runs
of [A-Za-z0-9_] become single tokens; case-folded; everything else dropped.

Ranking: Okapi BM25 (k1=1.5, b=0.75), with log((N-df+0.5)/(df+0.5)+1) IDF.

Used by: `/recall` skill's second-stage fallback; `.agent-harness/bin/memory
search` CLI; `/lfg` stage 0.2 history-loading fallback chain.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

from ._shared import require_harness

BM25_K1 = 1.5
BM25_B = 0.75
BM25_DEFAULT_TOP = 5

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")
_HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


def _tokenize(text: str) -> list[str]:
    """Mixed Chinese + Western tokenizer.

    CJK characters → 1-gram tokens. Western runs → single tokens. Case-folded.
    """
    if not text:
        return []
    tokens: list[str] = []
    for word in _WORD_RE.findall(text):
        tokens.append(word.lower())
    for ch in _CJK_RE.findall(text):
        tokens.append(ch)
    return tokens


def _segment_document(text: str) -> list[tuple[str, str]]:
    """Split markdown by `## ` headings → list of (title, body).

    Content before the first `## ` (usually a file header/index) is dropped.
    """
    if not text:
        return []
    segments: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            if current_title is not None:
                segments.append((current_title, "\n".join(current_lines).strip()))
            current_title = m.group("title").strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        segments.append((current_title, "\n".join(current_lines).strip()))
    return segments


def bm25_search(
    query: str,
    docs: list[tuple[str, str]],
    *,
    top: int = BM25_DEFAULT_TOP,
    k1: float = BM25_K1,
    b: float = BM25_B,
) -> list[tuple[float, str, str]]:
    """Okapi BM25 over (title, body) docs → top-K (score, title, body).

    Documents with score <= 0 are dropped. Empty query/docs → empty list.
    """
    query_tokens = _tokenize(query)
    if not query_tokens or not docs:
        return []

    doc_tokens = [_tokenize(f"{title} {body}") for title, body in docs]
    doc_lens = [len(toks) for toks in doc_tokens]
    n = len(docs)
    avgdl = sum(doc_lens) / n if n else 0.0

    df: dict[str, int] = {}
    for q in set(query_tokens):
        df[q] = sum(1 for toks in doc_tokens if q in toks)

    idf = {q: math.log((n - dfq + 0.5) / (dfq + 0.5) + 1.0) for q, dfq in df.items()}

    scored: list[tuple[float, str, str]] = []
    for (title, body), toks, dlen in zip(docs, doc_tokens, doc_lens):
        if dlen == 0:
            continue
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for q in query_tokens:
            freq = tf.get(q, 0)
            if freq == 0:
                continue
            denom = freq + k1 * (1 - b + b * dlen / avgdl) if avgdl else freq + k1
            score += idf[q] * (freq * (k1 + 1)) / denom
        if score > 0:
            scored.append((score, title, body))

    scored.sort(key=lambda r: r[0], reverse=True)
    return scored[: max(top, 0)]


def search_lessons(
    target_path: Path,
    query: str,
    *,
    scope: str = "all",
    top: int = BM25_DEFAULT_TOP,
) -> list[tuple[float, str, str]]:
    """Load lessons.md + task-log.md per scope, segment, run BM25.

    scope: "all" | "lessons" | "history". Missing files silently skipped.
    """
    require_harness(target_path)
    harness_dir = target_path / ".agent-harness"
    sources: list[Path] = []
    if scope in ("all", "lessons"):
        sources.append(harness_dir / "lessons.md")
    if scope in ("all", "history"):
        sources.append(harness_dir / "task-log.md")

    docs: list[tuple[str, str]] = []
    for src in sources:
        if not src.is_file():
            continue
        try:
            text = src.read_text(encoding="utf-8")
        except OSError:
            continue
        for title, body in _segment_document(text):
            docs.append((f"[{src.name}] {title}", body))

    return bm25_search(query, docs, top=top)
