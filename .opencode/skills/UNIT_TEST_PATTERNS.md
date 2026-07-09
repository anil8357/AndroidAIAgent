# Skill: Unit Test Patterns — MockK, Turbine, Coroutines

> Read this when generating **unit tests** (src/test/). For instrumented tests see
> `INSTRUMENTED_TEST_PATTERNS.md`.

---

## MockK Correct API — Reference

### Mock a singleton `object`
```kotlin
mockkObject(Session)
every { Session.get(any()) } returns mockSession
```

### Mock a companion factory
```kotlin
mockkObject(ApiClient)
every { ApiClient.getClient(any()) } returns mockApiClient
```

### Mock static/top-level functions
```kotlin
mockkStatic(Utility::class)
every { Utility.isNetworkAvailable(any()) } returns true

mockkStatic(Log::class)
every { Log.d(any(), any()) } returns 0
```

### Mock a constructor
```kotlin
mockkConstructor(AlertDialog.Builder::class)
every { anyConstructed<AlertDialog.Builder>().setTitle(any<String>()) } returns mockBuilder
every { anyConstructed<AlertDialog.Builder>().create() } returns mockDialog
```

### Mock ViewBinding static inflate
```kotlin
mockkStatic(ActivityMainBinding::class)
every { ActivityMainBinding.inflate(any()) } returns mockBinding
every { ActivityMainBinding.inflate(any(), any(), any()) } returns mockBinding
```

### Capture callbacks
```kotlin
val callbackSlot = slot<MyCallback>()
every { mockApi.fetchData(capture(callbackSlot)) } answers {
    callbackSlot.captured.onSuccess(fakeResponse)
}
```

---

## Private-Member Access (reflection helpers)

```kotlin
private fun Any.setPrivateField(name: String, value: Any?) {
    javaClass.getDeclaredField(name).apply {
        isAccessible = true
        set(this@setPrivateField, value)
    }
}

private fun Any.getPrivateField(name: String): Any? =
    javaClass.getDeclaredField(name).apply { isAccessible = true }.get(this)

private fun Any.callPrivateMethod(name: String, vararg args: Any?): Any? {
    val method = javaClass.declaredMethods.first { it.name == name }
    method.isAccessible = true
    return method.invoke(this, *args)
}
```

---

## Kotlin ViewModel Test (MVVM — Coroutines + Turbine)

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class <ClassName>Test {

    private val testDispatcher = StandardTestDispatcher()
    private val mock<Dep> = mockk<<DepType>>()
    private lateinit var sut: <ClassName>

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        sut = <ClassName>(mock<Dep>)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        unmockkAll()
    }

    @Test
    fun `loadData - success - emits Success state`() = runTest {
        coEvery { mock<Dep>.getData() } returns listOf(fakeItem)

        sut.uiState.test {
            sut.loadData()
            testDispatcher.scheduler.advanceUntilIdle()

            assertIs<UiState.Loading>(awaitItem())
            val success = awaitItem()
            assertIs<UiState.Success>(success)
            assertEquals(listOf(fakeItem), success.data)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `loadData - error - emits Error state`() = runTest {
        coEvery { mock<Dep>.getData() } throws RuntimeException("fail")

        sut.uiState.test {
            sut.loadData()
            testDispatcher.scheduler.advanceUntilIdle()

            assertIs<UiState.Loading>(awaitItem())
            val error = awaitItem()
            assertIs<UiState.Error>(error)
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

---

## MVI ViewModel Test (Intent + State + Effect)

```kotlin
@Test
fun `onIntent Load - success - state shows items`() = runTest {
    coEvery { getDataUseCase(any()) } returns Result.success(listOf(fakeItem))
    sut.state.test {
        assertEquals(MyState(), awaitItem())               // initial
        sut.onIntent(MyIntent.Load)
        advanceUntilIdle()
        assertTrue(awaitItem().isLoading)                  // loading
        val loaded = awaitItem()
        assertEquals(listOf(fakeItem), loaded.items)       // success
        assertFalse(loaded.isLoading)
        cancelAndIgnoreRemainingEvents()
    }
}

@Test
fun `onIntent ItemClicked - emits NavigateToDetail effect`() = runTest {
    sut.effect.test {
        sut.onIntent(MyIntent.ItemClicked("42"))
        advanceUntilIdle()
        assertEquals(MyEffect.NavigateToDetail("42"), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

---

## Java Test (Mockito — MVC/MVP)

```java
@RunWith(MockitoJUnitRunner.class)
public class <ClassName>Test {

    @Mock private <DepType> mock<Dep>;
    @Mock private Context mockContext;
    @Mock private SharedPreferences mockPrefs;
    @Mock private SharedPreferences.Editor mockEditor;
    private <ClassName> sut;

    @Before
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        when(mockContext.getSharedPreferences(anyString(), anyInt())).thenReturn(mockPrefs);
        when(mockPrefs.edit()).thenReturn(mockEditor);
        when(mockEditor.putString(anyString(), anyString())).thenReturn(mockEditor);
        sut = new <ClassName>();
    }

    @After
    public void tearDown() { Mockito.reset(mock<Dep>, mockContext); }

    @Test
    public void methodName_happyPath_expectedOutcome() {
        // Given
        when(mock<Dep>.someMethod()).thenReturn("value");
        // When
        String result = sut.publicMethod();
        // Then
        assertEquals("expected", result);
        verify(mock<Dep>).someMethod();
    }
}
```

---

## Kotlin Activity/Fragment Test (MVC — no ViewModel)

```kotlin
class <ActivityName>Test {
    // Include reflection helpers from above

    private val mockSession = mockk<Session>(relaxed = true)
    private lateinit var sut: <ActivityName>

    @Before
    fun setUp() {
        mockkStatic(Log::class)
        every { Log.d(any(), any()) } returns 0
        mockkObject(Session)
        every { Session.get(any()) } returns mockSession
        sut = <ActivityName>()
        sut.setPrivateField("mSession", mockSession)
    }

    @After
    fun tearDown() { unmockkAll() }

    @Test
    fun `methodName - scenario - expected`() {
        sut.setPrivateField("fieldName", testValue)
        val result = sut.callPrivateMethod("methodName") as Boolean
        assertTrue(result)
    }
}
```
