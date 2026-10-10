package com.adminstack.miasto.ui.river

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.adminstack.miasto.Graph
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.data.river.GaugeReading
import com.adminstack.miasto.data.river.RiverLevel
import com.adminstack.miasto.ui.common.ErrorBanner
import com.adminstack.miasto.ui.common.TIME_FMT
import com.adminstack.miasto.ui.common.humanLabel
import com.adminstack.miasto.ui.common.openExternalLink
import kotlinx.coroutines.launch

/** "1,80 m" for 180 cm: residents read river levels in metres, IMGW publishes cm. */
internal fun metres(cm: Int): String = "%.2f m".format(cm / 100.0).replace('.', ',')

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RiverScreen(onBack: () -> Unit) {
    val config = City.config.river ?: return
    val state by Graph.riverRepo.state.collectAsState()
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    LaunchedEffect(Unit) { Graph.riverRepo.refresh() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Stan ${config.nameGenitive}") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Wstecz")
                    }
                },
                actions = {
                    IconButton(onClick = { scope.launch { Graph.riverRepo.refresh() } }) {
                        Icon(Icons.Outlined.Refresh, contentDescription = "Odśwież")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            state.error?.let { ErrorBanner(it, onRetry = { scope.launch { Graph.riverRepo.refresh() } }) }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(16.dp).background(Color(state.worst.color), CircleShape))
                Spacer(Modifier.width(10.dp))
                Text(state.worst.label, style = MaterialTheme.typography.titleMedium)
            }

            // Upstream first, the order the water arrives in.
            for (station in config.stations) {
                val reading = state.readings.firstOrNull { it.station.id == station.id }
                if (reading != null) GaugeCard(reading)
            }

            config.note?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Text(
                "Dane: IMGW-PIB, pomiar co 10 minut. Stan ostrzegawczy i alarmowy wyznacza IMGW " +
                    "osobno dla każdego wodowskazu, więc centymetrów z różnych wodowskazów nie da się porównać.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            TextButton(onClick = { openExternalLink(context, "https://hydro.imgw.pl/") }) {
                Text("Mapa hydrologiczna IMGW")
            }
        }
    }
}

@Composable
private fun GaugeCard(reading: GaugeReading) {
    val level = reading.level()
    Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(12.dp).background(Color(level.color), CircleShape))
                Spacer(Modifier.width(8.dp))
                Column(Modifier.weight(1f)) {
                    Text(reading.station.name, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                    reading.station.where?.let {
                        Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                Text(
                    reading.levelCm?.let { metres(it) } ?: "brak",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            Spacer(Modifier.height(10.dp))
            LevelBar(reading)
            Spacer(Modifier.height(6.dp))
            Text(
                listOfNotNull(
                    reading.warningCm?.let { "ostrzegawczy ${metres(it)}" },
                    reading.alarmCm?.let { "alarmowy ${metres(it)}" },
                    reading.measuredAt?.let { "pomiar ${it.toLocalDate().humanLabel()}, ${it.toLocalTime().format(TIME_FMT)}" },
                ).joinToString(" · "),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (level == RiverLevel.NORMAL) {
                reading.marginToWarningCm?.takeIf { it > 0 }?.let {
                    Text(
                        "${metres(it)} do stanu ostrzegawczego",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

/** The level against the alarm mark, with the warning mark drawn in. */
@Composable
private fun LevelBar(reading: GaugeReading) {
    val alarm = reading.alarmCm ?: return
    val cm = reading.levelCm ?: return
    val fill = (cm.toFloat() / alarm).coerceIn(0f, 1f)
    val warn = reading.warningCm?.let { (it.toFloat() / alarm).coerceIn(0f, 1f) }
    Box(
        Modifier
            .fillMaxWidth()
            .height(10.dp)
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(5.dp)),
    ) {
        Box(
            Modifier
                .fillMaxWidth(fill)
                .fillMaxHeight()
                .background(Color(reading.level().color), RoundedCornerShape(5.dp)),
        )
        if (warn != null) {
            Row(Modifier.fillMaxSize()) {
                Spacer(Modifier.weight(warn.coerceAtLeast(0.001f)))
                Box(Modifier.width(2.dp).fillMaxHeight().background(Color(RiverLevel.WARNING.color)))
                Spacer(Modifier.weight((1f - warn).coerceAtLeast(0.001f)))
            }
        }
    }
}
