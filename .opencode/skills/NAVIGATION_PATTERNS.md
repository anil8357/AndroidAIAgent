# Skill: Navigation Component — Patterns

> Read this when generating multi-screen navigation (nav graph, SafeArgs, deep links,
> bottom nav, dialog destinations). Single-Activity architecture only.

---

## Nav Graph XML

```xml
<!-- res/navigation/nav_graph.xml -->
<navigation xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/nav_graph"
    app:startDestination="@id/homeFragment">

    <fragment
        android:id="@+id/homeFragment"
        android:name="com.example.app.ui.home.HomeFragment"
        android:label="@string/home_title">

        <action
            android:id="@+id/action_home_to_detail"
            app:destination="@id/detailFragment"
            app:enterAnim="@anim/slide_in_right"
            app:exitAnim="@anim/slide_out_left"
            app:popEnterAnim="@anim/slide_in_left"
            app:popExitAnim="@anim/slide_out_right" />
    </fragment>

    <fragment
        android:id="@+id/detailFragment"
        android:name="com.example.app.ui.detail.DetailFragment"
        android:label="@string/detail_title">

        <argument
            android:name="itemId"
            app:argType="string" />

        <argument
            android:name="title"
            app:argType="string"
            android:defaultValue="" />
    </fragment>

</navigation>
```

---

## SafeArgs — Passing Data

### Navigate with args
```kotlin
// From HomeFragment
val action = HomeFragmentDirections.actionHomeToDetail(
    itemId = item.id,
    title = item.name
)
findNavController().navigate(action)
```

### Receive args
```kotlin
// In DetailFragment
class DetailFragment : Fragment(R.layout.fragment_detail) {

    private val args: DetailFragmentArgs by navArgs()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val itemId = args.itemId
        val title = args.title
        // Use them
    }
}
```

### Complex argument types
```xml
<!-- Parcelable -->
<argument
    android:name="item"
    app:argType="com.example.app.domain.model.Item" />

<!-- Enum -->
<argument
    android:name="filter"
    app:argType="com.example.app.ui.FilterType"
    android:defaultValue="ALL" />

<!-- Array -->
<argument
    android:name="ids"
    app:argType="string[]" />

<!-- Nullable -->
<argument
    android:name="subtitle"
    app:argType="string"
    app:nullable="true"
    android:defaultValue="@null" />
```

---

## NavHostFragment in Activity Layout

```xml
<!-- res/layout/activity_main.xml -->
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <androidx.fragment.app.FragmentContainerView
        android:id="@+id/nav_host_fragment"
        android:name="androidx.navigation.fragment.NavHostFragment"
        android:layout_width="0dp"
        android:layout_height="0dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:defaultNavHost="true"
        app:navGraph="@navigation/nav_graph" />

    <com.google.android.material.bottomnavigation.BottomNavigationView
        android:id="@+id/bottom_nav"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:menu="@menu/bottom_nav_menu" />

</androidx.constraintlayout.widget.ConstraintLayout>
```

---

## Bottom Navigation + NavController

```kotlin
// In MainActivity
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        val navController = navHostFragment.navController

        binding.bottomNav.setupWithNavController(navController)

        // Optional: handle reselection
        binding.bottomNav.setOnItemReselectedListener { /* no-op or scroll to top */ }
    }
}
```

### Bottom nav menu
```xml
<!-- res/menu/bottom_nav_menu.xml -->
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@+id/homeFragment"
        android:icon="@drawable/ic_home"
        android:title="@string/nav_home" />
    <item android:id="@+id/searchFragment"
        android:icon="@drawable/ic_search"
        android:title="@string/nav_search" />
    <item android:id="@+id/profileFragment"
        android:icon="@drawable/ic_profile"
        android:title="@string/nav_profile" />
</menu>
```

---

## Nested Nav Graphs

```xml
<navigation android:id="@+id/nav_graph" app:startDestination="@id/homeFragment">

    <fragment android:id="@+id/homeFragment" ... />

    <!-- Auth flow as nested graph -->
    <navigation android:id="@+id/auth_graph"
        app:startDestination="@id/loginFragment">

        <fragment android:id="@+id/loginFragment" ...>
            <action android:id="@+id/action_login_to_register"
                app:destination="@id/registerFragment" />
        </fragment>

        <fragment android:id="@+id/registerFragment" ... />
    </navigation>

    <!-- Navigate into nested graph -->
    <action android:id="@+id/action_global_to_auth"
        app:destination="@id/auth_graph"
        app:popUpTo="@id/nav_graph"
        app:popUpToInclusive="true" />
</navigation>
```

---

## Deep Links

```xml
<fragment android:id="@+id/detailFragment" ...>
    <deepLink
        android:id="@+id/deeplink_detail"
        app:uri="myapp://detail/{itemId}" />
</fragment>
```

In `AndroidManifest.xml`:
```xml
<activity android:name=".MainActivity">
    <nav-graph android:value="@navigation/nav_graph" />
</activity>
```

---

## Conditional Start Destination

```kotlin
// In MainActivity.onCreate after navController is set up
val graph = navController.navInflater.inflate(R.navigation.nav_graph)
graph.setStartDestination(
    if (userIsLoggedIn) R.id.homeFragment else R.id.loginFragment
)
navController.graph = graph
```

---

## Dialog Destination

```xml
<dialog
    android:id="@+id/confirmDialog"
    android:name="com.example.app.ui.ConfirmDialogFragment"
    android:label="Confirm">
    <argument android:name="message" app:argType="string" />
</dialog>
```

```kotlin
findNavController().navigate(
    HomeFragmentDirections.actionHomeToConfirmDialog(message = "Delete this item?")
)
```

---

## popUpTo (clear back stack)

```xml
<!-- After login success, pop everything and go to home -->
<action
    android:id="@+id/action_login_to_home"
    app:destination="@id/homeFragment"
    app:popUpTo="@id/nav_graph"
    app:popUpToInclusive="true" />
```

---

## Toolbar + Navigation

```kotlin
// In Fragment with Toolbar
val navController = findNavController()
val appBarConfig = AppBarConfiguration(navController.graph)
binding.toolbar.setupWithNavController(navController, appBarConfig)
```

For top-level destinations (no back arrow):
```kotlin
val appBarConfig = AppBarConfiguration(
    setOf(R.id.homeFragment, R.id.searchFragment, R.id.profileFragment)
)
```

---

## Version Catalog entries needed

```toml
[libraries]
navigation-fragment = { group = "androidx.navigation", name = "navigation-fragment-ktx", version.ref = "navigation" }
navigation-ui = { group = "androidx.navigation", name = "navigation-ui-ktx", version.ref = "navigation" }
navigation-testing = { group = "androidx.navigation", name = "navigation-testing", version.ref = "navigation" }

[plugins]
navigation-safeargs = { id = "androidx.navigation.safeargs.kotlin", version.ref = "navigation" }
```

`build.gradle.kts`:
```kotlin
plugins { alias(libs.plugins.navigation.safeargs) }
dependencies {
    implementation(libs.navigation.fragment)
    implementation(libs.navigation.ui)
    androidTestImplementation(libs.navigation.testing)
}
```
