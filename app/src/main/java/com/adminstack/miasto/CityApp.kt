package com.adminstack.miasto

import com.adminstack.miasto.ui.river.RiverScreen
import com.adminstack.miasto.core.city.City
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.DirectionsBus
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.MoreHoriz
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextOverflow
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.adminstack.miasto.ui.events.EventDetailScreen
import com.adminstack.miasto.ui.events.EventListScreen
import com.adminstack.miasto.ui.home.HomeScreen
import com.adminstack.miasto.ui.more.AirScreen
import com.adminstack.miasto.ui.more.MoreScreen
import com.adminstack.miasto.ui.more.SettingsScreen
import com.adminstack.miasto.ui.more.SupportScreen
import com.adminstack.miasto.ui.news.NewsScreen
import com.adminstack.miasto.ui.points.WastePointsScreen
import com.adminstack.miasto.ui.gazette.GazetteScreen
import com.adminstack.miasto.ui.places.PlacesScreen
import com.adminstack.miasto.ui.sport.SportScreen
import com.adminstack.miasto.ui.transit.TransitScreen
import com.adminstack.miasto.ui.waste.AddressPickerScreen
import com.adminstack.miasto.ui.waste.WasteScreen
import com.adminstack.miasto.work.Reminders

private sealed class Tab(val route: String, val label: String, val icon: ImageVector) {
    data object Home : Tab("home", "Start", Icons.Outlined.Home)
    data object Events : Tab("events", "Wydarzenia", Icons.Outlined.CalendarMonth)
    data object Transit : Tab("transit", "Transport", Icons.Outlined.DirectionsBus)
    data object Waste : Tab("waste", "Śmieci", Icons.Outlined.Delete)
    data object More : Tab("more", "Więcej", Icons.Outlined.MoreHoriz)
}

/** Only the tabs this city has; Lubomia, with no buses, gets four. */
private val tabs: List<Tab>
    get() {
        val city = City.config
        return listOfNotNull(
            Tab.Home,
            Tab.Events.takeIf { city.modules.events },
            Tab.Transit.takeIf { city.hasTransit },
            Tab.Waste.takeIf { city.modules.waste },
            Tab.More,
        )
    }

private object Routes {
    const val NEWS = "news"
    const val AIR = "air"
    const val RIVER = "river"
    const val SETTINGS = "settings"
    const val FAVOURITES = "favourites"
    const val ADDRESS = "address"
    const val SUPPORT = "support"
    const val SPORT = "sport"
    const val POINTS = "points"
    const val GAZETTE = "gazette"
    const val PLACES = "places"
    const val EVENT_DETAIL = "event/{id}"
    fun event(id: String) = "event/$id"
}

