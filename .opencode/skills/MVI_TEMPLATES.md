# Skill: MVI — Code Templates

> Read this when generating **new feature code** using the MVI target.
> Do NOT read this for MVVM+Clean features — see `MVVM_CLEAN_TEMPLATES.md` instead.

---

## When to Use MVI

- 4+ distinct user intents on a screen
- Complex or derived state
- Strict unidirectional data flow required for correctness

---

## Contract (Intent / State / Effect)

```kotlin
// presentation/<name>/<Name>Contract.kt
sealed interface <Name>Intent {
    data object Load : <Name>Intent
    data class ItemClicked(val id: String) : <Name>Intent
    data object Refresh : <Name>Intent
}

data class <Name>State(
    val isLoading: Boolean = false,
    val items: List<<Model>> = emptyList(),
    val error: String? = null
)

sealed interface <Name>Effect {
    data class ShowMessage(val text: String) : <Name>Effect
    data class NavigateToDetail(val id: String) : <Name>Effect
}
```

---

## MVI ViewModel (Reducer)

```kotlin
@HiltViewModel
class <Name>ViewModel @Inject constructor(
    private val get<Data>UseCase: Get<Data>UseCase
) : ViewModel() {

    private val _state = MutableStateFlow(<Name>State())
    val state: StateFlow<<Name>State> = _state.asStateFlow()

    private val _effect = Channel<<Name>Effect>(Channel.BUFFERED)
    val effect: Flow<<Name>Effect> = _effect.receiveAsFlow()

    fun onIntent(intent: <Name>Intent) {
        when (intent) {
            is <Name>Intent.Load, is <Name>Intent.Refresh -> load()
            is <Name>Intent.ItemClicked ->
                viewModelScope.launch { _effect.send(<Name>Effect.NavigateToDetail(intent.id)) }
        }
    }

    private fun load() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            get<Data>UseCase(<Params>)
                .onSuccess { data -> _state.update { it.copy(isLoading = false, items = data) } }
                .onFailure { e ->
                    _state.update { it.copy(isLoading = false, error = e.message) }
                    _effect.send(<Name>Effect.ShowMessage(e.message ?: "Error"))
                }
        }
    }
}
```

---

## MVI Fragment

```kotlin
@AndroidEntryPoint
class <Name>Fragment : Fragment(R.layout.<layout_name>) {

    private var _binding: <LayoutBinding>? = null
    private val binding get() = _binding!!
    private val viewModel: <Name>ViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        _binding = <LayoutBinding>.bind(view)
        setupUi()
        observeState()
    }

    private fun setupUi() {
        // Wire user actions → viewModel.onIntent(...)
        binding.btnRetry.setOnClickListener { viewModel.onIntent(<Name>Intent.Refresh) }
    }

    private fun observeState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch { viewModel.state.collect { render(it) } }
                launch { viewModel.effect.collect { handleEffect(it) } }
            }
        }
    }

    private fun render(state: <Name>State) {
        // Update views based on state.isLoading, state.items, state.error
    }

    private fun handleEffect(effect: <Name>Effect) {
        when (effect) {
            is <Name>Effect.ShowMessage ->
                Snackbar.make(binding.root, effect.text, Snackbar.LENGTH_SHORT).show()
            is <Name>Effect.NavigateToDetail ->
                findNavController().navigate(<Name>FragmentDirections.actionToDetail(effect.id))
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
```

---

## Key MVI Rules

- **Single state** — one immutable data class. No multiple StateFlows for the same screen.
- **Intents only** — the View never mutates state directly, only sends intents.
- **Effects for one-shots** — navigation, snackbar, toast use a `Channel` (not state).
- **Reducer is pure** — `onIntent` → new state. Side effects happen inside `viewModelScope.launch`.
- **State updates via `update {}`** — guarantees atomicity under concurrency.
