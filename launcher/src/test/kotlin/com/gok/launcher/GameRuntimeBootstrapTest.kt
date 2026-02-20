package com.gok.launcher

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.nio.file.Files

class GameRuntimeBootstrapTest {
    private fun samplePayload(runtimeHost: RuntimeHost = RuntimeHost.godot): GameRuntimeBootstrap {
        return GameRuntimeBootstrap(
            generatedAt = "2026-02-20T15:00:00Z",
            session = RuntimeBootstrapSession(
                accessToken = "access",
                refreshToken = "refresh",
                sessionId = "session",
                userId = 7,
                email = "admin@admin.com",
                displayName = "admin",
                isAdmin = true,
            ),
            character = RuntimeBootstrapCharacter(
                id = 11,
                name = "Ikphelion",
                appearanceKey = "human_male",
                race = "Human",
                background = "Drifter",
                affiliation = "Unaffiliated",
                level = 1,
                experience = 0,
                equipment = mapOf("weapon_main" to "short_sword"),
            ),
            spawn = RuntimeBootstrapSpawn(
                levelId = 2,
                levelName = "tower_floor_01",
                descriptiveName = "Tower Floor 1 - Broken Gardens",
                orderIndex = 0,
                worldX = 96.0,
                worldY = 96.0,
                source = SpawnSource.character_persisted_location,
            ),
            content = RuntimeBootstrapContent(
                versionId = 25,
                versionKey = "cv_bootstrap_v1",
                schemaVersion = 1,
                contractSignature = "sig",
            ),
            release = RuntimeBootstrapRelease(
                clientVersion = "v1.0.81",
                latestVersion = "v1.0.81",
                minSupportedVersion = "v1.0.80",
                latestContentVersionKey = "cv_bootstrap_v1",
                minSupportedContentVersionKey = "cv_bootstrap_v1",
                updateFeedUrl = "https://storage.googleapis.com/example/RELEASES",
            ),
            runtime = RuntimeBootstrapConfig(
                runtimeHost = runtimeHost,
                windowMode = "borderless_fullscreen",
            ),
        )
    }

    @Test
    fun `codec round trip preserves schema and host fields`() {
        val payload = samplePayload()
        val json = GameRuntimeBootstrapCodec.toJson(payload)
        val parsed = GameRuntimeBootstrapCodec.fromJson(json)

        assertEquals(GAME_RUNTIME_BOOTSTRAP_SCHEMA_VERSION, parsed.schemaVersion)
        assertEquals(RuntimeHost.godot, parsed.runtime.runtimeHost)
        assertEquals("2:1_dimetric", parsed.runtime.isometricProjection)
        assertEquals(64, parsed.runtime.tileWidth)
        assertEquals(32, parsed.runtime.tileHeight)
        assertEquals(SpawnSource.character_persisted_location, parsed.spawn.source)
    }

    @Test
    fun `writeTo persists payload to disk with snake_case fields`() {
        val tempDir = Files.createTempDirectory("gok-bootstrap-test")
        val target = tempDir.resolve("runtime_bootstrap.json")

        GameRuntimeBootstrapCodec.writeTo(target, samplePayload(RuntimeHost.launcher_legacy))
        val json = Files.readString(target)

        assertTrue(json.contains("\"schema_version\""))
        assertTrue(json.contains("\"runtime_host\" : \"launcher_legacy\""))
        assertTrue(json.contains("\"latest_content_version_key\""))
    }
}
