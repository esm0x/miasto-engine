package com.adminstack.miasto.data.places

import android.content.Context
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.core.net.CachedRemoteSource
import com.adminstack.miasto.core.net.RemoteConfig
import com.adminstack.miasto.core.net.sharedJson
import kotlinx.serialization.Serializable
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.Month
import java.time.format.TextStyle
import java.util.Locale

@Serializable
data class PlacesPayload(
    val generated_at: String? = null,
    val places: List<Place> = emptyList(),
)

/**
 * A place with opening hours. Written by hand in cities/<slug>/places.json from the
 * city's pages; the engine watches those pages and raises an alarm when they change.
 */
@Serializable
data class Place(
    val id: String,
    val name: String,
    /** URZAD, PSZOK, ATRAKCJA or INNE. */
    val kind: String,
    val address: String? = null,
    val phone: String? = null,
    val url: String? = null,
    /** "Umów wizytę": the town hall's queue booking. https only, checked by the engine. */
    val bookingUrl: String? = null,
    /** The page the hours were copied from. */
    val sourceUrl: String? = null,
    val note: String? = null,
    /** Shut on public holidays (town hall, PSZOK). Others say nothing, so we warn instead. */
    val closedOnHolidays: Boolean = false,
    /** Null when the hours are not known well enough to say "open" or "closed". */
    val hours: List<OpeningHours>? = null,
)

@Serializable
data class OpeningHours(
    /** MON … SUN. */
    val days: List<String>,
    /** "07:30" */
    val open: String,
    val close: String,
    /** Only in these months (1-12); empty means all year. Rajska Fala: [6, 7, 8]. */
    val months: List<Int> = emptyList(),
)

sealed interface PlaceStatus {
    data class Open(val until: LocalTime) : PlaceStatus
    /** [nextOpen] null: not within the next two weeks, i.e. out of season. */
    data class Closed(val nextOpen: LocalDateTime?) : PlaceStatus
    /** No hours to go by. */
    data object Unknown : PlaceStatus
}

private val DAY_CODES = mapOf(
    "MON" to DayOfWeek.MONDAY, "TUE" to DayOfWeek.TUESDAY, "WED" to DayOfWeek.WEDNESDAY,
    "THU" to DayOfWeek.THURSDAY, "FRI" to DayOfWeek.FRIDAY, "SAT" to DayOfWeek.SATURDAY,
    "SUN" to DayOfWeek.SUNDAY,
)

private fun parseTime(s: String): LocalTime? = runCatching { LocalTime.parse(s) }.getOrNull()

/** Opening and closing time on [date], earliest first; empty when shut all day. */
fun Place.slotsOn(date: LocalDate, isHoliday: (LocalDate) -> Boolean = PolishHolidays::isHoliday): List<Pair<LocalTime, LocalTime>> {
    val all = hours ?: return emptyList()
    if (closedOnHolidays && isHoliday(date)) return emptyList()
    return all
        .filter { h -> h.days.any { DAY_CODES[it] == date.dayOfWeek } }
        .filter { h -> h.months.isEmpty() || date.monthValue in h.months }
        .mapNotNull { h ->
            val o = parseTime(h.open) ?: return@mapNotNull null
            val c = parseTime(h.close) ?: return@mapNotNull null
            if (o < c) o to c else null
        }
        .sortedBy { it.first }
}

fun Place.statusAt(
    now: LocalDateTime,
    isHoliday: (LocalDate) -> Boolean = PolishHolidays::isHoliday,
): PlaceStatus {
    if (hours == null) return PlaceStatus.Unknown
    val today = now.toLocalDate()
    val time = now.toLocalTime()
    val slots = slotsOn(today, isHoliday)
    slots.filter { (o, c) -> time >= o && time < c }.maxByOrNull { it.second }
        ?.let { return PlaceStatus.Open(it.second) }
    slots.firstOrNull { (o, _) -> o > time }?.let { return PlaceStatus.Closed(today.atTime(it.first)) }
    for (ahead in 1..14L) {
        val day = today.plusDays(ahead)
        slotsOn(day, isHoliday).firstOrNull()?.let { return PlaceStatus.Closed(day.atTime(it.first)) }
    }
    return PlaceStatus.Closed(null)
}

private val PL = Locale("pl", "PL")

private fun hm(t: LocalTime): String = "${t.hour}:%02d".format(t.minute)

/** "Otwarte do 17:00", "Zamknięte, otwarcie jutro o 7:30", "we wtorek o 8:30". */
fun PlaceStatus.describe(now: LocalDateTime): String = when (this) {
    is PlaceStatus.Open -> "Otwarte do ${hm(until)}"
    PlaceStatus.Unknown -> "Godziny zależą od sezonu"
    is PlaceStatus.Closed -> {
        val next = nextOpen
        if (next == null) {
            "Zamknięte poza sezonem"
        } else {
            val days = next.toLocalDate().toEpochDay() - now.toLocalDate().toEpochDay()
            val whenText = when (days) {
                0L -> "dziś"
                1L -> "jutro"
                else -> weekdayAccusative(next.dayOfWeek)
            }
            "Zamknięte, otwarcie $whenText o ${hm(next.toLocalTime())}"
        }
    }
}

