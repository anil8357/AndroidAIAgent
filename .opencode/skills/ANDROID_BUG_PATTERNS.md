# Skill: Common Android Bug Patterns

> Read this when diagnosing a bug. Maps symptoms → root causes → fix patterns.

---

## ViewBinding / NPE

| Symptom | Root Cause | Fix |
|---|---|---|
| NPE on `binding.someView` after rotation | Binding accessed after `onDestroyView()` | Null `_binding` in `onDestroyView()` |
| NPE in a callback/lambda | Fragment recreated but stale binding reference held | Use `_binding?.someView` or capture `viewLifecycleOwner` |
| NPE after back navigation | Fragment popped, binding gone but coroutine still collecting | Scope collection to `repeatOnLifecycle(STARTED)` |

---

## Lifecycle

| Symptom | Root Cause | Fix |
|---|---|---|
| State lost on config change | Observers not re-attached after Fragment recreation | Use `viewLifecycleOwner.lifecycleScope` not `lifecycleScope` |
| Flow keeps collecting in background | `lifecycleScope.launch` without `repeatOnLifecycle` | Wrap in `repeatOnLifecycle(Lifecycle.State.STARTED)` |
| Stale observer after back-stack pop | Fragment observer outlives its View | Null binding + use `viewLifecycleOwner` for collections |
| DialogFragment crash on dismiss | Show called after `onSaveInstanceState` | Use `showNow()` or check `isStateSaved` |

---

## Coroutines / Threading

| Symptom | Root Cause | Fix |
|---|---|---|
| ANR / UI freeze | `runBlocking` on main thread | Replace with `viewModelScope.launch` |
| NetworkOnMainThreadException | Missing `withContext(Dispatchers.IO)` | Wrap network/DB call in IO dispatcher |
| Leaked coroutine (logcat warning) | `GlobalScope` or unstructured scope | Use `viewModelScope` (auto-cancels) |
| CancellationException | Parent job cancelled while child running | Handle `CancellationException` specially or use `NonCancellable` for cleanup |
| Race condition on shared state | Multiple coroutines mutating same variable | Use `Mutex`, `StateFlow.update {}`, or `Channel` |

---

## Hilt / Dependency Injection

| Symptom | Root Cause | Fix |
|---|---|---|
| `UninitializedPropertyAccessException` on injected field | Missing `@AndroidEntryPoint` | Add annotation to Activity/Fragment |
| `CreationException: no binding exists` | ViewModel missing `@HiltViewModel` | Add `@HiltViewModel` + `@Inject constructor` |
| Wrong instance / stale data | Scope mismatch (Activity-scoped in singleton) | Match scope to component lifecycle |
| Crash on process death | Hilt entry point not found after restoration | Ensure Application class has `@HiltAndroidApp` |

---

## Room / Database

| Symptom | Root Cause | Fix |
|---|---|---|
| `IllegalStateException: Cannot access database on the main thread` | Query not on IO dispatcher | Make DAO functions `suspend` or use `Dispatchers.IO` |
| `IllegalStateException: Migration didn't properly handle` | Schema changed without migration | Add `Migration(N, N+1)` or use `fallbackToDestructiveMigration()` for debug |
| Entity not returned | Missing `@PrimaryKey` | Add `@PrimaryKey` to entity |
| Query returns stale data | Not using `Flow<List<T>>` return type | Return `Flow` from DAO for reactive updates |

---

## Navigation Component

| Symptom | Root Cause | Fix |
|---|---|---|
| `IllegalStateException: View not attached` | `findNavController()` called too early | Call after `onViewCreated`, not in `onCreateView` |
| Action ID crash | Mismatch between nav_graph action id and code | Verify action id in `nav_graph.xml` matches `R.id.action_x_to_y` |
| Back-stack corruption | Manual `popBackStack` conflicting with Navigation | Use Navigation actions with `popUpTo` instead of manual pops |
| Arguments lost on recreation | Using `arguments` directly instead of SafeArgs | Use generated `<Name>FragmentArgs` |

---

## State / MVI

| Symptom | Root Cause | Fix |
|---|---|---|
| Event fires twice on rotation | One-shot event modeled in `StateFlow` (re-emitted) | Use a `Channel` + `receiveAsFlow()` for Effects |
| Lost state update under concurrency | `_state.value = x` not atomic | Use `_state.update { it.copy(...) }` |
| Effect never received | Sent before collector is active | Use `Channel(Channel.BUFFERED)` |
| UI mutates state directly | View bypasses intent dispatching | Enforce `onIntent()` as the only way to change state |

---

## RecyclerView

| Symptom | Root Cause | Fix |
|---|---|---|
| Items not updating | `DiffUtil` not implemented / `notifyDataSetChanged()` | Use `ListAdapter` with proper `DiffUtil.ItemCallback` |
| Scroll position lost | Adapter recreated on data refresh | Reuse adapter instance; only `submitList()` |
| Click on wrong item | ViewHolder position stale | Use `bindingAdapterPosition` not `adapterPosition` |

---

## Memory Leaks

| Symptom | Root Cause | Fix |
|---|---|---|
| Activity/Fragment in heap after destroy | Anonymous inner class holds reference | Use `weak reference` or ViewModel pattern |
| `static` Context reference | Companion object or Java `static` holding Activity | Never store Context in static; use `applicationContext` if needed |
| Handler/Runnable leak | `postDelayed` not removed on destroy | Remove callbacks in `onDestroyView`/`onDestroy` |

---

## Diagnostic Procedure

1. **Read the stack trace** — identify the exact line and class.
2. **Match to a pattern above** — symptoms → root cause.
3. **Gather evidence** — read the implicated file(s), look for the anti-pattern.
4. **Propose fix** — before/after code, referencing the correct pattern.
5. **Check for spread** — same anti-pattern may exist elsewhere (`grep` for it).
