# Skill: Runtime Permissions — ActivityResult Patterns

> Read this when implementing camera, location, storage, notifications, or any
> runtime permission flow. Uses the modern ActivityResultContracts API only.

---

## Single Permission Request

```kotlin
@AndroidEntryPoint
class CameraFragment : Fragment(R.layout.fragment_camera) {

    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            openCamera()
        } else {
            showPermissionDeniedMessage()
        }
    }

    private fun requestCameraPermission() {
        when {
            ContextCompat.checkSelfPermission(
                requireContext(), Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED -> {
                openCamera()
            }
            shouldShowRequestPermissionRationale(Manifest.permission.CAMERA) -> {
                showRationale(
                    message = getString(R.string.camera_rationale),
                    onAccept = { cameraPermissionLauncher.launch(Manifest.permission.CAMERA) }
                )
            }
            else -> {
                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }
    }

    private fun openCamera() { /* launch camera */ }

    private fun showPermissionDeniedMessage() {
        Snackbar.make(binding.root, getString(R.string.camera_denied), Snackbar.LENGTH_LONG)
            .setAction(getString(R.string.settings)) { openAppSettings() }
            .show()
    }
}
```

---

## Multiple Permissions Request

```kotlin
private val locationPermissionLauncher = registerForActivityResult(
    ActivityResultContracts.RequestMultiplePermissions()
) { permissions ->
    val fineGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
    val coarseGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true

    when {
        fineGranted -> startPreciseLocationUpdates()
        coarseGranted -> startApproximateLocationUpdates()
        else -> showLocationDeniedMessage()
    }
}

private fun requestLocationPermissions() {
    locationPermissionLauncher.launch(
        arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
    )
}
```

---

## Permission Rationale Dialog

```kotlin
private fun showRationale(message: String, onAccept: () -> Unit) {
    MaterialAlertDialogBuilder(requireContext())
        .setTitle(getString(R.string.permission_needed))
        .setMessage(message)
        .setPositiveButton(getString(R.string.grant)) { _, _ -> onAccept() }
        .setNegativeButton(getString(R.string.deny)) { dialog, _ -> dialog.dismiss() }
        .show()
}
```

---

## Redirect to App Settings (permanent denial)

```kotlin
private fun openAppSettings() {
    Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.fromParts("package", requireContext().packageName, null)
        startActivity(this)
    }
}
```

---

## Notification Permission (Android 13+ / API 33)

```kotlin
private val notificationPermissionLauncher = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
) { isGranted ->
    if (isGranted) {
        // Notifications enabled
    } else {
        // Show explanation that notifications are off
    }
}

private fun requestNotificationPermission() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        when {
            ContextCompat.checkSelfPermission(
                requireContext(), Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED -> { /* already granted */ }
            shouldShowRequestPermissionRationale(Manifest.permission.POST_NOTIFICATIONS) -> {
                showRationale(getString(R.string.notification_rationale)) {
                    notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                }
            }
            else -> {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
}
```

---

## Photo/Media Picker (Android 13+ scoped, no READ_EXTERNAL_STORAGE)

```kotlin
private val pickMediaLauncher = registerForActivityResult(
    ActivityResultContracts.PickVisualMedia()
) { uri ->
    uri?.let { handleSelectedImage(it) }
}

private fun pickPhoto() {
    pickMediaLauncher.launch(
        PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
    )
}
```

For older APIs (< 13) that still need `READ_EXTERNAL_STORAGE`:
```kotlin
private val storagePermissionLauncher = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
) { isGranted ->
    if (isGranted) openGallery()
}

private fun requestStorageIfNeeded() {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
        storagePermissionLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
    } else {
        pickPhoto()  // No permission needed on 13+
    }
}
```

---

## Take Photo (Camera + File Provider)

```kotlin
private var photoUri: Uri? = null

private val takePictureLauncher = registerForActivityResult(
    ActivityResultContracts.TakePicture()
) { success ->
    if (success) photoUri?.let { handleCapturedPhoto(it) }
}

private fun takePhoto() {
    val photoFile = File.createTempFile("photo_", ".jpg", requireContext().cacheDir)
    photoUri = FileProvider.getUriForFile(
        requireContext(),
        "${requireContext().packageName}.fileprovider",
        photoFile
    )
    takePictureLauncher.launch(photoUri!!)
}
```

FileProvider in `AndroidManifest.xml`:
```xml
<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths" />
</provider>
```

`res/xml/file_paths.xml`:
```xml
<paths>
    <cache-path name="cache" path="." />
    <files-path name="files" path="." />
</paths>
```

---

## Permission Utility Extension

```kotlin
fun Fragment.hasPermission(permission: String): Boolean =
    ContextCompat.checkSelfPermission(requireContext(), permission) ==
        PackageManager.PERMISSION_GRANTED

fun Fragment.shouldShowRationale(permission: String): Boolean =
    shouldShowRequestPermissionRationale(permission)
```

---

## Manifest Declarations

```xml
<!-- Camera -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera" android:required="false" />

<!-- Location -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<!-- Notifications (Android 13+) -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

<!-- Storage (legacy, < API 33 only) -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
```
