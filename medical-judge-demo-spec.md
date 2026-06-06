# Evidence-Grounded Medical LLM-as-Judge — Build Spec

> A full-stack demo of a medical answer evaluator whose **confidence is capped by the
> strength of evidence it can ground each verdict to**, and which reports results
> **decomposed by clinical dimension** — never as a single mixed average.

This document is a build brief for an AI coding agent (Claude Code) + a human developer.
Read the **Thesis** and **Core mechanic** sections first; they define every downstream
design decision. When in doubt, preserve the thesis over convenience.

---

## 1. Thesis (the thing this demo argues)

In medicine, a judgment is only as **trustworthy** as the evidence it can be grounded to,
and only as **meaningful** as the dimension it is reported on. Therefore an evaluator must:

1. **Cap confidence by evidence tier** — a verdict's displayed confidence can never exceed
   the ceiling of the strongest source it actually grounded to. Evidence raises a *ceiling*;
   it never inflates a number. An ungrounded but confident-sounding verdict is structurally
   forced to low confidence.
2. **Decompose, never average** — report a per-dimension scorecard with evidence provenance,
   not one aggregate number. A single mixed score hides which verdicts are ungrounded.

The demo exists to make these two claims *visible and interactive*. The "villain" we are
arguing against is the confident, ungrounded, single-number medical score.

### Why this is defensible (design constraints, not decoration)

- **Ceiling, not floor.** Grounding only ever *lowers* confidence toward the evidence
  ceiling. It never raises a verdict above the model's own confidence. This protects against
  "the model misread the guideline" — a misread source can't inflate trust.
- **Grounding must be inspectable.** Every grounded verdict carries the actual source snippet
  so a human can verify it. No hidden retrieval.
- **Population vs individual claims.** EBM tiers grade *population-level* evidence. A claim
  about *this specific patient's application* is not gradeable the same way, so individual-scope
  claims get an additional hard ceiling regardless of source tier. Encode this distinction.
- **Cost follows stakes.** Deep grounding is expensive, so the system grounds hardest on
  safety-critical and high-acuity dimensions (see stretch goals).

This is a **demo on synthetic data**, not a clinical tool. See §10.

---

## 2. Core mechanic (the heart — implement as a pure, unit-tested function)

### Evidence ladder

| Key | Label | Code | Confidence ceiling |
|-----|-------|------|--------------------|
| `systematic_review` | Systematic review / meta-analysis | T1 | 0.95 |
| `rct` | Randomized controlled trial | T2 | 0.90 |
| `guideline` | Clinical guideline / consensus | T4 | 0.80 |
| `cohort` | Cohort / observational study | T3 | 0.75 |
| `expert` | Expert opinion / case report | T5 | 0.60 |
| `model_prior` | Model prior (ungrounded) | T6 | 0.40 |

Ceilings are configurable constants, not magic numbers in logic.

### Capping + escalation rule (reference implementation)

```python
# capping.py  — PURE. No I/O, no LLM calls. This is the thesis in code. Unit-test it hard.

EVIDENCE_CEILINGS = {
    "systematic_review": 0.95,
    "rct": 0.90,
    "guideline": 0.80,
    "cohort": 0.75,
    "expert": 0.60,
    "model_prior": 0.40,
}

INDIVIDUAL_SCOPE_CEILING = 0.60   # individual-application claims are never "highly certain"
LOW_CONFIDENCE_ESCALATION = 0.50  # below this -> human review

def cap_confidence(model_confidence: float, grounded_tier: str,
                   claim_scope: str = "population") -> float:
    """Displayed confidence is the model's confidence clamped down by what evidence backs it."""
    ceiling = EVIDENCE_CEILINGS[grounded_tier]
    capped = min(model_confidence, ceiling)
    if claim_scope == "individual":
        capped = min(capped, INDIVIDUAL_SCOPE_CEILING)
    return round(capped, 2)

def escalation(safety_critical: bool, grounded_tier: str,
               displayed_confidence: float) -> dict | None:
    # A safety claim with no real evidence is "unverified" regardless of how confident the model is.
    if safety_critical and grounded_tier == "model_prior":
        return {"flag": True, "reason": "unverified_safety_claim", "severity": "danger"}
    if displayed_confidence < LOW_CONFIDENCE_ESCALATION:
        return {"flag": True, "reason": "low_confidence", "severity": "warning"}
    return None
```

**Invariants the test suite must enforce:**
- `displayed_confidence <= EVIDENCE_CEILINGS[grounded_tier]` always.
- `displayed_confidence <= model_confidence` always (never inflated).
- A `safety_critical` verdict grounded to `model_prior` always escalates.
- Lowering a verdict's tier can only keep or raise its escalation severity, never lower it.

