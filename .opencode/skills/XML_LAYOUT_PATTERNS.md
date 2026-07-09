# Skill: XML Layout Patterns — Material 3, ConstraintLayout, RecyclerView

> Read this when generating UI layouts. All widgets are Material 3
> (`com.google.android.material.*`). Never Jetpack Compose.

---

## ConstraintLayout Recipes

### Basic constrained layout
```xml
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="16dp">

    <com.google.android.material.textview.MaterialTextView
        android:id="@+id/tv_screen_title"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:textAppearance="?attr/textAppearanceHeadlineMedium"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        android:text="@string/screen_title" />

</androidx.constraintlayout.widget.ConstraintLayout>
```

### Chain (distribute items evenly)
```xml
<!-- Horizontal chain: spread -->
<Button android:id="@+id/btn_cancel"
    app:layout_constraintHorizontal_chainStyle="spread"
    app:layout_constraintStart_toStartOf="parent"
    app:layout_constraintEnd_toStartOf="@id/btn_confirm" ... />

<Button android:id="@+id/btn_confirm"
    app:layout_constraintStart_toEndOf="@id/btn_cancel"
    app:layout_constraintEnd_toEndOf="parent" ... />
```

### Guideline
```xml
<androidx.constraintlayout.widget.Guideline
    android:id="@+id/guideline_half"
    android:orientation="vertical"
    app:layout_constraintGuide_percent="0.5" />
```

### Barrier
```xml
<androidx.constraintlayout.widget.Barrier
    android:id="@+id/barrier_labels_end"
    android:orientation="vertical"
    app:barrierDirection="end"
    app:constraint_referenced_ids="tv_label_1,tv_label_2,tv_label_3" />
```

### Percent dimensions
```xml
<View
    app:layout_constraintWidth_percent="0.7"
    android:layout_width="0dp"
    android:layout_height="wrap_content" ... />
```

---

## Common Screen Layouts

### List screen (Toolbar + RecyclerView + FAB)
```xml
<androidx.coordinatorlayout.widget.CoordinatorLayout
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <com.google.android.material.appbar.AppBarLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content">

        <com.google.android.material.appbar.MaterialToolbar
            android:id="@+id/toolbar_list"
            android:layout_width="match_parent"
            android:layout_height="?attr/actionBarSize"
            app:title="@string/list_title" />
    </com.google.android.material.appbar.AppBarLayout>

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/rv_list_items"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        app:layout_behavior="@string/appbar_scrolling_view_behavior"
        app:layoutManager="androidx.recyclerview.widget.LinearLayoutManager"
        tools:listitem="@layout/item_list" />

    <com.google.android.material.floatingactionbutton.FloatingActionButton
        android:id="@+id/fab_list_add"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_gravity="bottom|end"
        android:layout_margin="16dp"
        android:contentDescription="@string/add_item"
        app:srcCompat="@drawable/ic_add" />

</androidx.coordinatorlayout.widget.CoordinatorLayout>
```

### Form screen (scrollable inputs)
```xml
<androidx.core.widget.NestedScrollView
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:fillViewport="true">

    <androidx.constraintlayout.widget.ConstraintLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="16dp">

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/til_form_name"
            style="@style/Widget.Material3.TextInputLayout.OutlinedBox"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:hint="@string/form_name_hint"
            app:layout_constraintTop_toTopOf="parent"
            app:layout_constraintStart_toStartOf="parent"
            app:layout_constraintEnd_toEndOf="parent">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/et_form_name"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:inputType="textPersonName" />
        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/til_form_email"
            style="@style/Widget.Material3.TextInputLayout.OutlinedBox"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:hint="@string/form_email_hint"
            app:layout_constraintTop_toBottomOf="@id/til_form_name"
            app:layout_constraintStart_toStartOf="parent"
            app:layout_constraintEnd_toEndOf="parent"
            android:layout_marginTop="12dp">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/et_form_email"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:inputType="textEmailAddress" />
        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.button.MaterialButton
            android:id="@+id/btn_form_submit"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:text="@string/form_submit"
            android:layout_marginTop="24dp"
            app:layout_constraintTop_toBottomOf="@id/til_form_email"
            app:layout_constraintStart_toStartOf="parent"
            app:layout_constraintEnd_toEndOf="parent" />

    </androidx.constraintlayout.widget.ConstraintLayout>
</androidx.core.widget.NestedScrollView>
```

