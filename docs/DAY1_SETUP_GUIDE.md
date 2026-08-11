# Day 1 Setup Guide

Goal for today: everyone has a working local environment, the repo exists and everyone can push
to it, and every person has picked one task from Phase 0 below. Nobody needs to touch hardware today.

## 1. Tools to set up (30–45 min, do this together on a call)

| Purpose | Tool | Why |
|---|---|---|
| Code hosting + shared repo | **GitHub** (create an Org or one repo, add all members) | Single source of truth, free private repos for students |
| Live pair/group coding | **VS Code Live Share** or **GitHub Codespaces** | Lets multiple people edit/run code in the same session — useful for day 1 when you're setting things up together |
| Team chat (always-on) | **Discord** (or WhatsApp/Telegram group if you already have one) | Quick questions, async updates |
| Video calls | **Google Meet / Zoom / Discord voice** | Daily/weekly standups |
| Task tracking | **GitHub Projects** (built into the repo, free) or **Trello** | Turns the roadmap phases into a visible board |
| Docs | **This repo's `docs/` folder** (Markdown, versioned with code) | Keeps the SRS and setup guide next to the code instead of scattered across Docs/Drive |

You don't need all of these on day one — GitHub + Discord + one video call is enough to get moving.

## 2. Set up the repo (one person does this, ~10 min)

1. Create a new **private** GitHub repo, e.g. `smart-edusync`.
2. Add every team member as a collaborator (Settings → Collaborators).
3. Push this starter structure as the first commit.
4. Turn on branch protection on `main` if you want (optional for a student project — a simple
   rule of "don't push straight to main, open a PR" works fine even without enforcing it).
5. Create a GitHub Project board with three columns: **Backlog / In Progress / Done**, and add
   the Phase 0 tasks below as cards.

## 3. Everyone sets up locally (parallel, ~15–20 min)

Each person, on their own laptop:

```bash
git clone <repo-url>
cd smart-edusync
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_test.py
```

If `smoke_test.py` prints `✅ environment OK`, you're ready to write code.

Common blockers on day 1:
- **Python version** — use 3.10 or 3.11. Check with `python3 --version`.
- **Ollama not installed** (needed for Team 2 later, not required today) — install from
  ollama.com when you get to Phase 0's LLM task, skip it for now if you're on Perception/BKT.
- **Windows users** — use WSL2 if anything camera/audio-related misbehaves; pure logic/LLM work
  is fine on native Windows.

## 4. Split into Phase 0 tasks (today's actual work)

Everyone builds as one group now, but you still need to divide work so people aren't blocked on
each other. Suggested split for a ~4–6 person team (adjust to your actual headcount):

| Task | Folder | Suggested owner(s) | Definition of done for today |
|---|---|---|---|
| Freeze the event schema | `integration/schemas.py` | 1 person from each original team, together | Both teams have read and agreed on the event field names |
| Camera + MediaPipe hello-world | `part1_companion/perception/` | 1–2 people | Webcam opens, face landmarks print to console |
| BKT skeleton + SQLite schema | `part1_companion/mastery/` | 1 person | `bkt.py` runs, creates `mastery.db`, updates one fake topic's probability |
| Local LLM hello-world (Ollama) | `part2_knowledge/llm/` | 1–2 people | `dialogue.py` sends a prompt to a local model and prints a response |
| RAG skeleton | `part2_knowledge/rag/` | 1 person | Can embed and store one sample PDF/text file, retrieve it back by query |
| Repo/board/docs housekeeping | — | 1 person | Board created, README read by everyone, this guide followed by everyone |

If your team is smaller, merge rows; if larger, pair people up rather than leaving anyone idle.

## 5. End-of-day sync (15 min call)

Before logging off: everyone demos whatever ran today (even just "camera opened" or "LLM replied
to a prompt" counts), and you agree on Phase 0 targets for tomorrow. Use `docs/SRS_reference.md`
Section 9 for the full multi-week roadmap so today's work maps to the bigger plan.
