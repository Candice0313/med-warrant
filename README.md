# Med-Warrant

**Evidence-Grounded LLM Confidence Evaluation System**

When AI judges medical AI, what does a verdict actually mean? Med-Warrant is a system that evaluates and controls LLM confidence in medical contexts by grounding it in evidence.

## Core Thesis

**Evidence sets confidence ceilings, not inflates it.**

The model's displayed confidence = `min(model_confidence, evidence_ceiling)`. Evidence can only lower confidence, never raise it.

## Live Demo

- **🎬 Frontend Demo:** https://med-warrant.vercel.app
- **📄 Landing Page:** https://candice0313.github.io/med-warrant
- **🔧 Backend API:** https://med-warrant-production.up.railway.app

## Key Features

### 1. Confidence Capping
Six evidence tiers with specific confidence ceilings:
- **Systematic Review:** 95%
- **RCT:** 90%
- **Guideline:** 80%
- **Cohort:** 75%
- **Expert Opinion:** 60%
- **Model Prior (no evidence):** 40%

### 2. Individual Scope Limit
Any claim about a specific patient's applicability is capped at 60%, regardless of evidence strength. Group-level evidence doesn't guarantee individual safety.

### 3. Escalation Logic
Two conditions force human review:
- **DANGER:** Safety-critical claim + no evidence (Model Prior)
- **WARNING:** Displayed confidence < 50%

### 4. Human Review Queue
All escalated verdicts enter a review queue where clinicians can:
- **Approve** the AI verdict
- **Override** with corrected reasoning

### 5. Evidence Profile (Radar Chart)
Visual comparison of:
- Outer dashed ring: Model's original confidence
- Inner solid ring: Evidence-capped confidence
- Colored dots: Trust band status (green/amber/red)

### 6. Explore Mode
Interactive hypothesis testing—change evidence tiers in real-time and see how confidence and escalation status recalculate. No API calls, instant feedback.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + TypeScript, Vite, Tailwind CSS v3, recharts |
| **Backend** | FastAPI + Python 3.11+, Pydantic v2 |
| **Storage** | SQLite (JSON file-based in Phase 1) |
| **Testing** | pytest (90+ tests covering all core invariants) |
| **Deployment** | Vercel (frontend), Railway (backend), GitHub Pages (landing) |

## Local Development

### Backend

```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

API will be available at http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be available at http://localhost:5173

## Architecture

```
┌─────────────────────────────────────┐
│  Frontend (React)                   │
│  ├─ Scorecard (dimension results)   │
│  ├─ Explore Mode (hypothesis test)  │
│  ├─ Profile Radar (evidence chart)  │
│  └─ Review Queue (human review)     │
└─────────────────────────────────────┘
              ↓ HTTP API ↓
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│  ├─ LLM Judge (model evaluation)    │
│  ├─ Evidence Store (retrieval)      │
│  ├─ Tier Classifier (evidence tier) │
│  ├─ Capping (confidence ceiling)    │
│  └─ Escalation (safety logic)       │
└─────────────────────────────────────┘
         ↓ JSON Files ↓
┌─────────────────────────────────────┐
│  Data Layer                         │
│  ├─ Case definitions                │
│  ├─ Evidence sources                │
│  └─ Verdict store                   │
└─────────────────────────────────────┘
```

## System Invariants (enforced by tests)

1. Displayed confidence ≤ evidence ceiling
2. Displayed confidence ≤ model confidence
3. Safety-critical + model_prior → DANGER escalation
4. Individual scope → 60% ceiling
5. Evidence strength ∝ escalation severity

## Demo Cases

The system includes 4 synthetic medical scenarios:

1. **Warfarin + Ibuprofen** — Drug interaction safety failure
2. **Chest Pain** — Triage urgency and red-flag recognition failure
3. **Pediatric Acetaminophen** — Individual scope ceiling demonstration
4. **Metformin** — Contraindication check failure

All cases are synthetic for demonstration purposes only and do not constitute medical advice.

## Design Principles

### What the system DOES
- ✅ Grounds confidence in evidence strength
- ✅ Prevents unverified safety claims from passing
- ✅ Surfaces evidence to human reviewers
- ✅ Enables interactive hypothesis exploration
- ✅ Tracks and escalates failures

### What the system DOES NOT do
- ❌ Generate medical answers
- ❌ Replace human judgment
- ❌ Average multi-dimensional verdicts into a single score
- ❌ Let evidence inflate confidence

## Deployment

All three components are already deployed and production-ready:

**Frontend (Vercel):**
```bash
npm run build
vercel --prod
```

**Backend (Railway):**
- Automatic deployment from GitHub
- Uses `railway.json` and `Procfile` configuration
- Environment variables: `PORT` (auto-assigned)

**Landing Page (GitHub Pages):**
- Deployed from `/docs` directory
- Automatically published to GitHub Pages

See `DEPLOYMENT.md` for detailed setup instructions.

## Testing

```bash
cd backend
pytest tests/ -v
```

Run with 90+ test cases covering:
- Confidence capping logic
- Escalation rules
- Evidence retrieval
- Tier classification
- API endpoints

## Future Work (Phase 8+)

- Embedding-based evidence retrieval
- Real medical evidence database
- Multi-LLM comparison
- Persistent audit logs
- FHIR integration
- Clinical trial validation

## License

This system is a demonstration project created for educational and research purposes.

---

**Built in Phases 1–7 (June 2026)**  
**Evidence-grounded confidence evaluation for medical AI safety**
