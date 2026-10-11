package com.adminstack.miasto.work

import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.data.announce.shouldNotify
import android.Manifest
import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.adminstack.miasto.Graph
import com.adminstack.miasto.MainActivity
import com.adminstack.miasto.R
import com.adminstack.miasto.core.prefs.Settings
import com.adminstack.miasto.data.outages.OutageKind
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.time.Duration
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.util.concurrent.TimeUnit

object Reminders {

    const val CHANNEL_WASTE = "waste"
    const val CHANNEL_EVENTS = "events"
    const val CHANNEL_SMOG = "smog"
    const val CHANNEL_ALERTS = "alerts"
    const val CHANNEL_OUTAGES = "outages"
    const val CHANNEL_APP = "app"
    const val CHANNEL_RIVER = "river"
    const val CHANNEL_GAZETTE = "gazette"

    /**
     * Only the channels this city can use: the system lists every channel in the app's
     * settings, and a "Stan rzeki" switch in a town with no river module is a dead one.
     * A channel left over from a module the city has since dropped is removed.
     */
    fun createChannels(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val mgr = context.getSystemService(NotificationManager::class.java) ?: return
        val city = City.config
        data class Channel(val id: String, val name: String, val desc: String, val wanted: Boolean)
        listOf(
            Channel(CHANNEL_WASTE, "Wywóz odpadów", "Przypomnienie wieczorem przed wywozem", city.modules.waste),
            Channel(CHANNEL_EVENTS, "Ulubione wydarzenia", "Przypomnienie dzień przed wydarzeniem", city.modules.events),
            Channel(CHANNEL_SMOG, "Jakość powietrza", "Ostrzeżenia o smogu", city.hasAir),
            Channel(CHANNEL_ALERTS, alertsChannelName(), "Awarie i utrudnienia", city.modules.news),
            Channel(CHANNEL_OUTAGES, "Wyłączenia prądu", "Wyłączenia pod Twoim adresem", city.hasOutages),
            Channel(CHANNEL_APP, "Od autora aplikacji", "Ważne informacje o aplikacji, np. o aktualizacjach", true),
            Channel(
                CHANNEL_GAZETTE,
                city.gazette?.let { "Nowy numer: ${it.title}" } ?: "Nowy numer gazety",
                "Gdy miasto opublikuje kolejny numer",
                city.hasGazette,
            ),
            Channel(
                CHANNEL_RIVER,
                city.river?.let { "Stan ${it.nameGenitive}" } ?: "Stan rzeki",
                "Przekroczenie stanu ostrzegawczego lub alarmowego",
                city.hasRiver,
            ),
        ).forEach { c ->
            if (c.wanted) {
                mgr.createNotificationChannel(
                    NotificationChannel(c.id, c.name, NotificationManager.IMPORTANCE_DEFAULT).apply {
                        description = c.desc
                    }
                )
            } else {
                mgr.deleteNotificationChannel(c.id)
            }
        }
    }

    /** "Komunikaty miasta", "Komunikaty gminy": a village is not a town. */
    fun alertsChannelName(): String = "Komunikaty ${City.config.authorityGenitive}"

    /** Which screen a tapped reminder should open. Read by MainActivity. */
    const val EXTRA_DESTINATION = "miasto.destination"
    const val DEST_HOME = "home"
    const val DEST_WASTE = "waste"
    const val DEST_EVENTS = "events"
    const val DEST_NEWS = "news"
    const val DEST_AIR = "air"
    const val DEST_RIVER = "river"
    const val DEST_GAZETTE = "gazette"

    const val GROUP_ALERTS = "com.adminstack.miasto.ALERTS"
    private const val MAX_SUMMARY_LINES = 5

