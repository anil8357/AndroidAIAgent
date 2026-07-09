# 🎛️ Parametric Memory — Model Calibration

> **What it is**: Corrections and overrides to the LLM's trained defaults (parametric knowledge).
> The model "knows" things from pretraining that may be wrong, outdated, or inappropriate for
> this project. This file records those divergences so agents can self-correct.

---

## Protocol

### When to add a calibration entry
- When the model generates code using a pattern explicitly banned by this project
- When the model's default behavior contradicts project rules
- When a common model mistake is observed across multiple sessions
- When API documentation is outdated in the model's training data

### How agents use this file
- Read at session start alongside other memory files
- When generating code, check calibration entries for relevant corrections
- Treat entries here as **hard overrides** — they take precedence over what the model
  "thinks" is correct from pretraining

---

## Calibration Entries

### CE-001: Compose is the model's default — OVERRIDE
**Model default**: Generates Jetpack Compose for modern Android UI (post-2021 training)
**Project override**: XML + ViewBinding ONLY. Compose is absolutely banned.
**Correction**: When generating UI code, ALWAYS use XML layouts + ViewBinding. Never suggest
migration to Compose even if the user doesn't specify.
**Severity**: Critical — any Compose output is a complete failure

---

### CE-002: Model suggests LiveData for state — OVERRIDE
**Model default**: Uses `LiveData<T>` for observable state in ViewModel
**Project override**: `StateFlow<T>` / `SharedFlow<T>` for all new code
**Correction**: Replace any LiveData pattern with:
```kotlin
private val _uiState = MutableStateFlow<UiState>(UiState.Initial)
val uiState: StateFlow<UiState> = _uiState.asStateFlow()
```
**Severity**: Major — LiveData works but violates new-code standards

---

### CE-003: Model uses kapt for annotation processing — OVERRIDE
**Model default**: `kapt("com.google.dagger:hilt-compiler:...")`
**Project override**: `ksp(libs.hilt.compiler)` — always KSP, never kapt
**Correction**: Replace `kapt(...)` with `ksp(...)` for Hilt and Room
**Severity**: Major — kapt is deprecated and slower

---

### CE-004: Model uses raw dependency coordinates — OVERRIDE
**Model default**: `implementation("com.google.dagger:hilt-android:2.48")`
**Project override**: `implementation(libs.hilt.android)` — Version Catalog only
**Correction**: All dependencies must be declared in `gradle/libs.versions.toml` first,
then referenced as `libs.*` accessors. Never raw strings.
**Severity**: Major — breaks dependency management conventions

---

### CE-005: Model uses Moshi for JSON — OVERRIDE
**Model default**: Suggests Moshi with KSP code gen
**Project override**: Gson (preferred for all code)
**Correction**: Use `@SerializedName` with Gson, not `@JsonClass(generateAdapter = true)` with Moshi. Gson requires no annotation processing (no KSP needed for serialization).
**Severity**: Minor for existing code, Major for new code

---

### CE-006: Model uses launchWhenStarted — OVERRIDE
**Model default**: `lifecycleScope.launchWhenStarted { flow.collect {...} }`
**Project override**: `repeatOnLifecycle(Lifecycle.State.STARTED)` pattern
**Correction**: Always wrap collection in:
```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { ... }
    }
}
```
**Severity**: Major — deprecated API with lifecycle-safety issues

---

### CE-007: Model suggests Koin for DI — OVERRIDE
**Model default**: Sometimes suggests Koin as a simpler alternative to Hilt
**Project override**: Hilt ONLY. No Koin, no manual Dagger.
**Correction**: Always use Hilt with `@Inject`, `@HiltViewModel`, `@AndroidEntryPoint`
**Severity**: Major — wrong DI framework

---

### CE-008: Model uses findViewById — OVERRIDE
**Model default**: May generate `val textView = findViewById<TextView>(R.id.tv_name)`
**Project override**: ViewBinding only — `binding.tvName`
**Correction**: Generate ViewBinding class from layout name, use `binding.elementId`
**Severity**: Major — violates ViewBinding-only rule

