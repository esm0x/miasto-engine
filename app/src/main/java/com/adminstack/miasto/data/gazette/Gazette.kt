package com.adminstack.miasto.data.gazette

import android.content.Context
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.core.net.CachedRemoteSource
import com.adminstack.miasto.core.net.RemoteConfig
import com.adminstack.miasto.core.net.sharedJson
import kotlinx.serialization.Serializable

@Serializable
data class GazettePayload(
    val generated_at: String? = null,
    val title: String = "",
    val issues: List<GazetteIssue> = emptyList(),
)

/** One issue: "Nr 6, wrzesień 2026", a PDF on the city's site and its cover. */
@Serializable
data class GazetteIssue(
    /** "2026-06": year and number, so a later issue always sorts after an earlier one. */
    val id: String,
    val number: Int,
    val year: Int,
    val label: String,
    val pdfUrl: String,
    val coverUrl: String? = null,
)

/** Newest first, the way the scraper writes them; sorted again in case it ever does not. */
fun List<GazetteIssue>.newestFirst(): List<GazetteIssue> =
    sortedWith(compareByDescending<GazetteIssue> { it.year }.thenByDescending { it.number })

class GazetteRepository(context: Context) :
    CachedRemoteSource<GazettePayload>(context, RemoteConfig.dataUrl("gazette.json"), "gazette.json") {

    override val enabled: Boolean get() = City.config.hasGazette

    override fun parse(body: String): GazettePayload = sharedJson.decodeFromString(body)

    fun issues(): List<GazetteIssue> = data.value?.issues.orEmpty().newestFirst()

    fun newest(): GazetteIssue? = issues().firstOrNull()
}
