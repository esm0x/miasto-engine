package com.adminstack.miasto.core.city

import com.adminstack.miasto.core.net.sharedJson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Every real city file is parsed here, so a typo in a new city's config fails the test
 * run instead of crashing the app on its first launch.
 */
class CityConfigTest {

    /** Unit tests run with app/ as the working directory. */
    private val citiesDir = File("../cities")

    private fun allCities(): List<Pair<File, CityConfig>> =
        citiesDir.listFiles().orEmpty()
            .filter { File(it, "city.json").isFile }
            .map { dir -> dir to sharedJson.decodeFromString<CityConfig>(File(dir, "city.json").readText()) }

    @Test
    fun `every city file parses and is internally consistent`() {
        val cities = allCities()
        assertTrue("no cities found in ${citiesDir.absolutePath}", cities.isNotEmpty())
        for ((dir, c) in cities) {
            val where = "cities/${dir.name}/city.json"
            assertEquals("$where: slug must equal the directory name", dir.name, c.slug)
            assertTrue("$where: dataBaseUrl must be https", c.dataBaseUrl.startsWith("https://"))
            assertTrue("$where: dataBaseUrl must end with /", c.dataBaseUrl.endsWith("/"))
            assertTrue("$where: dataBaseUrl should point at data/${c.slug}/", c.dataBaseUrl.endsWith("/${c.slug}/"))
            assertTrue("$where: appName empty", c.appName.isNotBlank())
            assertTrue("$where: dataSources empty", c.dataSources.isNotBlank())
            if (c.modules.air) assertNotNull("$where: air module on but no air section", c.air)
            if (c.modules.outages) assertNotNull("$where: outages module on but no outages section", c.outages)
            if (c.modules.transit) assertNotNull("$where: transit module on but no transit section", c.transit)
            c.river?.let { r ->
                assertTrue("$where: river without stations", r.stations.isNotEmpty())
                assertTrue("$where: IMGW station ids are digits", r.stations.all { st -> st.id.all(Char::isDigit) })
                assertTrue("$where: at most one home gauge", r.stations.count { st -> st.home } <= 1)
            }
            for (hex in listOf(c.theme.primary, c.theme.primaryDark, c.theme.accent)) {
                assertTrue("$where: colour $hex is not #RRGGBB", Regex("#[0-9A-Fa-f]{6}").matches(hex))
            }
        }
    }

    /**
     * Lubomia and Żory once shipped the same placeholder silhouette, told apart only by
     * the background colour. In the status bar the colour is gone: someone with both apps
     * could not tell which one was calling. Each city's icons must differ from every
     * other's; the shared placeholder may serve one city at most, while it is being set up.
     */
    @Test
    fun `no two cities share a launcher glyph or a notification icon`() {
        val res = File("src")
        fun effective(slug: String, name: String): String {
            val own = File(res, "$slug/res/drawable/$name.xml")
            val file = if (own.isFile) own else File(res, "main/res/drawable/$name.xml")
            // Only the shape counts; comments and the crop around it may differ.
            return Regex("""android:pathData="([^"]+)"""").findAll(file.readText())
                .joinToString("|") { it.groupValues[1].replace(Regex("\\s+"), " ") }
        }
        val slugs = allCities().map { it.second.slug }
        for (name in listOf("ic_notification", "ic_city_glyph")) {
            // A city with full launcher artwork (Rybnik's mipmaps) does not use the glyph.
            val using = slugs.filter { name == "ic_notification" || !File(res, "$it/res/mipmap-anydpi-v26/ic_launcher.xml").isFile }
            val shapes = using.groupBy { effective(it, name) }
            val clashes = shapes.values.filter { it.size > 1 }
            assertTrue("$name is the same for ${clashes.joinToString()}", clashes.isEmpty())
        }
    }

    @Test
    fun `application ids are unique across cities`() {
        val ids = citiesDir.listFiles().orEmpty()
            .map { File(it, "city.json") }
            .filter { it.isFile }
            .map { Regex(""""applicationId"\s*:\s*"([^"]+)"""").find(it.readText())!!.groupValues[1] }
        assertEquals("two cities share an applicationId", ids.size, ids.toSet().size)
    }

    @Test
    fun `rybnik keeps the identifiers the released app depends on`() {
        val rybnik = allCities().first { it.second.slug == "rybnik" }
        val raw = File(rybnik.first, "city.json").readText()
        // Changing either makes the engine build a different app in the Play Store.
        assertTrue(raw.contains(""""applicationId": "com.adminstack.rybnik""""))
        assertEquals(834, rybnik.second.air?.stationId)
        assertEquals(13, rybnik.second.outages?.gaidFor("Boguszowice Stare"))
    }

    @Test
    fun `a missing module section switches the module off instead of crashing`() {
        val c = sharedJson.decodeFromString<CityConfig>(
            """{"slug":"x","name":"X","locative":"w X","appName":"Moje X",
               "dataBaseUrl":"https://e.x/data/x/","contactEmail":"a@b.c",
               "dataSources":"d","dataCredit":"d"}""",
        )
        assertTrue(c.modules.air)
        assertFalse(c.hasAir)
        assertFalse(c.hasOutages)
        assertFalse(c.hasTransit)
        assertFalse(c.hasGazette)
        assertFalse(c.hasPlaces)
    }

    @Test
    fun `outage ids per village, with a town-wide fallback`() {
        val rural = OutagesConfig(mapOf("Lubomia" to 1636, "Syrynia" to 1638))
        assertEquals(1638, rural.gaidFor("Syrynia"))
        assertNull("an unmapped village must not borrow another one's id", rural.gaidFor("Buków"))
        val town = OutagesConfig(mapOf("*" to 13))
        assertEquals(13, town.gaidFor("Niedobczyce"))
        assertEquals(13, town.gaidFor(null))
    }
}
