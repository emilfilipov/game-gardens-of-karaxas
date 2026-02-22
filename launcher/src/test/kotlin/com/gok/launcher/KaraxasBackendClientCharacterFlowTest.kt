package com.gok.launcher

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import kotlin.text.Charsets
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class KaraxasBackendClientCharacterFlowTest {
    private val mapper: ObjectMapper = jacksonObjectMapper()

    @Test
    fun createCharacterThenListCharactersRoundtrip() {
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        val characters = mutableListOf<com.fasterxml.jackson.databind.node.ObjectNode>()
        server.createContext("/characters") { exchange ->
            try {
                when (exchange.requestMethod.uppercase()) {
                    "POST" -> {
                        val body = exchange.requestBody.readBytes().toString(Charsets.UTF_8)
                        val payload = mapper.readTree(body)
                        val id = characters.size + 1
                        val created = mapper.createObjectNode().apply {
                            put("id", id)
                            put("name", payload.path("name").asText("Unnamed"))
                            putNull("level_id")
                            putNull("location_x")
                            putNull("location_y")
                            put("appearance_key", payload.path("appearance_key").asText("human_male"))
                            put("race", payload.path("race").asText("Human"))
                            put("background", payload.path("background").asText("Drifter"))
                            put("affiliation", payload.path("affiliation").asText("Unaffiliated"))
                            put("level", 1)
                            put("experience", 0)
                            put("experience_to_next_level", 100)
                            put("stat_points_total", payload.path("stat_points_total").asInt(10))
                            put("stat_points_used", 0)
                            set<com.fasterxml.jackson.databind.node.ObjectNode>("equipment", mapper.createObjectNode())
                            put("is_selected", false)
                        }
                        characters.add(created)
                        val responseBody = mapper.writeValueAsBytes(created)
                        exchange.responseHeaders.add("Content-Type", "application/json")
                        exchange.sendResponseHeaders(200, responseBody.size.toLong())
                        exchange.responseBody.use { it.write(responseBody) }
                    }

                    "GET" -> {
                        val responseBody = mapper.writeValueAsBytes(characters)
                        exchange.responseHeaders.add("Content-Type", "application/json")
                        exchange.sendResponseHeaders(200, responseBody.size.toLong())
                        exchange.responseBody.use { it.write(responseBody) }
                    }

                    else -> {
                        exchange.sendResponseHeaders(405, -1)
                    }
                }
            } finally {
                exchange.close()
            }
        }
        server.start()
        try {
            val baseUrl = "http://127.0.0.1:${server.address.port}"
            val client = KaraxasBackendClient(baseUrl, mapper)

            val created = client.createCharacter(
                accessToken = "test-token",
                clientVersion = "1.0.0",
                name = "RoundtripHero",
                appearanceKey = "human_male",
                race = "Human",
                background = "Drifter",
                affiliation = "Unaffiliated",
                totalPoints = 10,
                stats = emptyMap(),
                skills = emptyMap(),
                equipment = emptyMap(),
            )
            assertEquals("RoundtripHero", created.name)

            val listed = client.listCharacters(accessToken = "test-token", clientVersion = "1.0.0")
            assertEquals(1, listed.size)
            assertEquals(created.id, listed.first().id)
            assertEquals("RoundtripHero", listed.first().name)
            assertTrue(listed.first().equipment.isEmpty())
        } finally {
            server.stop(0)
        }
    }
}
