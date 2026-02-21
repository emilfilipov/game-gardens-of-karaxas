package com.gok.launcher

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.time.Instant
import java.util.Properties

data class RuntimeLaunchResult(
    val launched: Boolean,
    val process: Process?,
    val message: String,
)

data class RuntimeHostSettings(
    val runtimeHost: RuntimeHost,
    val godotExecutable: String,
    val godotProjectPath: String?,
    val source: String,
)

object GameRuntimeHostBridge {
    private const val RUNTIME_HOST_ENV = "GOK_RUNTIME_HOST"
    private const val GODOT_EXECUTABLE_ENV = "GOK_GODOT_EXECUTABLE"
    private const val GODOT_PROJECT_ENV = "GOK_GODOT_PROJECT_PATH"
    private const val RUNTIME_SETTINGS_FILE = "runtime_host.properties"
    private const val LEGACY_WORLD_TILE_SIZE = 32.0

    fun resolveRuntimeHostSettings(
        payloadRoot: Path,
        installRoot: Path,
        env: Map<String, String> = System.getenv(),
    ): RuntimeHostSettings {
        val fileProps = loadRuntimeProperties(payloadRoot, installRoot)
        val rawHost = env[RUNTIME_HOST_ENV]?.trim()?.ifBlank { null }
            ?: fileProps?.getProperty("runtime_host")?.trim()?.ifBlank { null }
        val runtimeHost = when (rawHost?.lowercase()) {
            RuntimeHost.godot.name -> RuntimeHost.godot
            else -> RuntimeHost.launcher_legacy
        }
        val godotExecutable = env[GODOT_EXECUTABLE_ENV]?.trim()?.ifBlank { null }
            ?: fileProps?.getProperty("godot_executable")?.trim()?.ifBlank { null }
            ?: "godot4"
        val godotProjectPath = env[GODOT_PROJECT_ENV]?.trim()?.ifBlank { null }
            ?: fileProps?.getProperty("godot_project_path")?.trim()?.ifBlank { null }
        val source = when {
            env.containsKey(RUNTIME_HOST_ENV) || env.containsKey(GODOT_EXECUTABLE_ENV) || env.containsKey(GODOT_PROJECT_ENV) -> "environment"
            fileProps != null -> "runtime_host.properties"
            else -> "default"
        }
        return RuntimeHostSettings(
            runtimeHost = runtimeHost,
            godotExecutable = godotExecutable,
            godotProjectPath = godotProjectPath,
            source = source,
        )
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
        settings: RuntimeHostSettings,
        env: Map<String, String> = System.getenv(),
    ): RuntimeLaunchResult {
        val projectPath = resolveGodotProjectPath(payloadRoot, installRoot, settings, env)
            ?: return RuntimeLaunchResult(
                launched = false,
                process = null,
                message = "Godot runtime requested but game-client project was not found. Set $GODOT_PROJECT_ENV.",
            )
        val executable = resolveGodotExecutableCommand(
            payloadRoot = payloadRoot,
            installRoot = installRoot,
            projectPath = projectPath,
            settings = settings,
            env = env,
        ) ?: return RuntimeLaunchResult(
            launched = false,
            process = null,
            message = "Godot runtime requested but executable is not configured. Set $GODOT_EXECUTABLE_ENV or ship bundled runtime.",
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
                message = "Launched Godot runtime executable '$executable' with project ${projectPath.toAbsolutePath()}",
            )
        } catch (ex: Exception) {
            RuntimeLaunchResult(
                launched = false,
                process = null,
                message = "Failed to launch Godot runtime: ${ex.message ?: ex::class.java.simpleName}",
            )
        }
    }

    internal fun resolveGodotExecutableCommand(
        payloadRoot: Path,
        installRoot: Path,
        projectPath: Path,
        settings: RuntimeHostSettings,
        env: Map<String, String> = System.getenv(),
    ): String? {
        val commandCandidates = mutableListOf<String>()
        val configuredTokens = listOf(
            env[GODOT_EXECUTABLE_ENV]?.trim(),
            settings.godotExecutable.trim(),
        )
            .mapNotNull { it?.trim()?.takeIf(String::isNotBlank) }
            .distinct()
        configuredTokens.forEach { token ->
            val pathCandidate = resolveExecutablePathToken(token, payloadRoot, installRoot, projectPath)
            if (pathCandidate != null) {
                return pathCandidate.toString()
            }
            if (!looksLikePathToken(token)) {
                commandCandidates.add(token)
            }
        }

        val bundledCandidates = listOf(
            projectPath.resolve("runtime/windows/godot4.exe"),
            installRoot.resolve("game-client/runtime/windows/godot4.exe"),
            payloadRoot.resolve("game-client/runtime/windows/godot4.exe"),
            projectPath.resolve("godot4.exe"),
        ).map { it.toAbsolutePath().normalize() }
        bundledCandidates.firstOrNull { Files.exists(it) }?.let { return it.toString() }

        val fallbackCommands = listOf("godot4.exe", "godot4", "godot.exe", "godot")
        val combined = (commandCandidates + fallbackCommands).distinct()
        return combined.firstOrNull()
    }

    private fun resolveExecutablePathToken(
        token: String,
        payloadRoot: Path,
        installRoot: Path,
        projectPath: Path,
    ): Path? {
        val raw = token.trim().trim('"')
        if (raw.isBlank()) return null
        val path = Paths.get(raw)
        val candidates = if (path.isAbsolute) {
            listOf(path)
        } else {
            listOf(
                projectPath.resolve(path),
                installRoot.resolve(path),
                payloadRoot.resolve(path),
                Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize().resolve(path),
            )
        }
        return candidates
            .map { it.toAbsolutePath().normalize() }
            .firstOrNull { Files.exists(it) }
    }

    private fun looksLikePathToken(token: String): Boolean {
        val normalized = token.trim()
        if (normalized.isBlank()) return false
        return normalized.contains("/") ||
            normalized.contains("\\") ||
            normalized.contains(":") ||
            normalized.lowercase().endsWith(".exe")
    }

    private fun resolveGodotProjectPath(
        payloadRoot: Path,
        installRoot: Path,
        settings: RuntimeHostSettings,
        env: Map<String, String>,
    ): Path? {
        val explicit = env[GODOT_PROJECT_ENV]?.trim()?.takeIf { it.isNotBlank() }?.let { Paths.get(it).toAbsolutePath().normalize() }
        if (explicit != null && Files.exists(explicit.resolve("project.godot"))) return explicit
        val fromSettings = settings.godotProjectPath?.trim()?.takeIf { it.isNotBlank() }?.let { raw ->
            val candidate = Paths.get(raw)
            if (candidate.isAbsolute) {
                candidate.toAbsolutePath().normalize()
            } else {
                installRoot.resolve(raw).toAbsolutePath().normalize()
            }
        }
        if (fromSettings != null && Files.exists(fromSettings.resolve("project.godot"))) return fromSettings

        val userDir = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize()
        val candidates = listOf(
            payloadRoot.resolve("game-client"),
            installRoot.resolve("game-client"),
            userDir.resolve("game-client"),
            userDir.parent?.resolve("game-client"),
        ).filterNotNull().map { it.toAbsolutePath().normalize() }

        return candidates.firstOrNull { Files.exists(it.resolve("project.godot")) }
    }

    private fun loadRuntimeProperties(payloadRoot: Path, installRoot: Path): Properties? {
        val candidates = listOf(
            installRoot.resolve(RUNTIME_SETTINGS_FILE),
            payloadRoot.resolve(RUNTIME_SETTINGS_FILE),
        )
        val source = candidates.firstOrNull { Files.exists(it) } ?: return null
        return try {
            val props = Properties()
            Files.newInputStream(source).use { props.load(it) }
            props
        } catch (_: Exception) {
            null
        }
    }
}
