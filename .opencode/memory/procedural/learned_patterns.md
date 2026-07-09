# ⚙️ Procedural Memory — Learned Patterns

> **What it is**: Reusable problem-solving recipes learned from experience. When the agent
> encounters a problem class it's seen before, it looks here for the proven solution path
> instead of reasoning from scratch. Think of it as "muscle memory" for coding.

---

## Protocol

### When to consult this file
- Before starting any task, scan the **Pattern Index** below for matching problem classes
- If a match exists, follow the recipe — don't reinvent
- If the recipe fails, update it with what went wrong and the corrected approach

### When to add a new pattern
- After solving a non-trivial problem that took multiple attempts
- After discovering a gotcha that isn't obvious from documentation
- After finding a combination of steps that must be done in a specific order
- After the verification loop self-corrects — extract what the fix was

### Pattern Template
```markdown
#### P-[number]: [Pattern Name]
**Problem class**: When you encounter [trigger condition]
**Context**: [When/where this applies]
**Recipe**:
1. Step one
2. Step two
3. ...
**Why this works**: [Brief explanation]
**Anti-patterns** (what NOT to do):
- Don't do X because Y
**Discovered**: [date] — [which session/task]
```

---

## Pattern Index

| ID | Pattern Name | Trigger |
|---|---|---|
| P-001 | Hilt Setup for New Module | Adding Hilt DI to a new feature module |
| P-002 | Flow Collection in Fragment | Setting up StateFlow observation in a Fragment |
| P-003 | Room + KSP Migration | Adding Room to a project or creating a new entity |
| P-004 | ViewBinding Fragment Lifecycle | Correct binding setup/teardown in a Fragment |
| P-005 | Legacy Java Interop Bridge | Exposing Kotlin coroutine API to Java caller |
| P-006 | MVI Reducer Pattern | Implementing a state reducer for MVI |
| P-007 | Unit Testing ViewModel with Turbine | Testing Flow emissions from ViewModel |
| P-008 | MockK Constructor Mocking | Mocking classes instantiated with `new` |
| P-009 | Retrofit + Gson Setup | Configuring network layer from scratch |
| P-010 | Navigation Component Setup | Single-activity navigation with safe args |

---

## Patterns

#### P-001: Hilt Setup for New Module
**Problem class**: Adding Hilt DI to a new feature module
**Context**: Any time you create a new Android module or add DI to existing code
**Recipe**:
1. Add KSP plugin to module's `build.gradle.kts`: `id("com.google.devtools.ksp")`
2. Add Hilt plugin: `id("dagger.hilt.android.plugin")`
3. Add dependencies via Version Catalog:
   - `implementation(libs.hilt.android)`
   - `ksp(libs.hilt.compiler)`
4. Annotate Application class with `@HiltAndroidApp`
5. Annotate Activity/Fragment with `@AndroidEntryPoint`
6. Annotate ViewModel with `@HiltViewModel` + `@Inject constructor`
7. Provide dependencies in `@Module @InstallIn(SingletonComponent::class)` class
**Why this works**: KSP generates the Hilt component code at compile time; annotations wire it up
**Anti-patterns**:
- Don't use `kapt` — deprecated, slower, breaks incremental compilation
- Don't forget `@AndroidEntryPoint` on the Activity hosting the Fragment
- Don't provide the same binding in two different scopes without qualification
**Discovered**: [initial] — built from project rules

---

#### P-002: Flow Collection in Fragment
**Problem class**: Observing ViewModel StateFlow safely in a Fragment
**Context**: Every Fragment that observes a ViewModel's UI state
**Recipe**:
1. In `onViewCreated()`:
```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            render(state)
        }
    }
}
```
2. For multiple flows, launch each in a separate coroutine inside `repeatOnLifecycle`:
```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        launch { viewModel.uiState.collect { render(it) } }
        launch { viewModel.effect.collect { handleEffect(it) } }
    }
}
```
**Why this works**: `repeatOnLifecycle` starts collection at STARTED and cancels at STOPPED — prevents background updates to a destroyed view
**Anti-patterns**:
- Don't use `launchWhenStarted` — deprecated, pauses instead of cancelling
- Don't collect in `onCreate()` — view may not exist yet
- Don't use `lifecycleScope.launch` without `repeatOnLifecycle` — leaks collection
**Discovered**: [initial] — mandatory per project rules

---

#### P-003: Room + KSP Migration
**Problem class**: Adding Room database or a new entity
**Context**: When creating or modifying Room database schema
**Recipe**:
1. Ensure KSP plugin is applied
2. Add Version Catalog entries:
   - `implementation(libs.room.runtime)`
   - `implementation(libs.room.ktx)`
   - `ksp(libs.room.compiler)`
