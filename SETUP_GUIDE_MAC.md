# Setup Guide — macOS

Complete setup for the Android OpenCode Agent system on macOS.
Time required: ~15 minutes.

---

## Prerequisites (Steps 1-4)

### Step 1 — Install Homebrew (Package Manager)

Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon (M1/M2/M3/M4), add to PATH:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify:
```bash
brew --version
```

---

### Step 2 — Install Python 3.12

```bash
brew install python@3.12
```

Verify:
```bash
python3 --version
pip3 --version
```

---

### Step 3 — Install Node.js

```bash
brew install node
```

Verify:
```bash
node --version
npm --version
```

---

### Step 4 — Install Docker Desktop

```bash
brew install --cask docker
```

Open Docker Desktop from Applications. Wait for the whale icon in the menu bar.

Verify:
```bash
docker info
```

---

## API Keys (Steps 5-6)

### Step 5 — Get Free API Keys

Sign up for each provider. No credit card required.

| Provider | Sign Up URL | Key Name |
|---|---|---|
| Google AI Studio | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |
| OpenRouter | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |
| Groq | https://console.groq.com/keys | `GROQ_API_KEY` |
| Cerebras | https://cloud.cerebras.ai/ | `CEREBRAS_API_KEY` |
| NaraRouter | https://bynara.id | `NARA_API_KEY` |
| NVIDIA NIM | https://build.nvidia.com | `NVIDIA_NIM_API_KEY` |

---

### Step 6 — Configure API Keys

