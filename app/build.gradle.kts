import groovy.json.JsonSlurper
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization") version "2.0.21"
    id("com.google.devtools.ksp")
}

// Keystore lives outside the repo: keystore.properties is gitignored, and a missing
// file must not break a debug build for anyone who just cloned the project — the
// release type simply falls back to unsigned and Gradle says so at assembly time.
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

/**
 * One flavour per directory under cities/ that holds a city.json. Adding a city is
 * adding that directory; nothing here needs editing. The same file is copied into the
 * flavour's assets for the app to read at runtime (see CopyCityConfig below), so the
 * build and the running app cannot disagree about which city this is.
 */
data class CityDef(
    val slug: String,
    val appName: String,
    val applicationId: String,
    val versionCode: Int,
    val versionName: String,
    val primary: String,
)

@Suppress("UNCHECKED_CAST")
val cities: List<CityDef> = rootProject.file("cities").listFiles().orEmpty()
    .filter { File(it, "city.json").isFile }
    .sortedBy { it.name }
    .map { dir ->
        val json = JsonSlurper().parse(File(dir, "city.json")) as Map<String, Any?>
        val android = json["android"] as? Map<String, Any?>
            ?: error("cities/${dir.name}/city.json: missing \"android\" section")
        val theme = json["theme"] as? Map<String, Any?> ?: emptyMap()
        val slug = json["slug"] as String
        check(slug == dir.name) { "cities/${dir.name}/city.json: slug \"$slug\" must equal the directory name" }
        check(Regex("[a-z][a-z0-9]*").matches(slug)) { "slug \"$slug\": lowercase letters and digits only" }
        CityDef(
            slug = slug,
            appName = json["appName"] as String,
            applicationId = android["applicationId"] as String,
            versionCode = (android["versionCode"] as Number).toInt(),
            versionName = android["versionName"] as String,
            // Same default as ThemeColors.primary in CityConfig.kt.
            primary = theme["primary"] as? String ?: "#0B6E7F",
        )
    }

check(cities.isNotEmpty()) { "No cities/<slug>/city.json found: at least one city is required" }

android {
    namespace = "com.adminstack.miasto"
    compileSdk = 36

    defaultConfig {
        minSdk = 26
        targetSdk = 36
    }

    flavorDimensions += "city"
    productFlavors {
        cities.forEach { city ->
            create(city.slug) {
                dimension = "city"
                applicationId = city.applicationId
                versionCode = city.versionCode
                versionName = city.versionName
                resValue("string", "app_name", city.appName)
                // Background of the default launcher icon; a city with its own artwork
                // in app/src/<slug>/res simply never uses it.
                resValue("color", "city_primary", city.primary)
            }
        }
    }

    signingConfigs {
        create("release") {
            if (keystoreProps.getProperty("storeFile") != null) {
                storeFile = rootProject.file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = if (keystoreProps.getProperty("storeFile") != null) {
                signingConfigs.getByName("release")
            } else {
                null
            }
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures {
        compose = true
        // VERSION_CODE lets a developer announcement target only older builds.
        buildConfig = true
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.10.01")
    implementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.activity:activity-compose:1.9.3")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    implementation("androidx.navigation:navigation-compose:2.8.4")

    // Networking + JSON
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    // Room — timetables and waste schedules are too big for a flat file
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // DataStore — user settings: address, favourites, notification toggles
    implementation("androidx.datastore:datastore-preferences:1.1.1")

    // Glance — the home-screen widget. Its own composable world, not Compose UI.
    implementation("androidx.glance:glance-appwidget:1.1.1")
    implementation("androidx.glance:glance-material3:1.1.1")

    // WorkManager — waste/event/smog reminders
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    testImplementation("junit:junit:4.13.2")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

/**
 * Puts cities/<slug>/city.json into the APK's assets, where CityConfig.load reads it,
 * and every JSON file of data/<slug> under seed/, as the data a fresh install shows
 * before its first download (see CachedRemoteSource.loadCache).
 *
 * Careful with comments in this file: Kotlin block comments nest, so a path written
 * with a slash and an asterisk, like a glob, opens a second comment and silently turns
 * the rest of the script into one. That is how this task once vanished from the build.
 */
abstract class CopyCityConfig : DefaultTask() {
    @get:InputFile
    abstract val source: RegularFileProperty

    @get:InputFiles
    @get:Optional
    abstract val seedData: ConfigurableFileCollection

    @get:OutputDirectory
    abstract val outputDir: DirectoryProperty

    @TaskAction
    fun copy() {
        val out = outputDir.get().asFile
        out.deleteRecursively()
        out.mkdirs()
        source.get().asFile.copyTo(File(out, "city.json"), overwrite = true)
        val seed = File(out, "seed").apply { mkdirs() }
        seedData.files.filter { it.isFile }.forEach { it.copyTo(File(seed, it.name), overwrite = true) }
    }
}

androidComponents {
    onVariants { variant ->
        val slug = variant.productFlavors.first { it.first == "city" }.second
        val task = tasks.register<CopyCityConfig>(
            "copy${variant.name.replaceFirstChar { it.uppercase() }}CityConfig",
        ) {
            source.set(rootProject.layout.projectDirectory.file("cities/$slug/city.json"))
            // Everything the scrapers produced, except the hand-written announcement: a
            // message baked into the APK would outlive its removal from the repo.
            seedData.from(
                rootProject.fileTree("data/$slug") {
                    include("*.json")
                    exclude("announcement.json")
                },
            )
        }
        variant.sources.assets?.addGeneratedSourceDirectory(task, CopyCityConfig::outputDir)
    }
}
