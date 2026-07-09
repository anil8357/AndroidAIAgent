# Skill: Security Patterns — Production Hardening

> Read this when implementing authentication, secure storage, certificate pinning,
> biometrics, or input validation.

---

## EncryptedSharedPreferences (Token/Secret Storage)

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object SecureStorageModule {

    @Provides
    @Singleton
    fun provideEncryptedPrefs(@ApplicationContext context: Context): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        return EncryptedSharedPreferences.create(
            context,
            "secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
}
```

### Token provider using encrypted prefs
```kotlin
class TokenProvider @Inject constructor(
    private val prefs: SharedPreferences
) {
    fun getAccessToken(): String? = prefs.getString("access_token", null)
    fun getRefreshToken(): String? = prefs.getString("refresh_token", null)

    fun saveTokens(access: String, refresh: String) {
        prefs.edit()
            .putString("access_token", access)
            .putString("refresh_token", refresh)
            .apply()
    }

    fun clearTokens() {
        prefs.edit().clear().apply()
    }
}
```

---

## Certificate Pinning (OkHttp)

```kotlin
val certificatePinner = CertificatePinner.Builder()
    .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .add("api.example.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")  // backup
    .build()

val okHttpClient = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```

> Get pin hashes: `openssl s_client -connect api.example.com:443 | openssl x509 -pubkey`
> then hash with SHA-256. Always include a backup pin.

---

## Network Security Config (XML)

```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <!-- Production: only trust system CAs + pin to your domain -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2025-12-31">
            <pin digest="SHA-256">AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</pin>
            <pin digest="SHA-256">BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=</pin>
        </pin-set>
    </domain-config>

    <!-- Debug: allow localhost cleartext for development proxy -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

In `AndroidManifest.xml`:
```xml
<application android:networkSecurityConfig="@xml/network_security_config" ...>
```

---

## BiometricPrompt Integration

```kotlin
class BiometricAuthHelper @Inject constructor(
    @ApplicationContext private val context: Context
) {
    fun canAuthenticate(): Boolean {
        val manager = BiometricManager.from(context)
        return manager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG) ==
            BiometricManager.BIOMETRIC_SUCCESS
    }

    fun showPrompt(
        fragment: Fragment,
        title: String,
        subtitle: String,
        onSuccess: () -> Unit,
        onError: (Int, String) -> Unit
    ) {
        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setNegativeButtonText(context.getString(R.string.biometric_cancel))
            .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
            .build()

        val biometricPrompt = BiometricPrompt(
            fragment,
            ContextCompat.getMainExecutor(context),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    onSuccess()
                }
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    onError(errorCode, errString.toString())
                }
                override fun onAuthenticationFailed() {
                    // Fingerprint not recognized — prompt stays open, user can retry
                }
            }
        )
        biometricPrompt.authenticate(promptInfo)
    }
}
```

---

## Input Validation / Sanitization

```kotlin
object InputValidator {
    private val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
    private val PHONE_REGEX = Regex("^\\+?[1-9]\\d{6,14}$")

    fun isValidEmail(input: String): Boolean = EMAIL_REGEX.matches(input.trim())

    fun isValidPhone(input: String): Boolean = PHONE_REGEX.matches(input.trim())

    fun isValidPassword(input: String): Boolean =
        input.length >= 8 &&
        input.any { it.isUpperCase() } &&
        input.any { it.isLowerCase() } &&
        input.any { it.isDigit() }

    /** Sanitize user input to prevent injection in queries/logs */
    fun sanitize(input: String): String =
        input.trim()
            .replace(Regex("[<>\"';&|]"), "")  // Strip dangerous chars
            .take(500)  // Limit length
}
```

### TextInputLayout validation in UI
```kotlin
private fun validateForm(): Boolean {
    var isValid = true

    if (!InputValidator.isValidEmail(binding.etFormEmail.text.toString())) {
        binding.tilFormEmail.error = getString(R.string.error_invalid_email)
        isValid = false
    } else {
        binding.tilFormEmail.error = null
    }

    if (!InputValidator.isValidPassword(binding.etFormPassword.text.toString())) {
        binding.tilFormPassword.error = getString(R.string.error_weak_password)
        isValid = false
    } else {
        binding.tilFormPassword.error = null
    }

    return isValid
}
```

---

## Auth Token Refresh (OkHttp Authenticator)

```kotlin
class TokenAuthenticator @Inject constructor(
    private val tokenProvider: TokenProvider,
    private val authApi: Lazy<AuthApi>  // Lazy to break circular dependency
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        // Prevent infinite retry loops
        if (response.request.header("X-Retry") != null) return null

        synchronized(this) {
            val refreshToken = tokenProvider.getRefreshToken() ?: return null
            val newTokens = runBlocking {
                try {
                    authApi.get().refreshToken(RefreshRequest(refreshToken))
                } catch (e: Exception) {
                    null
                }
            } ?: return null

            tokenProvider.saveTokens(newTokens.accessToken, newTokens.refreshToken)

            return response.request.newBuilder()
                .header("Authorization", "Bearer ${newTokens.accessToken}")
                .header("X-Retry", "true")
                .build()
        }
    }
}
```

Add to OkHttpClient:
```kotlin
OkHttpClient.Builder()
    .addInterceptor(authInterceptor)
    .authenticator(tokenAuthenticator)  // Called on 401
    .build()
```

---

## Secure WebView

```kotlin
webView.settings.apply {
    javaScriptEnabled = false          // Disable unless absolutely needed
    allowFileAccess = false
    allowContentAccess = false
    domStorageEnabled = false
    setSupportMultipleWindows(false)
}
// Always validate URLs before loading
if (url.startsWith("https://trusted-domain.com")) {
    webView.loadUrl(url)
}
```

---

## Version Catalog entries needed

```toml
[libraries]
security-crypto = { group = "androidx.security", name = "security-crypto", version.ref = "securityCrypto" }
biometric = { group = "androidx.biometric", name = "biometric", version.ref = "biometric" }
```
