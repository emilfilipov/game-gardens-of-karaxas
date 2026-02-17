package com.gok.launcher

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import java.net.URI
import java.net.URLEncoder
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets
import java.time.Duration

data class AuthSession(
    val accessToken: String,
    val refreshToken: String,
    val sessionId: String,
    val userId: Int,
    val email: String,
    val displayName: String,
    val isAdmin: Boolean,
    val latestVersion: String,
    val minSupportedVersion: String,
    val forceUpdate: Boolean,
    val updateAvailable: Boolean
)

data class CharacterView(
    val id: Int,
    val name: String,
    val levelId: Int?,
    val locationX: Int?,
    val locationY: Int?,
    val appearanceKey: String,
    val race: String,
    val background: String,
    val affiliation: String,
    val level: Int,
    val experience: Int,
    val experienceToNextLevel: Int,
    val statPointsTotal: Int,
    val statPointsUsed: Int,
    val isSelected: Boolean
) {
    override fun toString(): String {
        return "$name (Lv.$level)"
    }
}

data class LevelGridCellView(
    val x: Int,
    val y: Int
)

data class LevelLayerCellView(
    val layer: Int,
    val x: Int,
    val y: Int,
    val assetKey: String,
)

data class LevelSummaryView(
    val id: Int,
    val name: String,
    val schemaVersion: Int,
    val width: Int,
    val height: Int
) {
    override fun toString(): String = name
}

data class LevelDataView(
    val id: Int,
    val name: String,
    val schemaVersion: Int,
    val width: Int,
    val height: Int,
    val spawnX: Int,
    val spawnY: Int,
    val layers: Map<Int, List<LevelLayerCellView>>,
    val wallCells: List<LevelGridCellView>
)

data class ContentOptionEntryView(
    val value: String,
    val label: String,
    val description: String,
    val textKey: String,
)

data class ContentStatEntryView(
    val key: String,
    val label: String,
    val description: String,
    val tooltip: String,
    val textKey: String,
)

data class ContentSkillEntryView(
    val key: String,
    val label: String,
    val textKey: String,
    val skillType: String,
    val manaCost: Double,
    val energyCost: Double,
    val lifeCost: Double,
    val effects: String,
    val damageText: String,
    val cooldownSeconds: Double,
    val damageBase: Double,
    val intelligenceScale: Double,
    val description: String,
)

data class ContentBootstrapView(
    val contentSchemaVersion: Int,
    val contentVersionId: Int,
    val contentVersionKey: String,
    val fetchedAt: String,
    val pointBudget: Int,
    val xpPerLevel: Int,
    val maxPerStat: Int,
    val races: List<ContentOptionEntryView>,
    val backgrounds: List<ContentOptionEntryView>,
    val affiliations: List<ContentOptionEntryView>,
    val stats: List<ContentStatEntryView>,
    val skills: List<ContentSkillEntryView>,
    val movementSpeed: Double,
    val attackSpeedBase: Double,
    val uiText: Map<String, String>,
)

object LevelLayerPayloadCodec {
    fun toRequestLayers(layers: Map<Int, List<LevelLayerCellView>>): Map<String, List<Map<String, Any>>> {
        val payload = linkedMapOf<String, List<Map<String, Any>>>()
        layers.keys.sorted().forEach { layer ->
            val cells = layers[layer].orEmpty()
            payload[layer.toString()] = cells.map { cell ->
                mapOf(
                    "x" to cell.x,
                    "y" to cell.y,
                    "asset_key" to cell.assetKey,
                )
            }
        }
        return payload
    }

