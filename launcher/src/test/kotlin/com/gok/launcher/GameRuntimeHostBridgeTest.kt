package com.gok.launcher

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class GameRuntimeHostBridgeTest {
    @Test
    fun `configuredRuntimeHost defaults to launcher legacy`() {
        val host = GameRuntimeHostBridge.configuredRuntimeHost(emptyMap())
        assertEquals(RuntimeHost.launcher_legacy, host)
    }

    @Test
    fun `configuredRuntimeHost honors godot env value`() {
        val host = GameRuntimeHostBridge.configuredRuntimeHost(mapOf("GOK_RUNTIME_HOST" to "godot"))
        assertEquals(RuntimeHost.godot, host)
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
}
