package com.adminstack.miasto.data.places

import com.adminstack.miasto.data.gazette.GazetteIssue
import com.adminstack.miasto.work.NotificationRules
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime

/** Żory's town hall and PSZOK as in places.json, October 2026. */
class PlacesStatusTest {

    private val office = Place(
        id = "urzad-miasta", name = "Urząd Miasta Żory", kind = "URZAD", closedOnHolidays = true,
        hours = listOf(
            OpeningHours(listOf("MON"), "07:30", "17:00"),
            OpeningHours(listOf("TUE", "WED", "THU"), "07:30", "15:30"),
            OpeningHours(listOf("FRI"), "07:30", "14:00"),
        ),
    )
    private val beach = Place(
        id = "rajska-fala", name = "Kąpielisko", kind = "ATRAKCJA",
        hours = listOf(OpeningHours(listOf("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"), "10:00", "19:00", listOf(6, 7, 8))),
    )

    // 12.10.2026 is a Monday.
    private fun at(day: Int, h: Int, m: Int = 0) = LocalDateTime.of(2026, 10, day, h, m)

    @Test
    fun `open until closing time, closed from the minute it closes`() {
        assertEquals(PlaceStatus.Open(LocalTime.of(17, 0)), office.statusAt(at(12, 16, 59)))
        assertEquals("Zamknięte, otwarcie jutro o 7:30", office.statusAt(at(12, 17, 0)).describe(at(12, 17, 0)))
        assertEquals("Otwarte do 15:30", office.statusAt(at(13, 9)).describe(at(13, 9)))
    }

    @Test
    fun `before opening says today, over a weekend names the day`() {
        assertEquals("Zamknięte, otwarcie dziś o 7:30", office.statusAt(at(13, 6)).describe(at(13, 6)))
        // Friday 14:00 → Monday.
        assertEquals("Zamknięte, otwarcie w poniedziałek o 7:30", office.statusAt(at(16, 15)).describe(at(16, 15)))
    }

    @Test
    fun `a public holiday shuts what closes on holidays`() {
        // 11.11.2026, Wednesday, Narodowe Święto Niepodległości.
        val holiday = LocalDateTime.of(2026, 11, 11, 10, 0)
        assertEquals("Zamknięte, otwarcie jutro o 7:30", office.statusAt(holiday).describe(holiday))
        // 24.12.2026: Wigilia is a day off from 2025.
        val eve = LocalDateTime.of(2026, 12, 24, 9, 0)
        assertTrue(office.statusAt(eve) is PlaceStatus.Closed)
    }

    @Test
    fun `a seasonal place is closed out of season, not opening tomorrow`() {
        assertEquals("Zamknięte poza sezonem", beach.statusAt(at(12, 12)).describe(at(12, 12)))
        assertEquals(PlaceStatus.Open(LocalTime.of(19, 0)), beach.statusAt(LocalDateTime.of(2026, 7, 4, 12, 0)))
    }

    @Test
    fun `unknown hours say nothing about open or closed`() {
        val park = Place(id = "twinpigs", name = "Twinpigs", kind = "ATRAKCJA", hours = null)
        assertEquals(PlaceStatus.Unknown, park.statusAt(at(12, 12)))
    }

    @Test
    fun `hours read the way a sign would`() {
        assertEquals(
            listOf("pon. 7:30-17:00", "wt.-czw. 7:30-15:30", "pt. 7:30-14:00"),
            office.hoursLines(),
        )
        assertEquals(listOf("codziennie 10:00-19:00 (czerwiec-sierpień)"), beach.hoursLines())
        assertEquals("sob., niedz.", daysLabel(listOf("SAT", "SUN")))
    }

    @Test
    fun `holidays follow Easter`() {
        assertEquals(LocalDate.of(2026, 4, 5), PolishHolidays.easter(2026))
        assertEquals(LocalDate.of(2027, 3, 28), PolishHolidays.easter(2027))
        assertTrue(PolishHolidays.isHoliday(LocalDate.of(2026, 6, 4)))    // Boże Ciało
        assertTrue(PolishHolidays.isHoliday(LocalDate.of(2027, 5, 27)))
    }

    private fun issue(id: String) = GazetteIssue(id, id.takeLast(2).toInt(), id.take(4).toInt(), "Nr", "https://x/k.pdf")

    @Test
    fun `a new gazette issue is announced once, and never on the first look`() {
        assertNull("first run: nothing known yet", NotificationRules.gazetteToNotify(issue("2026-06"), null))
        assertNull(NotificationRules.gazetteToNotify(issue("2026-06"), "2026-06"))
        assertEquals("2026-07", NotificationRules.gazetteToNotify(issue("2026-07"), "2026-06")?.id)
        assertNull("an older issue on top is not news", NotificationRules.gazetteToNotify(issue("2026-05"), "2026-06"))
        assertEquals("2027-01", NotificationRules.gazetteToNotify(issue("2027-01"), "2026-08")?.id)
    }
}