### Empty / Error state
```xml
<LinearLayout
    android:id="@+id/layout_empty_state"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:gravity="center"
    android:visibility="gone"
    app:layout_constraintTop_toTopOf="parent"
    app:layout_constraintBottom_toBottomOf="parent"
    app:layout_constraintStart_toStartOf="parent"
    app:layout_constraintEnd_toEndOf="parent">

    <ImageView
        android:layout_width="120dp"
        android:layout_height="120dp"
        android:src="@drawable/ic_empty_state"
        android:contentDescription="@null"
        android:importantForAccessibility="no" />

    <com.google.android.material.textview.MaterialTextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/empty_state_message"
        android:textAppearance="?attr/textAppearanceBodyLarge"
        android:layout_marginTop="16dp" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_empty_retry"
        style="@style/Widget.Material3.Button.TextButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/retry"
        android:layout_marginTop="8dp" />
</LinearLayout>
```

---

## RecyclerView + ListAdapter + DiffUtil

### Item layout
```xml
<!-- res/layout/item_list.xml -->
<com.google.android.material.card.MaterialCardView
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginHorizontal="16dp"
    android:layout_marginVertical="4dp"
    app:cardElevation="1dp"
    app:cardCornerRadius="12dp">

    <androidx.constraintlayout.widget.ConstraintLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="12dp">

        <com.google.android.material.imageview.ShapeableImageView
            android:id="@+id/iv_item_avatar"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:contentDescription="@string/item_avatar_desc"
            app:shapeAppearanceOverlay="@style/ShapeAppearance.Material3.Corner.Full"
            app:layout_constraintTop_toTopOf="parent"
            app:layout_constraintStart_toStartOf="parent" />

        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/tv_item_title"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:textAppearance="?attr/textAppearanceTitleMedium"
            android:layout_marginStart="12dp"
            app:layout_constraintTop_toTopOf="@id/iv_item_avatar"
            app:layout_constraintStart_toEndOf="@id/iv_item_avatar"
            app:layout_constraintEnd_toEndOf="parent"
            tools:text="Item Title" />

        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/tv_item_subtitle"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:textAppearance="?attr/textAppearanceBodyMedium"
            android:layout_marginStart="12dp"
            app:layout_constraintTop_toBottomOf="@id/tv_item_title"
            app:layout_constraintStart_toEndOf="@id/iv_item_avatar"
            app:layout_constraintEnd_toEndOf="parent"
            tools:text="Subtitle text" />

    </androidx.constraintlayout.widget.ConstraintLayout>
</com.google.android.material.card.MaterialCardView>
```

### ListAdapter + DiffUtil + ViewBinding
```kotlin
class <Name>Adapter(
    private val onItemClick: (String) -> Unit
) : ListAdapter<<Model>, <Name>Adapter.ViewHolder>(DiffCallback) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = Item<Name>Binding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(
        private val binding: Item<Name>Binding
    ) : RecyclerView.ViewHolder(binding.root) {

        init {
            binding.root.setOnClickListener {
                val position = bindingAdapterPosition
                if (position != RecyclerView.NO_POSITION) {
                    onItemClick(getItem(position).id)
                }
            }
        }

        fun bind(item: <Model>) {
            binding.tvItemTitle.text = item.name
            binding.tvItemSubtitle.text = item.description
            // Load image with Coil:
            // binding.ivItemAvatar.load(item.avatarUrl)
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<<Model>>() {
        override fun areItemsTheSame(old: <Model>, new: <Model>) = old.id == new.id
        override fun areContentsTheSame(old: <Model>, new: <Model>) = old == new
    }
}
```

