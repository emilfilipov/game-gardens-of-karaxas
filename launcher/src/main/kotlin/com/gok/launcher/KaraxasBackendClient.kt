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
    val latestVersion: String,
    val minSupportedVersion: String,
    val forceUpdate: Boolean,
    val updateAvailable: Boolean
)

data class CharacterView(
    val id: Int,
    val name: String,
    val statPointsTotal: Int,
    val statPointsUsed: Int,
    val isSelected: Boolean
) {
    override fun toString(): String {
        val selection = if (isSelected) " [ACTIVE]" else ""
        return "$name (${statPointsUsed}/$statPointsTotal)$selection"
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
        fun fromEnvironment(): KaraxasBackendClient {
            val endpoint = System.getenv("GOK_API_BASE_URL")
                ?.takeIf { it.isNotBlank() }
                ?.trimEnd('/')
                ?: "http://localhost:8080"
            return KaraxasBackendClient(endpoint)
        }
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
        totalPoints: Int,
        stats: Map<String, Int>,
        skills: Map<String, Int>,
    ): CharacterView {
        val payload = mapOf(
            "name" to name,
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
            when {
                node.path("error").isObject -> node.path("error").path("message").asText(body)
                node.path("detail").isObject -> node.path("detail").path("message").asText(body)
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