---

## 3. Data model

All data is synthetic / from public sources. Three core entities.

### Evidence source (`data/evidence/*.json`)
```json
{
  "source_id": "bnf_warfarin_nsaid",
  "title": "Anticoagulants — interactions with NSAIDs",
  "tier": "guideline",
  "text": "Concurrent use of NSAIDs with warfarin increases bleeding risk ...",
  "url": "https://example.org/synthetic-guideline",
  "topics": ["warfarin", "nsaid", "ibuprofen", "bleeding"]
}
```

### Case (`data/cases/*.json`)
```json
{
  "id": "case_0421",
  "patient_question": "I'm on warfarin. My knee hurts — can I take ibuprofen for a few days?",
  "candidate_answer": "Yes, ibuprofen is an effective option for knee pain. Take 400 mg ...",
  "complexity": { "reasoning": "high", "visual_dependency": "low" },
  "dimensions": [
    { "id": "dosing_accuracy",        "label": "Dosing accuracy",         "safety_critical": false, "claim_scope": "population" },
    { "id": "drug_interaction_safety","label": "Drug-interaction safety", "safety_critical": true,  "claim_scope": "population" },
    { "id": "completeness_warnings",  "label": "Completeness of warnings","safety_critical": false, "claim_scope": "population" },
    { "id": "monitoring_followup",    "label": "Monitoring & follow-up",  "safety_critical": false, "claim_scope": "individual" }
  ]
}
```

### Verdict (produced at judge time, persisted)
```json
{
  "verdict_id": "case_0421:drug_interaction_safety",
  "case_id": "case_0421",
  "dimension": "drug_interaction_safety",
  "safety_critical": true,
  "claim_scope": "population",
  "model_confidence": 0.88,
  "model_reasoning": "short rationale from the judge model",
  "grounded_tier": "model_prior",
  "grounding": [
    { "source_id": "bnf_warfarin_nsaid", "tier": "guideline", "snippet": "...", "score": 0.0 }
  ],
  "displayed_confidence": 0.40,
  "escalation": { "flag": true, "reason": "unverified_safety_claim", "severity": "danger" },
  "human_review": null
}
```

> **Hard rule:** the API never returns a single aggregate "overall score" field. Summaries
> are counts (`trustworthy` / `caution` / `escalated`) plus the per-dimension array. If a UI
> wants a headline number, it shows the count of trustworthy dimensions, not an average.

---

## 4. API contract (FastAPI)

```
GET  /api/cases                  -> [CaseSummary]
GET  /api/cases/{id}             -> Case
POST /api/judge                  body: {case_id} -> { verdicts: [Verdict], summary: Summary }
GET  /api/evidence?q=...         -> [EvidenceSource]   (retrieval inspector / debug)
GET  /api/queue                  -> [Verdict]          (escalation.flag == true, unreviewed)
POST /api/review                 body: {verdict_id, decision: "approve"|"override", note} -> Verdict
```

`Summary`:
```json
{ "trustworthy": 2, "caution": 1, "escalated": 1, "mixed_average_suppressed": 81 }
```
`mixed_average_suppressed` is included only so the UI can show it struck-through, to make the
"we deliberately do not report this" point. It is never used in any logic.

---

## 5. Backend module layout

```
backend/
  main.py            FastAPI app + routes
  models.py          Pydantic + SQLModel schemas (Case, Verdict, Review, EvidenceSource)
  capping.py         PURE thesis logic from §2  (100% unit-tested)
  escalation.py      escalation rules (or fold into capping.py)
  evidence_store.py  load data/evidence/*.json; retrieve(query, dimension) -> ranked sources
  tier_classifier.py given retrieved sources for a verdict, pick the strongest tier actually
                     supporting the claim (start rule-based: top relevant source's tier;
                     model_prior if nothing relevant retrieved)
  grader.py          per-dimension judge: prompt the LLM for {model_confidence, reasoning};
                     then call retrieval + tier_classifier + capping to assemble a Verdict
  llm_provider.py    provider abstraction. ENV: LLM_PROVIDER, model id, API key.
                     Ship a MockProvider (deterministic) so the app runs with zero keys.
  db.py              SQLite engine (sqlmodel); tables: verdicts, reviews
  tests/
    test_capping.py  enforce the §2 invariants
```

Retrieval can start as keyword/topic matching over the JSON library. Embedding search is a
stretch goal, not required for v1.