    /**
     * Two mechanisms on purpose, because they fail differently.
     *
     * The periodic worker is the safety net: it survives reboots on its own and catches
     * smog, city alerts and power cuts, none of which care about the exact minute. The
     * daily alarm carries the reminders that do have a deadline, because WorkManager's
     * periodic interval is a floor, not a promise, and Doze stretches it further.
     */
    fun rescheduleAll(context: Context) {
        val wm = WorkManager.getInstance(context)
        // The single-city app enqueued this as "daily-reminders" with its worker under
        // com.adminstack.rybnik. WorkManager stores the class name, so an install
        // updated to the engine would keep failing to instantiate the old one. A new
        // name plus cancelling the old makes the move clean; a no-op everywhere else.
        wm.cancelUniqueWork("daily-reminders")
        wm.enqueueUniquePeriodicWork(
            "reminders",
            ExistingPeriodicWorkPolicy.UPDATE,
            // Three hours rather than six: the feed itself updates every six, so this
            // halves the wait between an alert being published and reaching the phone.
            // It is cheap now that the ledger stops every extra run from repeating itself.
            PeriodicWorkRequestBuilder<DailyReminderWorker>(3, TimeUnit.HOURS)
                .setInitialDelay(nextRunDelayMinutes(), TimeUnit.MINUTES)
                .build(),
        )
        rescheduleAlarm(context)
    }

    /** Books the daily alarm at the hour the user picked for the waste reminder. */
    fun rescheduleAlarm(context: Context) {
        Graph.scope.launch {
            val hour = runCatching { Graph.prefs.settings.first().wasteReminderHour }
                .getOrDefault(Settings.DEFAULT_WASTE_HOUR)
            ReminderAlarms.schedule(context, hour)
        }
    }

    /** Aim the first run at the top of the next hour so reminders land predictably. */
    private fun nextRunDelayMinutes(): Long {
        val now = LocalDateTime.now()
        val next = now.truncatedTo(java.time.temporal.ChronoUnit.HOURS).plusHours(1)
        return Duration.between(now, next).toMinutes().coerceAtLeast(1)
    }

    /**
     * @param destination which screen the tap should open, one of the DEST_ constants.
     */
    /**
     * @return whether it was actually posted. Only then may the caller record it in the
     *   ledger: a reminder swallowed for lack of permission was never delivered, and
     *   marking it sent would lose it for good once the permission is granted.
     */
    // Checked: canPost() runs first and returns early without POST_NOTIFICATIONS, and a
    // permission revoked in between surfaces as a SecurityException caught by runCatching.
    // Lint cannot see a check made in a helper, hence the suppression.
    @SuppressLint("MissingPermission")
    fun notify(
        context: Context,
        channel: String,
        id: Int,
        title: String,
        text: String,
        destination: String,
        group: String? = null,
    ): Boolean {
        if (!canPost(context)) return false

        val notification = NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setAutoCancel(true)
            .setContentIntent(openApp(context, id, destination))
            .apply { group?.let { setGroup(it) } }
            .build()

        return runCatching { NotificationManagerCompat.from(context).notify(id, notification) }
            .isSuccess
    }

    /**
     * The header of a stack of alerts. Android only folds notifications together under
     * one of these; without it, three alerts arrive as three unrelated banners.
     */
    // Checked: canPost() runs first and returns early without POST_NOTIFICATIONS, and a
    // permission revoked in between surfaces as a SecurityException caught by runCatching.
    // Lint cannot see a check made in a helper, hence the suppression.
    @SuppressLint("MissingPermission")
    fun notifyGroupSummary(
        context: Context,
        channel: String,
        id: Int,
        group: String,
        title: String,
        lines: List<String>,
        destination: String,
    ) {
        if (!canPost(context)) return
        val style = NotificationCompat.InboxStyle().setBigContentTitle(title)
        lines.take(MAX_SUMMARY_LINES).forEach { style.addLine(it) }
        if (lines.size > MAX_SUMMARY_LINES) {
            style.setSummaryText("i jeszcze ${lines.size - MAX_SUMMARY_LINES}")
        }
        val notification = NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(lines.firstOrNull().orEmpty())
            .setStyle(style)
            .setGroup(group)
            .setGroupSummary(true)
            .setAutoCancel(true)
            .setContentIntent(openApp(context, id, destination))
            .build()
        runCatching { NotificationManagerCompat.from(context).notify(id, notification) }
    }

