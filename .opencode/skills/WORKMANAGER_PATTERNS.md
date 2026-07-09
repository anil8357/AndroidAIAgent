# Skill: WorkManager — Background Work Patterns

> Read this when generating background tasks (sync, upload, periodic cleanup, notifications).
> WorkManager is the only acceptable background-work API (no AlarmManager, no JobScheduler
> directly, no foreground-service-for-work hacks).

---

## Simple OneTimeWorkRequest

```kotlin
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val repository: DataRepository
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            repository.syncToServer()
            Result.success()
        } catch (e: IOException) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        } catch (e: Exception) {
            Result.failure(workDataOf("error" to e.message))
        }
    }

    companion object {
        const val WORK_NAME = "sync_work"
    }
}
```

---

## Hilt Worker Injection (@HiltWorker)

```kotlin
@HiltWorker
class UploadWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val api: UploadApi
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val filePath = inputData.getString("file_path") ?: return Result.failure()
        return try {
            api.uploadFile(File(filePath))
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
```

Required Hilt setup (once per app):
```kotlin
// Application class
@HiltAndroidApp
class MyApp : Application(), Configuration.Provider {
    @Inject lateinit var workerFactory: HiltWorkerFactory

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
```

In `AndroidManifest.xml` — disable default initializer:
```xml
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    tools:node="merge">
    <meta-data
        android:name="androidx.work.WorkManagerInitializer"
        android:value="androidx.startup"
        tools:node="remove" />
</provider>
```

---

## PeriodicWorkRequest

```kotlin
fun schedulePeriodicSync(context: Context) {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .setRequiresBatteryNotLow(true)
        .build()

    val request = PeriodicWorkRequestBuilder<SyncWorker>(
        repeatInterval = 6, repeatIntervalTimeUnit = TimeUnit.HOURS,
        flexTimeInterval = 30, flexTimeIntervalUnit = TimeUnit.MINUTES
    )
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 15, TimeUnit.MINUTES)
        .addTag("periodic_sync")
        .build()

    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        SyncWorker.WORK_NAME,
        ExistingPeriodicWorkPolicy.KEEP,  // Don't replace if already scheduled
        request
    )
}
```

---

## Constraints

```kotlin
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.CONNECTED)      // Needs internet
    .setRequiresCharging(true)                          // Only when charging
    .setRequiresBatteryNotLow(true)                     // Not low battery
    .setRequiresStorageNotLow(true)                     // Not low storage
    .setRequiresDeviceIdle(true)                        // API 23+ only when idle
    .build()
```

---

## Chaining Workers

```kotlin
fun startUploadChain(context: Context, filePaths: List<String>) {
    val compressWork = OneTimeWorkRequestBuilder<CompressWorker>()
        .setInputData(workDataOf("files" to filePaths.toTypedArray()))
        .build()

    val uploadWork = OneTimeWorkRequestBuilder<UploadWorker>()
        .setConstraints(Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build())
        .build()

    val cleanupWork = OneTimeWorkRequestBuilder<CleanupWorker>().build()

    WorkManager.getInstance(context)
        .beginUniqueWork("upload_chain", ExistingWorkPolicy.REPLACE, compressWork)
        .then(uploadWork)
        .then(cleanupWork)
        .enqueue()
}
```

---

## Passing Data (Input/Output)

```kotlin
// Enqueue with input
val request = OneTimeWorkRequestBuilder<UploadWorker>()
    .setInputData(workDataOf(
        "file_path" to "/path/to/file.jpg",
        "user_id" to "123"
    ))
    .build()

// Read input in Worker
override suspend fun doWork(): Result {
    val path = inputData.getString("file_path")!!
    val userId = inputData.getString("user_id")!!
    // ...
    return Result.success(workDataOf("upload_url" to resultUrl))
}
```

---

## Observing Work Status from UI

```kotlin
// In ViewModel
class UploadViewModel @Inject constructor(
    private val workManager: WorkManager
) : ViewModel() {

    val uploadStatus: Flow<WorkInfo?> =
        workManager.getWorkInfoByIdFlow(uploadWorkId)
            .map { it }

    fun startUpload(filePath: String) {
        val request = OneTimeWorkRequestBuilder<UploadWorker>()
            .setInputData(workDataOf("file_path" to filePath))
            .build()
        uploadWorkId = request.id
        workManager.enqueue(request)
    }

    private var uploadWorkId: UUID = UUID.randomUUID()
}

// In Fragment
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uploadStatus.collect { workInfo ->
            when (workInfo?.state) {
                WorkInfo.State.RUNNING -> showProgress()
                WorkInfo.State.SUCCEEDED -> showSuccess()
                WorkInfo.State.FAILED -> showError(workInfo.outputData.getString("error"))
                else -> { /* ENQUEUED, BLOCKED, CANCELLED */ }
            }
        }
    }
}
```

---

## Expedited Work (high-priority, time-sensitive)

```kotlin
val request = OneTimeWorkRequestBuilder<CriticalSyncWorker>()
    .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
    .build()
WorkManager.getInstance(context).enqueue(request)
```

Worker must implement `getForegroundInfo()`:
```kotlin
override suspend fun getForegroundInfo(): ForegroundInfo {
    val notification = NotificationCompat.Builder(applicationContext, "sync_channel")
        .setContentTitle("Syncing...")
        .setSmallIcon(R.drawable.ic_sync)
        .build()
    return ForegroundInfo(NOTIFICATION_ID, notification)
}
```

---

## Version Catalog entries needed

```toml
[libraries]
work-runtime = { group = "androidx.work", name = "work-runtime-ktx", version.ref = "work" }
work-testing = { group = "androidx.work", name = "work-testing", version.ref = "work" }
hilt-work = { group = "androidx.hilt", name = "hilt-work", version.ref = "hiltWork" }
hilt-work-compiler = { group = "androidx.hilt", name = "hilt-compiler", version.ref = "hiltWork" }
```

```kotlin
dependencies {
    implementation(libs.work.runtime)
    implementation(libs.hilt.work)
    ksp(libs.hilt.work.compiler)
    androidTestImplementation(libs.work.testing)
}
```