---

### CE-009: Model puts business logic in Fragment — OVERRIDE
**Model default**: Quick examples often put logic directly in Fragment/Activity
**Project override**: Business logic goes in ViewModel (MVVM) or through UseCase (Clean)
**Correction**: Fragment only renders state and sends user actions. Logic lives in ViewModel.
**Severity**: Minor for trivial logic, Major for business rules

---

### CE-010: Model generates incomplete files with "// ... rest of code" — OVERRIDE
**Model default**: Truncates output with ellipsis placeholders to save tokens
**Project override**: ALWAYS generate complete files from first line to last line
**Correction**: Never use `// ...`, `// rest of file`, `// TODO: implement`. Every method
must be fully functional.
**Severity**: Critical — incomplete files cannot compile

---

### CE-011: Model uses RxJava — OVERRIDE
**Model default**: May suggest RxJava for reactive streams (legacy training data)
**Project override**: Coroutines + Flow exclusively
**Correction**: Replace `Observable<T>` with `Flow<T>`, `Single<T>` with `suspend fun`,
`Completable` with `suspend fun` returning Unit
**Severity**: Major — wrong async framework

---

### CE-012: MockK API mistakes — OVERRIDE
**Model default**: Generates incorrect MockK syntax from incomplete training examples
**Project override**: Strict correct MockK API usage
**Corrections**:
- `anyConstructed<T>()` takes NO parameters (not `anyConstructed<T>(0)`)
- `mockkObject(X)` is for Kotlin `object` only (not `mockkObject(X(args))`)
- `mockkStatic` is for static/top-level functions (not for Builder classes)
- `mockkConstructor` is for classes created with `new` (not for ViewBinding)
- ViewBinding uses `mockkStatic(XxxBinding::class)` + `every { XxxBinding.inflate(...) }`
**Severity**: Critical — incorrect tests won't compile or will test nothing

---

### CE-013: Model uses Robolectric — OVERRIDE
**Model default**: Suggests Robolectric for Android unit testing
**Project override**: Never use Robolectric. Mock all Android deps with MockK/Mockito.
**Correction**: Use `mockk<Context>(relaxed = true)`, `mockk<SharedPreferences>(relaxed = true)`, etc.
**Severity**: Critical — banned testing framework

---

### CE-014: Model generates Kotlin synthetics imports — OVERRIDE
**Model default**: May generate `import kotlinx.android.synthetic.main.fragment_x.*`
**Project override**: Kotlin Android Extensions is deprecated and removed. Use ViewBinding.
**Correction**: Remove synthetic imports, use `binding.viewId` instead
**Severity**: Critical — won't compile on modern Kotlin/AGP

---

### CE-015: Android API Level Assumptions — CALIBRATE
**Model default**: May assume minSdk 21 (Lollipop) or use APIs above minSdk 24
**Project override**: minSdk=24 (Android 7.0). Can use all APIs from level 24+.
**Correction**: Check API level before using APIs from 25+. APIs 24 and below are safe.
Available without checks: Java 8 desugaring, `Locale.getDefault()`, `NotificationChannel` (26+ needs check)
**Severity**: Major — crash on lower API devices

---

### CE-016: "My agent" means OpenCode, not Kiro — CALIBRATE
**Model default**: When running inside Kiro IDE and user says "my agent" or "how will my agent read it", model defaults to explaining Kiro features (drag-and-drop, chat attachments)
**Project override**: This workspace defines an OpenCode agent system (`.opencode/agents/`, `opencode.json`). When the user says "my agent" they mean the OpenCode-based agents running via LiteLLM.
**Correction**: Always interpret agent-capability questions in the context of the OpenCode agent system's actual tools (bash, write, edit, read) — not Kiro's IDE features.
**Severity**: Minor — wrong answer, easily corrected, but wastes user's time

---

