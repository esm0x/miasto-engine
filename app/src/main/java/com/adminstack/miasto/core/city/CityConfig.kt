package com.adminstack.miasto.core.city

import android.content.Context
import com.adminstack.miasto.core.net.sharedJson
import kotlinx.serialization.Serializable

/**
 * Everything that makes this build one city rather than another.
 *
 * Read from `cities/<slug>/city.json` at the root of the repo, which Gradle copies into
 * the flavour's assets (see app/build.gradle.kts). The same file drives the flavour
 * itself, its applicationId, version and launcher name, so a city is added by writing
 * one file, not by touching Kotlin. If a new city seems to need `if (slug == ...)`,
 * the field it needs belongs here instead.
 *
 * The format is documented, field by field, in docs/CITY_CONFIG.md.
 */
@Serializable
data class CityConfig(
    /** Directory name under cities/ and data/, also the flavour name. Lowercase ASCII. */
    val slug: String,
    /** "Rybnik". Shown in the dashboard header. */
    val name: String,
    /** "w Rybniku": Polish needs the locative, and it cannot be derived from the name. */
    val locative: String,
    /** Launcher label and the name in notifications' settings, "Mój Rybnik". */
    val appName: String,
    /** Where this city's scraped JSON lives. Must end with a slash. */
    val dataBaseUrl: String,
    val contactEmail: String,
    /** Linked from the support screen; null hides the "source code" row. */
    val repoUrl: String? = null,
    /** Linked from the support screen; null hides the donation row. */
    val donateUrl: String? = null,
    val modules: Modules = Modules(),
    val theme: ThemeColors = ThemeColors(),
    val air: AirConfig? = null,
    val outages: OutagesConfig? = null,
    val transit: TransitConfig? = null,
    val river: RiverConfig? = null,
    val waste: WasteConfig = WasteConfig(),
    /** "Dane: …" line at the foot of Settings: who provides what, nominative. */
    val dataSources: String,
    /** "Dane pochodzą od …" on the support screen: the same list, genitive. */
    val dataCredit: String,
    /** "miasta" or "gminy": "Aplikacja nie jest oficjalnym produktem …". */
    val authorityGenitive: String = "miasta",
    /** Subtitle of the Sport row in "Więcej", naming the clubs. */
    val sportSummary: String = "Wyniki i terminarz lokalnych drużyn",
) {
    fun dataUrl(fileName: String): String = dataBaseUrl + fileName

    /** Modules switched on in config and actually configured, so a typo cannot crash. */
    val hasAir: Boolean get() = modules.air && air != null
    val hasOutages: Boolean get() = modules.outages && outages != null
    val hasTransit: Boolean get() = modules.transit && transit != null
    val hasRiver: Boolean get() = modules.river && river != null

    companion object {
        const val ASSET = "city.json"

        fun load(context: Context): CityConfig =
            context.assets.open(ASSET).bufferedReader().use { sharedJson.decodeFromString(it.readText()) }
    }
}

/**
 * Which parts of the app exist for this city. A module switched off disappears from the
 * bottom bar, the dashboard, the "More" list, the notification settings and the worker.
 * Defaults are on, so a city file lists only what it lacks.
 */
@Serializable
data class Modules(
    val events: Boolean = true,
    val transit: Boolean = true,
    val waste: Boolean = true,
    val news: Boolean = true,
    val air: Boolean = true,
    val outages: Boolean = true,
    val sport: Boolean = true,
    val points: Boolean = true,
    /** Live river gauges; only meaningful with a "river" section, see [RiverConfig]. */
    val river: Boolean = true,
)

/**
 * The brand colours, as #RRGGBB. Defaults are Rybnik's petrol and amber, so the first
 * city keeps its look byte for byte and a new one can start by changing two values.
 */
