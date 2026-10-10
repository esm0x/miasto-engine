package com.adminstack.miasto.core.net

import android.content.Context
import android.util.Log
import com.adminstack.miasto.core.city.City
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import javax.net.ssl.SSLException
import java.util.concurrent.TimeUnit

/**
 * Where this city's scraped data lives. The base URL comes from cities/<slug>/city.json,
 * so each city can be hosted anywhere: a raw GitHub path today, a CDN later.
 */
object RemoteConfig {
    fun dataUrl(fileName: String) = City.config.dataUrl(fileName)
}

val sharedHttp: OkHttpClient by lazy {
    OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()
}

val sharedJson: Json by lazy {
    Json {
        ignoreUnknownKeys = true
        isLenient = true
        explicitNulls = false
    }
}

/**
 * Exception messages are written for developers: a failed handshake surfaces as
 * "java.security.cert.CertPathValidatorException: Trust anchor for certification path not
 * found", which tells a user nothing and looks broken on a release build. This maps the
 * handful of failures that actually happen in the field onto something actionable, and
 * leaves anything unexpected to the caller's own fallback.
 */
fun friendlyNetworkError(e: Throwable, fallback: String): String = when {
    e is UnknownHostException || e is ConnectException ->
        "Brak połączenia z internetem"
    e is SocketTimeoutException ->
        "Serwer nie odpowiada, spróbuj ponownie"
    e is SSLException || e.cause is SSLException ->
        "Serwer źródła ma problem z certyfikatem, spróbuj ponownie później"
    else -> e.message ?: fallback
}

/** What the UI needs to know about a background load, beyond the data itself. */
data class LoadState(
    val loading: Boolean = false,
    val error: String? = null,
    val lastUpdated: Long? = null,
)

/**
 * Fetches a JSON document over HTTP and keeps the raw body in internal storage so a
 * cold start shows the last known data instead of a spinner. Subclasses only supply
 * the parse step.
 */
abstract class CachedRemoteSource<T>(
    private val context: Context,
    private val url: String,
    private val cacheFileName: String,
) {
    protected abstract fun parse(body: String): T

    /**
     * False when this city has the module switched off. A disabled source never touches
     * the network: Lubomia has no buses, and a 404 for transit_meta.json every few hours
     * would only be noise in the logs and a stray error state.
     */
    protected open val enabled: Boolean = true

    private val _data = MutableStateFlow<T?>(null)
    val data: StateFlow<T?> = _data.asStateFlow()

    private val _state = MutableStateFlow(LoadState())
    val state: StateFlow<LoadState> = _state.asStateFlow()

    private val cacheFile: File get() = File(context.filesDir, cacheFileName)

    /**
     * Cheap blocking read of the last good payload. Safe to call on app start.
     *
     * With nothing cached yet, the snapshot built into the APK (assets/seed/, copied
     * from data/<slug>/ at build time) stands in, so a first launch without signal shows
     * a real waste schedule instead of empty cards. It is never written to the cache:
     * the first successful download replaces it, and its age is not claimed as fresh.
     */
    fun loadCache() {
        runCatching {
            if (cacheFile.exists()) {
                _data.value = parse(cacheFile.readText())
                _state.value = _state.value.copy(lastUpdated = cacheFile.lastModified())
                return
            }
            val seed = runCatching {
                context.assets.open("seed/$cacheFileName").bufferedReader().use { it.readText() }
            }.getOrNull() ?: return
            _data.value = parse(seed)
        }.onFailure { Log.w(TAG, "loadCache($cacheFileName) failed", it) }
    }

    suspend fun refresh(): Result<T> = withContext(Dispatchers.IO) {
        if (!enabled) return@withContext Result.failure(ModuleDisabledException(cacheFileName))
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching {
            val body = sharedHttp.newCall(Request.Builder().url(url).build()).execute().use { r ->
                if (!r.isSuccessful) error(httpMessage(r.code))
                r.body?.string() ?: error("Pusta odpowiedź serwera")
            }
            val parsed = parse(body)
            _data.value = parsed
            runCatching { cacheFile.writeText(body) }
                .onFailure { Log.w(TAG, "cache write failed", it) }
            _state.value = LoadState(loading = false, lastUpdated = System.currentTimeMillis())
            parsed
        }.onFailure { e ->
            Log.w(TAG, "refresh($url) failed", e)
            _state.value = _state.value.copy(
                loading = false,
                error = friendlyNetworkError(e, "Błąd pobierania"),
            )
        }
    }

    private fun httpMessage(code: Int) = when (code) {
        404 -> "Nie znaleziono danych (404). Sprawdź dataBaseUrl w city.json i czy workflow już się wykonał."
        403 -> "Brak dostępu (403). Repo z danymi musi być publiczne."
        else -> "Błąd HTTP $code"
    }

    private companion object {
        const val TAG = "CachedRemoteSource"
    }
}

/** Returned by a source whose module this city does not have. Not an error to show. */
class ModuleDisabledException(source: String) : IllegalStateException("$source: module disabled")
