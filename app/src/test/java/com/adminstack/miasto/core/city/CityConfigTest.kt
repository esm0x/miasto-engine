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
            for (hex in listOf(c.theme.primary, c.theme.primaryDark, c.theme.accent)) {
                assertTrue("$where: colour $hex is not #RRGGBB", Regex("#[0-9A-Fa-f]{6}").matches(hex))
            }
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
