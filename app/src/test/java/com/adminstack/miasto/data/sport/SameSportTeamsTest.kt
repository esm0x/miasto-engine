package com.adminstack.miasto.data.sport

import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate

/**
 * Lubomia has three football clubs and Rybnik one team per sport; both have to read right.
 * Rows from the real 2026/27 data: Wypoczynek Buków hosts Naprzód Syrynia on 11 November.
 */
class SameSportTeamsTest {

    private fun team(id: String, name: String, kind: SportKind = SportKind.FOOTBALL) =
        SportTeam(id = id, name = name, kind = kind, league = "Klasa A, gr. Racibórz", url = null)

    private val bukow = team("wypoczynek-bukow", "Wypoczynek Buków")
    private val syrynia = team("naprzod-syrynia", "Naprzód Syrynia")
    private val lubomia = team("silesia-lubomia", "Silesia Lubomia")

    private fun match(id: String, team: String, home: String, away: String, isHome: Boolean, date: String = "2026-11-11") =
        MatchDto(
            id = id, teamId = team, competition = "VII liga, Kolejka 14", date = date, time = null,
            home = home, away = away, isHome = isHome, homeScore = null, awayScore = null,
            scoreNote = null, status = "SCHEDULED",
        ).toDomainOrNull()!!

    @Test
    fun `clubs of one sport are told apart by name`() {
        val all = listOf(lubomia, syrynia, bukow)
        assertEquals("Naprzód Syrynia", teamLabel(syrynia, all))
        assertEquals("Wypoczynek Buków", teamLabel(bukow, all))
    }

    @Test
    fun `one team per sport keeps the sport as its label, as in Rybnik`() {
        val row = team("row-1964", "ROW 1964 Rybnik")
        val zuzel = team("row-zuzel", "INNPRO ROW Rybnik", SportKind.SPEEDWAY)
        assertEquals(SportKind.FOOTBALL.label, teamLabel(row, listOf(row, zuzel)))
        assertEquals(SportKind.SPEEDWAY.label, teamLabel(zuzel, listOf(row, zuzel)))
    }

    @Test
    fun `a derby is listed once, from the home side`() {
        val home = match("wypoczynek-bukow-2026-11-11-naprzod-syrynia", "wypoczynek-bukow",
            "Wypoczynek Buków", "Naprzód Syrynia", isHome = true)
        val away = match("naprzod-syrynia-2026-11-11-wypoczynek-bukow", "naprzod-syrynia",
            "Wypoczynek Buków", "Naprzód Syrynia", isHome = false)
        val other = match("silesia-lubomia-2026-11-11-x", "silesia-lubomia",
            "Silesia Lubomia", "Unia Racibórz", isHome = true)
        assertEquals(
            listOf(home.id, other.id),
            withoutDerbyCopies(listOf(away, home, other)).map { it.id },
        )
    }

    @Test
    fun `the home card is titled by the club when sports repeat`() {
        val m = match("naprzod-syrynia-2026-10-17-rozwoj", "naprzod-syrynia",
            "Rozwój Bełsznica", "Naprzód Syrynia", isHome = false, date = "2026-10-17")
        val pick = selectHighlight(listOf(m), listOf(lubomia, syrynia, bukow), LocalDate.parse("2026-10-11"))!!
        assertEquals("Naprzód Syrynia", pick.label)
    }
}
