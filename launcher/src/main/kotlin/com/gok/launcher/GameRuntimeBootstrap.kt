package com.gok.launcher

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.time.Instant

const val GAME_RUNTIME_BOOTSTRAP_SCHEMA_VERSION = "gok_runtime_bootstrap_v1"

enum class RuntimeHost {
    launcher_legacy,
    godot,
}

enum class SpawnSource {
    character_persisted_location,
    first_ordered_floor_spawn,
    admin_level_override_spawn,
}

data class RuntimeBootstrapSession(
    val accessToken: String,
    val refreshToken: String,
    val sessionId: String,
    val userId: Int,
    val email: String,
    val displayName: String,
    val isAdmin: Boolean,
)

data class RuntimeBootstrapCharacter(
    val id: Int,
    val name: String,
    val appearanceKey: String,
    val race: String,
    val background: String,
    val affiliation: String,
    val level: Int,
    val experience: Int,
    val equipment: Map<String, String>,
)

data class RuntimeBootstrapSpawn(
    val levelId: Int,
    val levelName: String,
    val descriptiveName: String,
    val orderIndex: Int,
    val worldX: Double,
    val worldY: Double,
    val source: SpawnSource,
)

data class RuntimeBootstrapContent(
    val versionId: Int,
    val versionKey: String,
    val schemaVersion: Int,
    val contractSignature: String,
)

data class RuntimeBootstrapRelease(
    val clientVersion: String,
    val latestVersion: String,
    val minSupportedVersion: String,
    val latestContentVersionKey: String,
    val minSupportedContentVersionKey: String,
    val updateFeedUrl: String?,
)

data class RuntimeBootstrapConfig(
    val runtimeHost: RuntimeHost,
    val windowMode: String,
    val isometricProjection: String = "2:1_dimetric",
    val tileWidth: Int = 64,
    val tileHeight: Int = 32,
    val defaultZoom: Double = 0.8,
    val zoomMin: Double = 0.7,
    val zoomMax: Double = 1.1,
)

data class GameRuntimeBootstrap(
    val schemaVersion: String = GAME_RUNTIME_BOOTSTRAP_SCHEMA_VERSION,
    val generatedAt: String = Instant.now().toString(),
    val session: RuntimeBootstrapSession,
    val character: RuntimeBootstrapCharacter,
    val spawn: RuntimeBootstrapSpawn,
    val content: RuntimeBootstrapContent,
    val release: RuntimeBootstrapRelease,
    val runtime: RuntimeBootstrapConfig,
)

object GameRuntimeBootstrapCodec {
    private val mapper = jacksonObjectMapper().setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)

    fun toJson(payload: GameRuntimeBootstrap, pretty: Boolean = true): String {
        return if (pretty) mapper.writerWithDefaultPrettyPrinter().writeValueAsString(payload)
        else mapper.writeValueAsString(payload)
    }

    fun fromJson(json: String): GameRuntimeBootstrap = mapper.readValue(json)

    fun writeTo(path: Path, payload: GameRuntimeBootstrap): Path {
        path.parent?.let { Files.createDirectories(it) }
        Files.writeString(
            path,
            toJson(payload),
            StandardOpenOption.CREATE,
            StandardOpenOption.TRUNCATE_EXISTING,
            StandardOpenOption.WRITE,
        )
        return path
    }
}