Create `.env` from template (run from this repo's root):

```bash
cp .env.example .env
```

Set each key (replace with YOUR actual keys):

```bash
sed -i '' 's|^GEMINI_API_KEY=.*|GEMINI_API_KEY=YOUR_KEY_HERE|' .env
sed -i '' 's|^OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=YOUR_KEY_HERE|' .env
sed -i '' 's|^GROQ_API_KEY=.*|GROQ_API_KEY=YOUR_KEY_HERE|' .env
sed -i '' 's|^CEREBRAS_API_KEY=.*|CEREBRAS_API_KEY=YOUR_KEY_HERE|' .env
sed -i '' 's|^NARA_API_KEY=.*|NARA_API_KEY=YOUR_KEY_HERE|' .env
sed -i '' 's|^NVIDIA_NIM_API_KEY=.*|NVIDIA_NIM_API_KEY=YOUR_KEY_HERE|' .env
```

Verify all 6 keys are set:
```bash
grep "API_KEY=" .env | grep -v "^#"
```

**Also set in `~/.zshrc`** (Docker uses shell env over `.env`):

```bash
echo 'export GEMINI_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
echo 'export OPENROUTER_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
echo 'export GROQ_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
echo 'export CEREBRAS_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
echo 'export NARA_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
echo 'export NVIDIA_NIM_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc
```

**Set `OPENAI_API_KEY` for OpenCode authentication:**

OpenCode uses the `OPENAI_API_KEY` env var to authenticate with the LiteLLM proxy. Set it
to the master key:

```bash
echo 'export OPENAI_API_KEY="sk-litellm-master-key"' >> ~/.zshrc
source ~/.zshrc
```

> **Key format reference:**
> - `GEMINI_API_KEY` — starts with `AQ.` or `AI`, ~39-53 chars
> - `OPENROUTER_API_KEY` — starts with `sk-or-v1-`, ~71-73 chars
> - `GROQ_API_KEY` — starts with `gsk_`, ~56 chars
> - `CEREBRAS_API_KEY` — starts with `csk-`, ~50 chars
> - `NARA_API_KEY` — starts with `sk-nry-` or `sk_nry_`, ~50 chars
> - `NVIDIA_NIM_API_KEY` — starts with `nvapi-`, ~70 chars

> **If you change a key later:** update in both `.env` AND `~/.zshrc`, then:
> `source ~/.zshrc && docker compose down && docker compose up -d --force-recreate`

---

## Proxy & Tools (Steps 7-8)

### Step 7 — Start the LiteLLM Proxy

From this repo's root:

```bash
docker compose up -d
```

Wait ~30 seconds, then verify:
```bash
docker compose logs litellm --tail 5
```

You should see `Uvicorn running on http://0.0.0.0:4000`.

**Services started (3 containers):**
- `db` — Postgres 16 (spend logs + tool call storage)
- `litellm` — LiteLLM proxy at **localhost:4000**
- `tool-viewer` — Tool Call Viewer at **localhost:5001** (shows all tool calls with no 50-item limit, auto-refreshes every 5s)

To stop: `docker compose down`
To restart: `docker compose up -d`

---

### Step 8 — Install OpenCode

```bash
npm install -g opencode-ai
```

If permission error:
```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH="$PATH:$HOME/.npm-global/bin"' >> ~/.zshrc
source ~/.zshrc
npm install -g opencode-ai
```

Verify:
```bash
opencode --version
```

---

## Project Setup (Steps 9-10)

### Step 9 — Deploy Agent to Your Project

Run the setup script from this repo's root, passing your Android project path:

```bash
chmod +x scripts/setup_project.sh
./scripts/setup_project.sh /path/to/YourAndroidProject
```

Then add the gitignore entries:
```bash
cat /path/to/YourAndroidProject/agent.gitignore >> /path/to/YourAndroidProject/.gitignore
rm /path/to/YourAndroidProject/agent.gitignore
```

**What gets deployed:**

| Item | Purpose |
|---|---|
| `opencode.json` | Agent definitions, model routing, tool permissions |
| `AGENTS.md` | Core rules (slim ~100 lines) all agents read |
| `.opencode/agents/` | 11 agent prompt files |
| `.opencode/rules/` | TESTING.md, ARCHITECTURE.md (read on demand) |
| `.opencode/skills/` | 16 reusable skill files (templates, patterns — loaded on demand to save tokens) |
| `.opencode/memory/` | 6-type persistent memory system |
| `.opencode/plans/` | Persistent plan files (auto-created by @planner, read by @coder) |
| `scripts/doc_watcher.py` | Document converter for `@doc-reader` |
| `scripts/screenshot_to_ui.py` | Optional: standalone vision-based UI spec tool |
| `docs/input/` + `docs/parsed/` | Document ingestion folders |

**After initial setup — syncing config changes:**

If you edit agent prompts, rules, skills, or calibration in this repo:
```bash
./scripts/sync_to_project.sh /path/to/YourAndroidProject
```
This copies only the config/memory files (not plans or project-specific goals). Then restart OpenCode.

---

### Step 10 — Install Document Watcher Dependencies

One-time install (machine-wide, not per-project):

```bash
pip3 install pymupdf4llm python-docx watchdog requests Pillow
```

---

### Step 10b — Install LSP Servers (Optional but Recommended)

LSP servers give agents real-time diagnostics (compile errors, type mismatches) without
running a full Gradle build. Configured in `opencode.json` under the `"lsp"` key.

**Python LSP** (for scripts in this repo):
```bash
pip3 install python-lsp-server
```

**Kotlin LSP** (for Android projects):
```bash
brew install fwcd/tap/kotlin-language-server
```

Or download from https://github.com/fwcd/kotlin-language-server/releases and add `bin/` to
PATH. Verify:
```bash
kotlin-language-server --version
```

> Both servers are pre-configured in `opencode.json`. If you skip this step, OpenCode
> still works — it just won't have inline diagnostics from LSP.

---

## Start Working (Steps 11-12)

### Step 11 — Launch OpenCode

Navigate to your Android project and launch:

```bash
opencode
```

Inside OpenCode, type `/models` and select:
- **Coder (NIM GLM-5.2)** — for coding tasks (fallback: NIM DeepSeek V4 Pro → Claude Sonnet 4.5 → Owl Alpha → Mistral Large → Laguna M.1 → Groq → Nex-N2 → Cerebras → Gemini Flash)
- **Planner (NIM Nemotron 3 Super)** — for feature planning (fallback: NIM GLM-5.2 → Claude Sonnet 4.5, 262K context)
- **Reasoner (NIM Nemotron 3 Super)** — for debugging/test logic (fallback: NIM DeepSeek V4 Pro → Claude Sonnet 4.5)
- **Reviewer (NIM Mistral Medium 3.5)** — for code reviews (fallback: NIM Llama-Nemotron-Super-49B → Claude Haiku 4.5 → Owl Alpha → Mistral Medium → Qwen3 → Groq → Cerebras → Gemini Flash)

---

### Step 12 — Initialize Project Memory

On first use, ask the agent to index your project:

```
@memory-manager update-index
```

This builds the codebase navigation index. Other memory files accumulate automatically.

---

## Using the Agents

### Agent Reference

| Agent | What It Does | Example |
|---|---|---|
| `@orchestrator` | Recommends which specialist(s) to run and in what order (+ the exact next command) | `@orchestrator add a login screen with social auth` |
| `@planner` | Plans features (writes plan files ONLY; cannot edit project code/gradle); fully autonomous | `@planner add a login screen ref: docs/parsed/spec.md` |
| `@coder` | Generates code, compiles, self-corrects; auto-reverts broken changes | `@coder implement LoginViewModel from the plan` |
| `@tester` | Writes unit tests (MockK/Mockito) | `@tester generate tests for LoginViewModel` |
| `@ui-tester` | Writes instrumented/UI tests (Espresso/Hilt) | `@ui-tester test the login screen flow` |
| `@reviewer` | Code review with severity ratings | `@reviewer review LoginFragment for memory leaks` |
| `@debugger` | Root-cause analysis from stack traces | `@debugger NPE in ProfileFragment line 87 after rotation` |
| `@refactorer` | Safe legacy-to-modern migration | `@refactorer convert this Activity from Java to Kotlin` |
| `@doc-reader` | Converts PDF/DOCX/images to Markdown | `@doc-reader parse the docs` |
| `@ui-builder` | Builds UI from text description | `@ui-builder build a profile screen with avatar, name, email, edit button` |
| `@memory-manager` | Memory system maintenance | `@memory-manager update-index` |

### Routing Advisor (Orchestrator)

Not sure which agent to use? Ask `@orchestrator` — it classifies your request and recommends
the chain (plan → code → test → review) plus the **exact next `@mention` to run**, flagging
any blocking questions you'll need to answer first:

```
@orchestrator add a login screen with social auth
```

It's advisory (no write access, doesn't run other agents) — you then run the recommended
commands yourself. It right-sizes the route: trivial fixes just point you at `@coder`.

