package com.gok.launcher

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.time.Instant

data class RuntimeLaunchResult(
    val launched: Boolean,
    val process: Process?,
    val message: String,
)

object GameRuntimeHostBridge {
    private const val RUNTIME_HOST_ENV = "GOK_RUNTIME_HOST"
    private const val GODOT_EXECUTABLE_ENV = "GOK_GODOT_EXECUTABLE"
    private const val GODOT_PROJECT_ENV = "GOK_GODOT_PROJECT_PATH"
    private const val LEGACY_WORLD_TILE_SIZE = 32.0

    fun configuredRuntimeHost(env: Map<String, String> = System.getenv()): RuntimeHost {
        val raw = env[RUNTIME_HOST_ENV]?.trim()?.lowercase()
        return when (raw) {
            RuntimeHost.godot.name -> RuntimeHost.godot
            else -> RuntimeHost.launcher_legacy
        }
    }

    fun buildBootstrap(
        session: AuthSession,
        character: CharacterView,
        level: LevelDataView,
        overrideLevelId: Int?,
        content: ContentBootstrapView,
        clientVersion: String,
        windowMode: String,
    ): GameRuntimeBootstrap {
        val hasPersisted = overrideLevelId == null &&
            character.levelId != null &&
            character.locationX != null &&
            character.locationY != null
        val spawnSource = when {
            overrideLevelId != null -> SpawnSource.admin_level_override_spawn
            hasPersisted -> SpawnSource.character_persisted_location
            else -> SpawnSource.first_ordered_floor_spawn
        }
        val spawnX = character.locationX?.toDouble()
            ?: ((level.spawnX.toDouble() + 0.5) * LEGACY_WORLD_TILE_SIZE)
        val spawnY = character.locationY?.toDouble()
            ?: ((level.spawnY.toDouble() + 0.5) * LEGACY_WORLD_TILE_SIZE)

        return GameRuntimeBootstrap(
            generatedAt = Instant.now().toString(),
            session = RuntimeBootstrapSession(
                accessToken = session.accessToken,
                refreshToken = session.refreshToken,
                sessionId = session.sessionId,
                userId = session.userId,
                email = session.email,
                displayName = session.displayName,
                isAdmin = session.isAdmin,
            ),
            character = RuntimeBootstrapCharacter(
                id = character.id,
                name = character.name,
                appearanceKey = character.appearanceKey,
                race = character.race,
                background = character.background,
                affiliation = character.affiliation,
                level = character.level,
                experience = character.experience,
                equipment = character.equipment,
            ),
            spawn = RuntimeBootstrapSpawn(
                levelId = level.id,
                levelName = level.name,
                descriptiveName = level.descriptiveName.ifBlank { level.name },
                orderIndex = level.orderIndex,
                worldX = spawnX,
                worldY = spawnY,
                source = spawnSource,
            ),
            content = RuntimeBootstrapContent(
                versionId = content.contentVersionId,
                versionKey = content.contentVersionKey,
                schemaVersion = content.contentSchemaVersion,
                contractSignature = content.contentContractSignature,
            ),
            release = RuntimeBootstrapRelease(
                clientVersion = clientVersion,
                latestVersion = session.latestVersion,
                minSupportedVersion = session.minSupportedVersion,
                latestContentVersionKey = session.latestContentVersionKey,
                minSupportedContentVersionKey = session.minSupportedContentVersionKey,
                updateFeedUrl = session.updateFeedUrl,
            ),
            runtime = RuntimeBootstrapConfig(
                runtimeHost = RuntimeHost.godot,
                windowMode = windowMode,
            ),
        )
    }

    fun writeBootstrap(installRoot: Path, payload: GameRuntimeBootstrap): Path {
        val dir = installRoot.resolve("runtime")
        val fileName = "runtime_bootstrap_${payload.character.id}.json"
        return GameRuntimeBootstrapCodec.writeTo(dir.resolve(fileName), payload)
    }

    fun launchGodot(
        payloadRoot: Path,
        installRoot: Path,
        bootstrapPath: Path,
        env: Map<String, String> = System.getenv(),
    ): RuntimeLaunchResult {
        val executable = resolveGodotExecutable(env)
            ?: return RuntimeLaunchResult(
                launched = false,
                process = null,
                message = "Godot runtime requested but executable is not configured. Set $GODOT_EXECUTABLE_ENV.",
            )
        val projectPath = resolveGodotProjectPath(payloadRoot, installRoot, env)
            ?: return RuntimeLaunchResult(
                launched = false,
                process = null,
                message = "Godot runtime requested but game-client project was not found. Set $GODOT_PROJECT_ENV.",
            )

        return try {
            val process = ProcessBuilder(
                executable,
                "--path",
                projectPath.toString(),
                "--",
                "--bootstrap=${bootstrapPath.toAbsolutePath()}",
            )
                .directory(projectPath.toFile())
                .redirectErrorStream(true)
                .start()
            RuntimeLaunchResult(
                launched = true,
                process = process,
                message = "Launched Godot runtime with project ${projectPath.toAbsolutePath()}",
            )
        } catch (ex: Exception) {
            RuntimeLaunchResult(
                launched = false,
                process = null,
                message = "Failed to launch Godot runtime: ${ex.message ?: ex::class.java.simpleName}",
            )
        }
    }

    private fun resolveGodotExecutable(env: Map<String, String>): String? {
        val fromEnv = env[GODOT_EXECUTABLE_ENV]?.trim()?.takeIf { it.isNotBlank() }
        if (fromEnv != null) return fromEnv
        return "godot4"
    }

    private fun resolveGodotProjectPath(
        payloadRoot: Path,
        installRoot: Path,
        env: Map<String, String>,
    ): Path? {
        val explicit = env[GODOT_PROJECT_ENV]?.trim()?.takeIf { it.isNotBlank() }?.let { Paths.get(it).toAbsolutePath().normalize() }
        if (explicit != null && Files.exists(explicit.resolve("project.godot"))) return explicit

        val userDir = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize()
        val candidates = listOf(
            payloadRoot.resolve("game-client"),
            installRoot.resolve("game-client"),
            userDir.resolve("game-client"),
            userDir.parent?.resolve("game-client"),
        ).filterNotNull().map { it.toAbsolutePath().normalize() }

        return candidates.firstOrNull { Files.exists(it.resolve("project.godot")) }
    }
}
