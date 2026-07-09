# Skill: CI/CD — GitHub Actions for Android

> Read this when setting up CI/CD pipelines, PR checks, or release automation.
> Adapt for GitLab CI / Bitrise / other CI by translating the workflow steps.

---

## PR Check Workflow (compile + unit test + lint)

```yaml
# .github/workflows/pr-check.yml
name: PR Check

on:
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties', '**/libs.versions.toml') }}
          restore-keys: gradle-${{ runner.os }}-

      - name: Grant execute permission
        run: chmod +x gradlew

      - name: Compile
        run: ./gradlew assembleDebug --no-daemon

      - name: Unit Tests
        run: ./gradlew testDebugUnitTest --no-daemon

      - name: Lint
        run: ./gradlew lintDebug --no-daemon

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: app/build/reports/tests/
          retention-days: 7

      - name: Upload lint report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: lint-report
          path: app/build/reports/lint-results-debug.html
          retention-days: 7
```

---

## Release Build Workflow (signed AAB + APK artifact)

```yaml
# .github/workflows/release.yml
name: Release Build

on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}

      - name: Decode keystore
        run: echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > app/release.jks

      - name: Build Release AAB
        env:
          KEYSTORE_PATH: release.jks
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
        run: ./gradlew bundleRelease --no-daemon

      - name: Build Release APK
        env:
          KEYSTORE_PATH: release.jks
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
        run: ./gradlew assembleRelease --no-daemon

      - name: Upload AAB
        uses: actions/upload-artifact@v4
        with:
          name: release-aab
          path: app/build/outputs/bundle/release/*.aab

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: release-apk
          path: app/build/outputs/apk/release/*.apk

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/build/outputs/bundle/release/*.aab
            app/build/outputs/apk/release/*.apk
```

---

## Instrumented Test Workflow (emulator)

```yaml
# .github/workflows/instrumented-tests.yml
name: Instrumented Tests

on:
  pull_request:
    branches: [main]
    paths: ['app/src/androidTest/**', 'app/src/main/**']

jobs:
  instrumented:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    strategy:
      matrix:
        api-level: [29, 34]

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*') }}

      - name: AVD cache
        uses: actions/cache@v4
        id: avd-cache
        with:
          path: |
            ~/.android/avd/*
            ~/.android/adb*
          key: avd-${{ matrix.api-level }}

      - name: Run instrumented tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: ${{ matrix.api-level }}
          arch: x86_64
          disable-animations: true
          script: ./gradlew connectedDebugAndroidTest --no-daemon

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: instrumented-results-api${{ matrix.api-level }}
          path: app/build/reports/androidTests/
```

---

## Secrets to Configure (in GitHub Settings → Secrets)

| Secret | Purpose |
|---|---|
| `KEYSTORE_BASE64` | Release keystore file, base64-encoded: `base64 -i release.jks` |
| `KEYSTORE_PASSWORD` | Keystore password |
| `KEY_ALIAS` | Key alias name |
| `KEY_PASSWORD` | Key password |

---

## Branch Protection Rules (recommended)

```
main branch:
  ✅ Require PR reviews (1+)
  ✅ Require status checks: "build-and-test"
  ✅ Require branches to be up to date
  ✅ No force push
  ✅ No deletion

develop branch:
  ✅ Require status checks: "build-and-test"
```

---

## Fastlane (Play Store upload — optional)

```ruby
# fastlane/Fastfile
default_platform(:android)

platform :android do
  desc "Deploy to Play Store internal track"
  lane :deploy_internal do
    gradle(task: "bundleRelease")
    upload_to_play_store(
      track: "internal",
      aab: "app/build/outputs/bundle/release/app-release.aab",
      skip_upload_metadata: true,
      skip_upload_images: true,
      skip_upload_screenshots: true
    )
  end
end
```

---

## Key Practices

- **Never commit secrets** — use GitHub Secrets or environment variables.
- **Cache Gradle** — saves 2-5 minutes per run.
- **Cancel in-progress** — `concurrency` with `cancel-in-progress: true` prevents queue pileup.
- **Fail fast** — upload artifacts only on failure for debugging.
- **Matrix test** — run instrumented tests on min and target API levels.
- **Tag-triggered releases** — push `v1.2.3` tag to trigger the release build automatically.