### Planning (Direct & Autonomous)

Call `@planner` directly — it's fast, no routing delay, fully autonomous.

Plans are saved to `.opencode/plans/` as persistent files. The planner writes in chunks
(create + append) and never asks you to "continue" — even for large multi-feature plans.

**Simple workflow:**
```
@planner add a login feature with social login     ← plan it (autonomous, one turn)
@coder implement step 1                            ← build it
@reviewer review                                   ← verify it
```

**Migration workflow:**
```
@planner migrate this project to MVVM + Clean Architecture (skip unit tests)
@refactorer execute the migration plan             ← phased execution with auto-revert
```

**Document-aware planning:**
1. Drop a PDF/DOCX into `docs/input/`
2. `@doc-reader parse the docs`
3. `@planner add login ref: docs/parsed/requirements.md`

### Text-Guided UI Building

The `@ui-builder` generates native Android screens from your text description:

```
@ui-builder build a login screen with email field, password field, forgot password link, and submit button
```

It generates the full implementation: XML layout (Material 3), Fragment with ViewBinding,
ViewModel, strings/colors/dimens resources. You can then iterate:
```
@ui-builder add a "Sign up" text link below the submit button
@ui-builder make the email field show an error when invalid
```

### Verification Loop

`@coder` compiles and tests its own output automatically:
- Compile → test → read errors → fix → re-run (up to 5 attempts)
- If budget exhausted → hands off to `@debugger`
- Only runs safe Gradle tasks (compile, unit test, lint)

### Memory System

6-type persistent memory in `.opencode/memory/`:

| Type | Purpose |
|---|---|
| Semantic | Facts, domain knowledge about your project |
| Episodic | Session history — decisions, outcomes, lessons |
| Procedural | Reusable solution recipes from past fixes |
| Retrieval | Codebase navigation index |
| Parametric | Corrections to model mistakes |
| Prospective | Active goals, multi-session continuity |

