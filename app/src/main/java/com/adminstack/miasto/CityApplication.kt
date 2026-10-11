package com.adminstack.miasto

import kotlinx.coroutines.flow.combine
import com.adminstack.miasto.data.river.RiverRepository
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.data.announce.AnnouncementRepository
import android.app.Application
import android.content.Context
import androidx.glance.appwidget.updateAll
import androidx.room.Room
import com.adminstack.miasto.core.prefs.UserPrefs
import com.adminstack.miasto.data.RemoteEventRepository
import com.adminstack.miasto.data.air.AirQualityRepository
import com.adminstack.miasto.data.news.NewsRepository
import com.adminstack.miasto.data.outages.OutageRepository
import com.adminstack.miasto.data.points.WastePointsRepository
import com.adminstack.miasto.data.sport.SportRepository
import com.adminstack.miasto.data.transit.TransitDb
import com.adminstack.miasto.data.transit.TransitRepository
import com.adminstack.miasto.data.waste.WasteRepository
import com.adminstack.miasto.widget.WasteWidget
import com.adminstack.miasto.work.ReminderAlarms
import com.adminstack.miasto.work.Reminders
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

class CityApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Graph.init(this)
        Reminders.createChannels(this)
        Graph.scope.launch { Reminders.rescheduleAll(this@CityApplication) }
    }
}

/**
 * Poor man's DI. Worth replacing with Hilt once anything here needs a real lifecycle,
 * but the whole graph is process-scoped singletons, so a manual object still fits.
 */
object Graph {

    lateinit var eventRepo: RemoteEventRepository private set
    lateinit var wasteRepo: WasteRepository private set
    lateinit var newsRepo: NewsRepository private set
    lateinit var transitRepo: TransitRepository private set
    lateinit var airRepo: AirQualityRepository private set
    lateinit var outageRepo: OutageRepository private set
    lateinit var sportRepo: SportRepository private set
    lateinit var pointsRepo: WastePointsRepository private set
    lateinit var announceRepo: AnnouncementRepository private set
    lateinit var riverRepo: RiverRepository private set
    lateinit var prefs: UserPrefs private set

    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun init(appContext: Context) {
        if (::eventRepo.isInitialized) return
        // First, before any repository asks where its data lives.
        City.init(appContext)

        val db = Room.databaseBuilder(appContext, TransitDb::class.java, "transit.db")
            .fallbackToDestructiveMigration()
            .build()

        eventRepo = RemoteEventRepository(appContext)
        wasteRepo = WasteRepository(appContext)
        newsRepo = NewsRepository(appContext)
        transitRepo = TransitRepository(appContext, db)
        airRepo = AirQualityRepository()
        outageRepo = OutageRepository()
        sportRepo = SportRepository(appContext)
        pointsRepo = WastePointsRepository(appContext)
        announceRepo = AnnouncementRepository(appContext)
        riverRepo = RiverRepository()
        prefs = UserPrefs(appContext)

        // A widget only redraws on its own half-hourly tick, so without this someone picks
        // an address, goes back to the home screen and finds "wybierz adres" still there.
        // The first emission also refreshes it whenever the app is opened.
        scope.launch {
            prefs.settings
                .map { it.wasteAddress }
                .distinctUntilChanged()
                .collect { runCatching { WasteWidget().updateAll(appContext) } }
        }

        // When a new year's schedule renames a rejon, the saved address is matched again
        // and its id updated, so everything keyed on it (reminder ledger, widget) follows.
        // An address that no longer matches anything is left alone; the waste screen
        // asks for it to be picked again.
        scope.launch {
            combine(wasteRepo.data, prefs.settings.map { it.wasteAddress }.distinctUntilChanged()) { _, a -> a }
                .collect { address ->
                    address ?: return@collect
                    val schedule = wasteRepo.schedule()
                    if (schedule.isEmpty || schedule.byId(address.rejonId) != null) return@collect
                    val rejon = schedule.rejonFor(address) ?: return@collect
                    prefs.setWasteAddress(address.copy(rejonId = rejon.id))
                }
        }

        // The alarm is booked for a specific hour, so moving the slider has to re-book it;
        // otherwise the reminder keeps arriving at the old time until the next reboot.
        scope.launch {
            prefs.settings
                .map { it.wasteReminderHour }
                .distinctUntilChanged()
                .collect { hour -> ReminderAlarms.schedule(appContext, hour) }
        }

        // Cached payloads first so a cold start renders real content instead of spinners.
        scope.launch {
            listOf(eventRepo, wasteRepo, newsRepo, transitRepo, sportRepo, pointsRepo, announceRepo)
                .forEach { it.loadCache() }
            if (City.config.hasTransit) transitRepo.checkReady()
            eventRepo.refresh()
            wasteRepo.refresh()
            newsRepo.refresh()
            airRepo.refresh()
            riverRepo.refresh()
            sportRepo.refresh()
            pointsRepo.refresh()
            announceRepo.refresh()
            // Fresh air reading and schedule: worth one more widget redraw.
            runCatching { WasteWidget().updateAll(appContext) }
        }
    }
}
