# Skill: Legacy → MVVM + Clean Architecture Migration

> Read this for **whole-project or large-scale** migrations of a legacy Android app
> (Java and/or old-pattern Kotlin) to MVVM + Clean Architecture. Used by `@planner` (to
> produce the phased plan) and `@refactorer` (to execute it phase by phase).
>
> This is different from a small refactor. It is a **planned, phased, resumable** effort —
> never a big-bang rewrite.

---

## Guiding Principle — Strangler-Fig, Never Big-Bang

Migrate incrementally so the app **compiles and runs after every phase**. You grow the new
architecture around the old code and retire legacy pieces feature by feature.

- **The build must stay green after every phase.** A phase that leaves the project not
  compiling is not "done" — it is a broken checkpoint.
- **One vertical slice at a time.** Migrate a whole feature (its data → domain → presentation)
  before starting the next, rather than converting all Activities, then all repositories, etc.
- **Legacy and new coexist during the transition.** New Kotlin/Hilt code interoperates with
  not-yet-migrated Java via bridges, `@JvmStatic`/`@JvmOverloads`, and mappers.
- **Preserve behavior.** A migration changes *structure*, not features. If behavior must
  change, that is a separate task — call it out, don't silently alter it.

---

## Target Structure (package layout)

Organize by feature, then by Clean layer inside each feature (or a shared `core` module/pkg):

```
<app pkg>/
├── core/                         # shared across features
│   ├── common/                   # Result type, dispatchers, extensions
│   ├── data/                     # Retrofit/OkHttp/Gson setup, Room, base data sources
│   ├── domain/                   # shared domain models / base UseCase
│   └── di/                       # app-wide Hilt modules (Network, Database)
└── feature/
    └── <feature>/
        ├── data/                 # repository impl, DTO/entity, mappers, data sources
        ├── domain/               # domain model, repository INTERFACE, use cases
        └── presentation/         # ViewModel (StateFlow), Fragment/Activity (ViewBinding), adapter
```

Layer dependency direction: `presentation → domain → data` (domain has no Android deps).

---

## The Phase Plan

`@planner` produces this as a numbered, dependency-ordered plan saved to `.opencode/plans/`.
`@refactorer` executes one phase per pass and checkpoints in `prospective/goals.md`.

### Phase 0 — Discovery & safety net
- Map the current project: modules, package layout, Java vs Kotlin split, DI state (none/
  manual/Dagger/Hilt), data access (raw SQLite/Room/network), threading (AsyncTask/Thread/
  RxJava/callbacks), UI (findViewById/synthetics/ViewBinding), God-Activities/Fragments.
- Record the **baseline**: does it currently compile? (`assembleDebug`) — this is your
  regression reference when unit tests are skipped.
- Decide feature migration order (usually: least-coupled / leaf features first, shared
  infrastructure they need is done in Phase 1–2).

### Phase 1 — Foundation (app still runs unchanged)
- Ensure Gradle is modern: Version Catalog, KSP plugin, Kotlin plugin. **Resolve versions via
  the Dependency & Build Integrity Protocol (see `coder.md`) — never invent them.**
- Add Hilt: `@HiltAndroidApp` on the Application, apply the Hilt + KSP plugins, add the
  dependency. Existing Activities keep working (add `@AndroidEntryPoint` as you migrate them).
- Add coroutines, lifecycle-viewmodel, and the shared `Result`/error type.
- Create base classes if useful (`BaseFragment`, `BaseViewModel`) — optional, match project.
- **Gate:** project still compiles and runs; no behavior change.

### Phase 2 — Core / shared infrastructure
- Stand up shared `core/data` (Retrofit + OkHttp + Gson; Room if used) and `core/di`
  Hilt modules (Network, Database).
- Introduce mappers and the shared domain contracts other features will reuse.
- **Gate:** compiles; nothing wired to UI yet, so no behavior change.

### Phase 3 — Per-feature vertical slice (repeat for each feature)
For one feature at a time, in dependency order:
1. **Domain** — define the domain model, the repository **interface**, and use case(s).
2. **Data** — repository **impl** + data source(s) + DTO/entity + mappers; provide via Hilt.
3. **Presentation** — `@HiltViewModel` ViewModel exposing immutable `StateFlow`; convert the
   Activity/Fragment to ViewBinding + `@AndroidEntryPoint`, collecting state with
   `repeatOnLifecycle(STARTED)`. Move all business logic out of the View into ViewModel/UseCase.
4. **Wire & retire** — point navigation/DI at the new code; delete the legacy implementation
   for this feature (or leave a thin bridge if other unmigrated code still calls it).
5. **Gate:** compiles; the migrated feature behaves as before.

### Phase 4 — Cleanup
- Remove dead legacy code, leftover `AsyncTask`/`Thread`/callback plumbing, `findViewById`,
  Kotlin synthetics, `kapt`, Moshi, raw dependency strings.
- Remove interop bridges that are no longer called.
- **Gate:** compiles; full app smoke-tested.

---

## Per-Pattern Conversion Recipes

