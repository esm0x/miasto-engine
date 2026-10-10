package com.adminstack.miasto.data.river

import com.adminstack.miasto.core.city.RiverStation
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.LocalDateTime

class RiverTest {

    private val station = RiverStation(id = "149180010", name = "Krzyżanowice", home = true)

    /** The real answer for Krzyżanowice on 10 October 2026, trimmed. */
    private val body = """[{"id_stacji":"149180010","stacja":"Krzyżanowice","rzeka":"Odra",
        "stan_alarmowy":"500","stan_ostrzegawczy":"360","stan_wody":"72",
        "stan_wody_data_pomiaru":"2026-10-10 19:20:00","przeplyw":"13.5"}]"""

    private fun reading(level: Int?, at: LocalDateTime? = LocalDateTime.of(2026, 10, 10, 19, 20)) =
        GaugeReading(station, "Odra", level, warningCm = 360, alarmCm = 500, measuredAt = at)

    private val now = LocalDateTime.of(2026, 10, 10, 19, 40)

    @Test
    fun `parses the IMGW answer`() {
        val r = RiverRepository.parse(station, body)
        assertEquals("Odra", r.river)
        assertEquals(72, r.levelCm)
        assertEquals(360, r.warningCm)
        assertEquals(500, r.alarmCm)
        assertEquals(LocalDateTime.of(2026, 10, 10, 19, 20), r.measuredAt)
        assertEquals(288, r.marginToWarningCm)
    }

    @Test
    fun `thresholds are the gauge's own and inclusive`() {
        assertEquals(RiverLevel.NORMAL, reading(359).level(now))
        assertEquals(RiverLevel.WARNING, reading(360).level(now))
        assertEquals(RiverLevel.WARNING, reading(499).level(now))
        assertEquals(RiverLevel.ALARM, reading(500).level(now))
    }

    @Test
    fun `an old or missing reading is unknown, never normal`() {
        assertEquals(RiverLevel.UNKNOWN, reading(72, at = now.minusHours(7)).level(now))
        assertEquals(RiverLevel.UNKNOWN, reading(null).level(now))
        assertEquals(RiverLevel.UNKNOWN, reading(72, at = null).level(now))
    }

    @Test
    fun `a gauge without thresholds is just a reading`() {
        val r = GaugeReading(station, "Olza", 114, warningCm = null, alarmCm = null, measuredAt = now)
        assertEquals(RiverLevel.NORMAL, r.level(now))
        assertNull(r.marginToWarningCm)
    }

    @Test
    fun `the worst gauge decides, and unknown does not hide an alarm`() {
        val ok = reading(100, at = LocalDateTime.now())
        val alarm = reading(520, at = LocalDateTime.now())
        val stale = reading(100, at = LocalDateTime.now().minusDays(1))
        assertEquals(RiverLevel.ALARM, RiverState(readings = listOf(ok, stale, alarm)).worst)
        assertEquals(RiverLevel.NORMAL, RiverState(readings = listOf(stale, ok)).worst)
        assertEquals(RiverLevel.UNKNOWN, RiverState(readings = listOf(stale)).worst)
    }
}
