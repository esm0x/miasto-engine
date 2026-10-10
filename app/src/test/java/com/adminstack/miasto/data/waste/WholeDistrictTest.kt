package com.adminstack.miasto.data.waste

import com.adminstack.miasto.core.prefs.HouseType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * A rural gmina, shaped like Lubomia's real schedule: one building type everywhere, two
 * villages with streets and three listed as whole villages.
 */
class WholeDistrictTest {

    private fun rejon(id: String, district: String, vararg streets: String) = RejonDto(
        id = id,
        name = id,
        district = district,
        houseType = "SINGLE_FAMILY",
        streets = streets.map { StreetDto(it) },
        pickups = listOf(PickupDto("ZMIESZANE", listOf("2026-10-12"))),
    )

    private val schedule = WasteSchedule(
        listOf(
            rejon("i", "Syrynia", "Wolności", "Bukowska"),
            rejon("iii", "Buków", WHOLE_DISTRICT),
            rejon("iii", "Grabówka", WHOLE_DISTRICT),
            rejon("iii-s", "Syrynia", "Dąbrowy"),
        ),
    )

    @Test
    fun `a gmina without blocks of flats is never asked about building type`() {
        assertEquals(listOf(HouseType.SINGLE_FAMILY), schedule.houseTypesIn("Syrynia"))
    }

    @Test
    fun `a whole village needs no street and resolves to its rejon`() {
        assertTrue(schedule.isWholeDistrict("Buków", HouseType.SINGLE_FAMILY))
        assertEquals("iii", schedule.resolveRejon("Buków", "", "", HouseType.SINGLE_FAMILY)?.id)
    }

    @Test
    fun `a village with streets is not mistaken for a whole one`() {
        assertFalse(schedule.isWholeDistrict("Syrynia", HouseType.SINGLE_FAMILY))
        assertEquals("iii-s", schedule.resolveRejon("Syrynia", "Dąbrowy", "4", HouseType.SINGLE_FAMILY)?.id)
        assertEquals("i", schedule.resolveRejon("Syrynia", "Wolności", "12", HouseType.SINGLE_FAMILY)?.id)
    }

    @Test
    fun `the wildcard of one village does not leak into another`() {
        assertEquals(null, schedule.resolveRejon("Syrynia", "Nieznana", "1", HouseType.SINGLE_FAMILY))
    }
}