/** "w poniedziałek", "we wtorek", "w środę", "w niedzielę". */
private fun weekdayAccusative(d: DayOfWeek): String = when (d) {
    DayOfWeek.MONDAY -> "w poniedziałek"
    DayOfWeek.TUESDAY -> "we wtorek"
    DayOfWeek.WEDNESDAY -> "w środę"
    DayOfWeek.THURSDAY -> "w czwartek"
    DayOfWeek.FRIDAY -> "w piątek"
    DayOfWeek.SATURDAY -> "w sobotę"
    DayOfWeek.SUNDAY -> "w niedzielę"
}

private val SHORT_DAY = mapOf(
    DayOfWeek.MONDAY to "pon.", DayOfWeek.TUESDAY to "wt.", DayOfWeek.WEDNESDAY to "śr.",
    DayOfWeek.THURSDAY to "czw.", DayOfWeek.FRIDAY to "pt.", DayOfWeek.SATURDAY to "sob.",
    DayOfWeek.SUNDAY to "niedz.",
)

/** "pon.-pt.", "sob., niedz.", "codziennie"; consecutive days are joined into a range. */
internal fun daysLabel(codes: List<String>): String {
    val days = codes.mapNotNull { DAY_CODES[it] }.distinct().sortedBy { it.value }
    if (days.size == 7) return "codziennie"
    val runs = mutableListOf<MutableList<DayOfWeek>>()
    for (d in days) {
        val last = runs.lastOrNull()
        if (last != null && last.last().value + 1 == d.value) last += d else runs += mutableListOf(d)
    }
    return runs.joinToString(", ") { run ->
        when (run.size) {
            1 -> SHORT_DAY.getValue(run.first())
            2 -> "${SHORT_DAY.getValue(run.first())}, ${SHORT_DAY.getValue(run.last())}"
            else -> "${SHORT_DAY.getValue(run.first())}-${SHORT_DAY.getValue(run.last())}"
        }
    }
}

private fun monthName(m: Int): String =
    if (m in 1..12) Month.of(m).getDisplayName(TextStyle.FULL_STANDALONE, PL) else "?"

/** One line per entry: "pon.-pt. 8:00-18:00", "codziennie 10:00-19:00 (czerwiec-sierpień)". */
fun Place.hoursLines(): List<String> = hours.orEmpty().map { h ->
    val months = h.months.sorted()
    val season = when {
        months.isEmpty() -> ""
        months.size > 1 && months.zipWithNext().all { (a, b) -> b == a + 1 } ->
            " (${monthName(months.first())}-${monthName(months.last())})"
        else -> " (${months.joinToString(", ") { monthName(it) }})"
    }
    val o = parseTime(h.open)?.let(::hm) ?: h.open
    val c = parseTime(h.close)?.let(::hm) ?: h.close
    "${daysLabel(h.days)} $o-$c$season"
}

/**
 * Polish public holidays (ustawa o dniach wolnych od pracy). Easter by the anonymous
 * Gregorian algorithm; Wigilia is a day off from 2025.
 */
object PolishHolidays {
    fun easter(year: Int): LocalDate {
        val a = year % 19
        val b = year / 100
        val c = year % 100
        val d = b / 4
        val e = b % 4
        val f = (b + 8) / 25
        val g = (b - f + 1) / 3
        val h = (19 * a + b - d - g + 15) % 30
        val i = c / 4
        val k = c % 4
        val l = (32 + 2 * e + 2 * i - h - k) % 7
        val m = (a + 11 * h + 22 * l) / 451
        val month = (h + l - 7 * m + 114) / 31
        val day = (h + l - 7 * m + 114) % 31 + 1
        return LocalDate.of(year, month, day)
    }

    fun of(year: Int): Set<LocalDate> {
        val e = easter(year)
        val fixed = mutableListOf(1 to 1, 1 to 6, 5 to 1, 5 to 3, 8 to 15, 11 to 1, 11 to 11, 12 to 25, 12 to 26)
        if (year >= 2025) fixed += 12 to 24
        return fixed.map { (m, d) -> LocalDate.of(year, m, d) }.toSet() +
            setOf(e, e.plusDays(1), e.plusDays(49), e.plusDays(60))
    }

    private val cache = mutableMapOf<Int, Set<LocalDate>>()

    fun isHoliday(date: LocalDate): Boolean =
        synchronized(cache) { cache.getOrPut(date.year) { of(date.year) } }.contains(date)
}

class PlacesRepository(context: Context) :
    CachedRemoteSource<PlacesPayload>(context, RemoteConfig.dataUrl("places.json"), "places.json") {

    override val enabled: Boolean get() = City.config.hasPlaces

    override fun parse(body: String): PlacesPayload = sharedJson.decodeFromString(body)

    /** The town hall first, then PSZOK, then the rest as the file lists them. */
    fun places(): List<Place> = data.value?.places.orEmpty()
        .sortedBy { listOf("URZAD", "PSZOK").indexOf(it.kind).let { i -> if (i < 0) 9 else i } }
}