### CE-017: Model invents library versions & coordinates — OVERRIDE (top cause of build failures)
**Model default**: Writes a concrete version number and `group:artifact` coordinate from
memory (e.g. `implementation("androidx.work:work-runtime-ktx:2.9.0")`), and invents plugin
ids and import paths. These are frequently stale, wrong, or mutually incompatible → toml/
gradle/import build failures.
**Project override**: NEVER invent a version, coordinate, plugin id, or import from memory.
Establish ground truth first:
1. Reuse the project's existing `gradle/libs.versions.toml` / build files (exact alias+version).
2. For anything new, look up the correct coordinate + compatible version + import via the
   `context7` MCP.
3. Let the Verification Loop compile — Gradle fails fast on bad coordinates; fix from ground
   truth, not another guess.
If you cannot confirm and there's no wrapper to resolve it, **state the dependency and ask** —
never fabricate a plausible-looking version.
**Severity**: Critical — the single most common reason generated projects don't compile

---

### CE-018: KSP version must track the Kotlin version — CALIBRATE
**Model default**: Pairs a KSP plugin version with a mismatched Kotlin version (e.g. Kotlin
2.1.0 with a KSP built for 1.9.x), which fails the build.
**Project override**: KSP is versioned as `<kotlin>-<ksp>` (e.g. `2.1.0-1.0.29` pairs with
Kotlin `2.1.0`). Whenever you set or change the Kotlin version, align the KSP plugin version
to the **same** Kotlin version. Resolve the exact KSP build via the project catalog or
`context7`; never mix.
**Severity**: Major — annotation processing (Hilt/Room) fails to build

---

### CE-019: Using an API without declaring its dependency — OVERRIDE
**Model default**: Writes code using an API (e.g. `Pager`/`PagingSource`, `WorkManager`,
`Coil`) but forgets to add the corresponding dependency + catalog entry, causing unresolved
references.
**Project override**: Every API you reference in code MUST have its dependency declared in the
module and catalog. After writing code, cross-check: for each third-party import, is the
backing library declared? (Paging → `androidx.paging`; WorkManager → `androidx.work`;
Coil → `io.coil-kt`; Hilt Worker → `androidx.hilt`.) Add any missing ones (coordinate/version
looked up, not invented).
**Severity**: Major — unresolved references fail compilation

---

### CE-020: Match the project's conventions — don't impose our defaults during migration
**Model default / our-rules risk**: Our skills show `build.gradle.kts` (Kotlin DSL), Gson,
KSP, and `compileSdk=35/minSdk=24`. Applying these blindly to an existing project breaks it.
**Project override (match the project first)**:
- **Gradle DSL** — if the project uses Groovy `.gradle` (not `.kts`), keep writing Groovy DSL.
  Never convert Groovy↔KTS unless explicitly asked. (Real example: `BusAttendantApp` uses
  Groovy `build.gradle` + a Version Catalog.)
- **SDK/versions** — take `compileSdk`/`minSdk`/`targetSdk` and all library versions from the
  project (e.g. compileSdk 36 / minSdk 25), NOT from our defaults. Our numbers are only a
  greenfield starting point.
- **Serialization** — Gson is our standard. If the app already uses Gson, keep it as-is.
  If the app uses Moshi/Jackson, a migration KEEPS the existing serialization; do not rip it
  out mid-migration (that just adds churn/risk).
- **Annotation processing** — introduce Hilt via KSP additively; it can coexist with the
  project's existing `annotationProcessor` (Room/Glide). Do not force-convert every existing
  `annotationProcessor` to KSP in the same pass unless asked.
- **Images** — keep the project's existing lib (e.g. Glide); don't swap to Coil mid-migration.
**Severity**: Major — imposing greenfield defaults on an existing project causes broken builds
and needless churn. The Architecture Decision Protocol's "match existing project" wins here.

---

