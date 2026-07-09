# Skill: Gradle, KSP, Dependencies & Configuration

> Read this when generating build configuration, adding dependencies, or setting up
> annotation processing. Also contains accessibility and ViewBinding lifecycle rules.

---

## Annotation Processing — KSP Only

**KSP (Kotlin Symbol Processing) is mandatory** for Hilt and Room.
Never use `kapt(...)` — it's deprecated and slower.

```kotlin
// build.gradle.kts (module)
plugins {
    id("com.google.devtools.ksp")
}

dependencies {
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    implementation(libs.gson)
}
```

---

## Dependency Management — Version Catalog (`gradle/libs.versions.toml`)

All dependencies **must** be declared in `gradle/libs.versions.toml` first, then
referenced as `libs.*` accessors. Raw `group:artifact:version` strings in build files
are **prohibited**.

### Adding a new dependency (step-by-step)

> Versions below are shown as `<…>` placeholders on purpose — resolve the real values from
> the project's existing catalog or via `context7` (see "Getting Versions & Coordinates Right").

1. Add the version key:
```toml
[versions]
hilt = "<resolved hilt version>"
```

2. Add the library alias:
```toml
[libraries]
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }
```

3. Add the plugin alias (if needed):
```toml
[plugins]
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
# KSP version MUST track the project's Kotlin version (form: <kotlin>-<ksp>)
ksp = { id = "com.google.devtools.ksp", version = "<kotlin>-<ksp>" }
```

4. Reference in `build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
}
dependencies {
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
```

---

## Getting Versions & Coordinates Right (never invent them)

There is **no pinned version list here on purpose** — a hardcoded list goes stale and becomes
the next source of wrong versions. Resolve every version, coordinate, plugin id, and import
at generation time using the **Dependency & Build Integrity Protocol** (see `coder.md`).
In short:

1. **Reuse the project first.** Read the project's existing `gradle/libs.versions.toml` and
   build files. If a library/plugin is already declared, reuse its exact alias and version.
   Match the project's existing `kotlin`/`agp`/`hilt`/`lifecycle` versions rather than adding
   new ones.
2. **Look up anything new via `context7` MCP** — the correct `group:artifact` coordinate, a
   compatible stable version, and the right import paths. Don't recall these from memory.
3. **Let Gradle resolve/verify.** The `@coder` Verification Loop compiles; Gradle fails fast
   on a bad coordinate/version. Fix from ground truth, not another guess.

### The alias shape (structure is stable; only values are looked up)

```toml
[versions]
<name> = "<resolved version>"          # e.g. from the project or context7

[libraries]
<alias> = { group = "<group>", name = "<artifact>", version.ref = "<name>" }

[plugins]
<alias> = { id = "<plugin.id>", version.ref = "<name>" }
```

Reference in `build.gradle.kts` as `libs.<alias>` (dashes → dots) and
`libs.plugins.<alias>`.

### Version-agnostic consistency invariants (verify every time)

- Every `version.ref = "x"` has a matching `[versions] x = "…"` key — no dangling refs.
- Every `libs.*` accessor used in a build file maps to a real `[libraries]`/`[plugins]` entry.
- The **KSP plugin version tracks the Kotlin version** (KSP is `<kotlin>-<ksp>`); never pair
  a KSP version with a mismatched Kotlin version.
- Any module with a `ksp(...)` or Hilt/SafeArgs dependency **applies the matching plugin**.
- Annotation processors use `ksp(...)`, never `kapt(...)`.

> If you cannot confirm a coordinate/version from the project or `context7`, and there is no
> Gradle wrapper to resolve it, **state the dependency you need and ask** — do not fabricate a
> plausible version.

---

## ViewBinding Lifecycle Discipline

### Fragment pattern (mandatory)
```kotlin
private var _binding: FragmentXxxBinding? = null
private val binding get() = _binding!!

override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
    super.onViewCreated(view, savedInstanceState)
    _binding = FragmentXxxBinding.bind(view)
}

override fun onDestroyView() {
    super.onDestroyView()
    _binding = null   // MANDATORY — prevents leaks
}
```

### Rules
- Binding is ONLY accessed between `onViewCreated` and `onDestroyView`
- Never store binding in a ViewModel or companion object
- Never use `findViewById` — always `binding.viewId`
- Binding class name is derived from layout: `fragment_login.xml` → `FragmentLoginBinding`

---

## Accessibility

### Non-decorative images
```xml
<ImageView
    android:contentDescription="@string/profile_avatar_description"
    ... />
```
The `contentDescription` must name the **purpose or action**, not appearance.

### Decorative images
```xml
<ImageView
    android:contentDescription="@null"
    android:importantForAccessibility="no"
    ... />
```

### Touch targets
All interactive elements must be **48dp × 48dp minimum**:
```xml
<ImageButton
    android:minWidth="48dp"
    android:minHeight="48dp"
    ... />
```
If the visual size must be smaller, expand the touch target with padding or `TouchDelegate`.

---

## SDK Versions

```kotlin
android {
    compileSdk = 35
    defaultConfig {
        minSdk = 24
        targetSdk = 35
    }
}
```

APIs at level 24 and below are always safe. Check API level before using 25+:
```kotlin
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
    // NotificationChannel (API 26+)
}
```