3. Create entity with `@Entity`, `@PrimaryKey`
4. Create DAO interface with `@Dao`
5. Create/update Database abstract class with `@Database(entities = [...], version = N)`
6. If updating existing DB: write a `Migration(oldVersion, newVersion)` with SQL
7. Provide via Hilt: `@Module @InstallIn(SingletonComponent::class)` with `@Provides @Singleton`
**Why this works**: Room needs compile-time code gen (KSP) to implement DAO methods
**Anti-patterns**:
- Don't forget migration — Room crashes on schema mismatch without one
- Don't run DAO queries on Main thread — use `suspend` or `Dispatchers.IO`
- Don't use `kapt(libs.room.compiler)` — must be `ksp(...)`
**Discovered**: [initial] — built from project rules

---

#### P-004: ViewBinding Fragment Lifecycle
**Problem class**: Correct ViewBinding setup and teardown in Fragment
**Context**: Every Fragment that uses ViewBinding
**Recipe**:
```kotlin
class MyFragment : Fragment(R.layout.fragment_my) {
    private var _binding: FragmentMyBinding? = null
    private val binding get() = _binding!!

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        _binding = FragmentMyBinding.bind(view)
        // Use binding here
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null  // CRITICAL — prevents memory leak
    }
}
```
**Why this works**: Fragment view lifecycle != Fragment lifecycle. View can be destroyed while Fragment lives (back stack). Nulling prevents stale reference access.
**Anti-patterns**:
- Don't access `binding` after `onDestroyView()` — NPE crash
- Don't forget to null `_binding` — memory leak
- Don't hold binding reference in a lambda/callback that outlives the view
**Discovered**: [initial] — built from project rules

---

#### P-005: Legacy Java Interop Bridge
**Problem class**: Existing Java code needs to call new Kotlin coroutine API
**Context**: Legacy Activity/Fragment that must consume a new UseCase or Repository
**Recipe**:
1. Create a `*Bridge.kt` class:
```kotlin
class FeatureBridge @Inject constructor(
    private val useCase: GetDataUseCase
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    @JvmOverloads
    fun load(params: Params, onResult: (List<Model>) -> Unit, onError: (Throwable) -> Unit = {}) {
        scope.launch {
            useCase(params).onSuccess(onResult).onFailure(onError)
        }
    }

    fun clear() = scope.cancel()
}
```
2. In the legacy Java code:
```java
bridge.load(params, result -> { /* handle */ }, error -> { /* handle */ });
// In onDestroy():
bridge.clear();
```
3. Add interop annotations: `@JvmStatic`, `@JvmField`, `@JvmOverloads` as needed
**Why this works**: Java can't call `suspend` functions; the bridge converts coroutines to callbacks
**Anti-patterns**:
- Don't expose `suspend` functions to Java callers — compilation error
- Don't forget `clear()` in `onDestroy()` — leaked coroutines
- Don't force Hilt onto the entire legacy project — use a factory if no DI exists
**Discovered**: [initial] — built from project rules

---

#### P-006: MVI Reducer Pattern
**Problem class**: Implementing state reduction from intents
**Context**: MVI architecture — ViewModel handling sealed Intent classes
**Recipe**:
```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val useCase: GetDataUseCase
) : ViewModel() {

    private val _state = MutableStateFlow(FeatureState())
    val state: StateFlow<FeatureState> = _state.asStateFlow()

    private val _effect = Channel<FeatureEffect>(Channel.BUFFERED)
    val effect: Flow<FeatureEffect> = _effect.receiveAsFlow()

    fun onIntent(intent: FeatureIntent) {
        when (intent) {
            is FeatureIntent.Load -> reduce { copy(isLoading = true) }.also { load() }
            is FeatureIntent.ItemClicked -> emitEffect(FeatureEffect.Navigate(intent.id))
        }
    }

    private fun reduce(reducer: FeatureState.() -> FeatureState) {
        _state.update(reducer)
    }

    private fun emitEffect(effect: FeatureEffect) {
        viewModelScope.launch { _effect.send(effect) }
    }

    private fun load() { /* ... */ }
}
```
**Why this works**: Single `reduce` function ensures all state changes go through one path — unidirectional data flow
**Anti-patterns**:
- Don't put one-shot events (navigation, toasts) in State — use Effect channel
- Don't mutate State directly — always use `_state.update { copy(...) }`
- Don't use unbuffered Channel for effects — events may be lost
**Discovered**: [initial] — built from project rules

---

