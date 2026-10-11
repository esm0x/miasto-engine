package com.adminstack.miasto.ui.places

import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.AccountBalance
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.EventAvailable
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import com.adminstack.miasto.Graph
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.data.places.Place
import com.adminstack.miasto.data.places.PlaceStatus
import com.adminstack.miasto.data.places.PolishHolidays
import com.adminstack.miasto.data.places.describe
import com.adminstack.miasto.data.places.hoursLines
import com.adminstack.miasto.data.places.statusAt
import com.adminstack.miasto.ui.common.EmptyState
import com.adminstack.miasto.ui.common.ErrorBanner
import com.adminstack.miasto.ui.common.openExternalLink
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.LocalDateTime

/** Green and grey that read on both themes; the status is also in words, never colour alone. */
internal val OPEN_COLOUR = Color(0xFF15803D)
internal val CLOSED_COLOUR = Color(0xFF9CA3AF)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlacesScreen(onBack: () -> Unit) {
    val payload by Graph.placesRepo.data.collectAsState()
    val state by Graph.placesRepo.state.collectAsState()
    val places = remember(payload) { Graph.placesRepo.places() }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var openOnly by rememberSaveable { mutableStateOf(false) }

    // "Otwarte do 15:30" has to turn into "Zamknięte" at 15:30 without anyone pulling.
    var now by remember { mutableStateOf(LocalDateTime.now()) }
    LaunchedEffect(Unit) {
        Graph.placesRepo.refresh()
        while (true) {
            delay(30_000)
            now = LocalDateTime.now()
        }
    }

    val shown = places.filter { !openOnly || it.statusAt(now) is PlaceStatus.Open }
    val holiday = PolishHolidays.isHoliday(now.toLocalDate())

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(City.config.places?.title ?: "Co dziś otwarte") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Wstecz")
                    }
                },
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            state.error?.let { ErrorBanner(it) { scope.launch { Graph.placesRepo.refresh() } } }
            if (places.isEmpty()) {
                EmptyState(Icons.Outlined.Schedule, "Brak danych o godzinach otwarcia")
                return@Column
            }
            Row(Modifier.padding(horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                FilterChip(
                    selected = openOnly,
                    onClick = { openOnly = !openOnly },
                    label = { Text("Tylko otwarte teraz") },
                )
            }
            if (holiday) {
                Text(
                    "Dziś święto. Miejsca zamknięte w święta pokazujemy jako zamknięte, " +
                        "pozostałe mogą mieć inne godziny niż zwykle.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                )
            }
            LazyColumn {
                if (shown.isEmpty()) {
                    item {
                        Text(
                            "O tej porze wszystko jest zamknięte.",
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(16.dp),
                        )
                    }
                }
                items(shown, key = { it.id }) { place ->
                    PlaceCard(
                        place = place,
                        now = now,
                        onLink = { openExternalLink(context, it) },
                        onCall = { number ->
                            runCatching { context.startActivity(Intent(Intent.ACTION_DIAL, "tel:$number".toUri())) }
                        },
                    )
                }
                item {
                    Text(
                        "Godziny przepisane ze strony miasta. Przed dłuższą wyprawą warto " +
                            "sprawdzić je u źródła.",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(16.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun PlaceCard(place: Place, now: LocalDateTime, onLink: (String) -> Unit, onCall: (String) -> Unit) {
    val status = place.statusAt(now)
    val isOffice = place.kind == "URZAD"
    Card(
        colors = if (isOffice) {
            CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        } else {
            CardDefaults.cardColors()
        },
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
    ) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (isOffice) {
                    Icon(Icons.Outlined.AccountBalance, null, Modifier.size(20.dp))
                    Spacer(Modifier.width(8.dp))
                }
                Text(
                    place.name,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f),
                )
            }
            Spacer(Modifier.height(6.dp))
            StatusLine(status, now)
            place.address?.let {
                Spacer(Modifier.height(4.dp))
                Text(it, style = MaterialTheme.typography.bodySmall)
            }
            val lines = place.hoursLines()
            if (lines.isNotEmpty()) {
                Spacer(Modifier.height(4.dp))
                Text(
                    lines.joinToString("\n"),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            place.note?.let {
                Spacer(Modifier.height(6.dp))
                Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            place.bookingUrl?.let { booking ->
                Spacer(Modifier.height(10.dp))
                Button(onClick = { onLink(booking) }) {
                    Icon(Icons.Outlined.EventAvailable, null, Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Umów wizytę")
                }
            }
            Row {
                place.phone?.takeIf { it.isNotBlank() }?.let { number ->
                    TextButton(onClick = { onCall(number) }) {
                        Icon(Icons.Outlined.Call, null, Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text(number)
                    }
                }
                place.url?.let { url ->
                    TextButton(onClick = { onLink(url) }) {
                        Icon(Icons.Outlined.Language, null, Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("Strona")
                    }
                }
            }
        }
    }
}

@Composable
internal fun StatusLine(status: PlaceStatus, now: LocalDateTime) {
    val colour = when (status) {
        is PlaceStatus.Open -> OPEN_COLOUR
        else -> CLOSED_COLOUR
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(10.dp).background(colour, CircleShape))
        Spacer(Modifier.width(8.dp))
        Text(
            status.describe(now),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (status is PlaceStatus.Open) FontWeight.SemiBold else FontWeight.Normal,
        )
    }
}
