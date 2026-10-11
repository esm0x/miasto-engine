package com.adminstack.miasto.ui.gazette

import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.outlined.PictureAsPdf
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.adminstack.miasto.Graph
import com.adminstack.miasto.core.city.City
import com.adminstack.miasto.core.net.sharedHttp
import com.adminstack.miasto.data.gazette.GazetteIssue
import com.adminstack.miasto.ui.common.EmptyState
import com.adminstack.miasto.ui.common.ErrorBanner
import com.adminstack.miasto.ui.common.openExternalLink
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.Request

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GazetteScreen(onBack: () -> Unit) {
    val config = City.config.gazette
    val payload by Graph.gazetteRepo.data.collectAsState()
    val state by Graph.gazetteRepo.state.collectAsState()
    val issues = remember(payload) { Graph.gazetteRepo.issues() }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) { Graph.gazetteRepo.refresh() }
    // Opening the kiosk is seeing the newest issue: the dashboard card has done its job.
    LaunchedEffect(issues.firstOrNull()?.id) {
        issues.firstOrNull()?.let { Graph.prefs.markGazetteSeen(it.id) }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(config?.title ?: "Gazeta") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Wstecz")
                    }
                },
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            state.error?.let { ErrorBanner(it) { scope.launch { Graph.gazetteRepo.refresh() } } }
            if (issues.isEmpty()) {
                EmptyState(Icons.AutoMirrored.Outlined.MenuBook, "Brak numerów", "Spróbuj odświeżyć za chwilę.")
                return@Column
            }
            LazyVerticalGrid(
                columns = GridCells.Adaptive(minSize = 150.dp),
                contentPadding = PaddingValues(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item(span = { GridItemSpan(maxLineSpan) }) {
                    NewestIssue(issues.first()) { openExternalLink(context, it.pdfUrl) }
                }
                if (issues.size > 1) {
                    item(span = { GridItemSpan(maxLineSpan) }) {
                        Text(
                            "Wcześniejsze numery",
                            style = MaterialTheme.typography.titleSmall,
                            modifier = Modifier.padding(top = 8.dp),
                        )
                    }
                    items(issues.drop(1), key = { it.id }) { issue ->
                        IssueTile(issue) { openExternalLink(context, issue.pdfUrl) }
                    }
                }
                item(span = { GridItemSpan(maxLineSpan) }) {
                    Text(
                        "Numery w PDF otwierają się w przeglądarce, ze strony miasta.",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(vertical = 8.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun NewestIssue(issue: GazetteIssue, onOpen: (GazetteIssue) -> Unit) {
    Card(
        onClick = { onOpen(issue) },
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Cover(issue.coverUrl, Modifier.width(110.dp))
            Spacer(Modifier.width(16.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    "NAJNOWSZY NUMER",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    issue.label,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
                Spacer(Modifier.height(12.dp))
                Button(onClick = { onOpen(issue) }) {
                    Icon(Icons.Outlined.PictureAsPdf, null, Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Czytaj")
                }
            }
        }
    }
}

@Composable
private fun IssueTile(issue: GazetteIssue, onOpen: () -> Unit) {
    Card(onClick = onOpen, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(10.dp)) {
            Cover(issue.coverUrl, Modifier.fillMaxWidth())
            Spacer(Modifier.height(8.dp))
            Text(
                issue.label,
                style = MaterialTheme.typography.labelMedium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

/** A cover is A4 upright; until it loads, or when it cannot, the same shape stays empty. */
@Composable
private fun Cover(url: String?, modifier: Modifier) {
    var bitmap by remember(url) { mutableStateOf(url?.let { CoverCache.get(it) }) }
    LaunchedEffect(url) {
        if (bitmap == null && url != null) bitmap = CoverCache.load(url)
    }
    Box(
        modifier
            .aspectRatio(0.707f)
            .clip(RoundedCornerShape(6.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant),
        contentAlignment = Alignment.Center,
    ) {
        val b = bitmap
        if (b != null) {
            Image(b, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
        } else {
            Icon(
                Icons.AutoMirrored.Outlined.MenuBook, null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(32.dp),
            )
        }
    }
}

/**
 * Covers are small PNGs on the city's site (about 50 KB). No image library for a dozen
 * thumbnails: OkHttp is already here, a memory cache is enough, and a cover that fails
 * leaves the placeholder. Only https, and nothing larger than [MAX_BYTES] is decoded.
 *
 * A small file is not a small image: a 100 KB PNG of 300 x 120000 pixels decodes to
 * 137 MB and crashes the screen when drawn. So the size is read first, anything not
 * shaped like a page or larger than [MAX_PIXELS] is refused, the sample size follows
 * the longer side, and the cache counts bytes, not covers.
 */
private object CoverCache {
    private const val MAX_BYTES = 3L * 1024 * 1024
    private const val MAX_PIXELS = 4_000_000L
    private const val TARGET_SIDE = 480
    private val cache = object : LruCache<String, ImageBitmap>(12 * 1024 * 1024) {
        override fun sizeOf(key: String, value: ImageBitmap): Int = value.width * value.height * 2
    }

    fun get(url: String): ImageBitmap? = cache.get(url)

    suspend fun load(url: String): ImageBitmap? = withContext(Dispatchers.IO) {
        if (!url.startsWith("https://")) return@withContext null
        runCatching {
            val bytes = sharedHttp.newCall(Request.Builder().url(url).build()).execute().use { r ->
                val body = r.body ?: return@use null
                if (!r.isSuccessful || body.contentLength() > MAX_BYTES) return@use null
                body.source().apply { request(MAX_BYTES + 1) }.buffer.let { buf ->
                    if (buf.size > MAX_BYTES) null else buf.readByteArray()
                }
            } ?: return@runCatching null
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
            val w = bounds.outWidth.toLong()
            val h = bounds.outHeight.toLong()
            if (w <= 0 || h <= 0 || w * h > MAX_PIXELS || h > 4 * w || w > 4 * h) return@runCatching null
            var sample = 1
            while (maxOf(w, h) / (sample * 2) >= TARGET_SIDE) sample *= 2
            val options = BitmapFactory.Options().apply {
                inSampleSize = sample
                inPreferredConfig = android.graphics.Bitmap.Config.RGB_565
            }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options)
                ?.asImageBitmap()
                ?.also { cache.put(url, it) }
        }.getOrNull()
    }
}