    /**
     * One id per alert, so a second alert sits beside the first instead of replacing it,
     * which is what the single shared id used to do. Kept above 0x10000000 so it cannot
     * collide with the fixed ids of the other reminder types.
     */
    fun alertNotificationId(alertId: String): Int = 0x10000000 or (alertId.hashCode() and 0x0FFFFFFF)

    private fun canPost(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    /**
     * Without this a reminder is a dead end: tapping it does nothing at all, and even
     * setAutoCancel has no effect, because there is no click for it to follow.
     *
     * [id] doubles as the request code. PendingIntents are matched on requestCode, action
     * and data, and *not* on extras — reuse one code for every reminder and Android hands
     * back the first PendingIntent it made, so the smog notification would open whichever
     * screen the waste one asked for.
     */
    private fun openApp(context: Context, id: Int, destination: String): PendingIntent {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(EXTRA_DESTINATION, destination)
        }
        return PendingIntent.getActivity(
            context,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }
}

/**
 * One periodic worker covers all four reminder types. They share a cadence and each check
 * is cheap, so separate workers would only multiply scheduling overhead.
 */
class DailyReminderWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    /**
     * The daily alarm and the periodic job can both start this worker, and WorkManager
     * will run them side by side. Without the lock both would read the ledger before
     * either wrote to it, and the same reminder would arrive twice.
     */
    override suspend fun doWork(): Result = runLock.withLock {
        val settings = Graph.prefs.settings.first()
        val ledger = settings.notifiedKeys.toMutableSet()
        val before = ledger.toSet()

        // A switch can be on for a module this city lacks: the defaults are all true.
        val city = City.config
        if (city.modules.waste && settings.notifyWaste) {
            runCatching { checkWaste(settings.wasteReminderHour, ledger) }
        }
        if (city.modules.events && settings.notifyEvents) runCatching { checkEvents(ledger) }
        if (city.hasAir && settings.notifySmog) runCatching { checkSmog(settings.smogThreshold, ledger) }
        if (city.modules.news && settings.notifyCityAlerts) runCatching { checkAlerts(ledger) }
        if (city.hasOutages && settings.notifyOutages) runCatching { checkOutages(ledger) }
        if (city.hasRiver && settings.notifyRiver) runCatching { checkRiver(ledger) }
        if (city.hasGazette) runCatching { checkGazette(settings.notifyGazette) }
        // No switch in the app's settings: it is rare, and its own system channel can be
        // silenced like any other.
        runCatching { checkAnnouncement() }

        val pruned = NotificationRules.prune(ledger, LocalDate.now())
        if (pruned != before) Graph.prefs.setNotifiedKeys(pruned)
        Result.success()
    }

    /**
     * Once per collection. Since 1.2.0 both the 18:00 alarm and the periodic job run after
     * the reminder hour, and each would have announced the same bins.
     */
    private suspend fun checkWaste(reminderHour: Int, ledger: MutableSet<String>) {
        val address = Graph.prefs.settings.first().wasteAddress ?: return
        if (LocalTime.now().hour < reminderHour) return
        val tomorrow = LocalDate.now().plusDays(1)
        val key = NotificationRules.key(tomorrow, "waste", address.rejonId)
        if (key in ledger) return

        Graph.wasteRepo.refresh()
        val next = Graph.wasteRepo.schedule()
            .collections(address, tomorrow, tomorrow)
            .firstOrNull() ?: return

        val posted = Reminders.notify(
            applicationContext, Reminders.CHANNEL_WASTE, NOTIF_WASTE,
            "Jutro wywóz odpadów",
            next.types.joinToString(", ") { it.label } + " · ${address.pretty}",
            Reminders.DEST_WASTE,
        )
        if (posted) ledger += key
    }

