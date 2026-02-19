package com.gok.launcher

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class ZoneRuntimeTest {
    @Test
    fun `playerCell clamps world coordinates to valid grid bounds`() {
        val cell = ZoneRuntime.playerCell(
            worldX = 123.4f,
            worldY = -10f,
            tileSize = 32f,
            widthCells = 5,
            heightCells = 4,
        )
        assertEquals(3 to 0, cell)

        val maxCell = ZoneRuntime.playerCell(
            worldX = 9999f,
            worldY = 9999f,
            tileSize = 32f,
            widthCells = 5,
            heightCells = 4,
        )
        assertEquals(4 to 3, maxCell)
    }

    @Test
    fun `shouldPreloadTransition activates only inside configured proximity`() {
        val transition = LevelTransitionView(x = 10, y = 10, transitionType = "stairs", destinationLevelId = 2)
        assertTrue(ZoneRuntime.shouldPreloadTransition(8, 9, transition, proximityCells = 2))
        assertFalse(ZoneRuntime.shouldPreloadTransition(7, 9, transition, proximityCells = 2))
    }

    @Test
    fun `triggeredTransition resolves current-cell handoff target`() {
        val transition = LevelTransitionView(x = 4, y = 6, transitionType = "ladder", destinationLevelId = 9)
        val transitions = mapOf((4 to 6) to transition)
        assertNotNull(ZoneRuntime.triggeredTransition(4 to 6, transitions))
        assertNull(ZoneRuntime.triggeredTransition(4 to 5, transitions))
    }
}
