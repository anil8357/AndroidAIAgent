# Skill: Room Database — Persistence Patterns

> Read this when generating local database code (entities, DAOs, database class,
> migrations, Hilt wiring). All dependencies via Version Catalog.

---

## Entity

```kotlin
@Entity(tableName = "<name>s")
data class <Name>Entity(
    @PrimaryKey
    @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "name") val name: String,
    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "is_synced") val isSynced: Boolean = false
)
```

### Entity with relation (foreign key)
```kotlin
@Entity(
    tableName = "comments",
    foreignKeys = [
        ForeignKey(
            entity = PostEntity::class,
            parentColumns = ["id"],
            childColumns = ["post_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("post_id")]
)
data class CommentEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "post_id") val postId: String,
    @ColumnInfo(name = "body") val body: String
)
```

### Embedded object
```kotlin
data class Address(
    val street: String,
    val city: String,
    val zipCode: String
)

@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val name: String,
    @Embedded(prefix = "addr_") val address: Address
)
```

### Type Converter
```kotlin
class Converters {
    @TypeConverter
    fun fromStringList(value: List<String>): String = value.joinToString(",")

    @TypeConverter
    fun toStringList(value: String): List<String> =
        if (value.isBlank()) emptyList() else value.split(",")

    @TypeConverter
    fun fromDate(date: Date?): Long? = date?.time

    @TypeConverter
    fun toDate(timestamp: Long?): Date? = timestamp?.let { Date(it) }
}
```

---

## DAO

```kotlin
@Dao
interface <Name>Dao {

    // --- Queries (return Flow for reactive UI) ---

    @Query("SELECT * FROM <name>s ORDER BY created_at DESC")
    fun observeAll(): Flow<List<<Name>Entity>>

    @Query("SELECT * FROM <name>s WHERE id = :id")
    fun observeById(id: String): Flow<<Name>Entity?>

    @Query("SELECT * FROM <name>s WHERE id = :id")
    suspend fun getById(id: String): <Name>Entity?

    @Query("SELECT * FROM <name>s WHERE name LIKE '%' || :query || '%'")
    fun search(query: String): Flow<List<<Name>Entity>>

    @Query("SELECT COUNT(*) FROM <name>s")
    suspend fun count(): Int

    // --- Writes ---

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: <Name>Entity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(entities: List<<Name>Entity>)

    @Update
    suspend fun update(entity: <Name>Entity)

    @Delete
    suspend fun delete(entity: <Name>Entity)

    @Query("DELETE FROM <name>s WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM <name>s")
    suspend fun deleteAll()

    // --- Transaction (multi-table atomic operation) ---

    @Transaction
    suspend fun replaceAll(entities: List<<Name>Entity>) {
        deleteAll()
        insertAll(entities)
    }
}
```

---

## Database Class

```kotlin
@Database(
    entities = [
        <Name>Entity::class,
        // Add more entities here
    ],
    version = 1,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun <name>Dao(): <Name>Dao
}
```

---

## Hilt Module (Database Wiring)

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app_database")
            .addMigrations(MIGRATION_1_2)
            .build()

    @Provides
    fun provide<Name>Dao(db: AppDatabase): <Name>Dao = db.<name>Dao()
}
```

---

## Migrations

### Auto-migration (Room 2.4+, simple cases)
```kotlin
@Database(
    entities = [...],
    version = 2,
    autoMigrations = [AutoMigration(from = 1, to = 2)]
)
```

### Manual migration (complex changes)
```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN avatar_url TEXT DEFAULT NULL")
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // Create new table with correct schema
        db.execSQL("""
            CREATE TABLE users_new (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT ''
            )
        """)
        // Copy data
        db.execSQL("INSERT INTO users_new (id, name) SELECT id, name FROM users")
        // Drop old, rename new
        db.execSQL("DROP TABLE users")
        db.execSQL("ALTER TABLE users_new RENAME TO users")
    }
}
```

### Destructive fallback (debug only — NEVER in production)
```kotlin
Room.databaseBuilder(context, AppDatabase::class.java, "app_database")
    .fallbackToDestructiveMigration()  // ⚠️ Wipes data on schema mismatch
    .build()
```

---

## Repository Pattern (offline-first)

```kotlin
class <Name>RepositoryImpl @Inject constructor(
    private val api: <Name>Api,
    private val dao: <Name>Dao,
    private val mapper: <Name>Mapper
) : <Name>Repository {

    /** Observe local DB as single source of truth — refresh from network in background. */
    override fun observeItems(): Flow<List<<Model>>> =
        dao.observeAll().map { entities -> entities.map(mapper::entityToDomain) }

    /** Fetch from network → save to DB. UI observes DB via Flow. */
    override suspend fun refreshItems(): ApiResult<Unit> =
        safeApiCall {
            val dtos = api.getItems(page = 1)
            val entities = dtos.map(mapper::dtoToEntity)
            dao.replaceAll(entities)
        }

    override suspend fun getItem(id: String): <Model>? =
        dao.getById(id)?.let(mapper::entityToDomain)
}
```

---

## Mapper (DTO ↔ Entity ↔ Domain)

```kotlin
class <Name>Mapper @Inject constructor() {

    fun dtoToEntity(dto: <Name>Dto): <Name>Entity = <Name>Entity(
        id = dto.id,
        name = dto.name.orEmpty(),
        createdAt = dto.createdAt?.toLongOrNull() ?: System.currentTimeMillis()
    )

    fun entityToDomain(entity: <Name>Entity): <Model> = <Model>(
        id = entity.id,
        name = entity.name
    )

    fun domainToEntity(model: <Model>): <Name>Entity = <Name>Entity(
        id = model.id,
        name = model.name
    )
}
```

---

## Relations (one-to-many query)

```kotlin
data class PostWithComments(
    @Embedded val post: PostEntity,
    @Relation(parentColumn = "id", entityColumn = "post_id")
    val comments: List<CommentEntity>
)

@Dao
interface PostDao {
    @Transaction
    @Query("SELECT * FROM posts WHERE id = :postId")
    fun getPostWithComments(postId: String): Flow<PostWithComments>
}
```

---

## Version Catalog entries needed

```toml
[libraries]
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
room-ktx = { group = "androidx.room", name = "room-ktx", version.ref = "room" }
room-compiler = { group = "androidx.room", name = "room-compiler", version.ref = "room" }
room-paging = { group = "androidx.room", name = "room-paging", version.ref = "room" }
```

`build.gradle.kts`:
```kotlin
plugins { id("com.google.devtools.ksp") }
dependencies {
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)
}
```
