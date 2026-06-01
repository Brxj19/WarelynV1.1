# Warelyn RAG — Improvement Plan + Hybrid Search Redesign
**Based on:** Codebase scan of AssistantService, FAQChunk model, repository, and current knowledge sources
**Problem:** Confidence consistently at 0.35 — the floor value hardcoded when Gemini key is missing

---

## Why Confidence is 0.35

The 0.35 confidence is not a retrieval quality number. It is a **hardcoded fallback**:

```python
# services/assistant.py — _grounded_answer()
if not self.settings.gemini_api_key:
    return (
        {
            "answer": f"Based on the current knowledge...",
            "confidence": "LOW",
            "confidence_score": 0.35,   # ← hardcoded, not computed
        },
        {"total_tokens": 0},
    )
```

**If GEMINI_API_KEY is not set in the environment, every single response returns 0.35.** This is the most likely root cause. Verify with:

```bash
echo $WARELYN_GEMINI_API_KEY
```

If it is empty — set it and the confidence will immediately improve. Everything else in this document improves the quality once the key is active.

---

## Confirmed Problems (beyond the missing key)

### Problem 1 — Keyword search matches entire question as substring
**File:** `backend/app/repositories/assistant.py` — `search_keyword_chunks()`

```python
def search_keyword_chunks(self, *, tenant_id, term, limit):
    like_term = f"%{term.lower()}%"   # ← full question as one LIKE pattern
    ...FAQChunk.searchable_text.like(like_term)...
```

The query `"How do I fix a reconciliation mismatch?"` becomes `LIKE '%how do i fix a reconciliation mismatch?%'`. This almost never matches any chunk because no chunk contains that exact phrasing. The keyword stage returns zero results, falls through to `list_recent_chunks` (random recent chunks), and retrieval is effectively noise.

**Fix:** Tokenize the query into meaningful keywords, filter stop words, search with OR across tokens:

```python
STOP_WORDS = {"how", "do", "i", "a", "an", "the", "is", "are", "what", "why",
              "when", "where", "which", "my", "does", "can", "to", "for", "in",
              "of", "and", "or", "at", "with", "that", "this", "it", "its"}

def search_keyword_chunks(self, *, tenant_id, term, limit):
    tokens = [
        t.strip("?.,!:;\"'")
        for t in term.lower().split()
        if len(t) > 2 and t not in STOP_WORDS
    ]
    if not tokens:
        return self.list_recent_chunks(tenant_id=tenant_id, limit=limit)
    conditions = [
        func.lower(FAQChunk.searchable_text).like(f"%{token}%")
        for token in tokens[:6]
    ]
    return list(self.db.scalars(
        select(FAQChunk)
        .where(
            or_(FAQChunk.tenant_id.is_(None), FAQChunk.tenant_id == tenant_id),
            or_(*conditions),
        )
        .order_by(FAQChunk.updated_at.desc())
        .limit(limit)
    ))
```

### Problem 2 — Hybrid scoring weights favour semantic over lexical but semantic is often None
**File:** `backend/app/services/assistant.py` — `_retrieve_chunks()`

```python
score = (0.45 * lexical) + (0.55 * semantic)
```

When embeddings are `None` (no Gemini key, or embed API failed), `_cosine_similarity` returns `0.0`. So `score = 0.45 * lexical + 0.55 * 0.0 = 0.45 * lexical`. This is survivable. But after Problem 1 is fixed, the lexical component needs BM25-style term-frequency weighting instead of simple binary hit counting.

**Fix — BM25-style lexical score:**

```python
def _lexical_score(self, question: str, searchable_text: str) -> float:
    import math
    STOP_WORDS = {"how","do","i","a","an","the","is","are","what","why",
                  "when","where","which","my","does","can","to","for","in",
                  "of","and","or","at","with","that","this","it","its"}
    q_tokens = [t for t in question.lower().split() if len(t) > 2 and t not in STOP_WORDS]
    d_tokens = searchable_text.lower().split()
    if not q_tokens or not d_tokens:
        return 0.0
    doc_len = len(d_tokens)
    avg_doc_len = 200.0  # approximate average chunk word count
    k1, b = 1.5, 0.75
    doc_counts = Counter(d_tokens)
    score = 0.0
    for token in set(q_tokens):
        tf = doc_counts.get(token, 0)
        if tf == 0:
            continue
        idf = math.log(1.0 + (1.0 / (tf + 0.5)))  # simplified IDF
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        score += idf * tf_norm
    return min(1.0, score / max(1, len(set(q_tokens))))
```