    /** Each favourite once; a favourite added later the same day still gets its turn. */
    private suspend fun checkEvents(ledger: MutableSet<String>) {
        val favourites = Graph.prefs.settings.first().favouriteEventIds
        if (favourites.isEmpty()) return
        Graph.eventRepo.refresh()
        val tomorrow = LocalDate.now().plusDays(1)
        val due = Graph.eventRepo.snapshot()
            .filter { it.id in favourites && it.start.toLocalDate() == tomorrow }
            .filter { NotificationRules.key(tomorrow, "event", it.id) !in ledger }
        if (due.isEmpty()) return

        // One event already has its title in the headline; repeating it said nothing new,
        // so the line gives where instead.
        val text = if (due.size == 1) {
            listOf(due.first().start.toLocalTime().toString(), due.first().venue)
                .filter { it.isNotBlank() }.joinToString(" · ")
        } else {
            due.joinToString("\n") { "${it.start.toLocalTime()} · ${it.title}" }
        }
        val posted = Reminders.notify(
            applicationContext, Reminders.CHANNEL_EVENTS, NOTIF_EVENTS,
            if (due.size == 1) "Jutro: ${due.first().title}" else "Jutro ${due.size} wydarzenia",
            text,
            Reminders.DEST_EVENTS,
        )
        if (posted) due.forEach { ledger += NotificationRules.key(tomorrow, "event", it.id) }
    }

    /**
     * Once a day while it lasts. Smog sits over Rybnik for days in winter, and with the
     * worker now running every three hours an unguarded check would sound eight times a day.
     */
    private suspend fun checkSmog(threshold: Int, ledger: MutableSet<String>) {
        val key = NotificationRules.key(LocalDate.now(), "smog", "pm10")
        if (key in ledger) return

        Graph.airRepo.refresh()
        val state = Graph.airRepo.state.value
        val pm10 = state.pm10 ?: return
        if (pm10.value < threshold) return

        // The user's own threshold can sit below the official information level, so the
        // index may still read "Dobre" when this fires. Announcing "Smog w Rybniku: Dobre"
        // contradicts itself, so the headline states the measurement and the body explains
        // why it arrived.
        val posted = Reminders.notify(
            applicationContext, Reminders.CHANNEL_SMOG, NOTIF_SMOG,
            "PM10 ${pm10.value.toInt()} µg/m³ ${City.config.locative}",
            "Powyżej Twojego progu $threshold µg/m³. Jakość powietrza: ${state.severity.label}.",
            Reminders.DEST_AIR,
        )
        if (posted) ledger += key
    }

    /**
     * Every new alert, each in its own notification, stacked under one header when there
     * are several. NotificationRules decides which; see there for why the old rule lost
     * most of them.
     */
    private suspend fun checkAlerts(ledger: MutableSet<String>) {
        Graph.newsRepo.refresh()
        Graph.prefs.pruneSeenAlerts(Graph.newsRepo.allIds())
        val settings = Graph.prefs.settings.first()

        val fresh = NotificationRules.alertsToNotify(
            items = Graph.newsRepo.items(settings.hiddenNewsIds),
            hidden = settings.hiddenNewsIds,
            seen = settings.seenAlertIds,
            ledger = ledger,
            now = LocalDateTime.now(),
        )
        if (fresh.isEmpty()) return

        var posted = false
        fresh.take(NotificationRules.MAX_ALERT_NOTIFICATIONS).forEach { alert ->
            posted = Reminders.notify(
                applicationContext, Reminders.CHANNEL_ALERTS,
                Reminders.alertNotificationId(alert.id),
                alert.title,
                listOfNotNull(alert.source, alert.summary?.takeIf { it.isNotBlank() })
                    .joinToString(" · "),
                Reminders.DEST_NEWS,
                group = Reminders.GROUP_ALERTS,
            ) || posted
        }
        if (fresh.size > 1) {
            Reminders.notifyGroupSummary(
                applicationContext, Reminders.CHANNEL_ALERTS, NOTIF_ALERTS,
                Reminders.GROUP_ALERTS,
                NotificationRules.newAlertsHeadline(fresh.size),
                fresh.map { it.title },
                Reminders.DEST_NEWS,
            )
        }
        // The overflow beyond the cap is in the summary, so it counts as announced too.
        if (posted) fresh.forEach { ledger += NotificationRules.alertKey(it) }
    }

