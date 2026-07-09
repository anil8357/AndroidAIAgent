# Android OpenCode Agent

A drop-in configuration that turns [OpenCode](https://opencode.ai) into an **11-agent
Android development assistant** with a **persistent cognitive memory system** — entirely
free, no credit card required.

## What It Does

Routes every coding task to a specialist agent, each backed by the best available
free LLM for that role, with automatic fallback across 6 providers when any hits its rate limit.

```
You (OpenCode)
    │
    ├── @orchestrator ─► reasoner (NIM Nemotron 3 Super / Claude Sonnet 4.5) → recommends the route (which agents, what order)
    ├── @planner  ──► planner  (NIM Nemotron 3 Super / Claude Sonnet 4.5)  → plans features
    ├── @coder    ──► coder    (NIM GLM-5.2 / DeepSeek V4 Pro → Gemini)   → writes Kotlin/Java + XML
    ├── @tester   ──► reasoner (NIM Nemotron 3 Super / Claude Sonnet 4.5)  → generates MockK tests
    ├── @ui-tester──► reasoner (NIM Nemotron 3 Super / Claude Sonnet 4.5)  → Espresso/Hilt tests
    ├── @reviewer ──► reviewer (NIM Mistral Medium 3.5 / Claude Haiku 4.5) → severity-rated reviews
    ├── @debugger ──► reasoner (NIM Nemotron 3 Super / Claude Sonnet 4.5) → root-cause diagnosis
    ├── @refactorer─► coder    (NIM GLM-5.2 / DeepSeek V4 Pro → Gemini)  → safe legacy migration
    ├── @doc-reader─► coder    (NIM GLM-5.2 / DeepSeek V4 Pro → Gemini)  → PDF/DOCX → Markdown
    ├── @ui-builder─► coder    (NIM GLM-5.2 / DeepSeek V4 Pro → Gemini)  → text → native Android UI
    └── @memory-manager─► coder (NIM GLM-5.2 / DeepSeek V4 Pro → Gemini) → persistent memory
             │
             ▼
    LiteLLM Proxy (localhost:4000)
             │
             ├── NVIDIA NIM    (free first-party — GLM-5.2, DeepSeek V4 Pro, Nemotron 3 Super, Mistral Medium 3.5)
             ├── Gemini        (gemini-2.5-flash, fast, 20 RPD)
             ├── NaraRouter    (Claude Sonnet 4.5, Haiku 4.5, Mistral Large/Medium)
             ├── OpenRouter    (Nemotron Super/Ultra, Owl Alpha, Laguna, Qwen3)
             ├── Groq          (Llama 4, Qwen3, gpt-oss — ultra-fast LPU)
             └── Cerebras      (gpt-oss-120b — wafer-scale inference)

    Tool Call Viewer (localhost:5001)
             │
             └── Postgres      (all tool calls, no 50-item limit, auto-refresh)
```

## Target Stack

Native Android only — **Jetpack Compose is banned**.

- **Language**: Kotlin / Java
- **Layouts**: XML + ViewBinding
- **Architecture**: MVVM + Repository + Hilt (or MVI for state-heavy screens)
- **SDK**: matches the project (compileSdk 35+ / minSdk 24+)

## Safety

Destructive commands are **blocked at the tool level** (`permission.bash` in `opencode.json`):
`git reset --hard`, `git clean*`, `git push*`, `git rebase*`, `rm -rf*`. Models physically
cannot run them. Code-writers (`coder`, `ui-builder`, `refactorer`) guarantee workspace
integrity — auto-revert a broken change-set so the build is always green at end of turn.

## Quick Start

Platform-specific setup guides:
- **[Windows Setup](./SETUP_GUIDE_WINDOWS.md)** — CMD and PowerShell
- **[macOS Setup](./SETUP_GUIDE_MAC.md)** — Terminal and Homebrew

Short version:

```bash
# 1. Install dependencies
npm install -g opencode-ai

# 2. Set API keys in .env (all free, no card needed)
#    NVIDIA_NIM_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, CEREBRAS_API_KEY, NARA_API_KEY
cp .env.example .env
# Edit .env with your keys

# 3. Start proxy (Docker)
docker compose up -d

# 4. Run OpenCode from your Android project root
cd /path/to/your/android/project
opencode
```

## Agent Reference

| Agent | Invoke | Permissions | Best For |
|---|---|---|---|
| Orchestrator | `@orchestrator <any request>` | Read only (advises) | Recommending which specialist(s) to run and in what order (plan→code→test→review) + the exact next command |
| Planner | `@planner <feature> ref: <doc_path>` | Read + Write + Edit (plans only) | Feature scoping, task ordering (pass ref doc path explicitly). Fully autonomous — saves plan in chunks, no "continue" needed. CANNOT edit project files. |
| Coder | `@coder <implementation task>` | Read + Write + Bash | New files, feature implementation, build/test verification |
| Tester | `@tester <class to test>` | Read + Write | Unit test generation (`src/test/`) |
| UI Tester | `@ui-tester <screen/flow to test>` | Read + Write | Instrumented/UI tests — Espresso, Hilt, `androidTest/` |
| Reviewer | `@reviewer <files or PR description>` | Read only | Pre-commit/merge review |
| Debugger | `@debugger <bug + stack trace>` | Read + Bash | Crash diagnosis, bug fixing |
| Refactorer | `@refactorer <legacy code to modernize>` | Read + Write + Bash | Two modes: targeted (≤5 files, test before/after) and Large-Scale Migration (plan-driven, phased, auto-revert, checkpoint commits) |
| Doc Reader | `@doc-reader parse the docs` | Read + Bash | Convert PDF/DOCX/image in `docs/input/` → Markdown |
| UI Builder | `@ui-builder build a login screen with email, password, submit` | Read + Write + Bash | Text description → XML layout + ViewBinding + Fragment |
| Memory Manager | `@memory-manager update-index` | Read + Write | Persistent memory CRUD, codebase index |

## Verification Loop

The **`coder`** is the primary owner of build/test command execution. After it generates or
modifies code in an Android project, it compiles the code, runs the affected unit tests,
reads the build output, applies a fix, and re-runs — repeating until the build and tests
pass or the iteration budget is exhausted.

- **Owner**: the `coder` runs build/test commands for the feature code it generates and for
  `@debugger` hand-back fixes. Its `bash` permission is `true`, the same value declared for
  `coder` in `opencode.json`. The `@refactorer` and `@ui-builder` run the same Allowed-only
  commands to verify the code they change; all other non-`debugger` agents have `bash` off.
- **Iteration_Budget = 5** — at most five self-correction attempts per task. If the budget
  is exhausted (or two consecutive attempts produce identical output), the `coder` stops
  and hands the remaining failures off to the `@debugger`.
- The `coder` runs only safe Gradle compile, unit-test, and lint tasks plus read-only
  inspection commands and recoverable git (`restore`/`stash`/green-only `commit`).
  Destructive git (`reset --hard`, `clean -f`, `push`, `rebase`, `rm -rf`) is **blocked
  at the tool level** by `permission.bash` in `opencode.json` — no agent can run them.
- Code-writers (`coder`, `ui-builder`, `refactorer`) guarantee **workspace integrity**:
  they never leave a previously-working file broken. If a change-set can't be made green
  within 5 attempts, it's auto-reverted (`git restore` / `git stash`) without a prompt.

The `debugger` keeps `bash` (`true`) for read-only evidence gathering only and never
writes or edits files. `planner` (lists/reads only, write+edit restricted to `.opencode/plans/`)
and `doc-reader` (runs the conversion script) also hold limited permissions. The test-writing
and review agents — `tester`, `ui-tester`, `reviewer`, and `memory-manager` — have `bash`
disabled (`false`).

## Write-Ahead Reflection (Self-Improvement)

Agents automatically learn from their mistakes *during* tasks — no manual memory calls needed:

- **Fix took ≥2 attempts** → error→fix pattern written to `learned_patterns.md` immediately
- **Budget exhausted** → failure entry written to `calibration.md` immediately
- **Novel success on non-trivial task** → recipe saved to `learned_patterns.md`

This is **write-ahead** — memory is persisted at the moment of learning, not at session end.
If the session crashes mid-task, everything learned up to that point survives on disk.

Applies to: `@coder`, `@refactorer`, `@ui-builder`. The `@debugger` proposes memory entries
in its diagnostic reports for the coder to write.

## Orchestration (Routing Advisor)

Not sure which agent to use? Ask **`@orchestrator`** — it reads your request, classifies
intent, and recommends the specialist chain plus the exact next `@mention` to run:

```
@orchestrator add a login screen with social auth
    → Chain: @planner → (answer blocking questions) → @coder → @tester → @reviewer
    → Run this next: @planner add a login screen with social auth
```

It's read-only by design (no write/edit/bash) and **advises** rather than executes — it keeps
the existing model where you drive handoffs via `@mention` in one shared conversation (so
`@planner`'s blocking questions get answered inline before `@coder` starts). Right-sizes
automatically: for a one-line fix it just tells you to run `@coder`.

## Context Hygiene (Compaction & Tool-Result Clearing)

Writing agents (`@coder`, `@refactorer`, `@ui-builder`) actively keep the context window
lean during long verification loops instead of drowning in stale build logs:

- **Tool-result clearing** — after each build, only a ≤10-line `Failure_Digest` (failing
  tests + compiler errors + relevant stack frames) is kept; the raw Gradle log is dropped.
- **Attempt compaction** — prior verification attempts collapse to a one-line trail.
- **Completed-step compaction** — finished files collapse to their `Files Touched` entry.

This keeps reasoning sharp on long, multi-file tasks and deep tool-call sessions.

## Observability (Workflow Traces)

Beyond the LiteLLM token/cost logs, the system records **agent-level telemetry** in
`.opencode/memory/episodic/traces.md` — a structured, greppable log of each workflow: which
agents ran, hand-offs, verification attempt counts, build status, and outcome. Answers
questions the spend logs can't, like "how often does `@coder` exhaust its budget?"
`@memory-manager` writes a trace at session-end (and `@orchestrator` can recommend logging
one); older traces roll up into aggregate counts.

## MCP — Live Documentation

The `mcp.context7` server (configured in `opencode.json`) gives agents on-demand access to
**up-to-date library/API docs** (AndroidX, Hilt, Room, Retrofit, etc.). Agents prefer a live
doc lookup over stale training data when `calibration.md` flags a version-specific risk.
Requires `npx` (Node) on the host; set `"enabled": false` in the `mcp` block to turn it off.

## Model Assignments

Each role uses a dedicated model group optimized for its task, with Claude Sonnet 4.5
(via NaraRouter) as the high-quality 2nd fallback across all groups.

Primaries are now **NVIDIA NIM** (free first-party) with Gemini/Claude/Nemotron as fallbacks.

| Agent | Logical Model | Primary Model (NIM) | 2nd | Reliable fallback |
|---|---|---|---|---|
| Orchestrator | `litellm/reasoner` | Nemotron 3 Super (NIM) | DeepSeek V4 Pro (NIM) | Claude Sonnet 4.5 |
| Planner | `litellm/planner` | Nemotron 3 Super (NIM) | GLM-5.2 (NIM) | Claude Sonnet 4.5 |
| Coder | `litellm/coder` | GLM-5.2 (NIM) | DeepSeek V4 Pro (NIM) | Gemini 2.5 Flash / Claude Sonnet 4.5 |
| Tester | `litellm/reasoner` | Nemotron 3 Super (NIM) | DeepSeek V4 Pro (NIM) | Claude Sonnet 4.5 |
| UI Tester | `litellm/reasoner` | Nemotron 3 Super (NIM) | DeepSeek V4 Pro (NIM) | Claude Sonnet 4.5 |
| Reviewer | `litellm/reviewer` | Mistral Medium 3.5 (NIM) | Llama-3.3-Nemotron-Super-49B (NIM) | Claude Haiku 4.5 / Gemini |
| Debugger | `litellm/reasoner` | Nemotron 3 Super (NIM) | DeepSeek V4 Pro (NIM) | Claude Sonnet 4.5 |
| Refactorer | `litellm/coder` | GLM-5.2 (NIM) | DeepSeek V4 Pro (NIM) | Gemini 2.5 Flash / Claude Sonnet 4.5 |
| Doc Reader | `litellm/coder` | GLM-5.2 (NIM) | DeepSeek V4 Pro (NIM) | Gemini 2.5 Flash |
| UI Builder | `litellm/coder` | GLM-5.2 (NIM) | DeepSeek V4 Pro (NIM) | Gemini 2.5 Flash / Claude Sonnet 4.5 |
| Memory Manager | `litellm/coder` | GLM-5.2 (NIM) | DeepSeek V4 Pro (NIM) | Gemini 2.5 Flash |

## Fallback Chain

When the primary returns 429 or 5xx, LiteLLM automatically cascades through the chain
defined for each logical model in `litellm_config.yaml`:

```
coder:    NIM GLM-5.2 → NIM DeepSeek V4 Pro → Gemini Flash → Claude Sonnet 4.5
          → Owl Alpha → Mistral Large → Laguna M.1 → Groq → Nex-N2 → Cerebras
planner:  NIM Nemotron 3 Super → NIM GLM-5.2 → Claude Sonnet 4.5 → OR Nemotron Super/Ultra
          → Owl Alpha → Mistral Large
reasoner: NIM Nemotron 3 Super → NIM DeepSeek V4 Pro → OR Nemotron Super → Claude Sonnet 4.5
          → Owl Alpha → Mistral Large → Groq → Cerebras → Nemotron Ultra
reviewer: NIM Mistral Medium 3.5 → NIM Llama-3.3-Nemotron-Super-49B → Claude Haiku 4.5
          → Gemini Flash → Owl Alpha → Mistral Medium 3.5 → Qwen3-235B → Groq → Cerebras
```

After 1 failure, a deployment enters a 120-second cooldown. Cross-group fallbacks activate
when ALL deployments in a group are exhausted (e.g., coder → reasoner → reviewer).

Streaming is enabled on Gemini (`stream: true`) — this eliminates the perceived hang where
TTFT ≈ Duration. With streaming off, users saw no output until the full response was
complete; with it on, tokens flow immediately.

**NaraRouter free tier:** 7M tokens/day, 10 req/min, no expiry — provides Claude Sonnet 4.5,
Claude Haiku 4.5, Mistral Large (252K ctx), Mistral Medium 3.5 (256K ctx, vision).

## Switching Models

Edit `litellm_config.yaml` to swap any model. The OpenCode agents reference only the
logical names (`coder`, `reasoner`, `reviewer`) — model changes require no edits to
agent prompts or `opencode.json`.

## Project Structure

```
AiAgent/
├── opencode.json              # Agent definitions + LiteLLM proxy routing
├── AGENTS.md                  # Global rules (tech stack, Compose ban, standards)
├── litellm_config.yaml        # Provider fallback chains
├── docker-compose.yml         # Docker services (LiteLLM + Postgres + Tool Call Viewer)
├── .env.example               # Environment variable template (copy to .env)
├── .gitignore                 # Ignores .env, keeps .env.example
├── SETUP_GUIDE_WINDOWS.md     # Windows-specific setup (CMD / PowerShell)
├── SETUP_GUIDE_MAC.md         # macOS-specific setup (Terminal / Homebrew)
├── README.md                  # This file
├── tool_call_viewer/          # Custom Flask dashboard (all tool calls, no 50-item limit)
├── scripts/
│   ├── doc_watcher.py         # PDF/DOCX/image → Markdown (for @doc-reader)
│   ├── screenshot_to_ui.py    # Optional: standalone vision-based UI spec tool
│   ├── sync_to_project.ps1    # Sync agent config changes to target project
│   └── setup_project.sh/.ps1  # One-command project deployment
├── strip_reasoning.py         # Proxy hook: strips reasoning_content for Groq/Cerebras
└── .opencode/
    ├── rules/                 # ARCHITECTURE.md, TESTING.md (read on demand)
    ├── skills/                # Reusable pattern files (read on demand, saves tokens)
    ├── memory/                # 6-type persistent memory + workflow traces & archive
    └── agents/
        ├── orchestrator.md    # Advisory router — recommends the specialist chain + next command
        ├── planner.md         # Planning protocol + output format
        ├── coder.md           # Code generation rules + templates + context hygiene
        ├── tester.md          # Unit test rules + MockK/Turbine patterns
        ├── ui-tester.md       # Instrumented/UI test rules (Espresso/Hilt)
        ├── reviewer.md        # Review checklist + severity scale
        ├── debugger.md        # Diagnostic protocol + Android bug patterns
        ├── refactorer.md      # Safe legacy → modern refactoring
        ├── doc-reader.md      # Document → Markdown conversion
        ├── ui-builder.md      # Screenshot → XML + ViewBinding
        └── memory-manager.md  # Persistent memory CRUD
```
