# Skill: ProGuard/R8, Signing & Release — Shipping to Play Store

> Read this when configuring build variants, signing, R8 rules, or preparing a release build.

---

## Build Variants & Flavors

```kotlin
// build.gradle.kts (app module)
android {
    buildTypes {
        debug {
            isDebuggable = true
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            buildConfigField("String", "BASE_URL", "\"https://api-dev.example.com/\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            buildConfigField("String", "BASE_URL", "\"https://api.example.com/\"")
        }
    }

    flavorDimensions += "environment"
    productFlavors {
        create("dev") {
            dimension = "environment"
            applicationIdSuffix = ".dev"
            buildConfigField("String", "BASE_URL", "\"https://api-dev.example.com/\"")
        }
        create("staging") {
            dimension = "environment"
            applicationIdSuffix = ".staging"
            buildConfigField("String", "BASE_URL", "\"https://api-staging.example.com/\"")
        }
        create("prod") {
            dimension = "environment"
            buildConfigField("String", "BASE_URL", "\"https://api.example.com/\"")
        }
    }
}
```

---

## Signing Configuration

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("KEYSTORE_PATH") ?: "keystore/release.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD") ?: ""
            keyAlias = System.getenv("KEY_ALIAS") ?: ""
            keyPassword = System.getenv("KEY_PASSWORD") ?: ""
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

> NEVER hardcode keystore passwords in build files. Use environment variables or
> `local.properties` (gitignored).

---

## R8/ProGuard Rules

### Base rules (`proguard-rules.pro`)
```proguard
# Keep app entry points
-keep class com.example.app.** { *; }

# Keep Parcelable
-keepclassmembers class * implements android.os.Parcelable {
    public static final ** CREATOR;
}

# Keep enums
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
```

### Retrofit + OkHttp
```proguard
# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepattributes Signature
-keepattributes Exceptions

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }
```

### Gson
```proguard
# Gson
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
# Keep data classes used with Gson (annotated with @SerializedName)
-keepclassmembers,allowobfuscation class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
```

### Room
```proguard
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**
```

### Hilt
```proguard
# Hilt (most rules auto-applied by the plugin, but keep these for safety)
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }
-keep class * extends dagger.hilt.android.internal.managers.ViewComponentManager$FragmentContextWrapper
```

### Navigation SafeArgs
```proguard
-keep class * extends androidx.navigation.NavArgs
```

### Coroutines
```proguard
-dontwarn kotlinx.coroutines.**
-keep class kotlinx.coroutines.** { *; }
```

---

## Baseline Profile (startup optimization)

```kotlin
// app/src/main/baseline-prof.txt
// Critical startup path classes
HSPLcom/example/app/MainActivity;->onCreate(Landroid/os/Bundle;)V
HSPLcom/example/app/ui/home/HomeFragment;->onViewCreated(Landroid/view/View;Landroid/os/Bundle;)V
HSPLcom/example/app/ui/home/HomeViewModel;-><init>(Lcom/example/app/domain/usecase/GetItemsUseCase;)V
```

For automated baseline profiles:
```kotlin
// build.gradle.kts
dependencies {
    implementation(libs.profileinstaller)
    baselineProfile(project(":baselineprofile"))
}
```

---

## APK Size Reduction

```kotlin
android {
    buildTypes {
        release {
            isMinifyEnabled = true       // R8 code shrinking
            isShrinkResources = true     // Remove unused resources
        }
    }

    // Split APKs by ABI (reduces per-device download size)
    splits {
        abi {
            isEnable = true
            reset()
            include("armeabi-v7a", "arm64-v8a", "x86", "x86_64")
            isUniversalApk = false
        }
    }

    // Remove unused languages
    defaultConfig {
        resourceConfigurations += listOf("en", "hi")  // keep only needed locales
    }
}
```

---

## App Bundle (AAB) for Play Store

```bash
# Build release bundle
./gradlew bundleRelease

# Output: app/build/outputs/bundle/release/app-release.aab
```

> Google Play requires AAB (not APK) for new apps. APK generation via `bundletool` for
> local testing only.

---

## Version Management

```kotlin
android {
    defaultConfig {
        versionCode = System.getenv("VERSION_CODE")?.toIntOrNull() ?: 1
        versionName = System.getenv("VERSION_NAME") ?: "1.0.0"
    }
}
```

Or from a version file:
```kotlin
val versionProps = Properties().apply {
    load(rootProject.file("version.properties").inputStream())
}
android {
    defaultConfig {
        versionCode = versionProps["VERSION_CODE"].toString().toInt()
        versionName = versionProps["VERSION_NAME"].toString()
    }
}
```
