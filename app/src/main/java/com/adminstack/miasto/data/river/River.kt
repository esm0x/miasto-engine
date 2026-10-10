package com.adminstack.miasto.data.river

import android.util.Log
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.core.city.RiverStation
import com.adminstack.miasto.core.net.ModuleDisabledException
import com.adminstack.miasto.core.net.friendlyNetworkError
import com.adminstack.miasto.core.net.sharedHttp
import com.adminstack.miasto.core.net.sharedJson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Request
import java.time.Duration
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Where a reading sits against the gauge's own thresholds, as IMGW defines them. */
enum class RiverLevel(val label: String, val color: Long) {
    NORMAL("Stan normalny", 0xFF10B981),
    WARNING("Powyżej stanu ostrzegawczego", 0xFFF97316),
    ALARM("Powyżej stanu alarmowego", 0xFFDC2626),
    UNKNOWN("Brak aktualnego pomiaru", 0xFF6B7280),
}

data class GaugeReading(
    val station: RiverStation,
    val river: String,
    /** Water level in cm on the gauge's own scale; not comparable between gauges. */
    val levelCm: Int?,
    val warningCm: Int?,
    val alarmCm: Int?,
    val measuredAt: LocalDateTime?,
) {
    /**
     * Stale counts as unknown: IMGW measures every ten minutes, and a reading hours old
     * says nothing about a river that can rise a metre in that time.
     */
    fun level(now: LocalDateTime = LocalDateTime.now()): RiverLevel {
        val cm = levelCm ?: return RiverLevel.UNKNOWN
        val at = measuredAt ?: return RiverLevel.UNKNOWN
        if (Duration.between(at, now).toHours() >= STALE_HOURS) return RiverLevel.UNKNOWN
        return when {
            alarmCm != null && cm >= alarmCm -> RiverLevel.ALARM
            warningCm != null && cm >= warningCm -> RiverLevel.WARNING
            else -> RiverLevel.NORMAL
        }
    }

    /** How far below the warning level, for "1,8 m do stanu ostrzegawczego". */
    val marginToWarningCm: Int? get() = if (levelCm != null && warningCm != null) warningCm - levelCm else null

    companion object {
        const val STALE_HOURS = 6L
    }
}

data class RiverState(
    val loading: Boolean = false,
    val error: String? = null,
    val readings: List<GaugeReading> = emptyList(),
) {
    /** The worst gauge decides what the dashboard says; unknown never hides a real alarm. */
    val worst: RiverLevel
        get() {
            val levels = readings.map { it.level() }
            return listOf(RiverLevel.ALARM, RiverLevel.WARNING, RiverLevel.NORMAL)
                .firstOrNull { it in levels } ?: RiverLevel.UNKNOWN
        }
}

/**
 * River gauges from IMGW's public hydrological API, live like the air reading: a flood
 * warning six hours late is no warning. One request per gauge, in parallel.
 *
 * The thresholds come with every reading (stan_ostrzegawczy, stan_alarmowy), set by
 * IMGW per gauge, so the app judges each gauge on its own scale and never compares
 * centimetres across gauges, which mean nothing to each other.
 */
class RiverRepository {

    private val _state = MutableStateFlow(RiverState())
    val state: StateFlow<RiverState> = _state.asStateFlow()

    suspend fun refresh(): Result<RiverState> = withContext(Dispatchers.IO) {
        val config = City.config.river
        if (!City.config.hasRiver || config == null) {
            return@withContext Result.failure(ModuleDisabledException("river"))
        }
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching {
            val readings = coroutineScope {
                config.stations.map { station -> async { runCatching { fetch(station) }.getOrNull() } }
                    .mapNotNull { it.await() }
            }
            check(readings.isNotEmpty()) { "Brak danych z wodowskazów" }
            RiverState(readings = readings).also { _state.value = it }
        }.onFailure { e ->
            Log.w(TAG, "river refresh failed", e)
            _state.value = _state.value.copy(loading = false, error = friendlyNetworkError(e, "Błąd pobierania"))
        }
    }

    private fun fetch(station: RiverStation): GaugeReading {
        val body = sharedHttp.newCall(Request.Builder().url("$BASE/id/${station.id}").build()).execute().use { r ->
            if (!r.isSuccessful) error("HTTP ${r.code}")
            r.body?.string() ?: error("Pusta odpowiedź")
        }
        return parse(station, body)
    }

    companion object {
        private const val TAG = "River"
        private const val BASE = "https://danepubliczne.imgw.pl/api/data/hydro"
        private val FMT: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

        /** The API answers a one-element array; every value is a string or null. */
        fun parse(station: RiverStation, body: String): GaugeReading {
            val root = sharedJson.parseToJsonElement(body)
            val o: JsonObject = runCatching { root.jsonArray.first().jsonObject }.getOrElse { root.jsonObject }
            fun str(key: String) = o[key]?.jsonPrimitive?.contentOrNull?.takeIf { it.isNotBlank() }
            fun cm(key: String) = str(key)?.toDoubleOrNull()?.toInt()
            return GaugeReading(
                station = station,
                river = str("rzeka").orEmpty(),
                levelCm = cm("stan_wody"),
                warningCm = cm("stan_ostrzegawczy"),
                alarmCm = cm("stan_alarmowy"),
                measuredAt = str("stan_wody_data_pomiaru")?.let { runCatching { LocalDateTime.parse(it, FMT) }.getOrNull() },
            )
        }
    }
}
