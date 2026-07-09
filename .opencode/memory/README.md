# 🧠 Agent Memory System

This directory implements a **six-type cognitive memory architecture** for the Android
OpenCode Agent. It gives the agent persistent knowledge, learning from past sessions,
and forward-looking goal tracking — far beyond the default stateless LLM behavior.

## Memory Types

| Type | File(s) | Purpose |
|---|---|---|
| **Semantic** | `semantic/knowledge_graph.md` | Structured facts, relationships, domain knowledge |
| **Episodic** | `episodic/sessions.md` | What happened in past sessions — decisions, outcomes, mistakes |
| **Procedural** | `procedural/learned_patterns.md` | How-to recipes learned from experience — reusable solutions |
| **External/Retrieval** | `retrieval/codebase_index.md` | Navigational index of the codebase — what's where |
| **Parametric** | `parametric/calibration.md` | Corrections to model defaults — project-specific overrides |
| **Prospective** | `prospective/goals.md` | Active goals, scheduled tasks, multi-session continuity |

## Protocol (Lean)

Memory is read **on demand**, not all at once — this keeps token cost low. The canonical
rules live in AGENTS.md ("Memory Protocol"). Summary:

| When | Read |
|---|---|
| Always (every agent) | `parametric/calibration.md` — avoid known model mistakes |
| Multi-session features | `prospective/goals.md` — check active goals |
| Problem feels familiar | `procedural/learned_patterns.md` — check known solutions |
| Need to locate files | `retrieval/codebase_index.md` — navigate the codebase |
| Need domain facts | `semantic/knowledge_graph.md` — relationships/facts |

Only `parametric/calibration.md` is **always** read. Everything else is pulled in only
when the task calls for it.

At **session end**, `@memory-manager` writes:
- An episode to `episodic/sessions.md` (≤ 10 lines)
- Goal progress to `prospective/goals.md`
- A new pattern to `procedural/learned_patterns.md` if a problem took 3+ attempts
- A calibration entry to `parametric/calibration.md` if the model made a mistake
- Index/semantic updates if files or architecture changed

## Memory Lifecycle

```
Session Start ──→ Load prospective goals + recent episodes
       │
       ▼
  Working Memory (context window) ◄── retrieval index for navigation
       │                           ◄── semantic graph for facts
       │                           ◄── procedural patterns for solutions
       ▼
  Task Execution ──→ parametric calibration overrides model defaults
       │
       ▼
Session End ──→ Write episodic log
           ──→ Update prospective goals (progress/new)
           ──→ Extract new procedural patterns (if learned)
           ──→ Update semantic graph (new facts discovered)
           ──→ Update retrieval index (new files/changes)
```