`grader.py` flow per dimension:
1. Ask the judge model to assess the candidate answer on this dimension → `model_confidence` (0–1) + short reasoning. Keep judge model **different family** from any model being evaluated, to avoid blind-spot overlap.
2. `evidence_store.retrieve(...)` → candidate sources.
3. `tier_classifier` → `grounded_tier` + `grounding` snippets (`model_prior` if nothing relevant).
4. `capping.cap_confidence(...)` → `displayed_confidence`.
5. `escalation(...)` → flag.
6. Persist + return Verdict.

---

## 6. Frontend layout (Vite + React + TypeScript + Tailwind)

```
frontend/
  src/
    components/
      ScoreCard.tsx        the dimension scorecard (one DimensionRow per dimension)
      DimensionRow.tsx     name + safety badge + capped% + dual bar
                           (faded bar = model_confidence, solid bar = displayed_confidence,
                            ceiling marker) + escalation pill
      TierSelector.tsx     "explore mode" dropdown to re-ground a verdict and watch the cap move
      EvidenceDrawer.tsx   click a grounding snippet -> verify the source text
      ReviewQueue.tsx      escalated verdicts; approve / override + note
      CaseList.tsx         pick a case
      ComplexityTags.tsx   reasoning x visual-dependency tags
      ProfileRadar.tsx     per-dimension profile (recharts) — NOT one number
    api.ts                 typed client for §4
    App.tsx
```

Color semantics (reuse everywhere): green = trustworthy (capped ≥ 0.75, no flag),
amber = caution, red = safety/danger. Show a persistent "demo · not for clinical use" banner.

The signature interaction (must work): in explore mode, changing a verdict's grounded tier
live-updates its capped confidence bar and its escalation pill. Grounding a safety verdict to
`model_prior` must visibly flip it red + escalate; grounding it to `rct` must clear it.

---

## 7. Build phases (suggested milestones)

0. **Scaffold** mono-repo: `backend/`, `frontend/`, `data/`. Mock LLM provider so it runs keyless.
1. **Thesis core first (TDD):** `capping.py` + `escalation.py` + `tests/` enforcing §2 invariants.
2. **Evidence + retrieval:** seed ~30 synthetic sources across all tiers; keyword retrieval.
3. **Grader + /api/judge:** wire model → retrieval → tier → capping → persist. Mock provider path green.
4. **Scorecard UI** reading the real API; dual confidence bars + capped readout.
5. **Human-in-the-loop:** `/api/queue`, `ReviewQueue`, `EvidenceDrawer` (inspect + verify).
6. **Explore mode:** `TierSelector` live re-grounding (the demo's "aha").
7. **Profile + complexity:** `ProfileRadar`, complexity tags, suppressed-average callout.
8. **Polish + seed cases** (3–4 cases: medication safety, dosing, triage, chronic care).

---

## 8. Tech stack

- Backend: Python 3.11+, FastAPI, SQLModel + SQLite, pydantic, pytest.
- Frontend: Vite, React, TypeScript, Tailwind, recharts.
- LLM access via a thin provider abstraction; `.env` for keys; a deterministic MockProvider for
  offline/dev so the whole demo runs without any API key.

---

## 9. Anti-patterns — do NOT do these (they break the thesis)

- ❌ Return or display a single aggregate/averaged score as the headline.
- ❌ Display a confidence above the grounded tier's ceiling.
- ❌ Let a safety-critical verdict grounded only to `model_prior` pass without escalation.
- ❌ Show a verdict's grounding without the inspectable source snippet.
- ❌ Use the same model family as judge and as the system under evaluation (blind-spot overlap).

---

## 10. Safety & framing

- All cases, answers, and evidence sources are synthetic or from public references. No PHI.
- Persistent UI banner: "Demo — not for clinical use."
- The system's stated goal is to **allocate human attention** to the verdicts that most need
  it (ungrounded safety claims, low confidence), not to replace clinicians.

---

## 11. Stretch goals (after v1)

- Embedding retrieval over the evidence library.
- Acuity-indexed compute: spend more grounding effort on high-acuity cases.
- Judge ensemble (jury of different model families) + "same verdict, different reasons"
  divergence as an extra escalation trigger.
- Auto stress-tests (shuffle options / paraphrase) producing a robustness-discounted view.
- Calibration panel: judge confidence vs human agreement over time (reliability diagram).

---

## 12. Kickoff prompt for Claude Code

> Read `medical-judge-demo-spec.md`. Scaffold the mono-repo in §5/§6 with a deterministic
> MockProvider so it runs without API keys. Then implement Phase 1 first: `capping.py`,
> `escalation.py`, and a pytest suite that enforces every invariant in §2. Show me the passing
> tests before moving on. Do not introduce any single aggregate score anywhere.
