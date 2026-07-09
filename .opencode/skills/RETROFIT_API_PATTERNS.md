# Skill: Retrofit + OkHttp + Gson — Networking Patterns

> Read this when generating networking code (API service, interceptors, error handling,
> pagination). All dependencies via Version Catalog (`libs.*`).

---

## Retrofit Service Interface

```kotlin
interface <Name>Api {

    @GET("endpoint/{id}")
    suspend fun getItem(@Path("id") id: String): <Name>Dto

    @GET("endpoint")
    suspend fun getItems(
        @Query("page") page: Int,
        @Query("limit") limit: Int = 20
    ): List<<Name>Dto>

    @POST("endpoint")
    suspend fun createItem(@Body request: Create<Name>Request): <Name>Dto

    @PUT("endpoint/{id}")
    suspend fun updateItem(
        @Path("id") id: String,
        @Body request: Update<Name>Request
    ): <Name>Dto

    @DELETE("endpoint/{id}")
    suspend fun deleteItem(@Path("id") id: String)

    @Multipart
    @POST("upload")
    suspend fun uploadFile(
        @Part file: MultipartBody.Part,
        @Part("description") description: RequestBody
    ): UploadResponse

    @Headers("Cache-Control: no-cache")
    @GET("endpoint/fresh")
    suspend fun getFresh(): <Name>Dto
}
```

---

## Gson DTOs

```kotlin
data class <Name>Dto(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("items") val items: List<ItemDto>? = null
)

data class Create<Name>Request(
    @SerializedName("name") val name: String,
    @SerializedName("email") val email: String
)

data class ApiErrorBody(
    @SerializedName("message") val message: String?,
    @SerializedName("code") val code: Int?
)
```

---

## OkHttp Client + Interceptors

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        loggingInterceptor: HttpLoggingInterceptor
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor =
        HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG)
                HttpLoggingInterceptor.Level.BODY
            else
                HttpLoggingInterceptor.Level.NONE
        }

    @Provides
    @Singleton
    fun provideGson(): Gson = GsonBuilder()
        .setDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'")
        .create()

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, gson: Gson): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()

    @Provides
    @Singleton
    fun provide<Name>Api(retrofit: Retrofit): <Name>Api =
        retrofit.create(<Name>Api::class.java)
}
```

---

## Auth Token Interceptor

```kotlin
class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()

        // Skip auth for login/register endpoints
        if (request.url.encodedPath.contains("auth/")) {
            return chain.proceed(request)
        }

        val token = tokenProvider.getAccessToken()
        val authenticatedRequest = request.newBuilder()
            .header("Authorization", "Bearer $token")
            .header("Content-Type", "application/json")
            .build()

        return chain.proceed(authenticatedRequest)
    }
}
```

---

## Error Handling — Sealed ApiResult

```kotlin
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class Error(val message: String, val code: Int? = null) : ApiResult<Nothing>
    data object Loading : ApiResult<Nothing>
}

suspend fun <T> safeApiCall(apiCall: suspend () -> T): ApiResult<T> =
    try {
        ApiResult.Success(apiCall())
    } catch (e: HttpException) {
        val errorBody = e.response()?.errorBody()?.string()
        val message = try {
            Gson().fromJson(errorBody, ApiErrorBody::class.java)?.message
        } catch (_: Exception) { null }
        ApiResult.Error(
            message = message ?: "HTTP ${e.code()}: ${e.message()}",
            code = e.code()
        )
    } catch (e: IOException) {
        ApiResult.Error(message = "Network error: check your connection")
    } catch (e: Exception) {
        ApiResult.Error(message = e.message ?: "Unknown error")
    }
```

---

## Repository Using safeApiCall

```kotlin
class <Name>RepositoryImpl @Inject constructor(
    private val api: <Name>Api,
    private val mapper: <Name>Mapper
) : <Name>Repository {

    override suspend fun getItems(): ApiResult<List<<Model>>> =
        safeApiCall { api.getItems(page = 1).map(mapper::toDomain) }

    override suspend fun getItem(id: String): ApiResult<<Model>> =
        safeApiCall { mapper.toDomain(api.getItem(id)) }

    override suspend fun createItem(request: Create<Name>Request): ApiResult<<Model>> =
        safeApiCall { mapper.toDomain(api.createItem(request)) }
}
```

---

## Pagination with Flow (offset-based)

```kotlin
class Get<Name>PagedUseCase @Inject constructor(
    private val repository: <Name>Repository
) {
    operator fun invoke(): Flow<PagingData<<Model>>> = Pager(
        config = PagingConfig(pageSize = 20, enablePlaceholders = false),
        pagingSourceFactory = { <Name>PagingSource(repository) }
    ).flow
}

class <Name>PagingSource(
    private val repository: <Name>Repository
) : PagingSource<Int, <Model>>() {

    override fun getRefreshKey(state: PagingState<Int, <Model>>): Int? =
        state.anchorPosition?.let { anchor ->
            state.closestPageToPosition(anchor)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(anchor)?.nextKey?.minus(1)
        }

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, <Model>> {
        val page = params.key ?: 1
        return when (val result = repository.getItems(page, params.loadSize)) {
            is ApiResult.Success -> LoadResult.Page(
                data = result.data,
                prevKey = if (page == 1) null else page - 1,
                nextKey = if (result.data.isEmpty()) null else page + 1
            )
            is ApiResult.Error -> LoadResult.Error(Exception(result.message))
            else -> LoadResult.Error(Exception("Unexpected state"))
        }
    }
}
```

---

## Custom Gson Type Adapters

### Date adapter
```kotlin
class DateTypeAdapter : TypeAdapter<Date>() {
    private val format = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    override fun write(out: JsonWriter, value: Date?) {
        out.value(value?.let { format.format(it) })
    }

    override fun read(`in`: JsonReader): Date? {
        return try { format.parse(`in`.nextString()) } catch (_: Exception) { null }
    }
}
```

### Generic API response wrapper
```kotlin
data class ApiResponse<T>(
    @SerializedName("status") val status: String,
    @SerializedName("data") val data: T?,
    @SerializedName("error") val error: String?
)
```

---

## Dependencies needed (resolve versions — do not invent them)

Declare these as Version Catalog aliases. **Resolve the actual versions/coordinates from the
project's existing catalog or via `context7`** — the `version.ref` names below are structure,
not pinned values (see `coder.md` → Dependency & Build Integrity Protocol).

```toml
[libraries]
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
retrofit-gson = { group = "com.squareup.retrofit2", name = "converter-gson", version.ref = "retrofit" }
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
okhttp-logging = { group = "com.squareup.okhttp3", name = "logging-interceptor", version.ref = "okhttp" }
gson = { group = "com.google.code.gson", name = "gson", version.ref = "gson" }
```

> **If you use the Pagination section above** (`Pager`, `PagingSource`, `PagingData`), you
> MUST also declare the Paging 3 dependency (`androidx.paging:paging-runtime-ktx`, plus
> `androidx.room:room-paging` if paging from Room) — otherwise those APIs won't resolve.
> Look up the current version; don't invent it.
>
> **Gson note:** Gson does not require annotation processing (no KSP/kapt needed for
> serialization). Use `@SerializedName` for JSON field mapping. Gson handles nullability
> via default values in data classes. No code generation step required — simpler build config.