@Composable
fun CityApp(
    notificationDestination: String? = null,
    onDestinationHandled: () -> Unit = {},
) {
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route

    // The bottom bar is for the five tabs only; detail screens own their whole viewport.
    val showBottomBar = currentRoute in tabs.map { it.route }

    // A tapped reminder should land where it is about, not just anywhere in the app.
    // Cleared once handled, otherwise returning to this screen would navigate again.
    // A destination this city does not have falls back to the dashboard.
    LaunchedEffect(notificationDestination) {
        val city = City.config
        when (notificationDestination) {
            null -> return@LaunchedEffect
            Reminders.DEST_WASTE ->
                navController.switchTab(if (city.modules.waste) Tab.Waste.route else Tab.Home.route)
            Reminders.DEST_EVENTS ->
                navController.switchTab(if (city.modules.events) Tab.Events.route else Tab.Home.route)
            Reminders.DEST_NEWS ->
                if (city.modules.news) navController.navigate(Routes.NEWS)
            Reminders.DEST_AIR ->
                if (city.hasAir) navController.navigate(Routes.AIR)
            Reminders.DEST_RIVER ->
                if (city.hasRiver) navController.navigate(Routes.RIVER)
            Reminders.DEST_GAZETTE ->
                if (city.hasGazette) navController.navigate(Routes.GAZETTE)
            else -> navController.switchTab(Tab.Home.route)
        }
        onDestinationHandled()
    }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    tabs.forEach { tab ->
                        val selected = backStack?.destination?.hierarchy?.any {
                            it.route == tab.route
                        } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = { if (!selected) navController.switchTab(tab.route) },
                            icon = { Icon(tab.icon, contentDescription = null) },
                            // At 130% font the labels wrapped mid-word, leaving a lone
                            // "t" from "Transport" on a second line. One line that
                            // truncates reads as a label; two lines read as a bug.
                            label = {
                                Text(tab.label, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            },
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Tab.Home.route,
            // Only the bottom bar's space is reserved here. Every screen brings its own
            // Scaffold + TopAppBar, which already consumes the status-bar inset — applying
            // the full innerPadding as well would inset the top twice and leave a gap.
            modifier = Modifier.padding(bottom = innerPadding.calculateBottomPadding()),
        ) {
            composable(Tab.Home.route) {
                HomeScreen(
                    onOpenWaste = { navController.switchTab(Tab.Waste.route) },
                    onOpenTransit = { navController.switchTab(Tab.Transit.route) },
                    onOpenEvents = { navController.switchTab(Tab.Events.route) },
                    onOpenNews = { navController.navigate(Routes.NEWS) },
                    onOpenAir = { navController.navigate(Routes.AIR) },
                    onOpenRiver = { navController.navigate(Routes.RIVER) },
                    onOpenSport = { navController.navigate(Routes.SPORT) },
                    onOpenGazette = { navController.navigate(Routes.GAZETTE) },
                    onOpenPlaces = { navController.navigate(Routes.PLACES) },
                    onEventClick = { navController.navigate(Routes.event(it)) },
                )
            }

            composable(Tab.Events.route) {
                EventListScreen(onEventClick = { navController.navigate(Routes.event(it)) })
            }

            composable(Tab.Transit.route) { TransitScreen() }

            composable(Tab.Waste.route) {
                WasteScreen(onPickAddress = { navController.navigate(Routes.ADDRESS) })
            }

            composable(Tab.More.route) {
                MoreScreen(
                    onOpenNews = { navController.navigate(Routes.NEWS) },
                    onOpenAir = { navController.navigate(Routes.AIR) },
                    onOpenRiver = { navController.navigate(Routes.RIVER) },
                    onOpenSport = { navController.navigate(Routes.SPORT) },
                    onOpenPoints = { navController.navigate(Routes.POINTS) },
                    onOpenGazette = { navController.navigate(Routes.GAZETTE) },
                    onOpenPlaces = { navController.navigate(Routes.PLACES) },
                    onOpenFavourites = { navController.navigate(Routes.FAVOURITES) },
                    onOpenSettings = { navController.navigate(Routes.SETTINGS) },
                    onOpenSupport = { navController.navigate(Routes.SUPPORT) },
                )
            }

            composable(Routes.NEWS) { NewsScreen() }

            composable(Routes.SPORT) { SportScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.POINTS) {
                WastePointsScreen(onBack = { navController.popBackStack() })
            }

            composable(Routes.GAZETTE) { GazetteScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.PLACES) { PlacesScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.SUPPORT) { SupportScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.AIR) { AirScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.RIVER) { RiverScreen(onBack = { navController.popBackStack() }) }

            composable(Routes.FAVOURITES) {
                EventListScreen(
                    onEventClick = { navController.navigate(Routes.event(it)) },
                    favouritesOnly = true,
                )
            }

            composable(Routes.SETTINGS) {
                SettingsScreen(
                    onBack = { navController.popBackStack() },
                    onPickAddress = { navController.navigate(Routes.ADDRESS) },
                )
            }

            composable(Routes.ADDRESS) {
                AddressPickerScreen(
                    onDone = { navController.popBackStack() },
                    onBack = { navController.popBackStack() },
                )
            }

            composable(Routes.EVENT_DETAIL) { entry ->
                val id = entry.arguments?.getString("id") ?: return@composable
                EventDetailScreen(eventId = id, onBack = { navController.popBackStack() })
            }
        }
    }
}

private fun NavHostController.switchTab(route: String) {
    navigate(route) {
        popUpTo(graph.startDestinationId) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
