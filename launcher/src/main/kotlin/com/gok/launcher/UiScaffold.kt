package com.gok.launcher

import java.awt.Dimension
import java.awt.Font
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.RenderingHints
import java.awt.GridBagConstraints
import java.awt.Insets
import java.awt.Color
import javax.swing.BorderFactory
import javax.swing.JComponent
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.JPasswordField
import javax.swing.JTextField
import javax.swing.SwingConstants

/**
 * Shared UI scaffold tokens so every account screen uses one structure/alignment system.
 */
object UiScaffold {
    val contentPadding: Insets = Insets(12, 12, 12, 12)
    val rowInsets: Insets = Insets(4, 0, 4, 0)
    val sectionInsets: Insets = Insets(10, 0, 10, 0)
    val fieldSize: Dimension = Dimension(260, 34)
    val titleFont: Font = Font("Serif", Font.BOLD, 26)
    val sectionTitleFont: Font = Font("Serif", Font.BOLD, 18)
    val bodyFont: Font = Font("Serif", Font.PLAIN, 14)

    fun contentPanel(): JPanel {
        return JPanel().apply {
            isOpaque = true
            background = Color(27, 20, 16, 245)
            border = BorderFactory.createEmptyBorder(contentPadding.top, contentPadding.left, contentPadding.bottom, contentPadding.right)
        }
    }

    fun gbc(row: Int, weightX: Double = 0.0, fill: Int = GridBagConstraints.NONE): GridBagConstraints {
        return GridBagConstraints().apply {
            gridx = 0
            gridy = row
            anchor = GridBagConstraints.WEST
            insets = rowInsets
            this.fill = fill
            this.weightx = weightX
        }
    }

    fun sectionLabel(text: String): JLabel {
        return JLabel(text, SwingConstants.LEFT).apply {
            font = sectionTitleFont
            foreground = Color(244, 230, 197)
        }
    }

    fun titledLabel(text: String): JLabel {
        return JLabel(text, SwingConstants.LEFT).apply {
            font = bodyFont
            foreground = Color(244, 230, 197)
        }
    }

    fun textField(columns: Int = 24): JTextField {
        return JTextField(columns).apply {
            preferredSize = fieldSize
            minimumSize = fieldSize
            maximumSize = fieldSize
            font = bodyFont
        }
    }

    fun ghostTextField(placeholder: String, columns: Int = 24): JTextField {
        return HintTextField(placeholder, columns).apply {
            preferredSize = fieldSize
            minimumSize = fieldSize
            maximumSize = fieldSize
            font = bodyFont
            foreground = Color(244, 230, 197)
            caretColor = Color(244, 230, 197)
            background = Color(0, 0, 0, 0)
            isOpaque = false
            border = BorderFactory.createEmptyBorder(6, 2, 6, 2)
        }
    }

    fun ghostPasswordField(placeholder: String, columns: Int = 24): JPasswordField {
        return HintPasswordField(placeholder, columns).apply {
            preferredSize = fieldSize
            minimumSize = fieldSize
            maximumSize = fieldSize
            font = bodyFont
            foreground = Color(244, 230, 197)
            caretColor = Color(244, 230, 197)
            background = Color(0, 0, 0, 0)
            isOpaque = false
            border = BorderFactory.createEmptyBorder(6, 2, 6, 2)
        }
    }

    fun applyBodyFont(component: JComponent): JComponent {
        component.font = bodyFont
        return component
    }
}

private class HintTextField(
    private val placeholder: String,
    columns: Int
) : JTextField(columns) {
    override fun paintComponent(graphics: Graphics) {
        super.paintComponent(graphics)
        if (text.isNotEmpty() || hasFocus()) return
        val g2 = graphics.create() as Graphics2D
        try {
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g2.color = Color(244, 230, 197, 140)
            g2.font = font
            val y = (height + g2.fontMetrics.ascent - g2.fontMetrics.descent) / 2
            g2.drawString(placeholder, insets.left, y)
        } finally {
            g2.dispose()
        }
    }
}

private class HintPasswordField(
    private val placeholder: String,
    columns: Int
) : JPasswordField(columns) {
    override fun paintComponent(graphics: Graphics) {
        super.paintComponent(graphics)
        if (password.isNotEmpty() || hasFocus()) return
        val g2 = graphics.create() as Graphics2D
        try {
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g2.color = Color(244, 230, 197, 140)
            g2.font = font
            val y = (height + g2.fontMetrics.ascent - g2.fontMetrics.descent) / 2
            g2.drawString(placeholder, insets.left, y)
        } finally {
            g2.dispose()
        }
    }
}