The agent reads calibration entries always, other memory on-demand. Gets smarter over time.

**Observability & retention:** Workflow telemetry (which agents ran, verification attempts,
outcomes) is logged to `.opencode/memory/episodic/traces.md`. Memory doesn't grow unbounded —
`@memory-manager` keeps the hot session log at ≤15 tagged episodes and moves older ones to
`archive.md` (nothing is ever deleted).

**Live docs (MCP):** The `mcp.context7` server in `opencode.json` lets agents fetch
up-to-date library/API docs on demand (needs `npx`, installed with Node in Step 3). Set
`"enabled": false` in the `mcp` block to turn it off.

**Self-improvement (automatic):** The `@coder`, `@refactorer`, and `@ui-builder` agents
automatically write patterns to memory *during* tasks — not just at session end. If a fix
takes 2+ attempts, the error→fix pattern is saved immediately. If the session crashes
mid-task, learnings from earlier steps are already on disk. No manual `@memory-manager`
call needed for basic learning.

---

## Safety Guards (tool-level, not just prompt)

Destructive commands that could delete files or rewrite history are **blocked at the tool
level** by `permission.bash` in `opencode.json` — they cannot run regardless of what the model
decides. This is not a prompt suggestion; it's a hard deny enforced by OpenCode.

**Blocked (deny):** `git reset --hard`, `git clean*`, `git push*`, `git rebase*`,
`git commit --amend*`, `git checkout -f*`, `git branch -D*`, `rm -rf*`.

**Allowed (for workspace-integrity auto-revert):** `git restore`, `git stash`, `git commit`
(green-only checkpoints in migration mode), `git add`, `git status`.

The agents guarantee **workspace integrity**: they never end a turn with a broken build. If a
change-set can't be fixed within 5 attempts, it's auto-reverted to the last green state
(`git restore` / `git stash push -u`) — no user prompt required. Keep `.opencode/` committed
so no cleanup command can destroy it.

---

## Daily Startup

1. Start Docker Desktop (if not running)
2. Start the proxy (from this repo's root):
   ```bash
   docker compose up -d
   ```
3. Navigate to your Android project and start OpenCode:
   ```bash
   opencode
   ```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Docker not running | `open -a Docker` — wait 30s for startup |
| `docker compose up` fails | Docker isn't ready. Wait 30s after launching. |
| 429 / Invalid API Key errors | Check keys in both `.env` AND `~/.zshrc` match. Restart Docker after changes. |
| Slow responses | Provider rate-limited, fell back to next in chain. Normal — wait a few minutes or keep working. |
| OpenCode wrong model | Run `/models` in OpenCode and select a LiteLLM model. |
| Port 4000 in use | Stop the other process or change port in `docker-compose.yml`. |
| Tool calls not visible beyond 50 | LiteLLM dashboard caps at 50 tool calls. Use the **Tool Call Viewer** at `http://localhost:5001` — it shows all tool calls with no limit. |
| Performance degraded (DEBUG mode) | Ensure `LITELLM_LOG=INFO` in docker-compose.yml (not DEBUG). DEBUG mode significantly degrades proxy performance. |
| Dashboard empty | The LiteLLM dashboard requires a valid auth key matching `LITELLM_MASTER_KEY` (`sk-litellm-master-key`). Verify the key in docker-compose.yml environment section. |
| LSP not providing diagnostics | Verify the server is installed (`kotlin-language-server --version` / `pylsp --version`). Check `"disabled": false` in `opencode.json` `"lsp"` block. Run with `"debugLSP": true` for verbose logs. |
| `brew` not found | `eval "$(/opt/homebrew/bin/brew shellenv)"` |
| `opencode` not found | Add npm global bin to PATH (see Step 8). |

### Verify API Keys Are Correct

```bash
grep "API_KEY=" .env | grep -v "^#"
grep "API_KEY" ~/.zshrc
```

### Reset Docker After Key Changes

```bash
source ~/.zshrc
docker compose down && docker compose up -d --force-recreate
```
