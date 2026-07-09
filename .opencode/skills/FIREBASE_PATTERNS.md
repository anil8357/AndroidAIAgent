# Skill: Firebase — FCM, Crashlytics, Remote Config, Analytics

> Read this when integrating Firebase services. All deps via Version Catalog.
> Use the Firebase BoM for version alignment.

---

## Firebase BoM + Version Catalog

```toml
[versions]
firebase-bom = "33.7.0"

[libraries]
firebase-bom = { group = "com.google.firebase", name = "firebase-bom", version.ref = "firebase-bom" }
firebase-messaging = { group = "com.google.firebase", name = "firebase-messaging-ktx" }
firebase-crashlytics = { group = "com.google.firebase", name = "firebase-crashlytics-ktx" }
firebase-analytics = { group = "com.google.firebase", name = "firebase-analytics-ktx" }
firebase-config = { group = "com.google.firebase", name = "firebase-config-ktx" }

[plugins]
google-services = { id = "com.google.gms.google-services", version = "4.4.2" }
firebase-crashlytics-plugin = { id = "com.google.firebase.crashlytics", version = "3.0.2" }
```

```kotlin
// build.gradle.kts (app)
plugins {
    alias(libs.plugins.google.services)
    alias(libs.plugins.firebase.crashlytics.plugin)
}
dependencies {
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.messaging)
    implementation(libs.firebase.crashlytics)
    implementation(libs.firebase.analytics)
    implementation(libs.firebase.config)
}
```

---

## FCM — Push Notifications

### Service
```kotlin
class AppFirebaseMessagingService : FirebaseMessagingService() {

    @Inject lateinit var tokenRepository: TokenRepository

    override fun onNewToken(token: String) {
        // Send to your backend
        CoroutineScope(Dispatchers.IO).launch {
            tokenRepository.updateFcmToken(token)
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val title = message.notification?.title ?: message.data["title"] ?: return
        val body = message.notification?.body ?: message.data["body"] ?: ""
        val deepLink = message.data["deep_link"]

        showNotification(title, body, deepLink)
    }

    private fun showNotification(title: String, body: String, deepLink: String?) {
        val channelId = getString(R.string.notification_channel_id)

        val intent = deepLink?.let {
            Intent(Intent.ACTION_VIEW, Uri.parse(it))
        } ?: Intent(this, MainActivity::class.java)

        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
```

### Notification Channel (create in Application or MainActivity)
```kotlin
private fun createNotificationChannel() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(
            getString(R.string.notification_channel_id),
            getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = getString(R.string.notification_channel_desc)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }
}
```

### Manifest
```xml
<service
    android:name=".service.AppFirebaseMessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

### Get current token
```kotlin
suspend fun getCurrentFcmToken(): String? = suspendCancellableCoroutine { cont ->
    FirebaseMessaging.getInstance().token
        .addOnSuccessListener { cont.resume(it) }
        .addOnFailureListener { cont.resume(null) }
}
```

---

## Crashlytics

### Initialize + custom keys
```kotlin
// Set user identifier for crash reports
FirebaseCrashlytics.getInstance().setUserId(userId)

// Add custom keys for debugging
FirebaseCrashlytics.getInstance().setCustomKey("screen", "HomeFragment")
FirebaseCrashlytics.getInstance().setCustomKey("user_type", "premium")

// Log non-fatal exceptions
try {
    riskyOperation()
} catch (e: Exception) {
    FirebaseCrashlytics.getInstance().recordException(e)
}

// Log breadcrumbs
FirebaseCrashlytics.getInstance().log("User tapped checkout with ${items.size} items")
```

### Opt-out (GDPR compliance)
```kotlin
FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(userConsented)
```

---

## Remote Config

```kotlin
class RemoteConfigManager @Inject constructor() {

    private val remoteConfig = Firebase.remoteConfig

    init {
        val configSettings = remoteConfigSettings {
            minimumFetchIntervalInSeconds = if (BuildConfig.DEBUG) 0 else 3600
        }
        remoteConfig.setConfigSettingsAsync(configSettings)
        remoteConfig.setDefaultsAsync(R.xml.remote_config_defaults)
    }

    suspend fun fetchAndActivate(): Boolean = suspendCancellableCoroutine { cont ->
        remoteConfig.fetchAndActivate()
            .addOnSuccessListener { cont.resume(it) }
            .addOnFailureListener { cont.resume(false) }
    }

    fun getString(key: String): String = remoteConfig.getString(key)
    fun getBoolean(key: String): Boolean = remoteConfig.getBoolean(key)
    fun getLong(key: String): Long = remoteConfig.getLong(key)
}
```

### Default values (`res/xml/remote_config_defaults.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<defaultsMap>
    <entry>
        <key>feature_new_ui_enabled</key>
        <value>false</value>
    </entry>
    <entry>
        <key>min_app_version</key>
        <value>1.0.0</value>
    </entry>
    <entry>
        <key>api_timeout_seconds</key>
        <value>30</value>
    </entry>
</defaultsMap>
```

---

## Analytics — Event Logging

```kotlin
class AnalyticsHelper @Inject constructor() {

    private val analytics = Firebase.analytics

    fun logScreenView(screenName: String, screenClass: String) {
        analytics.logEvent(FirebaseAnalytics.Event.SCREEN_VIEW) {
            param(FirebaseAnalytics.Param.SCREEN_NAME, screenName)
            param(FirebaseAnalytics.Param.SCREEN_CLASS, screenClass)
        }
    }

    fun logButtonClick(buttonName: String, screen: String) {
        analytics.logEvent("button_click") {
            param("button_name", buttonName)
            param("screen", screen)
        }
    }

    fun logPurchase(itemId: String, price: Double, currency: String) {
        analytics.logEvent(FirebaseAnalytics.Event.PURCHASE) {
            param(FirebaseAnalytics.Param.ITEM_ID, itemId)
            param(FirebaseAnalytics.Param.PRICE, price)
            param(FirebaseAnalytics.Param.CURRENCY, currency)
        }
    }

    fun setUserProperty(key: String, value: String) {
        analytics.setUserProperty(key, value)
    }
}
```

---

## Key Rules

- Always use the **Firebase BoM** — never specify individual Firebase library versions.
- FCM token can change at any time — always handle `onNewToken` and sync to backend.
- Create notification channels on app start (API 26+ requirement).
- Request `POST_NOTIFICATIONS` permission on Android 13+ before showing notifications.
- Remote Config defaults must cover every key — the app must work offline.
- Analytics: no PII in event parameters (no emails, phone numbers, names).
- Crashlytics: respect user opt-out (GDPR); disable collection if consent denied.
