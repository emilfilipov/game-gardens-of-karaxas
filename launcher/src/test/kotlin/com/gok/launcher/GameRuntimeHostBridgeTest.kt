package com.gok.launcher

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.nio.file.Files

class GameRuntimeHostBridgeTest {
    @Test
    fun `resolveRuntimeHostSettings defaults to launcher legacy`() {
        val root = Files.createTempDirectory("gok-runtime-host-default")
        val settings = GameRuntimeHostBridge.resolveRuntimeHostSettings(root, root, emptyMap())
        assertEquals(RuntimeHost.launcher_legacy, settings.runtimeHost)
        assertEquals("godot4", settings.godotExecutable)
    }

    @Test
    fun `resolveRuntimeHostSettings honors godot env value`() {
        val root = Files.createTempDirectory("gok-runtime-host-env")
        val settings = GameRuntimeHostBridge.resolveRuntimeHostSettings(
            payloadRoot = root,
            installRoot = root,
            env = mapOf("GOK_RUNTIME_HOST" to "godot"),
        )
        assertEquals(RuntimeHost.godot, settings.runtimeHost)
    }

    @Test
    fun `resolveRuntimeHostSettings reads packaged runtime_host properties`() {
        val root = Files.createTempDirectory("gok-runtime-host-props")
        val props = root.resolve("runtime_host.properties")
        Files.writeString(
            props,
            """
            runtime_host=godot
            godot_executable=custom-godot
            godot_project_path=game-client
            """.trimIndent()
        )
        val settings = GameRuntimeHostBridge.resolveRuntimeHostSettings(
            payloadRoot = root,
            installRoot = root,
            env = emptyMap(),
        )
        assertEquals(RuntimeHost.godot, settings.runtimeHost)
        assertEquals("custom-godot", settings.godotExecutable)
        assertEquals("game-client", settings.godotProjectPath)
    }

    @Test
    fun `buildBootstrap uses admin override spawn source when override level is provided`() {
        val payload = GameRuntimeHostBridge.buildBootstrap(
            session = AuthSession(
                accessToken = "a",
                refreshToken = "r",
                sessionId = "s",
                userId = 1,
                email = "admin@admin.com",
                displayName = "admin",
                isAdmin = true,
                mfaEnabled = false,
                latestVersion = "v1.0.90",
                minSupportedVersion = "v1.0.80",
                latestContentVersionKey = "cv_2",
                minSupportedContentVersionKey = "cv_1",
                clientContentVersionKey = "cv_2",
                forceUpdate = false,
                updateAvailable = false,
                contentUpdateAvailable = false,
                updateFeedUrl = "https://example.com/releases",
            ),
            character = CharacterView(
                id = 2,
                name = "Iph",
                levelId = 10,
                locationX = null,
                locationY = null,
                appearanceKey = "human_male",
                race = "human",
                background = "drifter",
                affiliation = "unaffiliated",
                level = 1,
                experience = 0,
                experienceToNextLevel = 100,
                statPointsTotal = 10,
                statPointsUsed = 0,
                equipment = mapOf("weapon_main" to "short_sword"),
                isSelected = true,
            ),
            level = LevelDataView(
                id = 10,
                name = "floor_01",
                descriptiveName = "Floor 1",
                orderIndex = 0,
                schemaVersion = 2,
                width = 100,
                height = 100,
                spawnX = 12,
                spawnY = 8,
                layers = emptyMap(),
                transitions = emptyList(),
                wallCells = emptyList(),
            ),
            overrideLevelId = 10,
            content = ContentBootstrapView(
                contentSchemaVersion = 1,
                contentContractSignature = "sig",
                contentVersionId = 4,
                contentVersionKey = "cv_2",
                fetchedAt = "2026-01-01T00:00:00Z",
                pointBudget = 10,
                xpPerLevel = 100,
                maxPerStat = 10,
                races = emptyList(),
                backgrounds = emptyList(),
                affiliations = emptyList(),
                stats = emptyList(),
                skills = emptyList(),
                assets = emptyList(),
                equipmentSlots = emptyList(),
                equipmentVisuals = emptyList(),
                movementSpeed = 220.0,
                attackSpeedBase = 1.0,
                uiText = emptyMap(),
            ),
            clientVersion = "v1.0.90",
            windowMode = "borderless_fullscreen",
        )

        assertEquals(SpawnSource.admin_level_override_spawn, payload.spawn.source)
        assertEquals(RuntimeHost.godot, payload.runtime.runtimeHost)
        assertEquals("gok_runtime_bootstrap_v1", payload.schemaVersion)
    }

    @Test
    fun `resolveGodotExecutableCommand prefers bundled runtime under install root`() {
        val root = Files.createTempDirectory("gok-runtime-bundled")
        val projectPath = root.resolve("game-client")
        Files.createDirectories(projectPath)
        Files.writeString(projectPath.resolve("project.godot"), "[gd_project]\n")
        val bundledExe = root.resolve("game-client/runtime/windows/godot4.exe")
        Files.createDirectories(bundledExe.parent)
        Files.writeString(bundledExe, "stub")

        val command = GameRuntimeHostBridge.resolveGodotExecutableCommand(
            payloadRoot = root,
            installRoot = root,
            projectPath = projectPath,
            settings = RuntimeHostSettings(
                runtimeHost = RuntimeHost.godot,
                godotExecutable = "godot4",
                godotProjectPath = "game-client",
                source = "test",
            ),
            env = emptyMap(),
        )

        assertEquals(bundledExe.toAbsolutePath().normalize().toString(), command)
    }

    @Test
    fun `resolveGodotExecutableCommand resolves configured relative executable path`() {
        val root = Files.createTempDirectory("gok-runtime-relative-exe")
        val projectPath = root.resolve("game-client")
        Files.createDirectories(projectPath)
        Files.writeString(projectPath.resolve("project.godot"), "[gd_project]\n")
        val configuredExe = root.resolve("runtime/bin/custom-godot.exe")
        Files.createDirectories(configuredExe.parent)
        Files.writeString(configuredExe, "stub")

        val command = GameRuntimeHostBridge.resolveGodotExecutableCommand(
            payloadRoot = root,
            installRoot = root,
            projectPath = projectPath,
            settings = RuntimeHostSettings(
                runtimeHost = RuntimeHost.godot,
                godotExecutable = "runtime/bin/custom-godot.exe",
                godotProjectPath = "game-client",
                source = "test",
            ),
            env = emptyMap(),
        )

        assertTrue(command?.endsWith("custom-godot.exe") == true)
        assertEquals(configuredExe.toAbsolutePath().normalize().toString(), command)
    }
}
