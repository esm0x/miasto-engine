package com.adminstack.miasto.data.waste

import com.adminstack.miasto.core.prefs.HouseType
import com.adminstack.miasto.core.prefs.WasteAddress
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

/** 1 January: the gmina publishes new rejony and the saved address has to keep working. */
class NewYearScheduleTest {

    private val address = WasteAddress(
        district = "Syrynia", street = "Wolności", houseNumber = "7",
        houseType = HouseType.SINGLE_FAMILY, rejonId = "rejon-i-syrynia",
    )

    private fun rejon(id: String, district: String, street: String, date: String) = RejonDto(
        id = id, name = id, district = district, houseType = "SINGLE_FAMILY",
        streets = listOf(StreetDto(street)),
        pickups = listOf(PickupDto("ZMIESZANE", listOf(date))),
    )

    @Test
    fun `the saved id still works when the rejon kept its name`() {
        val schedule = WasteSchedule(listOf(rejon("rejon-i-syrynia", "Syrynia", "Wolności", "2027-01-04")))
        assertEquals(LocalDate.of(2027, 1, 4), schedule.nextCollection(address, LocalDate.of(2027, 1, 1))?.date)
    }

    @Test
    fun `a renamed rejon is found again from the address`() {
        // 2027 merged rejony I and II into one: the old id is gone, the street is not.
        val schedule = WasteSchedule(listOf(rejon("rejon-a-syrynia", "Syrynia", "Wolności", "2027-01-05")))
        assertNull(schedule.byId(address.rejonId))
        assertEquals("rejon-a-syrynia", schedule.rejonFor(address)?.id)
        assertEquals(LocalDate.of(2027, 1, 5), schedule.nextCollection(address, LocalDate.of(2027, 1, 1))?.date)
    }

    @Test
    fun `an address that is in no rejon any more is reported, not silently empty`() {
        val schedule = WasteSchedule(listOf(rejon("rejon-a-lubomia", "Lubomia", "Szkolna", "2027-01-05")))
        assertNull(schedule.rejonFor(address))
        assertTrue(schedule.collections(address, LocalDate.of(2027, 1, 1), LocalDate.of(2027, 12, 31)).isEmpty())
        assertTrue(!schedule.isEmpty)
    }

    @Test
    fun `a whole-village address survives a rename too`() {
        val village = WasteAddress("Buków", "", "", HouseType.SINGLE_FAMILY, "rejon-iii-bukow")
        val schedule = WasteSchedule(listOf(rejon("rejon-c-bukow", "Buków", WHOLE_DISTRICT, "2027-01-07")))
        assertNotNull(schedule.rejonFor(village))
    }
}
