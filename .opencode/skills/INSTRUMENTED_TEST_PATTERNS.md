# Skill: Instrumented / UI Test Patterns — Espresso, Hilt, Room

> Read this when generating **instrumented tests** (androidTest/). For unit tests see
> `UNIT_TEST_PATTERNS.md`.

---

## Hilt Instrumented Test Setup

### Custom test runner (required once per module)
```kotlin
// app/src/androidTest/java/<pkg>/HiltTestRunner.kt
class HiltTestRunner : AndroidJUnitRunner() {
    override fun newApplication(cl: ClassLoader?, name: String?, context: Context?): Application =
        super.newApplication(cl, HiltTestApplication::class.java.name, context)
}
```

In module `build.gradle(.kts)`:
```kotlin
android {
    defaultConfig {
        testInstrumentationRunner = "<pkg>.HiltTestRunner"
    }
}
```

### HiltTestActivity helper (for FragmentScenario with Hilt)
```kotlin
@AndroidEntryPoint
class HiltTestActivity : AppCompatActivity()
```

### launchFragmentInHiltContainer helper
```kotlin
inline fun <reified F : Fragment> launchFragmentInHiltContainer(
    fragmentArgs: Bundle? = null,
    crossinline action: F.() -> Unit = {}
) {
    val intent = Intent.makeMainActivity(
        ComponentName(ApplicationProvider.getApplicationContext(), HiltTestActivity::class.java)
    )
    ActivityScenario.launch<HiltTestActivity>(intent).onActivity { activity ->
        val fragment = activity.supportFragmentManager.fragmentFactory.instantiate(
            F::class.java.classLoader!!, F::class.java.name
        )
        fragment.arguments = fragmentArgs
        activity.supportFragmentManager.beginTransaction()
            .add(android.R.id.content, fragment)
            .commitNow()
        (fragment as F).action()
    }
}
```

---

## Fragment Test (Espresso + Hilt)

```kotlin
@HiltAndroidTest
@RunWith(AndroidJUnit4::class)
class LoginFragmentTest {

    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)

    @Before
    fun setUp() { hiltRule.inject() }

    @Test
    fun submitButton_disabledUntilBothFieldsFilled() {
        launchFragmentInHiltContainer<LoginFragment>()

        onView(withId(R.id.btn_login_submit)).check(matches(not(isEnabled())))

        onView(withId(R.id.et_login_email)).perform(typeText("a@b.com"), closeSoftKeyboard())
        onView(withId(R.id.et_login_password)).perform(typeText("secret"), closeSoftKeyboard())

        onView(withId(R.id.btn_login_submit)).check(matches(isEnabled()))
    }
}
```

---

## Activity Test (ActivityScenario)

```kotlin
@RunWith(AndroidJUnit4::class)
class MainActivityTest {

    @Test
    fun bottomNav_switchesToProfileTab() {
        ActivityScenario.launch(MainActivity::class.java).use {
            onView(withId(R.id.nav_profile)).perform(click())
            onView(withId(R.id.tv_profile_title)).check(matches(isDisplayed()))
        }
    }
}
```

---

## RecyclerView Interactions

```kotlin
// Click item at position
onView(withId(R.id.rv_home_items))
    .perform(RecyclerViewActions.actionOnItemAtPosition<RecyclerView.ViewHolder>(0, click()))

// Scroll to item with text
onView(withId(R.id.rv_home_items))
    .perform(RecyclerViewActions.scrollTo<RecyclerView.ViewHolder>(
        hasDescendant(withText("Item Name"))
    ))
```

---

## Intent Verification (Espresso-Intents)

```kotlin
@Test
fun tappingItem_launchesDetailWithId() {
    Intents.init()
    try {
        ActivityScenario.launch(HomeActivity::class.java).use {
            onView(withId(R.id.rv_home_items))
                .perform(RecyclerViewActions.actionOnItemAtPosition<RecyclerView.ViewHolder>(0, click()))
            intended(allOf(
                hasComponent(DetailActivity::class.java.name),
                hasExtra("id", "42")
            ))
        }
    } finally {
        Intents.release()
    }
}
```

---

## Navigation Component (TestNavHostController)

```kotlin
@Test
fun clickingNext_navigatesToDetail() {
    val navController = TestNavHostController(ApplicationProvider.getApplicationContext())
    launchFragmentInHiltContainer<ListFragment> {
        navController.setGraph(R.navigation.nav_graph)
        Navigation.setViewNavController(requireView(), navController)
    }
    onView(withId(R.id.btn_list_next)).perform(click())
    assertEquals(R.id.detailFragment, navController.currentDestination?.id)
}
```

---

## Room Integration (in-memory DB)

```kotlin
@RunWith(AndroidJUnit4::class)
class UserDaoTest {
    private lateinit var db: AppDatabase
    private lateinit var dao: UserDao

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = db.userDao()
    }

    @After
    fun tearDown() { db.close() }

    @Test
    fun insertAndQuery_returnsInsertedUser() = runTest {
        dao.insert(UserEntity(id = 1, name = "Ada"))
        assertEquals("Ada", dao.getById(1)?.name)
    }
}
```

---

## IdlingResource (async synchronization — never Thread.sleep)

```kotlin
// In production code:
object EspressoIdlingResource {
    val countingIdlingResource = CountingIdlingResource("GLOBAL")
    fun increment() = countingIdlingResource.increment()
    fun decrement() { if (!countingIdlingResource.isIdleNow) countingIdlingResource.decrement() }
}

// In test:
@Before fun register() { IdlingRegistry.getInstance().register(EspressoIdlingResource.countingIdlingResource) }
@After  fun unregister() { IdlingRegistry.getInstance().unregister(EspressoIdlingResource.countingIdlingResource) }
```

---

## Key Rules Reminder

- **androidTest/ only** — never put Espresso/ActivityScenario in `src/test/`
- **No Compose test APIs** — `createComposeRule` etc. are BANNED
- **No Thread.sleep** — use IdlingResource
- **No real network** — stub with MockWebServer or test module
- **Animations off** — tell user to disable on test device
