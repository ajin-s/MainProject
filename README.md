# SmartEduSync

Privacy-first, emotion-aware AI tutoring robot. Two engines, one robot:

- `part1_companion/` — emotion sensing, proactive intervention, exam-risk tracking, voice (Team 1)
- `part2_knowledge/` — local LLM, RAG/GraphRAG, Socratic tutor, verification (Team 2)
- `integration/` — the event schema and shared state store that connect the two engines

See `docs/DAY1_SETUP_GUIDE.md` to get your environment running today, and `docs/SRS_reference.md`
for the full design doc this repo implements.

## Quick start (any team member, any OS)

```bash
git clone <your-repo-url>
cd smart-edusync
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/smoke_test.py     # confirms your environment can import both engines
```

You do **not** need a Raspberry Pi or robot hardware to start writing and testing software.
Everything in `part1_companion` and `part2_knowledge` runs on a laptop first; hardware
(camera/servos/screen) gets swapped in during Phase 3 (see roadmap in the SRS).

## Repo layout

```
smart-edusync/
├── part1_companion/     # Team 1: perception, intervention, mastery (BKT), voice
├── part2_knowledge/     # Team 2: LLM dialogue, RAG, GraphRAG, Socratic tutor, verification
├── integration/         # shared event schemas + event bus + state store (BOTH teams touch this)
├── docs/                # SRS reference + setup guide
├── scripts/             # setup/smoke-test helper scripts
└── requirements.txt
```

## The one rule that keeps two teams in sync

Nobody changes `integration/schemas.py` without posting in the team channel first — it's the
contract between Part 1 and Part 2. Everything else, each team owns independently.