    fun fromResponse(item: JsonNode): Map<Int, List<LevelLayerCellView>> {
        val layersNode = item.path("layers")
        val parsed = linkedMapOf<Int, MutableList<LevelLayerCellView>>()
        if (layersNode.isObject) {
            val fields = layersNode.fields()
            while (fields.hasNext()) {
                val (key, value) = fields.next()
                val layerId = key.toIntOrNull() ?: continue
                if (!value.isArray) continue
                val list = parsed.getOrPut(layerId) { mutableListOf() }
                value.forEach { cell ->
                    list.add(
                        LevelLayerCellView(
                            layer = layerId,
                            x = cell.path("x").asInt(),
                            y = cell.path("y").asInt(),
                            assetKey = cell.path("asset_key").asText("decor"),
                        )
                    )
                }
            }
        }
        if (parsed.isNotEmpty()) {
            return parsed
        }
        val legacy = item.path("wall_cells")
        if (!legacy.isArray) {
            return emptyMap()
        }
        val legacyWalls = mutableListOf<LevelLayerCellView>()
        legacy.forEach { cell ->
            legacyWalls.add(
                LevelLayerCellView(
                    layer = 1,
                    x = cell.path("x").asInt(),
                    y = cell.path("y").asInt(),
                    assetKey = "wall_block",
                )
            )
        }
        return if (legacyWalls.isEmpty()) emptyMap() else mapOf(1 to legacyWalls)
    }
}

data class ChannelView(
    val id: Int,
    val name: String,
    val kind: String
) {
    override fun toString(): String = "$name [$kind]"
}

data class ChatMessageView(
    val id: Int,
    val senderDisplayName: String,
    val content: String,
    val createdAt: String
)

data class LobbyOverviewView(
    val friends: List<String>,
    val guilds: List<String>
)

class BackendClientException(message: String) : RuntimeException(message)

