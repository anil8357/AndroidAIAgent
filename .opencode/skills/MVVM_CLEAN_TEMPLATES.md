# Skill: MVVM + Clean Architecture — Code Templates

> Read this when generating **new feature code** using the MVVM + Clean Architecture target.
> Do NOT read this for MVI features — see `MVI_TEMPLATES.md` instead.

---

## Layer Structure

```
presentation (ViewModel + immutable UI state)
    → domain (UseCases + domain models + repository interfaces)
    → data (repository impl + data sources + DTO/entity + mappers)
```

---

## UseCase (domain layer)

```kotlin
class Get<Data>UseCase @Inject constructor(
    private val repository: <Name>Repository   // domain interface
) {
    suspend operator fun invoke(params: <Params>): Result<List<<Model>>> =
        repository.get<Data>(params)
}
```

---

## Repository interface (domain) + impl (data)

```kotlin
// domain/repository/<Name>Repository.kt
interface <Name>Repository {
    suspend fun get<Data>(params: <Params>): Result<List<<Model>>>
}

// data/repository/<Name>RepositoryImpl.kt
class <Name>RepositoryImpl @Inject constructor(
    private val api: <Name>Api,
    private val dao: <Name>Dao
) : <Name>Repository {

    override suspend fun get<Data>(params: <Params>): Result<List<<Model>>> =
        withContext(Dispatchers.IO) {
            runCatching {
                api.fetch<Data>(params).map { it.toDomain() }   // DTO → domain via mapper
            }
        }
}
```

---

## Mapper (data ↔ domain boundary)

```kotlin
// data/mapper/<Name>Mapper.kt
fun <Name>Dto.toDomain(): <Model> = <Model>(
    id = id,
    name = name.orEmpty()
)
```

---

## ViewModel

```kotlin
@HiltViewModel
class <Name>ViewModel @Inject constructor(
    private val get<Data>UseCase: Get<Data>UseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow<<UiState>>(<UiState>.Loading)
    val uiState: StateFlow<<UiState>> = _uiState.asStateFlow()

    fun load<Data>() {
        viewModelScope.launch {
            _uiState.value = <UiState>.Loading
            get<Data>UseCase(<Params>)
                .onSuccess { _uiState.value = <UiState>.Success(it) }
                .onFailure { _uiState.value = <UiState>.Error(it.message ?: "Unknown error") }
        }
    }
}
```

---

## Fragment (presentation)

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
        // Wire click listeners → call viewModel.loadX(), viewModel.onAction(...)
    }

    private fun observeState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state -> render(state) }
            }
        }
    }

    private fun render(state: <UiState>) {
        // Update binding views based on state
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
```

---

## Legacy Interop Bridge (for existing Java projects)

```kotlin
// presentation/<name>/<Name>Bridge.kt
class <Name>Bridge @Inject constructor(
    private val get<Data>UseCase: Get<Data>UseCase
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    /** Java-friendly entry point — no suspend, result delivered on main thread. */
    @JvmOverloads
    fun load(
        params: <Params>,
        onResult: (List<<Model>>) -> Unit,
        onError: (Throwable) -> Unit = {}
    ) {
        scope.launch {
            get<Data>UseCase(params)
                .onSuccess(onResult)
                .onFailure(onError)
        }
    }

    /** Call from the legacy component's onDestroy() to cancel in-flight work. */
    fun clear() = scope.cancel()
}
```

---

## Hilt DI Module (data layer wiring)

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class <Name>Module {

    @Binds
    abstract fun bind<Name>Repository(
        impl: <Name>RepositoryImpl
    ): <Name>Repository
}

@Module
@InstallIn(SingletonComponent::class)
object <Name>NetworkModule {

    @Provides
    @Singleton
    fun provide<Name>Api(retrofit: Retrofit): <Name>Api =
        retrofit.create(<Name>Api::class.java)
}
```
