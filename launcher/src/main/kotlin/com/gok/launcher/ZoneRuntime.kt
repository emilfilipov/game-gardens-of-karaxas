package com.gok.launcher

object ZoneRuntime {
    fun playerCell(
        worldX: Float,
        worldY: Float,
        tileSize: Float,
        widthCells: Int,
        heightCells: Int,
    ): Pair<Int, Int> {
        if (tileSize <= 0f) return 0 to 0
        val safeWidth = widthCells.coerceAtLeast(1)
        val safeHeight = heightCells.coerceAtLeast(1)
        val x = kotlin.math.floor(worldX / tileSize).toInt().coerceIn(0, safeWidth - 1)
        val y = kotlin.math.floor(worldY / tileSize).toInt().coerceIn(0, safeHeight - 1)
        return x to y
    }

    fun shouldPreloadTransition(
        playerCellX: Int,
        playerCellY: Int,
        transition: LevelTransitionView,
        proximityCells: Int = 2,
    ): Boolean {
        val threshold = proximityCells.coerceAtLeast(0)
        val nearX = kotlin.math.abs(playerCellX - transition.x) <= threshold
        val nearY = kotlin.math.abs(playerCellY - transition.y) <= threshold
        return nearX && nearY
    }

    fun triggeredTransition(
        playerCell: Pair<Int, Int>,
        transitions: Map<Pair<Int, Int>, LevelTransitionView>,
    ): LevelTransitionView? {
        return transitions[playerCell]
    }
}
