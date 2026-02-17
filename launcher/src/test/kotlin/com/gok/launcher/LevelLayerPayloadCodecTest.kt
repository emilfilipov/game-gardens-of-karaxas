package com.gok.launcher

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class LevelLayerPayloadCodecTest {
    private val mapper = jacksonObjectMapper()

    @Test
    fun `fromResponse parses layered payload`() {
        val json = """
            {
              "layers": {
                "0": [{"x": 1, "y": 2, "asset_key": "grass_tile"}],
                "1": [{"x": 4, "y": 6, "asset_key": "wall_block"}],
                "2": [{"x": 9, "y": 3, "asset_key": "cloud_soft"}]
              }
            }
        """.trimIndent()
        val node = mapper.readTree(json)

        val parsed = LevelLayerPayloadCodec.fromResponse(node)

        assertEquals(setOf(0, 1, 2), parsed.keys)
        assertEquals(LevelLayerCellView(layer = 0, x = 1, y = 2, assetKey = "grass_tile"), parsed[0]?.first())
        assertEquals(LevelLayerCellView(layer = 1, x = 4, y = 6, assetKey = "wall_block"), parsed[1]?.first())
        assertEquals(LevelLayerCellView(layer = 2, x = 9, y = 3, assetKey = "cloud_soft"), parsed[2]?.first())
    }

    @Test
    fun `fromResponse falls back to legacy wall cells`() {
        val json = """
            {
              "wall_cells": [{"x": 7, "y": 8}, {"x": 2, "y": 1}]
            }
        """.trimIndent()
        val node = mapper.readTree(json)

        val parsed = LevelLayerPayloadCodec.fromResponse(node)

        assertEquals(setOf(1), parsed.keys)
        assertEquals(
            listOf(
                LevelLayerCellView(layer = 1, x = 7, y = 8, assetKey = "wall_block"),
                LevelLayerCellView(layer = 1, x = 2, y = 1, assetKey = "wall_block"),
            ),
            parsed[1],
        )
    }

    @Test
    fun `toRequestLayers emits deterministic layer payload`() {
        val layers = linkedMapOf(
            2 to listOf(LevelLayerCellView(layer = 2, x = 9, y = 9, assetKey = "cloud_soft")),
            0 to listOf(LevelLayerCellView(layer = 0, x = 0, y = 0, assetKey = "grass_tile")),
            1 to listOf(LevelLayerCellView(layer = 1, x = 3, y = 4, assetKey = "tree_oak")),
        )

        val payload = LevelLayerPayloadCodec.toRequestLayers(layers)

        assertEquals(listOf("0", "1", "2"), payload.keys.toList())
        assertEquals("grass_tile", payload["0"]?.first()?.get("asset_key"))
        assertEquals("tree_oak", payload["1"]?.first()?.get("asset_key"))
        assertEquals("cloud_soft", payload["2"]?.first()?.get("asset_key"))
    }
}