#### P-007: Unit Testing ViewModel with Turbine
**Problem class**: Testing StateFlow emissions from a ViewModel
**Context**: Unit testing any ViewModel that exposes StateFlow
**Recipe**:
```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class FeatureViewModelTest {
    private val testDispatcher = StandardTestDispatcher()
    private val mockUseCase = mockk<GetDataUseCase>()
    private lateinit var sut: FeatureViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        sut = FeatureViewModel(mockUseCase)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        unmockkAll()
    }

    @Test
    fun `load - success - emits data`() = runTest {
        coEvery { mockUseCase(any()) } returns Result.success(listOf(fakeItem))

        sut.uiState.test {
            sut.loadData()
            testDispatcher.scheduler.advanceUntilIdle()
            // Assert emissions in order
            assertIs<UiState.Loading>(awaitItem())
            val success = awaitItem()
            assertIs<UiState.Success>(success)
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```
**Why this works**: Turbine gives deterministic assertion over async Flow emissions; StandardTestDispatcher controls coroutine execution
**Anti-patterns**:
- Don't forget `Dispatchers.setMain(testDispatcher)` — viewModelScope uses Main
- Don't forget `advanceUntilIdle()` — coroutines won't execute without it
- Don't use `UnconfinedTestDispatcher` for state testing — order becomes non-deterministic
**Discovered**: [initial] — built from project rules

---

#### P-008: MockK Constructor Mocking
**Problem class**: Mocking a class that's instantiated with `new` inside the code under test
**Context**: When you can't inject a dependency and it's created inline
**Recipe**:
```kotlin
// Mock the constructor
mockkConstructor(AlertDialog.Builder::class)

// Set up behaviors on ANY constructed instance
every { anyConstructed<AlertDialog.Builder>().setTitle(any<String>()) } returns mockk(relaxed = true)
every { anyConstructed<AlertDialog.Builder>().setMessage(any<String>()) } returns mockk(relaxed = true)
every { anyConstructed<AlertDialog.Builder>().create() } returns mockDialog

// For ViewBinding — use mockkStatic instead (static factory method)
mockkStatic(ActivityMainBinding::class)
every { ActivityMainBinding.inflate(any()) } returns mockBinding
```
**Why this works**: `mockkConstructor` intercepts `new` calls; `mockkStatic` intercepts static methods
**Anti-patterns**:
- Don't use `anyConstructed<Type>(index)` — API takes NO parameters
- Don't use `mockkStatic` on Builder classes — they're not static, use `mockkConstructor`
- Don't use `mockkObject` on instances — only for Kotlin `object` singletons
- Don't use `mockkConstructor` on ViewBinding — it uses static `inflate()`
**Discovered**: [initial] — built from testing standards

---

#### P-009: Retrofit + Gson Setup
**Problem class**: Configuring network layer from scratch
**Context**: New feature or project needs API communication
**Recipe**:
1. Version Catalog entries for: retrofit, converter-gson, okhttp, logging-interceptor, gson
2. Create API interface:
```kotlin
interface FeatureApi {
    @GET("endpoint")
    suspend fun getData(): Response<List<DataDto>>
}
```
3. Create DTOs with `@SerializedName` annotations
4. Create Hilt NetworkModule:
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton
    fun provideGson(): Gson = GsonBuilder()
        .setDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'")
        .create()

    @Provides @Singleton
    fun provideOkHttp(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(HttpLoggingInterceptor().setLevel(BODY))
        .build()

    @Provides @Singleton
    fun provideRetrofit(okHttp: OkHttpClient, gson: Gson): Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttp)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()

    @Provides @Singleton
    fun provideFeatureApi(retrofit: Retrofit): FeatureApi =
        retrofit.create(FeatureApi::class.java)
}
```
5. Create mapper: `DataDto.toDomain() -> DomainModel`
**Why this works**: Gson requires no annotation processing (simpler build); Hilt provides singleton networking
**Anti-patterns**:
- Don't use Moshi — Gson is the project standard
- Don't put base URL in code — use BuildConfig or a constants file
- Don't forget `suspend` on API methods — required for coroutine integration
**Discovered**: [initial] — built from project rules

---

#### P-010: Navigation Component Setup
**Problem class**: Setting up single-Activity navigation
**Context**: New app or new feature with multiple screens
**Recipe**:
1. Version Catalog entries for navigation-fragment-ktx, navigation-ui-ktx, safe-args plugin
2. Create nav graph XML in `res/navigation/nav_graph.xml`
3. Add `NavHostFragment` to Activity layout:
```xml
<androidx.fragment.app.FragmentContainerView
    android:id="@+id/nav_host_fragment"
    android:name="androidx.navigation.fragment.NavHostFragment"
    app:defaultNavGraph="@navigation/nav_graph"
    app:navHost="true"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
```
4. Set up Activity:
```kotlin
val navController = findNavController(R.id.nav_host_fragment)
setupActionBarWithNavController(navController)
```
5. Navigate from Fragment:
```kotlin
findNavController().navigate(R.id.action_listToDetail)
// Or with Safe Args:
findNavController().navigate(ListFragmentDirections.actionListToDetail(itemId))
```
**Why this works**: Navigation Component handles back stack, animations, deep links, and type-safe argument passing
**Anti-patterns**:
- Don't call `findNavController()` before view is attached — crash
- Don't manage Fragment transactions manually — use NavController
- Don't hardcode action IDs — use Safe Args generated directions
**Discovered**: [initial] — built from project rules
