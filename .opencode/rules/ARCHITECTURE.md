# Architecture — Detailed Rules

Read this file when planning features or generating production code.

---

## MVVM + Clean Architecture (Default)

### Layering
```
presentation (ViewModel + immutable UI state)
    → domain (UseCases + domain models + repository interfaces)
    → data (repository impl + data sources + DTO/entity + mappers)
```

### Key Rules
- ViewModel depends on UseCases (or repository interface for trivial cases)
- ViewModel never depends on data-layer types directly
- Domain layer has NO Android dependencies
- DTOs live in data layer, domain models in domain layer
- Mapper functions convert between them at the boundary

---

## MVI

### Structure
- **Intent**: sealed interface of user actions
- **State**: single immutable data class
- **Effect**: one-shot events (navigation, toasts) via Channel
- **ViewModel**: reduces intents into new state

### Key Rules
- View only sends intents and renders state
- Single state object — no multiple LiveData/StateFlow streams
- Effects are consumed once (Channel, not StateFlow)

---

## Legacy Interop Policy

When adding modern code to legacy projects:

1. **Java-interop annotations** on boundaries: `@JvmStatic`, `@JvmField`, `@JvmOverloads`
2. **Callback adapters** for Java callers that can't use `suspend`:
   ```kotlin
   fun load(onResult: (Result<T>) -> Unit) {
       scope.launch { getDataUseCase().let(onResult) }
   }
   ```
3. **DI bridging**: Hilt if project uses it; plain factory if not
4. **Separate models**: new domain models + mapper functions at boundary
5. **Never break build setup** — don't change minSdk/compileSdk

---

## Flow Collection (mandatory pattern)

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state -> render(state) }
    }
}
```

Never use `launchWhenStarted` (deprecated).

---

## Dependency Management

- All deps in `gradle/libs.versions.toml` — version key + library alias
- Reference via `libs.*` accessors only
- If a dep isn't in the catalog, add it first, then reference
- KSP plugin required for Hilt, Room — never kapt

---

## Accessibility

- Non-decorative images: `contentDescription` naming purpose/action
- Decorative: `contentDescription="@null"` or `importantForAccessibility="no"`
- Interactive elements: minimum 48dp × 48dp touch target
