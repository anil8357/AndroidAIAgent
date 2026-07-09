# Unit Testing Standards

Read this file when generating or reviewing test code.

---

## ⛔ Prohibited Testing Patterns

| Banned Pattern | Correct Alternative |
|---|---|
| `ActivityScenario` in unit tests | `mockk<Activity>(relaxed = true)` or test extracted logic |
| `@RunWith(AndroidJUnit4::class)` in unit tests | No runner with MockK, or `MockitoJUnitRunner` |
| `ApplicationProvider.getApplicationContext()` | `mockk<Context>(relaxed = true)` |
| `activity["fieldName"]` bracket syntax | Reflection: `javaClass.getDeclaredField(...)` |
| `anyConstructed<Type>(index)` | `anyConstructed<Type>()` without arguments |
| `mockkObject(SomeClass(args))` on instances | `mockkObject(SomeClass)` for singletons, `mockk<>()` for instances |
| `mockkStatic(AlertDialog.Builder::class)` | `mockkConstructor(AlertDialog.Builder::class)` |
| `mockkConstructor(ViewBinding::class)` | `mockkStatic(XxxBinding::class)` + mock `inflate()` |
| Testing private methods directly | Test through public API or extract to helper |
| `Robolectric` | Mock all Android deps with MockK/Mockito |

---

## ✅ Required Test Structure (Kotlin + MockK)

```kotlin
class SomeClassTest {
    private val mockDep = mockk<DepType>(relaxed = true)
    private lateinit var sut: SomeClass

    @Before
    fun setUp() { sut = SomeClass(mockDep) }

    @After
    fun tearDown() { unmockkAll() }

    @Test
    fun `methodName - scenario - expected result`() {
        // Given
        every { mockDep.someMethod() } returns "value"
        // When
        val result = sut.publicMethod()
        // Then
        assertEquals("expected", result)
        verify { mockDep.someMethod() }
    }
}
```

---

## MockK Correct API Usage

```kotlin
// ✅ Mock singleton object
mockkObject(Session)
every { Session.get(any()) } returns mockSession

// ✅ Mock companion factory
mockkObject(ApiClient.Companion)
every { ApiClient.getClient(any()) } returns mockApiClient

// ✅ Mock static methods
mockkStatic(Utility::class)
every { Utility.isNetworkAvailable(any()) } returns true

// ✅ Mock constructor
mockkConstructor(AlertDialog.Builder::class)
every { anyConstructed<AlertDialog.Builder>().setTitle(any<String>()) } returns mockBuilder

// ✅ Mock ViewBinding inflate
mockkStatic(ActivityMainBinding::class)
every { ActivityMainBinding.inflate(any()) } returns mockBinding

// ✅ Capture callbacks
val slot = slot<MyCallback>()
every { mockApi.fetchData(capture(slot)) } answers { slot.captured.onSuccess(fakeResponse) }
```

---

## Accessing Private Members (when absolutely necessary)

```kotlin
fun <T> Any.setPrivateField(name: String, value: T) {
    javaClass.getDeclaredField(name).apply { isAccessible = true; set(this@setPrivateField, value) }
}

fun Any.callPrivateMethod(name: String, vararg args: Any?): Any? {
    val method = javaClass.declaredMethods.first { it.name == name }
    method.isAccessible = true
    return method.invoke(this, *args)
}
```

---

## Test Classification

| Type | Runner | Location | Use Case |
|---|---|---|---|
| Unit test | JUnit 4 (no Android runner) | `app/src/test/` | ViewModel, Repository, UseCase, utilities |
| Instrumented | `AndroidJUnit4` | `app/src/androidTest/` | UI flows, lifecycle, real DB |

`@tester` generates **unit tests only** in `app/src/test/`. If a class requires the
Android runtime, state it needs an instrumented test instead.

---

## Testing Legacy Activities/Fragments (MVC)

1. **Preferred**: Extract logic to helper classes and test those
2. **If not possible**: Mock the Activity, test public/internal methods only
3. **Never mix** `ActivityScenario` (instrumented) with MockK (unit) — pick one