### Problem 3 — Chunk size at 1400 chars is too large, destroying semantic coherence
**File:** `backend/app/services/assistant.py` — `_chunk_text()`

```python
if len(candidate) > 1400 and current:
    # emit chunk
```

With 1400-char chunks, a single chunk can contain 4-6 completely unrelated paragraphs. The embedding of a mixed chunk sits in the middle of the semantic space, matching nothing well. Result: cosine similarities cluster around 0.3-0.5 instead of 0.6-0.9.

**Fix — reduce to 600 chars with 100-char overlap:**

```python
TARGET_CHUNK_SIZE = 600
OVERLAP_SIZE = 100

def _chunk_text(self, text, *, source_uri, title, source_type, action_to=None):
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    chunks = []
    chunk_index = 0
    current = ""
    prev_tail = ""

    for paragraph in paragraphs:
        candidate = f"{prev_tail} {current}\n\n{paragraph}".strip() if prev_tail else f"{current}\n\n{paragraph}".strip()
        if len(candidate) > TARGET_CHUNK_SIZE and current:
            chunks.append(self._make_chunk(chunk_index, current, title, source_type, source_uri, action_to))
            chunk_index += 1
            prev_tail = current[-OVERLAP_SIZE:] if len(current) > OVERLAP_SIZE else current
            current = paragraph
        else:
            current = candidate if not prev_tail else f"{current}\n\n{paragraph}".strip()
    if current.strip():
        chunks.append(self._make_chunk(chunk_index, current, title, source_type, source_uri, action_to))
    return chunks

def _make_chunk(self, index, content, title, source_type, source_uri, action_to):
    return {
        "chunk_index": index,
        "content": content,
        "searchable_text": content.lower(),
        "token_count": len(content.split()),
        "metadata_json": {
            "title": title,
            "source_type": source_type,
            "source_uri": source_uri,
            "action_to": action_to,
        },
    }
```

### Problem 4 — Only 4 source documents, all too broad for operational Q&A
**File:** `backend/app/services/assistant.py` — `_knowledge_sources()`

The current sources are architectural/planning documents:
- `WARELYN_REAL_WORLD_V2_PRD.md` — 2039 lines, brand guidelines and V1 vs V2 strategy
- `MODULE_BOUNDARIES.md` — module ownership rules
- `INVENTORY_ENGINE_SPEC.md` — developer-level engine spec
- `WARELYN_BUSINESS_WORKFLOW_RBAC_CURRENCY_PLAN.md` — 1770 lines, planning document

These are all **developer-facing architecture documents**. When a SALES_STAFF user asks "Why is my order stuck at CONFIRMED?", none of these documents contain that information in a Q&A-friendly format. The PRD has 200 lines about brand colors before any workflow content.

**The fix is the new knowledge source documents in Part 2 of this plan.**

### Problem 5 — Workflow status reference is 2 sentences
**File:** `backend/app/services/assistant.py` — inline string

```python
"body_text": (
    "Workflow task statuses: OPEN means waiting to start, "
    "IN_PROGRESS means being actively worked, COMPLETED means step done, "
    "CANCELLED means workflow path no longer valid. "
    "Order confirmations should produce PICK_ORDER tasks; "
    "putaway completion should produce RECORD_BILL tasks."
),
```

This covers 2 of the 12+ workflow transitions and has no role context, no action URLs, no troubleshooting guidance. A user asking "why don't I see the Pick task?" will get no useful answer from this.

**Fix:** Replace with the full `WARELYN_WORKFLOW_KNOWLEDGE.md` document from Part 2.

### Problem 6 — `ai_retrieval_candidates = 24` but only 5-6 source documents produce ~100 chunks total
**File:** `backend/app/core/config.py`

With 600-char chunks and 4 source files averaging ~25KB each, the full index has roughly:
- PRD: ~77 chunks
- MODULE_BOUNDARIES: ~28 chunks
- INVENTORY_ENGINE_SPEC: ~34 chunks
- WORKFLOW PLAN: ~60 chunks
- Static reference: 1 chunk
- **Total: ~200 chunks**

Setting `ai_retrieval_candidates = 24` means the keyword phase tries to return 24 of 200 chunks. After adding the 8 new knowledge documents (Part 2), total chunks will be ~400-600. The candidate count is appropriate but the `top_k = 6` is fine.