### CE-021: Never move many files without compiling; no wholesale package-restructuring phase
**What went wrong (real incident)**: In a migration, the refactorer moved ~50 files from
`busEvent/` into new `data/domain/presentation` packages as one "Phase 2 — Package
Restructuring" step, with `Last Build Status: NOT RUN`, and checked off the steps. The build
broke and needed a manual revert.
**Correct approach**:
- **Compile gate is mandatory**: a change-set is not "done" until `assembleDebug` is green;
  `NOT RUN`/`FAILED` is never a completed state; never check off a goal step on a red/unverified
  build; never start the next slice on a red build.
- **No standalone "move all files / restructure packages" phase.** Package placement happens
  *inside* each feature vertical slice; compile after each slice (and each chunk if large).
- **Auto-revert without a prompt**: checkpoint each green slice (commit in migration mode), and
  if a change-set can't be made green within `Iteration_Budget = 5`, revert it
  (`git restore .` to the checkpoint, or `git stash push -u`), confirm green, log, and stop —
  never leave a broken build at end of turn.
**Severity**: Critical — unverified bulk moves are the top cause of broken migrations

---

### CE-022: Destructive git is blocked at the tool level — never attempt it
**What went wrong (real incident)**: During a revert, an agent ran `git reset --hard` then
`git clean -fd`. Because `.opencode/` was untracked, `clean -fd` permanently deleted the
project's agent config, memory (goals/G-006), and migration plan. A prompt prohibition alone
did NOT stop the model.
**Now enforced in `opencode.json`** via `permission.bash` (a `deny` is enforced even in auto
mode): `git reset --hard*`, `git clean*`, `git push*`, `git rebase*`, `git commit --amend*`,
`git checkout -f*`, `git branch -D*`, `rm -rf*` are DENIED. Do not attempt them — they will be
blocked. To revert, use the recoverable path: `git stash push -u` or `git restore <paths>`.
**Also**: keep `.opencode/` (config + memory + plans) **committed** to git so no `clean`/
`reset` can ever destroy it, and commit compile-green checkpoints before risky work.
**Severity**: Critical — irreversible data loss

---

### CE-023: Planner write tool silently fails on large content — OVERRIDE
**What went wrong (real incident)**: The planner agent called the `write` tool with a full
migration plan (~15,000+ characters). OpenCode reported success to the model, but the file
was never created on disk. A small test file ("hello world") written by `@coder` succeeded
immediately — proving the tool works but silently drops oversized payloads.
**Root cause**: The plan content exceeds the maximum argument size for a single tool call.
The model generates a tool-call JSON with the entire plan embedded as a string argument;
if this exceeds the output token limit or OpenCode's argument buffer, the call is silently
dropped while the model believes it succeeded.
**Correct approach**:
- **Cap the initial `write` call at ~3000 characters** (header + discovery + architecture).
- **Use sequential `edit` calls to APPEND subsequent sections** — each edit adds only the
  new section (~2000-3000 chars), NOT the entire file. This avoids the size limit entirely.
- **Verify the file exists after the final edit** — read it back. If empty/missing, retry
  with even smaller initial write.
- **Never attempt to write a full migration plan (100+ tasks) in one tool call.**
- Planner now has `edit: true` specifically for this purpose (restricted to `.opencode/plans/`).
**Severity**: Critical — plan appears saved but is lost; downstream agents can't find it

---

## Version-Specific Knowledge

> The model's training data is stale for versions. **Do not treat any number below as a pin to
> emit** — resolve real versions at generation time (project catalog first, then `context7`,
> then let Gradle resolve). The table records *relationships and directions*, not values to
> hardcode:

| Topic | Model may think | Actual (as of 2026) |
|---|---|---|
| KSP maturity | "Experimental" | Stable, production-ready, recommended over kapt |
| Compose adoption | "New and optional" | Mainstream but BANNED in this project |
| Material 3 | "Material Design 2 is current" | Material 3 is current (com.google.android.material) |
| AGP version | Various old versions | Use latest stable in Version Catalog |
| Kotlin version | 1.8.x or 1.9.x | Use latest stable (likely 2.x) |
| Gradle | 7.x or 8.0 | Use latest stable (8.x+) |
| compileSdk | 33 or 34 | 35 (this project) |