### Wire in Fragment
```kotlin
private val adapter = <Name>Adapter { itemId ->
    val action = <Name>FragmentDirections.actionToDetail(itemId)
    findNavController().navigate(action)
}

override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
    super.onViewCreated(view, savedInstanceState)
    binding.rvListItems.adapter = adapter

    viewLifecycleOwner.lifecycleScope.launch {
        viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.items.collect { adapter.submitList(it) }
        }
    }
}
```

---

## Material 3 Components Cheatsheet

### Buttons
```xml
<!-- Filled (primary action) -->
<com.google.android.material.button.MaterialButton style="@style/Widget.Material3.Button" />
<!-- Outlined (secondary) -->
<com.google.android.material.button.MaterialButton style="@style/Widget.Material3.Button.OutlinedButton" />
<!-- Text (tertiary) -->
<com.google.android.material.button.MaterialButton style="@style/Widget.Material3.Button.TextButton" />
<!-- Icon button -->
<com.google.android.material.button.MaterialButton style="@style/Widget.Material3.Button.IconButton" app:icon="@drawable/ic_x" />
```

### Chips
```xml
<com.google.android.material.chip.ChipGroup android:id="@+id/chip_group_filters">
    <com.google.android.material.chip.Chip
        style="@style/Widget.Material3.Chip.Filter"
        android:text="@string/filter_all"
        android:checkable="true" />
</com.google.android.material.chip.ChipGroup>
```

### Bottom Sheet
```xml
<FrameLayout
    android:id="@+id/bottom_sheet"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    app:layout_behavior="com.google.android.material.bottomsheet.BottomSheetBehavior"
    app:behavior_peekHeight="80dp"
    app:behavior_hideable="true">
    <!-- content -->
</FrameLayout>
```

### Snackbar (from code)
```kotlin
Snackbar.make(binding.root, getString(R.string.item_deleted), Snackbar.LENGTH_LONG)
    .setAction(getString(R.string.undo)) { viewModel.undoDelete() }
    .show()
```

### Switch
```xml
<com.google.android.material.materialswitch.MaterialSwitch
    android:id="@+id/switch_notifications"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="@string/enable_notifications"
    android:minHeight="48dp" />
```

---

## Collapsing Toolbar

```xml
<androidx.coordinatorlayout.widget.CoordinatorLayout>
    <com.google.android.material.appbar.AppBarLayout
        android:layout_width="match_parent"
        android:layout_height="200dp">

        <com.google.android.material.appbar.CollapsingToolbarLayout
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            app:layout_scrollFlags="scroll|exitUntilCollapsed"
            app:contentScrim="?attr/colorSurface"
            app:title="@string/profile_title">

            <ImageView
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:scaleType="centerCrop"
                android:contentDescription="@string/header_image_desc"
                app:layout_collapseMode="parallax" />

            <com.google.android.material.appbar.MaterialToolbar
                android:id="@+id/toolbar"
                android:layout_width="match_parent"
                android:layout_height="?attr/actionBarSize"
                app:layout_collapseMode="pin" />
        </com.google.android.material.appbar.CollapsingToolbarLayout>
    </com.google.android.material.appbar.AppBarLayout>

    <androidx.core.widget.NestedScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        app:layout_behavior="@string/appbar_scrolling_view_behavior">
        <!-- content -->
    </androidx.core.widget.NestedScrollView>
</androidx.coordinatorlayout.widget.CoordinatorLayout>
```

---

## Dark Theme Resources

```
res/values/themes.xml         → Light theme (default)
res/values-night/themes.xml   → Dark theme overrides
res/values/colors.xml         → Semantic color names (color_surface, color_on_surface)
```

Use Material theme attributes (not hardcoded colors) so dark mode works automatically:
```xml
android:background="?attr/colorSurface"
android:textColor="?attr/colorOnSurface"
```

---

## Responsive Layouts

```
res/layout/fragment_home.xml           → Phone portrait (default)
res/layout-sw600dp/fragment_home.xml   → Tablet (master-detail side by side)
res/layout-land/fragment_home.xml      → Phone landscape (optional)
```

Use `0dp` + constraints instead of fixed widths to let layouts adapt.
