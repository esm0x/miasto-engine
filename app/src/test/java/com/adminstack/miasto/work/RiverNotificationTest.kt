package com.adminstack.miasto.work

import com.adminstack.miasto.core.city.RiverStation
import com.adminstack.miasto.data.river.GaugeReading
import com.adminstack.miasto.data.river.RiverLevel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDateTime

/**
 * The flood alert cannot be tried on a real river on demand, so every case it has to get
 * right is here, with the thresholds of the real Krzyżanowice gauge (360 / 500 cm).
 */
class RiverNotificationTest {

    private val now = LocalDateTime.parse("2026-10-10T19:40")
    private val krzyzanowice = RiverStation(id = "149180010", name = "Krzyżanowice", home = true)
    private val olza = RiverStation(id = "149180300", name = "Olza")

    private fun reading(
        cm: Int?,
        station: RiverStation = krzyzanowice,
        at: LocalDateTime = now.minusMinutes(20),
    ) = GaugeReading(station, "Odra", cm, warningCm = 360, alarmCm = 500, measuredAt = at)

    private fun pick(vararg readings: GaugeReading, ledger: Set<String> = emptySet()) =
        NotificationRules.riverToNotify(readings.toList(), ledger, now)
            .map { (r, level) -> "${r.station.name}-$level" }

    @Test
    fun `a normal river stays quiet`() {
        assertEquals(emptyList<String>(), pick(reading(72), reading(359, olza)))
    }

    @Test
    fun `warning and alarm are announced, at the threshold itself too`() {
        assertEquals(listOf("Krzyżanowice-WARNING"), pick(reading(360)))
        assertEquals(listOf("Krzyżanowice-ALARM"), pick(reading(500)))
    }

    @Test
    fun `each gauge over its level gets its own notification`() {
        assertEquals(
            listOf("Krzyżanowice-WARNING", "Olza-ALARM"),
            pick(reading(420), reading(610, olza)),
        )
    }

    /** Every three hours the worker runs again; the ledger keeps it to one per day. */
    @Test
    fun `the same level is not repeated the same day`() {
        val first = NotificationRules.riverToNotify(listOf(reading(420)), emptySet(), now)
        val ledger = first.map { (r, level) -> NotificationRules.riverKey(now.toLocalDate(), r, level) }.toSet()
        assertEquals(emptyList<String>(), pick(reading(430), ledger = ledger))
    }

    @Test
    fun `rising from warning to alarm is a new message`() {
        val ledger = setOf(NotificationRules.riverKey(now.toLocalDate(), reading(420), RiverLevel.WARNING))
        assertEquals(listOf("Krzyżanowice-ALARM"), pick(reading(505), ledger = ledger))
    }

    @Test
    fun `a river still high the next day is announced again`() {
        val yesterday = setOf(NotificationRules.riverKey(now.toLocalDate().minusDays(1), reading(420), RiverLevel.WARNING))
        assertEquals(listOf("Krzyżanowice-WARNING"), pick(reading(420), ledger = yesterday))
    }

    /** A gauge that went silent at its peak must not keep sounding as if it were live. */
    @Test
    fun `a stale or missing reading never alarms`() {
        assertEquals(emptyList<String>(), pick(reading(520, at = now.minusHours(7)), reading(null)))
    }

    @Test
    fun `the ledger key survives pruning`() {
        val key = NotificationRules.riverKey(now.toLocalDate(), reading(420), RiverLevel.WARNING)
        assertTrue(key in NotificationRules.prune(setOf(key), now.toLocalDate()))
    }

    @Test
    fun `the text reads right in Polish and in metres`() {
        assertEquals(
            "Odra, Krzyżanowice: stan ostrzegawczy",
            NotificationRules.riverTitle("Odra", reading(372), RiverLevel.WARNING),
        )
        assertEquals("3,72 m, próg 3,60 m · IMGW", NotificationRules.riverText(reading(372), RiverLevel.WARNING))
        assertEquals(
            "Odra, Krzyżanowice: stan alarmowy",
            NotificationRules.riverTitle("Odra", reading(512), RiverLevel.ALARM),
        )
        assertEquals("5,12 m, próg 5,00 m · IMGW", NotificationRules.riverText(reading(512), RiverLevel.ALARM))
    }
}
