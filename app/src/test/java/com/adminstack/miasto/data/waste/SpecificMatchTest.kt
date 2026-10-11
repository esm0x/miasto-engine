package com.adminstack.miasto.data.waste

import com.adminstack.miasto.core.prefs.HouseType
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Żory, shaped like the real 2026 schedule: Wodzisławska whole in rejon 1, four numbers
 * of it in rejon 2, and a stretch of hard-to-reach houses in a rejon of their own.
 * Listed in that order, so "the first match" would be wrong for every specific house.
 */
class SpecificMatchTest {

    private fun rejon(id: String, vararg streets: StreetDto) = RejonDto(
        id = id,
        name = id,
        district = "Żory",
        houseType = "SINGLE_FAMILY",
        streets = streets.toList(),
        pickups = listOf(PickupDto("ZMIESZANE", listOf("2026-10-12"))),
    )

    private fun numbers(vararg n: Int) = n.map { NumberRuleDto(from = it, to = it) }

    private val schedule = WasteSchedule(
        listOf(
            rejon("rejon-1", StreetDto("Wodzisławska"), StreetDto("Brodecka")),
            rejon("rejon-2", StreetDto("Wodzisławska", numbers(218, 244, 252, 258))),
            rejon("rejon-1-utrudniony", StreetDto("Wodzisławska", numbers(72, 114)), StreetDto("Brodecka", numbers(11))),
            rejon("rejon-10", StreetDto("Kościuszki")),
            rejon("rejon-2-utrudniony", StreetDto("Kościuszki", listOf(NumberRuleDto(to = 20)))),
            rejon("rejon-14", StreetDto("Miarki")),
            rejon("rejon-x", StreetDto("K. Miarki")),
        ),
    )

    private fun resolve(street: String, number: String) =
        schedule.resolveRejon("Żory", street, number, HouseType.SINGLE_FAMILY)?.id

    @After
    fun resetLabels() {
        WasteType.labelOverrides = emptyMap()
    }

    @Test
    fun `a rule naming the number beats the whole street listed before it`() {
        assertEquals("rejon-2", resolve("Wodzisławska", "218"))
        assertEquals("rejon-1-utrudniony", resolve("Wodzisławska", "72B"))
        assertEquals("rejon-1-utrudniony", resolve("Brodecka", "11A"))
    }

    @Test
    fun `the rest of the street stays with the whole-street rejon`() {
        assertEquals("rejon-1", resolve("Wodzisławska", "100"))
        assertEquals("rejon-1", resolve("Brodecka", "12"))
    }

    @Test
    fun `an open range counts as specific`() {
        assertEquals("rejon-2-utrudniony", resolve("Kościuszki", "5"))
        assertEquals("rejon-10", resolve("Kościuszki", "33"))
    }

    @Test
    fun `the exact spelling beats a fuzzy match`() {
        assertEquals("rejon-x", resolve("K. Miarki", "3"))
        assertEquals("rejon-14", resolve("Miarki", "3"))
    }

    @Test
    fun `an empty street matches no street, only a whole district`() {
        assertEquals(null, resolve("", ""))
    }

    @Test
    fun `a city can rename a waste type`() {
        assertEquals("Gabaryty i elektro", WasteType.GABARYTY.label)
        WasteType.labelOverrides = mapOf("GABARYTY" to "Gabaryty")
        assertEquals("Gabaryty", WasteType.GABARYTY.label)
        assertEquals("Elektronika", WasteType.ELEKTRO.label)
    }

    @Test
    fun `the types Żory brought are read, not folded into mixed waste`() {
        for (t in listOf("ZIELONE", "ELEKTRO", "OPONY", "LISCIE_CHOINKI", "PAPIER_PLASTIK")) {
            assertEquals(t, WasteType.from(t).name)
        }
    }
}
