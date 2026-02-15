package com.gok.launcher

import java.awt.Dimension
import java.awt.Font
import java.awt.GridBagConstraints
import java.awt.Insets
import javax.swing.BorderFactory
import javax.swing.JComponent
import javax.swing.JLabel
import javax.swing.JPanel
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
            isOpaque = false
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
        }
    }

    fun titledLabel(text: String): JLabel {
        return JLabel(text, SwingConstants.LEFT).apply {
            font = bodyFont
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

    fun applyBodyFont(component: JComponent): JComponent {
        component.font = bodyFont
        return component
    }
}