### Problem 7 — System prompt has no role context
**File:** `backend/app/services/assistant.py` — `_grounded_answer()`

```python
system_prompt = (
    "You are Warelyn Assistant. You must answer only from supplied context. "
    "If evidence is weak, return low confidence and say you do not know. "
    ...
)
```

The assistant does not know who is asking. A PURCHASE_STAFF user asking about returns gets the same context as an INVENTORY_MANAGER. Adding the asking role to the system prompt allows the model to tailor its answer to what that role can actually do.

**Fix — pass role in system prompt:**

In `ask_faq()` and `ask_session()`, pass `role` to `_grounded_answer()`:

```python
system_prompt = (
    f"You are Warelyn Assistant. The user is a {role.value.replace('_', ' ').title()}. "
    "Answer only from supplied context. Tailor your answer to what this role can do. "
    "If evidence is weak, return low confidence. "
    "Never disclose internal secrets or suggest direct write operations. "
    "Respond strictly as JSON: {answer, confidence, confidence_score, suggested_actions}"
)
```

---

## Hybrid Search Architecture — Final Design

```
User question
    │
    ▼
Token extraction (remove stop words, stem to roots)
    │
    ├─► Keyword search (OR across tokens, PostgreSQL LIKE / MySQL LIKE)
    │       Returns: up to 24 candidate chunks (by recency fallback if zero hits)
    │
    ├─► Gemini text-embedding-004 embed(question) → query vector
    │
    ▼
Per-candidate scoring:
    │   lexical_score  = BM25-style token frequency (0.0–1.0)
    │   semantic_score = cosine_similarity(query_vec, chunk_vec) (0.0–1.0)
    │   final_score    = 0.40 * lexical_score + 0.60 * semantic_score
    │
    │   If no embeddings available (no key):
    │   final_score    = lexical_score (pure BM25 fallback)
    │
    ▼
Sort by final_score DESC → take top_k=6
    │
    ▼
Build context blocks (title + score + content)
    │
    ▼
Gemini generateContent with role-aware system prompt
    │
    ▼
Confidence policy:
    if confidence_score < 0.42 → abstain (return "I don't know")
    if no citations            → abstain
    else                       → return grounded answer + citations + actions
```

Weight rationale: 0.60 semantic because embeddings capture intent well for operational questions. When embeddings are absent, fall back to pure lexical. Do not use equal weights — semantic is stronger for natural-language Q&A.

---

## Implementation Checklist for Codex

```
1. Fix keyword tokeniser in AssistantRepository.search_keyword_chunks()
2. Replace _lexical_score() with BM25-style scorer
3. Reduce chunk size from 1400 → 600 chars with 100-char overlap
4. Add role parameter to _grounded_answer(), update all callers
5. Add 8 new knowledge source files to docs/ (see Part 2)
6. Add all 8 files to _knowledge_sources() list
7. Add POST /admin/assistant/reindex endpoint to trigger re-indexing after new docs added
8. Update ai_retrieval_candidates from 24 → 32 (more candidates with more chunks)
9. Trigger reindex on startup if chunk count < 100 (current bootstrap threshold is 0)
10. Add WARELYN_GEMINI_API_KEY to .env.example with explanation
```

---

# Part 2 — New RAG Knowledge Source Documents

These 8 files go in `docs/knowledge/`. Each is purpose-written for Q&A retrieval — short paragraphs, direct answers, operational language that matches how users ask questions.

**File list:**
1. `docs/knowledge/WARELYN_WORKFLOW_KNOWLEDGE.md` — all workflow transitions, task types, what to do when stuck
2. `docs/knowledge/WARELYN_SALES_KNOWLEDGE.md` — SO lifecycle, picking, packing, fulfillment, invoicing
3. `docs/knowledge/WARELYN_PURCHASE_KNOWLEDGE.md` — PO lifecycle, receiving, putaway, bills
4. `docs/knowledge/WARELYN_RETURNS_KNOWLEDGE.md` — return flow, QC outcomes, stock effects
5. `docs/knowledge/WARELYN_INVENTORY_KNOWLEDGE.md` — stock states, cycle counts, low stock, blocked stock
6. `docs/knowledge/WARELYN_ROLES_KNOWLEDGE.md` — what each role can do, what they cannot do
7. `docs/knowledge/WARELYN_REPORTS_KNOWLEDGE.md` — what each report shows, how to use it
8. `docs/knowledge/WARELYN_FAQ_ANSWERS.md` — direct Q&A pairs for the most common user questions