| Legacy | Target | Notes |
|---|---|---|
| God Activity/Fragment (logic inline) | ViewModel + UseCase + Repository | Move logic out; View only renders state + sends actions |
| `findViewById` / Kotlin synthetics | ViewBinding | Null binding in `onDestroyView()`; never `findViewById` |
| `AsyncTask` / `Thread` / `Handler` | Coroutines (`viewModelScope`, `Dispatchers.IO`) | Cancel on lifecycle; no work on main thread |
| Callback interfaces | `suspend` fun + `Flow` | For Java callers still needing callbacks, keep a bridge |
| RxJava | Coroutines + `Flow` | `Observable`→`Flow`, `Single`→`suspend`, `Completable`→`suspend Unit` |
| Manual singletons / static getInstance | Hilt (`@Inject`, `@Module`, `@Provides`) | `@HiltViewModel`, `@AndroidEntryPoint` |
| `LiveData` (new code) | `StateFlow`/`SharedFlow` | Existing LiveData can stay until its feature is migrated |
| Gson | Gson (keep — it's the standard) | — |
| `kapt` | KSP | KSP version tracks the Kotlin version |
| Raw `group:artifact:version` | Version Catalog `libs.*` | Resolve versions, don't invent |
| Java class | Kotlin | Convert per slice; add `@JvmStatic`/`@JvmOverloads` where Java still calls it |

For the interop bridge pattern (new Kotlin coroutine API consumed by legacy Java), follow
learned pattern **P-005** in `procedural/learned_patterns.md`.

---

## Match the Project — Don't Impose Greenfield Defaults

A migration adapts to the project that exists; it does not rewrite its conventions. Before
writing anything, adopt the project's:
- **Gradle DSL** — Groovy `.gradle` or Kotlin `.kts`. Keep whichever the project uses; never
  convert one to the other during a migration unless explicitly asked.
- **SDK & versions** — read `compileSdk`/`minSdk`/`targetSdk` and all library versions from
  the project's build files / catalog. Reuse them; don't substitute our greenfield numbers.
- **Serialization** — Gson is the project standard; keep it as-is. If the app uses
  Jackson or another serialization library, keep the existing one. Don't swap serialization
  libraries mid-migration.
- **Annotation processing** — add Hilt via KSP **additively**; it coexists with existing
  `annotationProcessor` (Room/Glide). Don't force-convert everything to KSP in one pass.
- **Images / other libs** — keep the project's existing choices (e.g. Glide) unless asked.

The point of the migration is **architecture** (extract logic into ViewModel/UseCase/
Repository, add DI), not churning the toolchain. Changing serialization/DSL/image libs at the
same time multiplies risk — especially with tests skipped.

---

## Interop During the Transition

While both worlds coexist:
- New `suspend`/`Flow` APIs are **not** exposed directly to Java callers — wrap them in a
  callback/listener bridge (see P-005).
- Convert between legacy models and new domain models with explicit **mappers**; never mutate
  legacy models from new code.
- If the project has no DI yet, you can introduce Hilt incrementally — a class is only
  `@AndroidEntryPoint`/injected once its feature is migrated; untouched legacy keeps its old
  wiring until then.
- Do not change `minSdk`/`compileSdk`/build setup in a way that breaks unmigrated code.

---

## Verification When Unit Tests Are Skipped

Unit tests are the normal safety net for refactoring. When the user skips them, the safety
net degrades — be explicit about this and compensate:

1. **Compile-green is the hard gate.** After every phase (and every slice within Phase 3),
   run the compile `Build_Command` (`assembleDebug` / `compileDebugKotlin`) via the OS-correct
   Gradle wrapper. A phase is complete only when it compiles. Same allow-listed commands and
   `Iteration_Budget = 5` as the `@coder` loop.
2. **Behavior preservation is manual.** Without tests, regressions are NOT auto-caught. State
   clearly, per migrated feature, what the user should **smoke-test manually** (the key flows).
3. **Recommend tests re-entry.** After the migration (or per feature), recommend `@tester` /
   `@ui-tester` to lock in behavior — note it as a follow-up, don't block on it now.
4. **Small, reversible slices.** Keep each slice small enough that if the user reports a
   regression, the change is easy to locate and revert.

> ⚠️ Migrating a whole app with tests skipped is riskier by definition. The compile gate
> catches structural breakage, not behavioral. Say so.

---

## Dependency Integrity

Migrations add many new dependencies (Hilt, coroutines, lifecycle, Room, Retrofit, Gson).
This is exactly where toml/gradle breakage happens. Follow the **Dependency & Build Integrity
Protocol** in `coder.md`: reuse the project's existing catalog/versions first, look up anything
new via `context7`, let the compile loop resolve/verify, and never invent a version or
coordinate. Verify the version-agnostic invariants (every `version.ref` resolves, KSP tracks
Kotlin, every `libs.*` accessor declared, every used API's dependency declared).

---

## Checkpointing (resumability is mandatory for a big migration)

A whole-project migration spans many passes/sessions. Checkpoint in
`prospective/goals.md` per the writing-agent protocol:
- Create the Active Goal **before** Phase 1, listing the phases and feature order.
- After each phase/slice: check it off, update **Files Touched**, **Next Action**, and
  **Last Build Status** (compile PASSED/FAILED).
- The **Next Action** must be specific enough that a fresh session resumes cold (e.g.
  "Phase 3, migrate `profile` feature — domain layer done, next: ProfileRepositoryImpl").

---

## Definition of Done (per feature and overall)

Per feature:
- [ ] Domain (model + repo interface + use cases), Data (impl + sources + mappers + Hilt),
      Presentation (ViewModel StateFlow + ViewBinding + `repeatOnLifecycle`) all in place
- [ ] All business logic out of the View
- [ ] Legacy implementation retired or bridged
- [ ] Compiles; key flows smoke-tested manually (tests skipped)

Overall:
- [ ] Every targeted feature migrated; app compiles and runs
- [ ] No `findViewById`/synthetics/AsyncTask/kapt/Moshi/raw-coords left in migrated code
- [ ] Follow-ups noted: `@tester`/`@ui-tester` to add coverage