class KaraxasBackendClient(
    private val baseUrl: String,
    private val mapper: ObjectMapper = jacksonObjectMapper(),
    private val httpClient: HttpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build(),
) {
    companion object {
        private const val DEFAULT_CLOUD_BACKEND = "https://karaxas-backend-rss3xj2ixq-ew.a.run.app"

        fun fromEnvironment(): KaraxasBackendClient {
            val endpoint = System.getenv("GOK_API_BASE_URL")
                ?.takeIf { it.isNotBlank() }
                ?.trimEnd('/')
                ?: DEFAULT_CLOUD_BACKEND
            return KaraxasBackendClient(endpoint)
        }
    }

    fun endpoint(): String = baseUrl

    private fun parseContentOptions(node: JsonNode): List<ContentOptionEntryView> {
        if (!node.isArray) return emptyList()
        return node.mapNotNull { item ->
            val value = item.path("value").asText("").trim()
            val label = item.path("label").asText("").trim()
            if (value.isBlank() || label.isBlank()) return@mapNotNull null
            ContentOptionEntryView(
                value = value,
                label = label,
                description = item.path("description").asText("").trim(),
                textKey = item.path("text_key").asText("").trim(),
            )
        }
    }

    private fun parseContentStats(node: JsonNode): List<ContentStatEntryView> {
        if (!node.isArray) return emptyList()
        return node.mapNotNull { item ->
            val key = item.path("key").asText("").trim()
            val label = item.path("label").asText("").trim()
            if (key.isBlank() || label.isBlank()) return@mapNotNull null
            ContentStatEntryView(
                key = key,
                label = label,
                description = item.path("description").asText("").trim(),
                tooltip = item.path("tooltip").asText("").trim(),
                textKey = item.path("text_key").asText("").trim(),
            )
        }
    }

    private fun parseContentSkills(node: JsonNode): List<ContentSkillEntryView> {
        if (!node.isArray) return emptyList()
        return node.mapNotNull { item ->
            val key = item.path("key").asText("").trim()
            val label = item.path("label").asText("").trim()
            if (key.isBlank() || label.isBlank()) return@mapNotNull null
            ContentSkillEntryView(
                key = key,
                label = label,
                textKey = item.path("text_key").asText("").trim(),
                skillType = item.path("skill_type").asText("Skill").trim(),
                manaCost = item.path("mana_cost").asDouble(0.0),
                energyCost = item.path("energy_cost").asDouble(0.0),
                lifeCost = item.path("life_cost").asDouble(0.0),
                effects = item.path("effects").asText("").trim(),
                damageText = item.path("damage_text").asText("").trim(),
                cooldownSeconds = item.path("cooldown_seconds").asDouble(0.0),
                damageBase = item.path("damage_base").asDouble(0.0),
                intelligenceScale = item.path("intelligence_scale").asDouble(0.0),
                description = item.path("description").asText("").trim(),
            )
        }
    }

    fun fetchContentBootstrap(clientVersion: String? = null): ContentBootstrapView {
        val response = request(
            method = "GET",
            path = "/content/bootstrap",
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        val root = mapper.readTree(response.body())
        val domains = root.path("domains")
        val progression = domains.path("progression")
        val options = domains.path("character_options")
        val stats = domains.path("stats")
        val skills = domains.path("skills")
        val tuning = domains.path("tuning")
        val uiText = domains.path("ui_text").path("strings")

        val races = parseContentOptions(options.path("race"))
        val backgrounds = parseContentOptions(options.path("background"))
        val affiliations = parseContentOptions(options.path("affiliation"))
        val statEntries = parseContentStats(stats.path("entries"))
        val skillEntries = parseContentSkills(skills.path("entries"))

        val uiTextMap = linkedMapOf<String, String>()
        if (uiText.isObject) {
            val fields = uiText.fields()
            while (fields.hasNext()) {
                val (key, value) = fields.next()
                val text = value.asText("").trim()
                if (key.isNotBlank() && text.isNotBlank()) {
                    uiTextMap[key] = text
                }
            }
        }

        return ContentBootstrapView(
            contentSchemaVersion = root.path("content_schema_version").asInt(1),
            contentVersionId = root.path("content_version_id").asInt(0),
            contentVersionKey = root.path("content_version_key").asText("unknown"),
            fetchedAt = root.path("fetched_at").asText(""),
            pointBudget = options.path("point_budget").asInt(10),
            xpPerLevel = progression.path("xp_per_level").asInt(100),
            maxPerStat = stats.path("max_per_stat").asInt(10),
            races = races,
            backgrounds = backgrounds,
            affiliations = affiliations,
            stats = statEntries,
            skills = skillEntries,
            movementSpeed = tuning.path("movement_speed").asDouble(220.0),
            attackSpeedBase = tuning.path("attack_speed_base").asDouble(1.0),
            uiText = uiTextMap,
        )
    }

    fun register(email: String, password: String, displayName: String, clientVersion: String): AuthSession {
        val payload = mapOf(
            "email" to email,
            "password" to password,
            "display_name" to displayName,
        )
        val response = request(
            method = "POST",
            path = "/auth/register",
            body = mapper.writeValueAsString(payload),
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return parseSession(response.body())
    }

    fun login(email: String, password: String, clientVersion: String): AuthSession {
        val payload = mapOf(
            "email" to email,
            "password" to password,
            "client_version" to clientVersion,
        )
        val response = request(
            method = "POST",
            path = "/auth/login",
            body = mapper.writeValueAsString(payload),
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return parseSession(response.body())
    }

    fun refresh(refreshToken: String, clientVersion: String): AuthSession {
        val payload = mapOf(
            "refresh_token" to refreshToken,
            "client_version" to clientVersion,
        )
        val response = request(
            method = "POST",
            path = "/auth/refresh",
            body = mapper.writeValueAsString(payload),
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return parseSession(response.body())
    }

    fun logout(accessToken: String, clientVersion: String) {
        val response = request(
            method = "POST",
            path = "/auth/logout",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
    }

    fun lobbyOverview(accessToken: String, clientVersion: String): LobbyOverviewView {
        val response = request(
            method = "GET",
            path = "/lobby/overview",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        val root = mapper.readTree(response.body())
        val friends = root.path("friends").map { friend ->
            val name = friend.path("display_name").asText("Unknown")
            val status = friend.path("status").asText("accepted")
            "$name ($status)"
        }
        val guilds = root.path("guilds").map { guild ->
            val guildName = guild.path("guild_name").asText("Guild")
            val members = guild.path("members").size()
            "$guildName ($members members)"
        }
        return LobbyOverviewView(friends = friends, guilds = guilds)
    }

    fun listCharacters(accessToken: String, clientVersion: String): List<CharacterView> {
        val response = request(
            method = "GET",
            path = "/characters",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return mapper.readTree(response.body()).map { item ->
            CharacterView(
                id = item.path("id").asInt(),
                name = item.path("name").asText(),
                levelId = item.path("level_id").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
                locationX = item.path("location_x").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
                locationY = item.path("location_y").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
                appearanceKey = item.path("appearance_key").asText("human_male"),
                race = item.path("race").asText("Human"),
                background = item.path("background").asText("Drifter"),
                affiliation = item.path("affiliation").asText("Unaffiliated"),
                level = item.path("level").asInt(1),
                experience = item.path("experience").asInt(0),
                experienceToNextLevel = item.path("experience_to_next_level").asInt(100),
                statPointsTotal = item.path("stat_points_total").asInt(),
                statPointsUsed = item.path("stat_points_used").asInt(),
                isSelected = item.path("is_selected").asBoolean(false),
            )
        }
    }

    fun createCharacter(
        accessToken: String,
        clientVersion: String,
        name: String,
        appearanceKey: String,
        race: String,
        background: String,
        affiliation: String,
        totalPoints: Int,
        stats: Map<String, Int>,
        skills: Map<String, Int>,
    ): CharacterView {
        val payload = mapOf(
            "name" to name,
            "appearance_key" to appearanceKey,
            "race" to race,
            "background" to background,
            "affiliation" to affiliation,
            "stat_points_total" to totalPoints,
            "stats" to stats,
            "skills" to skills,
        )
        val response = request(
            method = "POST",
            path = "/characters",
            accessToken = accessToken,
            clientVersion = clientVersion,
            body = mapper.writeValueAsString(payload),
        )
        ensureSuccess(response)
        val item = mapper.readTree(response.body())
        return CharacterView(
            id = item.path("id").asInt(),
            name = item.path("name").asText(),
            levelId = item.path("level_id").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
            locationX = item.path("location_x").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
            locationY = item.path("location_y").takeIf { !it.isMissingNode && !it.isNull }?.asInt(),
            appearanceKey = item.path("appearance_key").asText("human_male"),
            race = item.path("race").asText("Human"),
            background = item.path("background").asText("Drifter"),
            affiliation = item.path("affiliation").asText("Unaffiliated"),
            level = item.path("level").asInt(1),
            experience = item.path("experience").asInt(0),
            experienceToNextLevel = item.path("experience_to_next_level").asInt(100),
            statPointsTotal = item.path("stat_points_total").asInt(),
            statPointsUsed = item.path("stat_points_used").asInt(),
            isSelected = item.path("is_selected").asBoolean(false),
        )
    }

    fun selectCharacter(accessToken: String, clientVersion: String, characterId: Int) {
        val response = request(
            method = "POST",
            path = "/characters/$characterId/select",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
    }

    fun deleteCharacter(accessToken: String, clientVersion: String, characterId: Int) {
        val response = request(
            method = "DELETE",
            path = "/characters/$characterId",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
    }

    fun assignCharacterLevel(accessToken: String, clientVersion: String, characterId: Int, levelId: Int?) {
        val payload = mapOf("level_id" to levelId)
        val response = request(
            method = "POST",
            path = "/characters/$characterId/level",
            accessToken = accessToken,
            clientVersion = clientVersion,
            body = mapper.writeValueAsString(payload),
        )
        ensureSuccess(response)
    }

    fun updateCharacterLocation(
        accessToken: String,
        clientVersion: String,
        characterId: Int,
        levelId: Int?,
        locationX: Int,
        locationY: Int,
    ) {
        val payload = mapOf(
            "level_id" to levelId,
            "location_x" to locationX,
            "location_y" to locationY,
        )
        val response = request(
            method = "POST",
            path = "/characters/$characterId/location",
            accessToken = accessToken,
            clientVersion = clientVersion,
            body = mapper.writeValueAsString(payload),
        )
        ensureSuccess(response)
    }

    fun listLevels(accessToken: String, clientVersion: String): List<LevelSummaryView> {
        val response = request(
            method = "GET",
            path = "/levels",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return mapper.readTree(response.body()).map { item ->
            LevelSummaryView(
                id = item.path("id").asInt(),
                name = item.path("name").asText(),
                schemaVersion = item.path("schema_version").asInt(2),
                width = item.path("width").asInt(40),
                height = item.path("height").asInt(24),
            )
        }
    }

    fun getLevel(accessToken: String, clientVersion: String, levelId: Int): LevelDataView {
        val response = request(
            method = "GET",
            path = "/levels/$levelId",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        val item = mapper.readTree(response.body())
        val layers = LevelLayerPayloadCodec.fromResponse(item)
        val wallCells = layers
            .getOrDefault(1, emptyList())
            .filter { it.assetKey == "wall_block" || it.assetKey == "tree_oak" }
            .map { LevelGridCellView(x = it.x, y = it.y) }
        return LevelDataView(
            id = item.path("id").asInt(),
            name = item.path("name").asText(),
            schemaVersion = item.path("schema_version").asInt(2),
            width = item.path("width").asInt(40),
            height = item.path("height").asInt(24),
            spawnX = item.path("spawn_x").asInt(1),
            spawnY = item.path("spawn_y").asInt(1),
            layers = layers,
            wallCells = wallCells,
        )
    }

    fun saveLevel(
        accessToken: String,
        clientVersion: String,
        name: String,
        width: Int,
        height: Int,
        spawnX: Int,
        spawnY: Int,
        layers: Map<Int, List<LevelLayerCellView>>,
    ): LevelDataView {
        val collisionWalls = layers
            .getOrDefault(1, emptyList())
            .filter { it.assetKey == "wall_block" || it.assetKey == "tree_oak" }
            .map { mapOf("x" to it.x, "y" to it.y) }

        val layerPayload = LevelLayerPayloadCodec.toRequestLayers(layers)
        val payload = mapOf(
            "name" to name,
            "schema_version" to 2,
            "width" to width,
            "height" to height,
            "spawn_x" to spawnX,
            "spawn_y" to spawnY,
            "layers" to layerPayload,
            "wall_cells" to collisionWalls,
        )
        val response = request(
            method = "POST",
            path = "/levels",
            accessToken = accessToken,
            clientVersion = clientVersion,
            body = mapper.writeValueAsString(payload),
        )
        ensureSuccess(response)
        val item = mapper.readTree(response.body())
        val parsedLayers = LevelLayerPayloadCodec.fromResponse(item)
        val parsedWalls = parsedLayers
            .getOrDefault(1, emptyList())
            .filter { it.assetKey == "wall_block" || it.assetKey == "tree_oak" }
            .map { LevelGridCellView(x = it.x, y = it.y) }
        return LevelDataView(
            id = item.path("id").asInt(),
            name = item.path("name").asText(),
            schemaVersion = item.path("schema_version").asInt(2),
            width = item.path("width").asInt(40),
            height = item.path("height").asInt(24),
            spawnX = item.path("spawn_x").asInt(1),
            spawnY = item.path("spawn_y").asInt(1),
            layers = parsedLayers,
            wallCells = parsedWalls,
        )
    }

    fun listChannels(accessToken: String, clientVersion: String): List<ChannelView> {
        val response = request(
            method = "GET",
            path = "/chat/channels",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return mapper.readTree(response.body()).map { item ->
            ChannelView(
                id = item.path("id").asInt(),
                name = item.path("name").asText(),
                kind = item.path("kind").asText(),
            )
        }
    }

    fun listMessages(accessToken: String, clientVersion: String, channelId: Int): List<ChatMessageView> {
        val encoded = URLEncoder.encode(channelId.toString(), StandardCharsets.UTF_8)
        val response = request(
            method = "GET",
            path = "/chat/messages?channel_id=$encoded&limit=120",
            accessToken = accessToken,
            clientVersion = clientVersion,
        )
        ensureSuccess(response)
        return mapper.readTree(response.body()).map { item ->
            ChatMessageView(
                id = item.path("id").asInt(),
                senderDisplayName = item.path("sender_display_name").asText("Unknown"),
                content = item.path("content").asText(),
                createdAt = item.path("created_at").asText(),
            )
        }
    }

    fun sendMessage(accessToken: String, clientVersion: String, channelId: Int, content: String): ChatMessageView {
        val payload = mapOf(
            "channel_id" to channelId,
            "content" to content,
        )
        val response = request(
            method = "POST",
            path = "/chat/messages",
            accessToken = accessToken,
            clientVersion = clientVersion,
            body = mapper.writeValueAsString(payload),
        )
        ensureSuccess(response)
        val item = mapper.readTree(response.body())
        return ChatMessageView(
            id = item.path("id").asInt(),
            senderDisplayName = item.path("sender_display_name").asText("Unknown"),
            content = item.path("content").asText(),
            createdAt = item.path("created_at").asText(),
        )
    }

    private fun parseSession(payload: String): AuthSession {
        val root = mapper.readTree(payload)
        val versionNode = root.path("version_status")
        return AuthSession(
            accessToken = root.path("access_token").asText(),
            refreshToken = root.path("refresh_token").asText(),
            sessionId = root.path("session_id").asText(),
            userId = root.path("user_id").asInt(),
            email = root.path("email").asText(),
            displayName = root.path("display_name").asText(),
            isAdmin = root.path("is_admin").asBoolean(false),
            latestVersion = versionNode.path("latest_version").asText("0.0.0"),
            minSupportedVersion = versionNode.path("min_supported_version").asText("0.0.0"),
            forceUpdate = versionNode.path("force_update").asBoolean(false),
            updateAvailable = versionNode.path("update_available").asBoolean(false),
        )
    }

    private fun ensureSuccess(response: HttpResponse<String>) {
        if (response.statusCode() in 200..299) return
        val message = extractError(response.body())
        throw BackendClientException("${response.statusCode()}: $message")
    }

    private fun extractError(body: String): String {
        return try {
            val node = mapper.readTree(body)
            val detailObject = when {
                node.path("error").isObject -> node.path("error")
                node.path("detail").isObject -> node.path("detail")
                else -> null
            }
            if (detailObject != null) {
                val baseMessage = detailObject.path("message").asText("").ifBlank {
                    detailObject.path("code").asText("Request failed")
                }
                val details = detailObject.path("details")
                if (details.isArray && details.size() > 0) {
                    val first = details[0]
                    val loc = mutableListOf<String>()
                    if (first.path("loc").isArray) {
                        first.path("loc").forEach { part ->
                            val text = part.asText().trim()
                            if (text.isNotBlank() && text != "body") {
                                loc.add(text)
                            }
                        }
                    }
                    val fieldPath = loc.joinToString(".")
                    val message = first.path("msg").asText("").trim()
                    if (message.isNotBlank()) {
                        return if (fieldPath.isNotBlank()) {
                            "$baseMessage ($fieldPath: $message)"
                        } else {
                            "$baseMessage ($message)"
                        }
                    }
                }
                if (baseMessage.isNotBlank()) {
                    baseMessage
                } else {
                    body
                }
            } else when {
                node.path("detail").isTextual -> node.path("detail").asText(body)
                else -> body
            }
        } catch (_: Exception) {
            body
        }
    }

    private fun request(
        method: String,
        path: String,
        body: String? = null,
        accessToken: String? = null,
        clientVersion: String? = null,
    ): HttpResponse<String> {
        val builder = HttpRequest.newBuilder()
            .uri(URI.create("$baseUrl$path"))
            .timeout(Duration.ofSeconds(15))
            .header("Accept", "application/json")

        if (clientVersion != null) {
            builder.header("X-Client-Version", clientVersion)
        }
        if (accessToken != null) {
            builder.header("Authorization", "Bearer $accessToken")
        }
        if (body != null) {
            builder.header("Content-Type", "application/json")
        }

        when (method.uppercase()) {
            "GET" -> builder.GET()
            "POST" -> builder.POST(HttpRequest.BodyPublishers.ofString(body ?: ""))
            "PUT" -> builder.PUT(HttpRequest.BodyPublishers.ofString(body ?: ""))
            "DELETE" -> builder.DELETE()
            else -> throw IllegalArgumentException("Unsupported method: $method")
        }

        return httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString())
    }

    fun rawJsonForDebug(json: JsonNode): String = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(json)
}