@Serializable
data class ThemeColors(
    val primary: String = "#0B6E7F",
    val primaryDark: String = "#14A2B8",
    val primaryContainer: String = "#CFEBF0",
    val primaryContainerDark: String = "#08505E",
    val onPrimaryContainer: String = "#063540",
    val accent: String = "#E4A11B",
    val accentContainer: String = "#FDEBC7",
    val onAccentContainer: String = "#5A3E00",
)

/** GIOŚ station. Its sensors are looked up at runtime, so only the id is needed. */
@Serializable
data class AirConfig(
    val stationId: Int,
    /** "Rybnik, ul. Borki". Shown under the reading, so say where it is measured. */
    val stationName: String,
)

/**
 * Tauron's ids for the places this city's addresses can be in.
 *
 * Pinned rather than looked up by name: five places in Poland are called Rybnik, and the
 * first hit is a village in Łódzkie. A town is one id under "*"; a rural gmina, where
 * every village is a separate place to Tauron, maps each district name from the waste
 * address to its own id.
 */
@Serializable
data class OutagesConfig(
    val cityGaids: Map<String, Int>,
) {
    fun gaidFor(district: String?): Int? = district?.let { cityGaids[it] } ?: cityGaids["*"]
}

/**
 * River gauges from IMGW, for a place that lives with a river. Lubomia sits on the Odra
 * between the Racibórz Dolny flood reservoir and the Buków polder; Nieboczowy was moved
 * out of the reservoir's bowl. Ids from https://danepubliczne.imgw.pl/api/data/hydro/.
 */
@Serializable
data class RiverConfig(
    /** "Odra": the card's title says "Stan Odry". */
    val name: String,
    /** "Odry": Polish needs the genitive, and it cannot be derived from the name. */
    val nameGenitive: String,
    /** Upstream first, the way water reaches the town. */
    val stations: List<RiverStation>,
    /** One sentence under the gauges: where they are relative to the town. */
    val note: String? = null,
)

@Serializable
data class RiverStation(
    val id: String,
    /** "Krzyżanowice": the gauge's own name, as IMGW publishes it. */
    val name: String,
    /** "najbliższy, ok. 6 km od Lubomi": where it is, in words a resident uses. */
    val where: String? = null,
    /** The gauge the dashboard shows in normal times: the one nearest the town. */
    val home: Boolean = false,
)

@Serializable
data class TransitConfig(
    /** "KM Rybnik": named on the download prompt, so people know whose timetable it is. */
    val operatorName: String,
    /** Approximate size of the GTFS zip, shown before the user agrees to download it. */
    val downloadSizeLabel: String = "ok. 1 MB",
    /** Route short names that are not real lines (depot runs, shift changes). */
    val ignoredRoutes: List<String> = emptyList(),
)

@Serializable
data class WasteConfig(
    /** Header of the first address step: "Wybierz dzielnicę" or "Wybierz miejscowość". */
    val districtPickTitle: String = "Wybierz dzielnicę",
    /** Under the empty state on the waste screen: why the schedule needs an address. */
    val addressHint: String = "Harmonogram zależy od adresu.",
    /** Shown when the city splits single- and multi-family schedules. */
    val houseTypeHint: String? = null,
    /**
     * Overrides for the one-line hints in "gdzie wyrzucić", keyed by destination
     * (ZMIESZANE, PAPIER, GPZON, INNE…). Bin colours and the hazardous-waste address
     * differ between gminas; anything not listed keeps the generic wording.
     */
    val destinationHints: Map<String, String> = emptyMap(),
)

/**
 * The config of the city this APK was built for. Loaded once, before anything else in
 * [com.adminstack.miasto.Graph.init], and never changes while the process lives.
 */
object City {
    @Volatile
    private var loaded: CityConfig? = null

    val config: CityConfig
        get() = loaded ?: error("City.init() has not run: Graph.init must load the config first")

    fun init(context: Context) {
        if (loaded == null) loaded = CityConfig.load(context.applicationContext)
    }
}