    /** Only cuts starting within the next two days, each one once. */
    private suspend fun checkOutages(ledger: MutableSet<String>) {
        val address = Graph.prefs.settings.first().wasteAddress ?: return
        Graph.outageRepo.refresh(address)
        val soon = LocalDate.now().plusDays(2)
        fun keyOf(o: com.adminstack.miasto.data.outages.Outage) =
            NotificationRules.key(o.from.toLocalDate(), "outage", "${o.kind}-${o.from}")

        val next = Graph.outageRepo.state.value.outages
            .filter { !it.from.toLocalDate().isAfter(soon) }
            .firstOrNull { keyOf(it) !in ledger } ?: return

        val posted = Reminders.notify(
            applicationContext, Reminders.CHANNEL_OUTAGES, NOTIF_OUTAGES,
            if (next.kind == OutageKind.PLANNED) "Planowane wyłączenie prądu"
            else "Awaria zasilania",
            "${next.from.toLocalDate()} ${next.from.toLocalTime()} · ${address.pretty}",
            Reminders.DEST_HOME,
        )
        if (posted) ledger += keyOf(next)
    }

    /** Which gauges and how often: [NotificationRules.riverToNotify]. */
    private suspend fun checkRiver(ledger: MutableSet<String>) {
        Graph.riverRepo.refresh()
        val config = City.config.river ?: return
        val now = LocalDateTime.now()
        val high = NotificationRules.riverToNotify(Graph.riverRepo.state.value.readings, ledger, now)
        for ((reading, level) in high) {
            val key = NotificationRules.riverKey(now.toLocalDate(), reading, level)
            val posted = Reminders.notify(
                applicationContext, Reminders.CHANNEL_RIVER,
                NOTIF_RIVER + (config.stations.indexOf(reading.station).coerceAtLeast(0)),
                NotificationRules.riverTitle(config.name, reading, level),
                NotificationRules.riverText(reading, level),
                Reminders.DEST_RIVER,
            )
            if (posted) ledger += key
        }
    }

    /**
     * A new issue, once. The newest issue is recorded as known even with the switch off,
     * so turning it on later does not announce an issue from months ago.
     */
    private suspend fun checkGazette(enabled: Boolean) {
        Graph.gazetteRepo.refresh()
        val newest = Graph.gazetteRepo.newest() ?: return
        // Never record an implausible issue as known; see NotificationRules.gazetteToNotify.
        if (newest.year > LocalDate.now().year + 1 || newest.number !in 1..99) return
        val settings = Graph.prefs.settings.first()
        val issue = NotificationRules.gazetteToNotify(newest, settings.gazetteKnownId)
        val posted = issue != null && enabled && newest.id != settings.gazetteSeenId &&
            Reminders.notify(
                applicationContext, Reminders.CHANNEL_GAZETTE, NOTIF_GAZETTE,
                "Nowy numer: ${City.config.gazette?.title.orEmpty()}",
                "${issue.label}. Stuknij, żeby przeczytać.",
                Reminders.DEST_GAZETTE,
            )
        // Not posted for lack of permission: leave it unknown, so it is announced once allowed.
        if (posted || issue == null || !enabled || newest.id == settings.gazetteSeenId) {
            Graph.prefs.setGazetteKnown(newest.id)
        }
    }

    /** The developer's message, once, unless it was already read on the dashboard. */
    private suspend fun checkAnnouncement() {
        Graph.announceRepo.refresh()
        val announcement = Graph.announceRepo.current() ?: return
        val settings = Graph.prefs.settings.first()
        if (!announcement.shouldNotify(settings.announcementSeenId, settings.announcementDismissedId)) return
        val posted = Reminders.notify(
            applicationContext, Reminders.CHANNEL_APP, NOTIF_APP,
            announcement.title,
            announcement.body.orEmpty(),
            Reminders.DEST_HOME,
        )
        if (posted) Graph.prefs.markAnnouncementSeen(announcement.id)
    }

    private companion object {
        const val NOTIF_WASTE = 1001
        const val NOTIF_EVENTS = 1002
        const val NOTIF_SMOG = 1003
        const val NOTIF_ALERTS = 1004
        const val NOTIF_OUTAGES = 1005
        const val NOTIF_APP = 1006
        const val NOTIF_GAZETTE = 1007
        /** One id per gauge, 1100…, so two gauges over their levels both show. */
        const val NOTIF_RIVER = 1100

        val runLock = Mutex()
    }
}
