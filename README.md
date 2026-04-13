# Music Recommender — RAG + Agentic AI

A music recommendation system that started as a scoring-based engine and was extended with a conversational AI interface powered by Claude.

---

## Original Project

**Music Recommender Simulation** was the foundation of this project. Its original goals were to represent songs and user taste profiles as structured data, design a scoring formula that turns that data into ranked recommendations, and evaluate what such a system gets right and wrong. The original system matched users to songs by computing a weighted score across genre, mood, and energy attributes — no AI, no natural language.

---

## What This Project Does

The system recommends songs from a catalog based on user preferences. It has two modes:

- **Classic mode** — three hardcoded user profiles run through the scoring engine and print ranked results to the terminal.
- **AI mode** — a conversational interface where you describe what you want to listen to in plain English. Claude interprets the request, calls the scoring engine as a retrieval tool, and responds with grounded, natural language recommendations.

The AI mode is a genuine **RAG + Agentic Workflow** implementation: Claude retrieves real songs before generating any response, and uses tool-calling to plan and execute that retrieval autonomously.

---

## Architecture Overview

```
User (natural language)
        │
        ▼
   Claude Agent (claude-haiku-4-5-20251001)
        │  tool call: get_song_recommendations(genre, mood, energy)
        ▼
   execute_tool()  ──►  recommend_songs()  ──►  score_song()
                              │
                         songs.csv (10 songs)
                              │
                        ranked results (JSON)
        │
        ▼
   Claude generates grounded response
        │
        ▼
   Terminal output
```

**Key components:**

| File | Role |
|------|------|
| `src/recommender.py` | Core scoring engine — `score_song()`, `recommend_songs()`, `load_songs()` |
| `src/ai_recommender.py` | AI layer — tool schemas, tool handlers, agentic loop, logging, guardrails |
| `src/main.py` | Entry point — classic mode or `--ai` mode via argparse |
| `data/songs.csv` | 10-song catalog with genre, mood, energy, tempo, valence, danceability, acousticness |
| `tests/` | 13 unit tests — 7 cover AI tool handlers (no API key needed), 6 cover the scoring engine |

**Scoring formula (classic and retrieval):**

```
score = 1 × genre_match + 1 × mood_match + 4 × energy_similarity
```

Where `energy_similarity = 1 − |song_energy − user_energy|`, scaled 0–1. Maximum score is 6.0.

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com) (required for AI mode only)

### Steps

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd applied-ai-system-project
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS / Linux
   .venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run classic mode** (no API key needed)

   ```bash
   python src/main.py
   ```

5. **Run AI mode** (requires API key)

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...   # macOS / Linux
   set ANTHROPIC_API_KEY=sk-ant-...      # Windows
   python src/main.py --ai
   ```

6. **Run tests**

   ```bash
   pytest tests/ -v
   ```

---

## Sample Interactions

All examples are from running `python src/main.py --ai`.

### Example 1 — High-energy workout

**Input:** `I want something high energy for a workout`

The agent calls `get_song_recommendations(mood="intense", energy=0.9, k=5)` and retrieves Storm Runner, Gym Hero, and Sunrise City as the top results.

**Output:**
> For a high-energy workout, here are your top picks:
> 1. **Storm Runner** by Voltline (rock / intense, energy 0.93) — score 5.76/6. Hard-hitting rock with a near-perfect energy match.
> 2. **Gym Hero** by BeatForge (pop / intense, energy 0.88) — score 4.76/6. High-energy pop built for training.
> 3. **Sunrise City** by Neon Pulse (pop / happy, energy 0.90) — score 4.68/6. Upbeat and bright — great momentum for a run.

---

### Example 2 — Late-night study session

**Input:** `I need something calm and focused for studying late at night`

The agent calls `get_song_recommendations(genre="lofi", mood="chill", energy=0.3, k=5)` and retrieves Library Rain, Midnight Coding, and Focus Flow.

**Output:**
> Here are some calm, focused tracks for a late-night study session:
> 1. **Library Rain** by ChillWave Co (lofi / chill, energy 0.28) — score 5.80/6. Almost perfectly matches your low-energy, chill profile.
> 2. **Midnight Coding** by LoopDreamer (lofi / chill, energy 0.37) — score 5.52/6. Slow-tempo lofi ideal for staying in a flow state.
> 3. **Focus Flow** by ZenBeats (lofi / focused, energy 0.40) — score 4.60/6. Slightly more energized but still quiet enough to concentrate.

---

### Example 3 — Guardrail: genre not in catalog

**Input:** `I want some drum and bass`

The agent calls `get_song_recommendations(genre="drum and bass", energy=0.9)`. The tool detects an unknown genre, logs a warning, and returns the available options instead of crashing.

**Output:**
> Drum and bass isn't in my current catalog. Available genres are: pop, lofi, rock, ambient, jazz, synthwave, indie pop. If you want something high-energy and driving, **Storm Runner** (rock / intense) or **Night Drive Loop** (synthwave / moody) are the closest matches. Want me to pull recommendations for one of those?

---

## Design Decisions

**Why RAG + Agentic Workflow?**
The scoring engine was already doing the retrieval work — scoring every song against user preferences and returning ranked results. Wrapping it as a callable tool makes it a natural RAG system. The agent layer means Claude decides what parameters to query with, rather than the user having to spell out genre/mood/energy manually.

**Why keep the scoring engine unchanged?**
The original `score_song()` logic is well-tested and produces explainable results. Rather than replacing it, the AI layer sits on top of it. This keeps the two concerns cleanly separated: scoring logic can be updated without touching the AI layer, and the scoring logic can be tested without an API key.

**Trade-offs:**
- The 10-song catalog limits recommendation diversity. Several different queries surface the same top results.
- Exact string matching for genre and mood means "chill" and "calm" are treated as completely different.

---

## Reliability

**Automated tests:** 16 tests, 0 failures — run with `pytest tests/ -v`. The AI tool layer is fully testable without an API key. Key checks include: results are always sorted descending by score, unknown genres/moods return a structured warning instead of crashing, and out-of-range energy values are clamped silently.

**Confidence scoring:** Every song result includes a `confidence_pct` field — the raw score as a percentage of the maximum possible (6.0). A perfect genre + mood + energy match scores 100%; a genre/mood mismatch with close energy scores around 65%. This gives a consistent, human-readable signal of how well each song fits the request.

**Logging:** Every session writes to `ai_recommender.log`, recording each user query, every tool call and its parameters, the number of results returned, and any guardrail warnings. Errors from the API are caught and logged at `ERROR` level rather than surfaced as tracebacks.

---

## Testing Summary

16 tests pass with no API key needed. The suite verifies correct ranking order, confidence scores in range, guardrails for unknown genres/moods and out-of-range energy, and unknown tool names. Claude's natural language interpretation is validated manually through the sample interactions above.

---

## Model Card

See [model_card.md](model_card.md) for a detailed breakdown of the scoring model's intended use, limitations, bias analysis, and evaluation results.