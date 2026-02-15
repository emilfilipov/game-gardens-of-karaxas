package com.gok.launcher

import java.awt.BorderLayout
import java.awt.CardLayout
import java.awt.Color
import java.awt.Component
import java.awt.Dimension
import java.awt.EventQueue
import java.awt.Font
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.GradientPaint
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import java.awt.GridLayout
import java.awt.Insets
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import java.awt.event.ComponentAdapter
import java.awt.event.ComponentEvent
import java.awt.event.WindowAdapter
import java.awt.event.WindowEvent
import java.awt.event.ActionEvent
import java.awt.event.KeyEvent
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.net.http.HttpTimeoutException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardOpenOption
import java.time.Instant
import java.time.ZoneId
import java.util.Properties
import javax.imageio.ImageIO
import javax.swing.BorderFactory
import javax.swing.ImageIcon
import javax.swing.JButton
import javax.swing.JCheckBox
import javax.swing.JMenuItem
import javax.swing.JComboBox
import javax.swing.JList
import javax.swing.DefaultListCellRenderer
import javax.swing.JOptionPane
import javax.swing.JPasswordField
import javax.swing.JEditorPane
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.JPopupMenu
import javax.swing.JProgressBar
import javax.swing.JScrollPane
import javax.swing.JTextArea
import javax.swing.JTextField
import javax.swing.SwingConstants
import javax.swing.Timer
import javax.swing.UIManager
import javax.swing.Box
import javax.swing.AbstractAction
import javax.swing.border.TitledBorder
import javax.swing.plaf.basic.BasicProgressBarUI
import javax.net.ssl.SSLException

object LauncherMain {
    private data class PatchNotesSource(
        val path: Path?,
        val markdown: String
    )

    private data class PatchNotesMeta(
        val version: String?,
        val date: String?
    )

    private data class PatchNotesView(
        val title: String,
        val html: String
    )

    private data class LauncherPrefs(
        val lastEmail: String = "",
        val autoLoginEnabled: Boolean = false,
        val autoLoginRefreshToken: String = ""
    )

    private data class CharacterArtOption(
        val key: String,
        val label: String,
        val idle: BufferedImage?,
        val walkSheet: BufferedImage?,
        val runSheet: BufferedImage?,
        val frameWidth: Int = 32,
        val frameHeight: Int = 32,
        val directions: Int = 4,
        val framesPerDirection: Int = 6,
    ) {
        override fun toString(): String = label
    }

    @JvmStatic
    fun main(args: Array<String>) {
        Thread.setDefaultUncaughtExceptionHandler { _, throwable ->
            log("Unhandled exception", throwable)
        }
        val autoPlay = args.any { it == "--autoplay" }
        log("Launcher starting. Args=${args.joinToString(" ")}")
        if (args.any { it.startsWith("--veloapp-") }) {
            log("Detected Velopack hook args. Exiting after logging.")
            return
        }
        EventQueue.invokeLater {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName())
                UIManager.put("AuditoryCues.playList", null)
                createAndShow(autoPlay)
            } catch (ex: Exception) {
                log("Failed to start launcher UI.", ex)
                throw ex
            }
        }
    }

    private fun createAndShow(autoPlay: Boolean = false) {
        val frame = JFrame("Gardens of Karaxas")
        frame.defaultCloseOperation = JFrame.EXIT_ON_CLOSE
        frame.isUndecorated = true
        frame.minimumSize = Dimension(1280, 720)
        frame.preferredSize = Dimension(1600, 900)

        val backgroundImage = loadUiImage("/ui/main_menu_background.png")
        val rectangularButtonImage: BufferedImage? = null
        val textColor = Color(244, 230, 197)

        val rootPanel = BackgroundPanel(backgroundImage).apply {
            layout = BorderLayout()
            border = BorderFactory.createEmptyBorder(8, 12, 8, 12)
        }

        val screenTitle = JLabel("Gardens of Karaxas", SwingConstants.CENTER).apply {
            foreground = textColor
            font = Font("Serif", Font.BOLD, 56)
            border = BorderFactory.createEmptyBorder(4, 0, 4, 0)
        }
        val settingsButton = JButton("\u2699").apply {
            font = Font("Serif", Font.BOLD, 24)
            foreground = textColor
            isFocusPainted = false
            isContentAreaFilled = false
            isBorderPainted = false
            isOpaque = false
            preferredSize = Dimension(42, 42)
            toolTipText = "Menu"
        }
        val headerPanel = JPanel(BorderLayout()).apply {
            isOpaque = false
            add(Box.createHorizontalStrut(42), BorderLayout.WEST)
            add(screenTitle, BorderLayout.CENTER)
            add(settingsButton, BorderLayout.EAST)
        }
        rootPanel.add(headerPanel, BorderLayout.NORTH)

        val backendClient = KaraxasBackendClient.fromEnvironment()
        var launcherPrefs = loadLauncherPrefs()
        var lastEmail = launcherPrefs.lastEmail
        var autoLoginEnabled = launcherPrefs.autoLoginEnabled
        var autoLoginRefreshToken = launcherPrefs.autoLoginRefreshToken

        fun defaultClientVersion(): String {
            val source = loadPatchNotesSource()
            val meta = loadPatchNotesMeta(source.path, source.markdown)
            return meta.version ?: "0.0.0"
        }

        fun footerVersionText(): String {
            val source = loadPatchNotesSource()
            val meta = loadPatchNotesMeta(source.path, source.markdown)
            val version = meta.version ?: defaultClientVersion()
            val date = meta.date ?: Instant.now().atZone(ZoneId.systemDefault()).toLocalDate().toString()
            return "v$version ($date)"
        }

        val footerVersionLabel = JLabel(footerVersionText(), SwingConstants.CENTER).apply {
            foreground = textColor
            font = Font("Serif", Font.PLAIN, 12)
            border = BorderFactory.createEmptyBorder(3, 0, 0, 0)
        }
        rootPanel.add(footerVersionLabel, BorderLayout.SOUTH)

        val settingsPopup = JPopupMenu()
        val welcomeItem = JMenuItem("Welcome [Guest].")
        val quickUpdateItem = JMenuItem("Update & Restart")
        val settingsItem = JMenuItem("Settings")
        val logoutMenuItem = JMenuItem("Logout")
        val exitItem = JMenuItem("Exit")
        val menuBg = Color(52, 39, 32)
        val menuHover = Color(84, 58, 41)
        val menuFg = Color(247, 236, 209)
        val panelBg = Color(42, 31, 25, 190)
        val panelBorder = Color(172, 132, 87)
        fun stylePopupItem(item: JMenuItem) {
            item.font = Font("Serif", Font.BOLD, 15)
            item.foreground = menuFg
            item.background = menuBg
            item.isOpaque = true
            item.border = BorderFactory.createEmptyBorder(8, 14, 8, 14)
            item.model.addChangeListener {
                item.background = if (item.model.isArmed || item.model.isSelected) menuHover else menuBg
            }
        }
        settingsPopup.background = menuBg
        settingsPopup.border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
        stylePopupItem(welcomeItem)
        stylePopupItem(quickUpdateItem)
        stylePopupItem(settingsItem)
        stylePopupItem(logoutMenuItem)
        stylePopupItem(exitItem)
        welcomeItem.isEnabled = false
        settingsPopup.add(welcomeItem)
        settingsPopup.add(quickUpdateItem)
        settingsPopup.add(settingsItem)
        settingsPopup.add(logoutMenuItem)
        settingsPopup.add(exitItem)
        exitItem.addActionListener {
            frame.dispose()
            kotlin.system.exitProcess(0)
        }
        settingsButton.addActionListener {
            settingsPopup.show(settingsButton, settingsButton.width - settingsPopup.preferredSize.width, settingsButton.height)
        }

        val centeredContent = JPanel(GridBagLayout()).apply { isOpaque = false }
        val shellPanel = MenuContentBoxPanel().apply {
            layout = BorderLayout()
            border = BorderFactory.createEmptyBorder(28, 34, 28, 34)
            preferredSize = Dimension(1040, 660)
            minimumSize = Dimension(900, 560)
        }
        val gameSceneContainer = JPanel(BorderLayout()).apply {
            isOpaque = true
            background = Color(12, 10, 9, 240)
            isVisible = false
            border = BorderFactory.createEmptyBorder(20, 20, 20, 20)
        }
        val authStandaloneContainer = JPanel(GridBagLayout()).apply {
            isOpaque = false
            isVisible = false
        }
        centeredContent.add(shellPanel)
        centeredContent.add(gameSceneContainer)
        centeredContent.add(authStandaloneContainer)
        rootPanel.add(centeredContent, BorderLayout.CENTER)

        val patchNotesPane = JEditorPane().apply {
            contentType = "text/html"
            isEditable = false
            putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, true)
            isOpaque = false
            background = Color(0, 0, 0, 0)
            foreground = Color(245, 232, 206)
            font = Font("Serif", Font.PLAIN, 13)
            border = BorderFactory.createEmptyBorder(8, 10, 8, 10)
        }
        val patchNotes = JScrollPane(patchNotesPane).apply {
            border = BorderFactory.createEmptyBorder(6, 8, 6, 8)
            viewportBorder = BorderFactory.createEmptyBorder(0, 0, 0, 0)
            preferredSize = Dimension(680, 410)
            isOpaque = false
            viewport.isOpaque = false
            background = Color(0, 0, 0, 0)
            viewport.background = Color(0, 0, 0, 0)
            verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_NEVER
            horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_NEVER
            verticalScrollBar.preferredSize = Dimension(0, 0)
            horizontalScrollBar.preferredSize = Dimension(0, 0)
            setWheelScrollingEnabled(true)
        }
        val updateStatus = JLabel("")
        val progress = JProgressBar().apply {
            isIndeterminate = false
            isVisible = false
            string = ""
            isStringPainted = true
            preferredSize = Dimension(680, 18)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            setUI(ThemedProgressBarUI())
        }
        val checkUpdates = buildMenuButton("Check Updates", rectangularButtonImage, Dimension(206, 42), 14f)
        val launcherLogButton = buildMenuButton("Launcher Log", rectangularButtonImage, Dimension(206, 42), 14f)
        val gameLogButton = buildMenuButton("Game Log", rectangularButtonImage, Dimension(206, 42), 14f)
        val updateLogButton = buildMenuButton("Update Log", rectangularButtonImage, Dimension(206, 42), 14f)
        val clearLogsButton = buildMenuButton("Clear Logs", rectangularButtonImage, Dimension(206, 42), 14f)
        val showPatchNotesButton = buildMenuButton("Patch Notes", rectangularButtonImage, Dimension(206, 42), 14f)
        val updateBackButton = buildMenuButton("Back", rectangularButtonImage, Dimension(206, 42), 14f)
        val launcherButtons = JPanel(GridLayout(3, 2, 8, 8)).apply {
            isOpaque = false
            add(checkUpdates)
            add(showPatchNotesButton)
            add(launcherLogButton)
            add(gameLogButton)
            add(updateLogButton)
            add(clearLogsButton)
        }
        val buildVersionLabel = JLabel("", SwingConstants.CENTER).apply {
            foreground = Color(246, 233, 201)
            font = Font("Serif", Font.BOLD, 18)
            border = BorderFactory.createEmptyBorder(4, 8, 8, 8)
        }
        val updateContent = UiScaffold.contentPanel().apply {
            layout = BorderLayout(0, 8)
            isOpaque = true
            background = Color(24, 18, 15)
            border = BorderFactory.createEmptyBorder(6, 10, 6, 10)
            add(buildVersionLabel, BorderLayout.NORTH)
            add(patchNotes, BorderLayout.CENTER)
            add(JPanel(BorderLayout(0, 8)).apply {
                isOpaque = false
                add(progress, BorderLayout.NORTH)
                add(launcherButtons, BorderLayout.CENTER)
                add(updateBackButton, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }

        val cardsLayout = CardLayout()
        val menuCards = JPanel(cardsLayout).apply {
            isOpaque = true
            background = Color(24, 18, 15)
        }
        shellPanel.add(menuCards, BorderLayout.CENTER)

        val clientVersion = defaultClientVersion().ifBlank { "0.0.0" }
        var authSession: AuthSession? = null
        fun persistLauncherPrefs() {
            if (!autoLoginEnabled) {
                autoLoginRefreshToken = ""
            }
            launcherPrefs = LauncherPrefs(
                lastEmail = lastEmail,
                autoLoginEnabled = autoLoginEnabled,
                autoLoginRefreshToken = autoLoginRefreshToken
            )
            saveLauncherPrefs(launcherPrefs)
        }
        fun updateSettingsMenuAccess() {
            val loggedIn = authSession != null
            welcomeItem.isVisible = loggedIn
            welcomeItem.text = authSession?.let { session ->
                val username = session.displayName.ifBlank { session.email }
                "Welcome [$username]."
            } ?: "Welcome [Guest]."
            settingsItem.isVisible = loggedIn
            settingsItem.isEnabled = loggedIn
            logoutMenuItem.isVisible = loggedIn
            logoutMenuItem.isEnabled = loggedIn
        }

        fun themedTitledBorder(title: String): TitledBorder {
            return BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(panelBorder, 1),
                title
            ).apply {
                titleColor = textColor
                titleFont = Font("Serif", Font.BOLD, 14)
            }
        }

        fun themeComboBox(combo: JComboBox<String>) {
            combo.background = Color(58, 42, 33)
            combo.foreground = textColor
            combo.isOpaque = true
            combo.border = BorderFactory.createLineBorder(panelBorder, 1)
            combo.renderer = object : DefaultListCellRenderer() {
                override fun getListCellRendererComponent(
                    list: JList<*>?,
                    value: Any?,
                    index: Int,
                    isSelected: Boolean,
                    cellHasFocus: Boolean
                ): Component {
                    val rendered = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus)
                    rendered.foreground = textColor
                    rendered.background = if (isSelected) menuHover else Color(58, 42, 33)
                    return rendered
                }
            }
        }

        fun themeStatusLabel(label: JLabel) {
            label.foreground = textColor
            label.font = UiScaffold.bodyFont
        }

        val lobbyStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val characterSummary = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            foreground = textColor
            background = Color(31, 24, 20, 220)
            border = BorderFactory.createEmptyBorder(10, 10, 10, 10)
            text = "No characters loaded."
        }
        val tabLobby = buildMenuButton("Lobby", rectangularButtonImage, Dimension(150, 38), 13f)
        val tabCreate = buildMenuButton("Create", rectangularButtonImage, Dimension(150, 38), 13f)
        val tabSelect = buildMenuButton("Select", rectangularButtonImage, Dimension(150, 38), 13f)

        val authEmail = UiScaffold.ghostTextField("Email")
        val authPassword = UiScaffold.ghostPasswordField("Password")
        val authDisplayName = UiScaffold.ghostTextField("Display Name")
        val authSubmit = buildMenuButton("Login", rectangularButtonImage, Dimension(180, 42), 14f)
        val authToggleMode = buildMenuButton("Create Account", rectangularButtonImage, Dimension(180, 42), 13f)
        val authStatus = JLabel(" ", SwingConstants.CENTER).apply {
            foreground = textColor
            font = UiScaffold.bodyFont
        }
        authEmail.text = lastEmail
        var registerMode = false

        var loadedCharacters: List<CharacterView> = emptyList()
        val characterRowsPanel = JPanel().apply {
            layout = javax.swing.BoxLayout(this, javax.swing.BoxLayout.Y_AXIS)
            isOpaque = true
            background = Color(24, 18, 15)
            border = BorderFactory.createEmptyBorder(8, 8, 8, 8)
        }
        val characterRowsScroll = JScrollPane(characterRowsPanel).apply {
            border = themedTitledBorder("Characters")
            viewport.isOpaque = true
            viewport.background = Color(24, 18, 15)
            isOpaque = true
            background = Color(24, 18, 15)
            verticalScrollBar.unitIncrement = 18
        }

        val createName = UiScaffold.ghostTextField("Character Name")
        val sexChoice = JComboBox<String>(arrayOf("Male", "Female")).apply {
            preferredSize = UiScaffold.fieldSize
            minimumSize = UiScaffold.fieldSize
            maximumSize = UiScaffold.fieldSize
            font = UiScaffold.bodyFont
        }
        val createStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val createSubmit = buildMenuButton("Create Character", rectangularButtonImage, Dimension(220, 42), 14f)
        val createBackToLobby = buildMenuButton("Back to Lobby", rectangularButtonImage, Dimension(180, 42), 14f)
        val createAppearancePreview = JLabel("No art loaded", SwingConstants.CENTER).apply {
            preferredSize = Dimension(230, 250)
            minimumSize = Dimension(230, 250)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            foreground = Color(245, 232, 206)
            font = Font("Serif", Font.BOLD, 14)
        }
        val createAnimationMode = JComboBox<String>(arrayOf("Idle", "Walk", "Run")).apply {
            preferredSize = UiScaffold.fieldSize
            minimumSize = UiScaffold.fieldSize
            maximumSize = UiScaffold.fieldSize
            font = UiScaffold.bodyFont
        }
        themeComboBox(sexChoice)
        themeComboBox(createAnimationMode)

        val selectStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val selectBackToLobby = buildMenuButton("Back to Lobby", rectangularButtonImage, Dimension(180, 42), 14f)
        val selectCharacterDetails = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            foreground = textColor
            background = Color(31, 24, 20, 220)
            border = BorderFactory.createEmptyBorder(10, 10, 10, 10)
            text = "Choose a character row to preview."
        }

        val gameStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val playStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val playBackToLobby = buildMenuButton("Back to Lobby", rectangularButtonImage, Dimension(180, 42), 14f)
        var selectedCharacterId: Int? = null
        var selectedCharacterView: CharacterView? = null

        fun loadCharacterArtOptions(): List<CharacterArtOption> {
            val options = mutableListOf<CharacterArtOption>()
            val roots = mutableListOf<Path>()
            System.getenv("GOK_CHARACTER_ART_DIR")
                ?.takeIf { it.isNotBlank() }
                ?.let { roots.add(Paths.get(it)) }
            roots.add(payloadRoot().resolve("assets").resolve("characters"))
            roots.add(installRoot().resolve("assets").resolve("characters"))
            roots.add(Paths.get(System.getProperty("user.dir")).resolve("assets").resolve("characters"))
            roots.add(Paths.get(System.getProperty("user.dir")))

            val grouped = linkedMapOf<String, MutableMap<String, BufferedImage>>()
            val matcher = Regex("^karaxas_([a-z0-9_]+)_(idle_32|walk_sheet_4dir_6f|run_sheet_4dir_6f)\\.png$")
            for (root in roots.distinct()) {
                if (!Files.isDirectory(root)) continue
                try {
                    Files.list(root).use { stream ->
                        stream
                            .filter { Files.isRegularFile(it) }
                            .sorted()
                            .forEach { path ->
                                val fileName = path.fileName.toString().lowercase()
                                val match = matcher.matchEntire(fileName) ?: return@forEach
                                val image = try {
                                    ImageIO.read(path.toFile())
                                } catch (_: Exception) {
                                    null
                                }
                                if (image != null) {
                                    val key = match.groupValues[1]
                                    val kind = match.groupValues[2]
                                    grouped.getOrPut(key) { mutableMapOf() }[kind] = image
                                }
                            }
                    }
                } catch (_: Exception) {
                    // Ignore invalid art directories.
                }
            }

            fun formatLabel(key: String): String {
                return key.split('_').joinToString(" ") { part ->
                    if (part.isEmpty()) part else part.replaceFirstChar { c -> c.uppercase() }
                }
            }

            grouped.entries.sortedBy { it.key }.forEach { (key, images) ->
                val idle = images["idle_32"]
                val walk = images["walk_sheet_4dir_6f"]
                val run = images["run_sheet_4dir_6f"]
                val reference = walk ?: run
                val frameWidth = when {
                    reference != null && reference.width % 6 == 0 -> reference.width / 6
                    idle != null -> idle.width
                    else -> 32
                }.coerceAtLeast(1)
                val frameHeight = when {
                    reference != null && reference.height % 4 == 0 -> reference.height / 4
                    idle != null -> idle.height
                    else -> 32
                }.coerceAtLeast(1)
                options.add(
                    CharacterArtOption(
                        key = key,
                        label = formatLabel(key),
                        idle = idle,
                        walkSheet = walk,
                        runSheet = run,
                        frameWidth = frameWidth,
                        frameHeight = frameHeight,
                    )
                )
            }
            return options
        }

        val appearanceOptions = loadCharacterArtOptions()
        val appearanceByKey = appearanceOptions.associateBy { it.key }
        fun appearanceForSex(isFemale: Boolean): String {
            if (appearanceOptions.isEmpty()) return if (isFemale) "human_female" else "human_male"
            val needle = if (isFemale) "female" else "male"
            val matched = appearanceOptions.firstOrNull { it.key.contains(needle) }
            return matched?.key ?: appearanceOptions.first().key
        }
        var createAppearanceKey = when {
            appearanceByKey.containsKey("human_male") -> "human_male"
            appearanceOptions.isNotEmpty() -> appearanceOptions.first().key
            else -> "human_male"
        }

        val selectAppearancePreview = JLabel("No preview", SwingConstants.CENTER).apply {
            preferredSize = Dimension(180, 190)
            minimumSize = Dimension(180, 190)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            foreground = Color(245, 232, 206)
            font = Font("Serif", Font.BOLD, 14)
        }
        var previewFrameIndex = 0
        var previewDirection = 0

        fun renderArtFrame(option: CharacterArtOption, mode: String, frameIndex: Int, direction: Int): BufferedImage? {
            fun safeFrameFromSheet(sheet: BufferedImage?, frameCount: Int): BufferedImage? {
                if (sheet == null || frameCount <= 0) return null
                val dir = direction.coerceIn(0, option.directions - 1)
                val animationFrame = frameIndex.coerceIn(0, frameCount - 1)
                val x = animationFrame * option.frameWidth
                val y = dir * option.frameHeight
                if (x + option.frameWidth > sheet.width || y + option.frameHeight > sheet.height) return null
                return sheet.getSubimage(x, y, option.frameWidth, option.frameHeight)
            }

            return when (mode) {
                "Walk" -> safeFrameFromSheet(option.walkSheet, option.framesPerDirection)
                    ?: option.idle
                    ?: safeFrameFromSheet(option.runSheet, option.framesPerDirection)
                "Run" -> safeFrameFromSheet(option.runSheet, option.framesPerDirection)
                    ?: option.idle
                    ?: safeFrameFromSheet(option.walkSheet, option.framesPerDirection)
                else -> option.idle
                    ?: safeFrameFromSheet(option.walkSheet, option.framesPerDirection)
                    ?: safeFrameFromSheet(option.runSheet, option.framesPerDirection)
            }
        }

        fun applyCreateAppearancePreview() {
            val option = appearanceByKey[createAppearanceKey]
            val mode = createAnimationMode.selectedItem?.toString() ?: "Idle"
            val image = option?.let { renderArtFrame(it, mode, previewFrameIndex, previewDirection) }
            if (image == null) {
                createAppearancePreview.icon = null
                createAppearancePreview.text = if (appearanceOptions.isEmpty()) "No art loaded" else "Preview unavailable"
                return
            }
            val scaled = scaleImage(image, createAppearancePreview.width.coerceAtLeast(180), createAppearancePreview.height.coerceAtLeast(220))
            createAppearancePreview.icon = ImageIcon(scaled)
            createAppearancePreview.text = ""
        }

        fun applySelectionPreview(character: CharacterView?) {
            if (character == null) {
                selectAppearancePreview.icon = null
                selectAppearancePreview.text = "No preview"
                return
            }
            val option = appearanceByKey[character.appearanceKey]
            val image = if (option != null) renderArtFrame(option, "Idle", 0, 0) else null
            if (image == null) {
                selectAppearancePreview.icon = null
                selectAppearancePreview.text = "No art loaded"
                return
            }
            val scaled = scaleImage(image, selectAppearancePreview.width.coerceAtLeast(140), selectAppearancePreview.height.coerceAtLeast(160))
            selectAppearancePreview.icon = ImageIcon(scaled)
            selectAppearancePreview.text = ""
        }

        val previewTimer = Timer(140) {
            val option = appearanceByKey[createAppearanceKey] ?: return@Timer
            val mode = createAnimationMode.selectedItem?.toString() ?: "Idle"
            val frameCount = if (mode == "Idle") 1 else option.framesPerDirection
            previewFrameIndex = (previewFrameIndex + 1) % frameCount.coerceAtLeast(1)
            applyCreateAppearancePreview()
        }
        previewTimer.start()

        val buildPointBudget = 10
        var pointsRemaining = buildPointBudget
        val statAllocations = linkedMapOf(
            "strength" to 0,
            "agility" to 0,
            "intellect" to 0,
        )
        val skillAllocations = linkedMapOf(
            "alchemy" to 0,
            "sword_mastery" to 0,
        )
        val valueLabels = mutableMapOf<String, JLabel>()

        fun updatePointUi() {
            statAllocations.forEach { (key, value) -> valueLabels["stat:$key"]?.text = value.toString() }
            skillAllocations.forEach { (key, value) -> valueLabels["skill:$key"]?.text = value.toString() }
        }

        fun adjustAllocation(bucket: MutableMap<String, Int>, key: String, delta: Int) {
            val current = bucket[key] ?: 0
            if (delta > 0 && pointsRemaining <= 0) return
            if (delta < 0 && current <= 0) return
            bucket[key] = current + delta
            pointsRemaining -= delta
            updatePointUi()
        }

        fun allocationRow(title: String, bucket: MutableMap<String, Int>, key: String, scope: String): JPanel {
            val minus = JButton("-").apply {
                preferredSize = Dimension(36, 28)
                minimumSize = Dimension(36, 28)
                maximumSize = Dimension(36, 28)
                font = Font("Serif", Font.BOLD, 15)
            }
            val plus = JButton("+").apply {
                preferredSize = Dimension(36, 28)
                minimumSize = Dimension(36, 28)
                maximumSize = Dimension(36, 28)
                font = Font("Serif", Font.BOLD, 15)
            }
            val value = JLabel("0", SwingConstants.CENTER).apply {
                preferredSize = Dimension(42, 28)
                foreground = textColor
                font = Font("Serif", Font.BOLD, 16)
            }
            valueLabels["$scope:$key"] = value
            minus.addActionListener { adjustAllocation(bucket, key, -1) }
            plus.addActionListener { adjustAllocation(bucket, key, 1) }
            return JPanel(BorderLayout(8, 0)).apply {
                isOpaque = false
                add(UiScaffold.titledLabel(title), BorderLayout.WEST)
                add(JPanel(GridLayout(1, 3, 4, 0)).apply {
                    isOpaque = false
                    add(minus)
                    add(value)
                    add(plus)
                }, BorderLayout.EAST)
            }
        }

        val gameWorldWidth = 2400f
        val gameWorldHeight = 1600f
        val gameWorldBorder = 96f
        val spriteHalf = 16f
        var gamePlayerX = gameWorldWidth / 2f
        var gamePlayerY = gameWorldHeight / 2f
        var gameDirection = 0
        var gameAnimationFrame = 0
        var gameAnimationCarryMs = 0.0
        var gameMoving = false
        var gameCharacterName = "Character"
        var gameCharacterAppearance: CharacterArtOption? = null
        val heldKeys = mutableSetOf<Int>()

        fun resetPlayerToSpawn() {
            gamePlayerX = gameWorldWidth / 2f
            gamePlayerY = gameWorldHeight / 2f
            gameDirection = 0
            gameAnimationFrame = 0
            gameAnimationCarryMs = 0.0
        }

        fun clampPlayerToWorld() {
            gamePlayerX = gamePlayerX.coerceIn(gameWorldBorder + spriteHalf, gameWorldWidth - gameWorldBorder - spriteHalf)
            gamePlayerY = gamePlayerY.coerceIn(gameWorldBorder + spriteHalf, gameWorldHeight - gameWorldBorder - spriteHalf)
        }

        val gameWorldPanel = object : JPanel() {
            init {
                isOpaque = false
                isFocusable = true
                border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            }

            override fun paintComponent(graphics: Graphics) {
                super.paintComponent(graphics)
                val g2 = graphics.create() as Graphics2D
                try {
                    g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR)
                    g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_SPEED)

                    g2.color = Color(22, 28, 24)
                    g2.fillRect(0, 0, width, height)

                    val maxCamX = (gameWorldWidth - width).coerceAtLeast(0f)
                    val maxCamY = (gameWorldHeight - height).coerceAtLeast(0f)
                    val camX = (gamePlayerX - (width / 2f)).coerceIn(0f, maxCamX)
                    val camY = (gamePlayerY - (height / 2f)).coerceIn(0f, maxCamY)

                    val worldScreenX = (-camX).toInt()
                    val worldScreenY = (-camY).toInt()
                    val worldW = gameWorldWidth.toInt()
                    val worldH = gameWorldHeight.toInt()
                    val border = gameWorldBorder.toInt()

                    g2.color = Color(63, 78, 65)
                    g2.fillRect(worldScreenX, worldScreenY, worldW, worldH)

                    g2.color = Color(74, 90, 76)
                    val grid = 96
                    var gx = 0
                    while (gx <= worldW) {
                        val sx = worldScreenX + gx
                        g2.drawLine(sx, worldScreenY, sx, worldScreenY + worldH)
                        gx += grid
                    }
                    var gy = 0
                    while (gy <= worldH) {
                        val sy = worldScreenY + gy
                        g2.drawLine(worldScreenX, sy, worldScreenX + worldW, sy)
                        gy += grid
                    }

                    g2.color = Color(34, 29, 24)
                    g2.fillRect(worldScreenX, worldScreenY, worldW, border)
                    g2.fillRect(worldScreenX, worldScreenY + worldH - border, worldW, border)
                    g2.fillRect(worldScreenX, worldScreenY, border, worldH)
                    g2.fillRect(worldScreenX + worldW - border, worldScreenY, border, worldH)
                    g2.color = Color(188, 150, 103)
                    g2.drawRect(worldScreenX, worldScreenY, worldW, worldH)

                    val option = gameCharacterAppearance
                    val mode = if (gameMoving) "Walk" else "Idle"
                    val animationFrame = if (gameMoving) gameAnimationFrame else 0
                    val sprite = option?.let { renderArtFrame(it, mode, animationFrame, gameDirection) }
                    val drawSize = 64
                    val playerDrawX = (gamePlayerX - camX - drawSize / 2f).toInt()
                    val playerDrawY = (gamePlayerY - camY - drawSize / 2f).toInt()
                    if (sprite != null) {
                        g2.drawImage(sprite, playerDrawX, playerDrawY, drawSize, drawSize, null)
                    } else {
                        g2.color = Color(241, 221, 170)
                        g2.fillOval(playerDrawX, playerDrawY, drawSize, drawSize)
                    }

                    g2.color = textColor
                    g2.font = Font("Serif", Font.BOLD, 15)
                    g2.drawString(gameCharacterName, playerDrawX - 4, playerDrawY - 8)
                    g2.font = Font("Serif", Font.PLAIN, 14)
                    g2.drawString("WASD to move. Border blocks world edge.", 12, 22)
                } finally {
                    g2.dispose()
                }
            }
        }

        fun bindMovementKey(panel: JPanel, keyName: String, keyCode: Int) {
            val inputMap = panel.getInputMap(JPanel.WHEN_IN_FOCUSED_WINDOW)
            val actionMap = panel.actionMap
            val pressAction = "press_$keyName"
            val releaseAction = "release_$keyName"
            inputMap.put(javax.swing.KeyStroke.getKeyStroke("pressed $keyName"), pressAction)
            inputMap.put(javax.swing.KeyStroke.getKeyStroke("released $keyName"), releaseAction)
            actionMap.put(pressAction, object : AbstractAction() {
                override fun actionPerformed(event: ActionEvent?) {
                    heldKeys.add(keyCode)
                }
            })
            actionMap.put(releaseAction, object : AbstractAction() {
                override fun actionPerformed(event: ActionEvent?) {
                    heldKeys.remove(keyCode)
                }
            })
        }

        bindMovementKey(gameWorldPanel, "W", KeyEvent.VK_W)
        bindMovementKey(gameWorldPanel, "A", KeyEvent.VK_A)
        bindMovementKey(gameWorldPanel, "S", KeyEvent.VK_S)
        bindMovementKey(gameWorldPanel, "D", KeyEvent.VK_D)

        var lastGameTickNanos = System.nanoTime()
        val gameLoopTimer = Timer(16) {
            val now = System.nanoTime()
            val elapsedNs = (now - lastGameTickNanos).coerceIn(0L, 100_000_000L)
            lastGameTickNanos = now
            val dt = elapsedNs / 1_000_000_000.0

            var dx = 0.0
            var dy = 0.0
            if (heldKeys.contains(KeyEvent.VK_A)) dx -= 1.0
            if (heldKeys.contains(KeyEvent.VK_D)) dx += 1.0
            if (heldKeys.contains(KeyEvent.VK_W)) dy -= 1.0
            if (heldKeys.contains(KeyEvent.VK_S)) dy += 1.0

            gameMoving = dx != 0.0 || dy != 0.0
            if (gameMoving) {
                val length = kotlin.math.sqrt((dx * dx) + (dy * dy))
                val speed = 220.0
                val nx = dx / length
                val ny = dy / length
                gamePlayerX += (nx * speed * dt).toFloat()
                gamePlayerY += (ny * speed * dt).toFloat()
                clampPlayerToWorld()

                gameDirection = if (kotlin.math.abs(nx) >= kotlin.math.abs(ny)) {
                    if (nx >= 0.0) 2 else 1
                } else {
                    if (ny >= 0.0) 0 else 3
                }

                val frameCount = gameCharacterAppearance?.framesPerDirection ?: 1
                gameAnimationCarryMs += dt * 1000.0
                if (gameAnimationCarryMs >= 110.0) {
                    gameAnimationCarryMs = 0.0
                    gameAnimationFrame = (gameAnimationFrame + 1) % frameCount.coerceAtLeast(1)
                }
            } else {
                gameAnimationCarryMs = 0.0
                gameAnimationFrame = 0
            }
            gameWorldPanel.repaint()
        }
        gameLoopTimer.start()

        fun enterGameWithCharacter(character: CharacterView) {
            selectedCharacterId = character.id
            selectedCharacterView = character
            gameCharacterName = character.name
            gameCharacterAppearance = appearanceByKey[character.appearanceKey]
            resetPlayerToSpawn()
            clampPlayerToWorld()
            gameStatus.text = " "
            playStatus.text = " "
            gameWorldPanel.requestFocusInWindow()
        }

        fun withSession(onMissing: () -> Unit = {}, block: (AuthSession) -> Unit) {
            val session = authSession
            if (session == null) {
                onMissing()
                return
            }
            block(session)
        }

        fun formatServiceError(ex: Exception, fallback: String): String {
            val chain = generateSequence<Throwable>(ex) { it.cause }
            if (chain.any { it is UnknownHostException }) return "No internet connection. Check your network."
            if (chain.any { it is ConnectException }) return "Servers are currently unavailable. Please try again."
            if (chain.any { it is HttpTimeoutException || it is SocketTimeoutException }) return "Connection timed out. Please try again."
            if (chain.any { it is SSLException }) return "Secure connection failed. Please try again."
            val message = ex.message?.trim().orEmpty()
            if (message.contains(":")) {
                val detail = message.substringAfter(":").trim()
                if (detail.isNotBlank()) return detail
            }
            return if (message.isNotBlank()) message else fallback
        }

        lateinit var showCard: (String) -> Unit
        lateinit var populateCharacterViewsFn: (List<CharacterView>) -> Unit

        fun playWithCharacter(character: CharacterView) {
            withSession(onMissing = { authStatus.text = "Please login first." }) { session ->
                Thread {
                    try {
                        backendClient.selectCharacter(session.accessToken, clientVersion, character.id)
                        javax.swing.SwingUtilities.invokeLater {
                            selectedCharacterId = character.id
                            selectedCharacterView = character
                            showCard("play")
                        }
                    } catch (ex: Exception) {
                        log("Character play handoff failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            selectStatus.text = formatServiceError(ex, "Unable to start play session.")
                        }
                    }
                }.start()
            }
        }

        fun deleteCharacter(character: CharacterView) {
            val confirm = JOptionPane.showConfirmDialog(
                frame,
                "Delete character '${character.name}'?",
                "Delete Character",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if (confirm != JOptionPane.YES_OPTION) return
            withSession(onMissing = { selectStatus.text = "Please login first." }) { session ->
                Thread {
                    try {
                        backendClient.deleteCharacter(session.accessToken, clientVersion, character.id)
                        val refreshed = backendClient.listCharacters(session.accessToken, clientVersion)
                        javax.swing.SwingUtilities.invokeLater {
                            if (selectedCharacterId == character.id) {
                                selectedCharacterId = null
                                selectedCharacterView = null
                            }
                            populateCharacterViewsFn(refreshed)
                            if (refreshed.isEmpty()) {
                                showCard("create_character")
                            }
                        }
                    } catch (ex: Exception) {
                        log("Character delete failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            selectStatus.text = formatServiceError(ex, "Unable to delete character.")
                        }
                    }
                }.start()
            }
        }

        fun renderCharacterRows(characters: List<CharacterView>) {
            characterRowsPanel.removeAll()
            if (characters.isEmpty()) {
                characterRowsPanel.add(JLabel("No characters yet. Create your first character.").apply {
                    foreground = textColor
                    font = UiScaffold.bodyFont
                    border = BorderFactory.createEmptyBorder(12, 6, 12, 6)
                })
            } else {
                characters.forEach { character ->
                    val playButton = buildMenuButton("Play", rectangularButtonImage, Dimension(110, 32), 12f)
                    val deleteButton = buildMenuButton("Delete", rectangularButtonImage, Dimension(110, 32), 12f)
                    val row = JPanel(BorderLayout(8, 0)).apply {
                        isOpaque = true
                        background = Color(39, 29, 24, 220)
                        val rowSize = Dimension(760, 72)
                        preferredSize = rowSize
                        minimumSize = rowSize
                        maximumSize = Dimension(Int.MAX_VALUE, 72)
                        border = BorderFactory.createCompoundBorder(
                            BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                            BorderFactory.createEmptyBorder(8, 10, 8, 10)
                        )
                    }
                    val info = JLabel("${character.name}  |  Level ${character.level}  |  XP ${character.experience} (next ${character.experienceToNextLevel})").apply {
                        foreground = textColor
                        font = Font("Serif", Font.BOLD, 14)
                    }
                    val actions = JPanel(GridLayout(1, 2, 6, 0)).apply {
                        isOpaque = false
                        add(playButton)
                        add(deleteButton)
                    }
                    row.add(info, BorderLayout.CENTER)
                    row.add(actions, BorderLayout.EAST)
                    row.addMouseListener(object : java.awt.event.MouseAdapter() {
                        override fun mouseClicked(e: java.awt.event.MouseEvent?) {
                            selectedCharacterId = character.id
                            selectedCharacterView = character
                            selectCharacterDetails.text =
                                "Name: ${character.name}\nLevel: ${character.level}\nExperience: ${character.experience}\nAppearance: ${character.appearanceKey}"
                            applySelectionPreview(character)
                        }
                    })
                    playButton.addActionListener { playWithCharacter(character) }
                    deleteButton.addActionListener { deleteCharacter(character) }
                    characterRowsPanel.add(row)
                    characterRowsPanel.add(Box.createVerticalStrut(8))
                }
            }
            characterRowsPanel.revalidate()
            characterRowsPanel.repaint()
        }

        populateCharacterViewsFn = fun(characters: List<CharacterView>) {
            loadedCharacters = characters
            val primary = characters.firstOrNull()
            selectedCharacterId = primary?.id
            selectedCharacterView = primary
            if (primary != null) {
                selectCharacterDetails.text =
                    "Name: ${primary.name}\nLevel: ${primary.level}\nExperience: ${primary.experience}\nAppearance: ${primary.appearanceKey}"
                applySelectionPreview(primary)
            } else {
                selectCharacterDetails.text = "Choose a character row to preview."
                applySelectionPreview(null)
            }
            renderCharacterRows(characters)
            characterSummary.text = if (characters.isEmpty()) {
                "No characters created yet.\nUse Create Character to start."
            } else {
                characters.joinToString("\n") { c ->
                    "${c.name} (Lv.${c.level}) - ${c.appearanceKey}"
                }
            }
        }

        fun refreshCharacters(
            statusLabel: JLabel,
            onLoaded: ((List<CharacterView>) -> Unit)? = null
        ) {
            withSession(onMissing = { statusLabel.text = "Please login first." }) { session ->
                statusLabel.text = " "
                Thread {
                    try {
                        val characters = backendClient.listCharacters(session.accessToken, clientVersion)
                        javax.swing.SwingUtilities.invokeLater {
                            populateCharacterViewsFn(characters)
                            statusLabel.text = " "
                            onLoaded?.invoke(characters)
                        }
                    } catch (ex: Exception) {
                        log("Character list refresh failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            statusLabel.text = formatServiceError(ex, "Unable to load characters.")
                        }
                    }
                }.start()
            }
        }

        fun resetAuthInputsForMode() {
            if (registerMode) {
                authEmail.text = ""
                authPassword.text = ""
                authDisplayName.text = ""
            } else {
                authEmail.text = lastEmail
                authPassword.text = ""
                authDisplayName.text = ""
            }
        }

        fun applyAuthenticatedSession(session: AuthSession) {
            authSession = session
            lastEmail = session.email
            if (autoLoginEnabled) {
                autoLoginRefreshToken = session.refreshToken
            }
            persistLauncherPrefs()
            registerMode = false
            updateSettingsMenuAccess()
            authStatus.text = "Loading account..."
            resetAuthInputsForMode()
            refreshCharacters(lobbyStatus) { characters ->
                authStatus.text = " "
                if (characters.isEmpty()) {
                    createStatus.text = " "
                    showCard("create_character")
                } else {
                    selectStatus.text = " "
                    showCard("select_character")
                }
            }
        }

        fun applyAuthMode() {
            authDisplayName.isVisible = registerMode
            authSubmit.text = if (registerMode) "Register" else "Login"
            authToggleMode.text = if (registerMode) "Use Login" else "Create Account"
            authStatus.text = " "
            resetAuthInputsForMode()
            authStandaloneContainer.revalidate()
            authStandaloneContainer.repaint()
            centeredContent.revalidate()
            centeredContent.repaint()
        }

        val authInnerPanel = UiScaffold.contentPanel().apply {
            layout = GridBagLayout()
            add(authDisplayName, UiScaffold.gbc(0))
            add(authEmail, UiScaffold.gbc(1))
            add(authPassword, UiScaffold.gbc(2))
            add(JPanel(GridLayout(1, 2, 8, 0)).apply {
                isOpaque = false
                add(authSubmit)
                add(authToggleMode)
            }, UiScaffold.gbc(3))
            add(authStatus, UiScaffold.gbc(4, weightX = 1.0, fill = GridBagConstraints.HORIZONTAL))
        }
        val authCard = JPanel(GridBagLayout()).apply {
            isOpaque = false
            add(MenuContentBoxPanel().apply {
                layout = BorderLayout()
                preferredSize = Dimension(470, 300)
                minimumSize = Dimension(420, 270)
                border = BorderFactory.createEmptyBorder(20, 24, 18, 24)
                add(authInnerPanel, BorderLayout.CENTER)
            })
        }
        authStandaloneContainer.add(authCard)
        applyAuthMode()
        fun openSettingsDialog() {
            val session = authSession ?: run {
                authStatus.text = "Login first to open settings."
                return
            }
            val autoLoginCheck = JCheckBox("Enable automatic login on startup").apply {
                isOpaque = false
                foreground = textColor
                font = UiScaffold.bodyFont
                isSelected = autoLoginEnabled
            }
            val noteLabel = JLabel("Automatic login uses your current session token.", SwingConstants.LEFT).apply {
                foreground = textColor
                font = Font("Serif", Font.PLAIN, 12)
            }
            val panel = JPanel(BorderLayout(0, 8)).apply {
                isOpaque = false
                border = BorderFactory.createEmptyBorder(8, 8, 2, 8)
                add(autoLoginCheck, BorderLayout.NORTH)
                add(noteLabel, BorderLayout.CENTER)
            }
            val result = JOptionPane.showConfirmDialog(
                frame,
                panel,
                "Settings",
                JOptionPane.OK_CANCEL_OPTION,
                JOptionPane.PLAIN_MESSAGE
            )
            if (result == JOptionPane.OK_OPTION) {
                autoLoginEnabled = autoLoginCheck.isSelected
                autoLoginRefreshToken = if (autoLoginEnabled) session.refreshToken else ""
                persistLauncherPrefs()
                lobbyStatus.text = " "
            }
        }
        settingsItem.addActionListener { openSettingsDialog() }
        updateSettingsMenuAccess()

        val accountTabButtons = linkedMapOf(
            "lobby" to tabLobby,
            "create_character" to tabCreate,
            "select_character" to tabSelect
        )
        fun setActiveAccountTab(card: String) {
            accountTabButtons.forEach { (name, button) ->
                val isActive = name == card
                button.isEnabled = !isActive
                button.foreground = if (isActive) Color(255, 247, 224) else textColor
            }
        }
        val accountTabsPanel = JPanel(GridLayout(1, 3, 8, 0)).apply {
            isOpaque = false
            add(tabLobby)
            add(tabCreate)
            add(tabSelect)
        }
        val accountTopBar = JPanel(BorderLayout(10, 0)).apply {
            isOpaque = true
            background = panelBg
            border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(panelBorder, 1),
                BorderFactory.createEmptyBorder(8, 10, 8, 10)
            )
            add(JLabel("Account", SwingConstants.LEFT).apply {
                foreground = textColor
                font = Font("Serif", Font.BOLD, 18)
            }, BorderLayout.WEST)
            add(accountTabsPanel, BorderLayout.EAST)
            isVisible = false
        }
        shellPanel.add(accountTopBar, BorderLayout.NORTH)

        val lobbyPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(JScrollPane(characterSummary).apply {
                border = themedTitledBorder("Account Characters")
                preferredSize = Dimension(780, 340)
                viewport.isOpaque = true
                viewport.background = Color(24, 18, 15)
                isOpaque = true
                background = Color(24, 18, 15)
            }, BorderLayout.CENTER)
            add(lobbyStatus, BorderLayout.SOUTH)
        }

        val createCharacterPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(12, 8)
            add(UiScaffold.sectionLabel("Character Creation"), BorderLayout.NORTH)
            add(JPanel(BorderLayout(12, 8)).apply {
                isOpaque = false
                add(JPanel(BorderLayout(0, 6)).apply {
                    isOpaque = false
                    border = themedTitledBorder("Character Art Preview")
                    add(createAppearancePreview, BorderLayout.CENTER)
                }, BorderLayout.WEST)
                add(JPanel(GridBagLayout()).apply {
                    isOpaque = false
                    add(UiScaffold.titledLabel("Name"), UiScaffold.gbc(0))
                    add(createName, UiScaffold.gbc(1))
                    add(UiScaffold.titledLabel("Sex"), UiScaffold.gbc(2))
                    add(sexChoice, UiScaffold.gbc(3))
                    add(UiScaffold.titledLabel("Preview Animation"), UiScaffold.gbc(4))
                    add(createAnimationMode, UiScaffold.gbc(5))
                    add(UiScaffold.titledLabel("Scaffold: Start stats/skills"), UiScaffold.gbc(6))
                    add(allocationRow("Strength", statAllocations, "strength", "stat"), UiScaffold.gbc(7, 1.0, GridBagConstraints.HORIZONTAL))
                    add(allocationRow("Agility", statAllocations, "agility", "stat"), UiScaffold.gbc(8, 1.0, GridBagConstraints.HORIZONTAL))
                    add(allocationRow("Intellect", statAllocations, "intellect", "stat"), UiScaffold.gbc(9, 1.0, GridBagConstraints.HORIZONTAL))
                    add(allocationRow("Alchemy", skillAllocations, "alchemy", "skill"), UiScaffold.gbc(10, 1.0, GridBagConstraints.HORIZONTAL))
                    add(allocationRow("Sword Mastery", skillAllocations, "sword_mastery", "skill"), UiScaffold.gbc(11, 1.0, GridBagConstraints.HORIZONTAL))
                    add(JPanel(GridLayout(1, 2, 6, 0)).apply {
                        isOpaque = false
                        add(createSubmit)
                        add(createBackToLobby)
                    }, UiScaffold.gbc(12))
                    add(createStatus, UiScaffold.gbc(13))
                }, BorderLayout.CENTER)
            }, BorderLayout.CENTER)
        }

        val selectCharacterPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(10, 8)
            add(UiScaffold.sectionLabel("Character Selection"), BorderLayout.NORTH)
            add(characterRowsScroll, BorderLayout.CENTER)
            add(JPanel(BorderLayout(0, 8)).apply {
                isOpaque = false
                add(selectAppearancePreview, BorderLayout.NORTH)
                add(JScrollPane(selectCharacterDetails).apply {
                    border = themedTitledBorder("Selection Details")
                    preferredSize = Dimension(260, 220)
                    viewport.isOpaque = true
                    viewport.background = Color(24, 18, 15)
                    isOpaque = true
                    background = Color(24, 18, 15)
                }, BorderLayout.CENTER)
            }, BorderLayout.EAST)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = false
                add(JPanel(GridLayout(1, 1, 6, 0)).apply {
                    isOpaque = false
                    add(selectBackToLobby)
                }, BorderLayout.NORTH)
                add(selectStatus, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }

        val playPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(UiScaffold.sectionLabel("Game World"), BorderLayout.NORTH)
            add(gameWorldPanel, BorderLayout.CENTER)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = false
                add(playBackToLobby, BorderLayout.NORTH)
                add(JPanel(GridLayout(2, 1)).apply {
                    isOpaque = false
                    add(gameStatus)
                    add(playStatus)
                }, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }
        gameSceneContainer.add(playPanel, BorderLayout.CENTER)

        menuCards.add(lobbyPanel, "lobby")
        menuCards.add(createCharacterPanel, "create_character")
        menuCards.add(selectCharacterPanel, "select_character")
        menuCards.add(updateContent, "update")
        var lastAccountCard = "lobby"

        var activeLog: Path? = null
        val controls = listOf(checkUpdates, launcherLogButton, gameLogButton, updateLogButton, clearLogsButton, showPatchNotesButton)
        checkUpdates.addActionListener {
            updateStatus.text = "Checking for updates..."
            runUpdate(updateStatus, patchNotesPane, patchNotes, progress, controls)
        }
        launcherLogButton.addActionListener {
            val target = logsRoot().resolve("launcher.log")
            activeLog = toggleLogView(activeLog, target, "Launcher Log", patchNotesPane, patchNotes, updateStatus)
        }
        gameLogButton.addActionListener {
            val target = logsRoot().resolve("game.log")
            activeLog = toggleLogView(activeLog, target, "Game Log", patchNotesPane, patchNotes, updateStatus)
        }
        updateLogButton.addActionListener {
            val target = resolveUpdateLogPath(installRoot())
            activeLog = toggleLogView(activeLog, target, "Update Log", patchNotesPane, patchNotes, updateStatus)
        }
        clearLogsButton.addActionListener {
            clearLogs()
            val currentLog = activeLog
            if (currentLog != null && Files.exists(currentLog)) {
                patchNotesPane.text = renderLogHtml(currentLog)
                scrollToTop(patchNotesPane, patchNotes)
                updateStatus.text = "Logs cleared."
            } else {
                applyPatchNotesView(patchNotesPane, patchNotes)
                activeLog = null
                updateStatus.text = "Logs cleared."
            }
        }
        showPatchNotesButton.addActionListener {
            activeLog = null
            applyPatchNotesView(patchNotesPane, patchNotes)
            updateStatus.text = "Showing patch notes."
        }

        showCard = fun(card: String) {
            val requiresAuth = card == "lobby" || card == "create_character" || card == "select_character" || card == "play"
            if (requiresAuth && authSession == null) {
                showCard("auth")
                authStatus.text = "Please login first."
                return
            }
            if (card == "auth") {
                shellPanel.isVisible = false
                gameSceneContainer.isVisible = false
                authStandaloneContainer.isVisible = true
                accountTopBar.isVisible = false
                resetAuthInputsForMode()
                centeredContent.revalidate()
                centeredContent.repaint()
                return
            }
            authStandaloneContainer.isVisible = false
            if (card == "play") {
                shellPanel.isVisible = false
                gameSceneContainer.isVisible = true
                accountTopBar.isVisible = false
            } else {
                shellPanel.isVisible = true
                gameSceneContainer.isVisible = false
            }
            if (card != "update" && card != "play") {
                lastAccountCard = card
                accountTopBar.isVisible = true
                setActiveAccountTab(card)
            } else if (card == "update") {
                accountTopBar.isVisible = false
            }
            if (card == "play" && selectedCharacterId == null) {
                JOptionPane.showMessageDialog(frame, "Select a character before entering game features.", "Character Required", JOptionPane.WARNING_MESSAGE)
                showCard("select_character")
                return
            }
            if (card == "update") {
                buildVersionLabel.text = "Build Version: v${defaultClientVersion()} (${Instant.now().atZone(ZoneId.systemDefault()).toLocalDate()})"
                activeLog = null
                applyPatchNotesView(patchNotesPane, patchNotes)
                updateStatus.text = "Ready."
            }
            if (card == "play") {
                val active = selectedCharacterView ?: loadedCharacters.firstOrNull()
                if (active != null) {
                    enterGameWithCharacter(active)
                }
                gameWorldPanel.requestFocusInWindow()
            } else if (card == "select_character") {
                refreshCharacters(selectStatus)
            } else if (card == "lobby" && loadedCharacters.isEmpty()) {
                refreshCharacters(lobbyStatus)
            }
            if (card != "play") {
                cardsLayout.show(menuCards, card)
            }
            centeredContent.revalidate()
            centeredContent.repaint()
        }

        quickUpdateItem.addActionListener {
            showCard("update")
            updateStatus.text = "Checking for updates..."
            runUpdate(updateStatus, patchNotesPane, patchNotes, progress, controls, autoRestartOnSuccess = true)
        }

        fun networkErrorMessage(ex: Exception): String? {
            val chain = generateSequence<Throwable>(ex) { it.cause }
            if (chain.any { it is UnknownHostException }) return "No internet connection. Check your network."
            if (chain.any { it is ConnectException }) return "Servers are currently unavailable. Please try again."
            if (chain.any { it is HttpTimeoutException || it is SocketTimeoutException }) return "Connection timed out. Please try again."
            if (chain.any { it is SSLException }) return "Secure connection failed. Please try again."
            return null
        }

        fun formatAuthError(ex: Exception, registering: Boolean): String {
            networkErrorMessage(ex)?.let { return it }

            val message = ex.message?.trim().orEmpty()
            val code = Regex("^(\\d{3}):").find(message)?.groupValues?.getOrNull(1)?.toIntOrNull()
            if (code == 401) return "This account doesn't exist."
            if (registering && code == 409) return "This account already exists."
            if (code == 422 && message.contains(":")) return message.substringAfter(":").trim()
            if (code != null && message.contains(":")) return message.substringAfter(":").trim()
            return if (message.isNotBlank()) message else "Unable to contact authentication service."
        }

        fun formatAutoLoginError(ex: Exception): String {
            networkErrorMessage(ex)?.let { return it }
            val message = ex.message?.trim().orEmpty()
            val code = Regex("^(\\d{3}):").find(message)?.groupValues?.getOrNull(1)?.toIntOrNull()
            if (code == 401 || code == 403) return "Automatic login expired. Please login."
            return "Automatic login failed. Please login."
        }

        authSubmit.addActionListener {
            val email = authEmail.text.trim()
            val password = String(authPassword.password)
            val displayName = authDisplayName.text.trim()
            val registering = registerMode
            if (email.isBlank() || password.isBlank()) {
                authStatus.text = "Email and password are required."
                return@addActionListener
            }
            val emailPattern = Regex("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")
            if (!emailPattern.matches(email)) {
                authStatus.text = "Enter a valid email address."
                return@addActionListener
            }
            if (password.length < 8) {
                authStatus.text = "Password must be at least 8 characters."
                return@addActionListener
            }
            if (password.length > 128) {
                authStatus.text = "Password must be 128 characters or fewer."
                return@addActionListener
            }
            if (registering && displayName.length < 2) {
                authStatus.text = "Display name must be at least 2 characters."
                return@addActionListener
            }
            if (registering && displayName.length > 64) {
                authStatus.text = "Display name must be 64 characters or fewer."
                return@addActionListener
            }
            authStatus.text = if (registering) "Creating account..." else "Logging in..."
            Thread {
                try {
                    val session = if (registering) {
                        backendClient.register(email, password, displayName, clientVersion)
                    } else {
                        backendClient.login(email, password, clientVersion)
                    }
                    javax.swing.SwingUtilities.invokeLater {
                        applyAuthenticatedSession(session)
                    }
                } catch (ex: Exception) {
                    log("Authentication request failed against ${backendClient.endpoint()}", ex)
                    javax.swing.SwingUtilities.invokeLater {
                        authStatus.text = formatAuthError(ex, registering)
                    }
                }
            }.start()
        }
        authEmail.addActionListener { authSubmit.doClick() }
        authPassword.addActionListener { authSubmit.doClick() }
        authDisplayName.addActionListener { authSubmit.doClick() }

        authToggleMode.addActionListener {
            registerMode = !registerMode
            applyAuthMode()
        }

        tabLobby.addActionListener { showCard("lobby") }
        tabCreate.addActionListener { showCard("create_character") }
        tabSelect.addActionListener { showCard("select_character") }
        updateBackButton.addActionListener { showCard(lastAccountCard) }
        createBackToLobby.addActionListener { showCard("lobby") }
        selectBackToLobby.addActionListener { showCard("lobby") }
        playBackToLobby.addActionListener { showCard("select_character") }
        createAnimationMode.addActionListener {
            previewFrameIndex = 0
            applyCreateAppearancePreview()
        }
        sexChoice.addActionListener {
            createAppearanceKey = appearanceForSex(isFemale = sexChoice.selectedIndex == 1)
            previewFrameIndex = 0
            applyCreateAppearancePreview()
        }
        applyCreateAppearancePreview()
        updatePointUi()

        createSubmit.addActionListener {
            withSession(onMissing = { createStatus.text = "Please login first." }) { session ->
                val name = createName.text.trim()
                if (name.isBlank()) {
                    createStatus.text = "Character name is required."
                    return@withSession
                }
                val stats = statAllocations.toMap()
                val skills = skillAllocations.toMap()
                createStatus.text = " "
                Thread {
                    try {
                        backendClient.createCharacter(
                            accessToken = session.accessToken,
                            clientVersion = clientVersion,
                            name = name,
                            appearanceKey = createAppearanceKey,
                            totalPoints = buildPointBudget,
                            stats = stats,
                            skills = skills,
                        )
                        val refreshed = backendClient.listCharacters(session.accessToken, clientVersion)
                        javax.swing.SwingUtilities.invokeLater {
                            pointsRemaining = buildPointBudget
                            statAllocations.keys.forEach { statAllocations[it] = 0 }
                            skillAllocations.keys.forEach { skillAllocations[it] = 0 }
                            updatePointUi()
                            createName.text = ""
                            populateCharacterViewsFn(refreshed)
                            createStatus.text = " "
                            lobbyStatus.text = " "
                            if (refreshed.isNotEmpty()) {
                                showCard("select_character")
                            }
                        }
                    } catch (ex: Exception) {
                        log("Character create failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            createStatus.text = formatServiceError(ex, "Character creation failed.")
                        }
                    }
                }.start()
            }
        }

        fun performLogout() {
            val session = authSession
            authSession = null
            autoLoginRefreshToken = ""
            persistLauncherPrefs()
            if (session != null) {
                Thread {
                    try {
                        backendClient.logout(session.accessToken, clientVersion)
                    } catch (_: Exception) {
                        // best effort logout
                    }
                }.start()
            }
            characterSummary.text = ""
            loadedCharacters = emptyList()
            characterRowsPanel.removeAll()
            characterRowsPanel.revalidate()
            characterRowsPanel.repaint()
            selectedCharacterId = null
            selectedCharacterView = null
            heldKeys.clear()
            lobbyStatus.text = " "
            createStatus.text = " "
            selectStatus.text = " "
            gameStatus.text = " "
            playStatus.text = " "
            registerMode = false
            updateSettingsMenuAccess()
            showCard("auth")
        }
        logoutMenuItem.addActionListener { performLogout() }

        frame.contentPane.add(rootPanel, BorderLayout.CENTER)
        loadIconImages()?.let { images ->
            frame.iconImages = images
            frame.iconImage = images.first()
            applyTaskbarIcon(images)
            applyDialogIcon(images)
        }
        frame.pack()
        frame.extendedState = frame.extendedState or JFrame.MAXIMIZED_BOTH
        frame.isVisible = true
        showCard("auth")
        if (autoLoginEnabled && autoLoginRefreshToken.isNotBlank()) {
            authStatus.text = "Attempting automatic login..."
            Thread {
                try {
                    val session = backendClient.refresh(autoLoginRefreshToken, clientVersion)
                    javax.swing.SwingUtilities.invokeLater {
                        applyAuthenticatedSession(session)
                    }
                } catch (ex: Exception) {
                    log("Automatic login failed against ${backendClient.endpoint()}", ex)
                    val code = Regex("^(\\d{3}):").find(ex.message?.trim().orEmpty())
                        ?.groupValues
                        ?.getOrNull(1)
                        ?.toIntOrNull()
                    if (code == 401 || code == 403) {
                        autoLoginRefreshToken = ""
                        persistLauncherPrefs()
                    }
                    javax.swing.SwingUtilities.invokeLater {
                        authStatus.text = formatAutoLoginError(ex)
                    }
                }
            }.start()
        }

        frame.addWindowListener(object : WindowAdapter() {
            override fun windowClosing(e: WindowEvent?) {
                authSession = null
            }
        })

        if (autoPlay) {
            javax.swing.SwingUtilities.invokeLater {
                if (authSession != null && selectedCharacterId != null) {
                    showCard("play")
                } else {
                    authStatus.text = "Login to continue."
                }
            }
        }
    }

    private fun loadUiImage(resourcePath: String): BufferedImage? {
        return try {
            LauncherMain::class.java.getResourceAsStream(resourcePath)?.use { input ->
                ImageIO.read(input)
            }
        } catch (ex: Exception) {
            log("Failed to load UI image $resourcePath", ex)
            null
        }
    }

    private fun buildMenuButton(text: String, buttonTexture: BufferedImage?, size: Dimension, fontSize: Float = 25f): JButton {
        val button = JButton(text).apply {
            alignmentX = Component.CENTER_ALIGNMENT
            horizontalTextPosition = SwingConstants.CENTER
            verticalTextPosition = SwingConstants.CENTER
            foreground = Color(247, 236, 209)
            isFocusPainted = false
            margin = Insets(0, 0, 0, 0)
            isContentAreaFilled = true
            isBorderPainted = true
            isOpaque = true
            border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                BorderFactory.createEmptyBorder(4, 10, 4, 10)
            )
            background = Color(68, 50, 37)
            isRolloverEnabled = true
            model.addChangeListener {
                background = when {
                    !model.isEnabled -> Color(45, 34, 26)
                    model.isPressed -> Color(52, 39, 30)
                    model.isRollover -> Color(84, 62, 45)
                    else -> Color(68, 50, 37)
                }
            }
        }
        resizeThemedButton(button, size.width, size.height, fontSize, buttonTexture)
        return button
    }

    private fun resizeThemedButton(
        button: JButton,
        width: Int,
        height: Int,
        fontSize: Float,
        buttonTexture: BufferedImage? = null
    ) {
        val size = Dimension(width, height)
        button.preferredSize = size
        button.maximumSize = size
        button.minimumSize = size
        button.font = Font("Serif", Font.BOLD, fontSize.toInt())
        if (buttonTexture != null) {
            // The launcher intentionally ignores button art in favor of shape-based themed controls.
        }
    }

    private fun scaleImage(source: BufferedImage, width: Int, height: Int): BufferedImage {
        val scaled = BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB)
        val graphics = scaled.createGraphics()
        graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
        graphics.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)
        graphics.drawImage(source, 0, 0, width, height, null)
        graphics.dispose()
        return scaled
    }

    private class BackgroundPanel(private val background: BufferedImage?) : JPanel() {
        override fun paintComponent(graphics: Graphics) {
            super.paintComponent(graphics)
            val g2 = graphics.create() as Graphics2D
            try {
                if (background == null) {
                    g2.color = Color(16, 20, 28)
                    g2.fillRect(0, 0, width, height)
                    return
                }
                g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
                g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)
                val scale = maxOf(width.toDouble() / background.width.toDouble(), height.toDouble() / background.height.toDouble())
                val drawWidth = (background.width * scale).toInt()
                val drawHeight = (background.height * scale).toInt()
                val x = (width - drawWidth) / 2
                val y = (height - drawHeight) / 2
                g2.drawImage(background, x, y, drawWidth, drawHeight, null)
            } finally {
                g2.dispose()
            }
        }
    }

    private class ThemedProgressBarUI : BasicProgressBarUI() {
        override fun paintDeterminate(graphics: Graphics, component: javax.swing.JComponent) {
            val g2 = graphics.create() as Graphics2D
            try {
                val width = progressBar.width
                val height = progressBar.height
                g2.color = Color(54, 41, 33, 220)
                g2.fillRect(0, 0, width, height)
                val amount = getAmountFull(Insets(0, 0, 0, 0), width, height).coerceAtLeast(0)
                if (amount > 0) {
                    g2.color = Color(210, 167, 102, 245)
                    g2.fillRect(0, 0, amount, height)
                    g2.color = Color(239, 210, 156, 185)
                    g2.fillRect(0, 0, amount, (height / 2).coerceAtLeast(1))
                }
                g2.color = Color(120, 86, 54, 255)
                g2.drawRect(0, 0, width - 1, height - 1)
                if (progressBar.isStringPainted) {
                    paintString(graphics, 0, 0, width, height, amount, Insets(0, 0, 0, 0))
                }
            } finally {
                g2.dispose()
            }
        }
    }

    private class MenuContentBoxPanel : JPanel() {
        init {
            isOpaque = true
            background = Color(27, 20, 16)
        }

        override fun paintComponent(graphics: Graphics) {
            super.paintComponent(graphics)
            val g2 = graphics.create() as Graphics2D
            try {
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
                g2.paint = GradientPaint(
                    0f,
                    0f,
                    Color(50, 36, 28, 245),
                    0f,
                    height.toFloat(),
                    Color(28, 21, 17, 250)
                )
                g2.fillRect(0, 0, width, height)
                g2.color = Color(171, 131, 86, 240)
                g2.drawRect(0, 0, (width - 1).coerceAtLeast(0), (height - 1).coerceAtLeast(0))
                g2.color = Color(240, 210, 157, 65)
                g2.drawRect(2, 2, (width - 5).coerceAtLeast(0), (height - 5).coerceAtLeast(0))
            } finally {
                g2.dispose()
            }
        }
    }

    private fun runUpdate(
        status: JLabel,
        patchNotesPane: JEditorPane,
        patchNotesPaneScroll: JScrollPane,
        progress: JProgressBar,
        controls: List<JButton>,
        autoRestartOnSuccess: Boolean = false
    ) {
        setUpdatingState(progress, controls, true)
        val payloadRoot = payloadRoot()
        val root = installRoot(payloadRoot)
        val helperExe = findUpdateHelper(payloadRoot)
        if (helperExe == null) {
            status.text = "Updater helper not found. Reinstall from the latest release."
            log("Update helper missing. Checked ${payloadRoot.toAbsolutePath()}")
            setUpdatingState(progress, controls, false)
            return
        }
        Thread {
            try {
                val logPath = logsRoot().resolve("velopack.log")
                val repoFile = payloadRoot.resolve("update_repo.txt")
                val tokenFile = payloadRoot.resolve("update_token.txt")
                val waitPid = ProcessHandle.current().pid().toString()
                log("Starting update helper using ${helperExe.toAbsolutePath()}")
                val builder = ProcessBuilder(
                    helperExe.toString(),
                    "--repo-file",
                    repoFile.toString(),
                    "--token-file",
                    tokenFile.toString(),
                    "--log-file",
                    logPath.toString(),
                    "--waitpid",
                    waitPid,
                    "--restart-args",
                    "--autoplay"
                )
                    .directory(root.toFile())
                    .redirectErrorStream(true)
                val token = resolveUpdateToken(payloadRoot, root)
                if (!token.isNullOrBlank()) {
                    builder.environment()["VELOPACK_GITHUB_TOKEN"] = token
                    builder.environment()["VELOPACK_TOKEN"] = token
                    log("Update token loaded.")
                } else {
                    log("No update token found.")
                }
                val process = builder.start()
                val outputLines = mutableListOf<String>()
                process.inputStream.bufferedReader().useLines { lines ->
                    lines.forEach { rawLine ->
                        val line = rawLine.trim()
                        if (line.isEmpty()) return@forEach
                        outputLines.add(line)
                        log("Update helper output: $line")
                        handleUpdateHelperLine(line, status, progress)
                    }
                }
                val exitCode = process.waitFor()
                val output = outputLines.joinToString("\n")
                javax.swing.SwingUtilities.invokeLater {
                    status.text = when (exitCode) {
                        0 -> {
                            applyPatchNotesView(patchNotesPane, patchNotesPaneScroll)
                            if (outputLines.any { it == "UPDATE_APPLYING" } || autoRestartOnSuccess) {
                                log("Update applying. Exiting launcher.")
                                Thread {
                                    Thread.sleep(750)
                                    kotlin.system.exitProcess(0)
                                }.start()
                                "Update ready. Restarting automatically..."
                            } else {
                                "Update downloaded. Restart to apply."
                            }
                        }
                        2 -> "No updates available."
                        else -> buildUpdateFailureMessage(exitCode, root, output)
                    }
                    setUpdatingState(progress, controls, false)
                }
                log("Update finished with exit code $exitCode")
            } catch (ex: Exception) {
                javax.swing.SwingUtilities.invokeLater {
                    status.text = "Update failed: ${ex.message}"
                    setUpdatingState(progress, controls, false)
                }
                log("Update failed", ex)
            }
        }.start()
    }

    private fun launchGame(status: JLabel) {
        val root = payloadRoot()
        val overridePath = System.getenv("GOK_GAME_EXE")
        val gameExe = if (!overridePath.isNullOrBlank()) {
            Paths.get(overridePath)
        } else {
            root.resolve("game").resolve("GardensOfKaraxas.exe")
        }
        if (!Files.exists(gameExe)) {
            status.text = "Game executable not found: ${gameExe.toAbsolutePath()}"
            log("Game executable missing at ${gameExe.toAbsolutePath()}")
            return
        }
        try {
            log("Launching game from ${gameExe.toAbsolutePath()}")
            ProcessBuilder(gameExe.toString())
                .directory(gameExe.parent.toFile())
                .start()
            status.text = "Game running."
        } catch (ex: Exception) {
            status.text = "Launch failed: ${ex.message}"
            log("Launch failed", ex)
        }
    }

    private fun installRoot(): Path {
        return installRoot(payloadRoot())
    }

    private fun renderPatchNotes(): String {
        val view = buildPatchNotesView()
        return view.html
    }

    private fun applyPatchNotesView(
        pane: JEditorPane,
        scrollPane: JScrollPane
    ) {
        val view = buildPatchNotesView()
        pane.text = view.html
        scrollToTop(pane, scrollPane)
    }

    private fun toggleLogView(
        activeLog: Path?,
        requestedLog: Path?,
        label: String,
        pane: JEditorPane,
        scrollPane: JScrollPane,
        status: JLabel
    ): Path? {
        if (requestedLog == null) {
            status.text = "$label not found."
            return activeLog
        }
        val normalizedRequested = requestedLog.toAbsolutePath().normalize()
        val normalizedActive = activeLog?.toAbsolutePath()?.normalize()
        if (normalizedActive == normalizedRequested) {
            applyPatchNotesView(pane, scrollPane)
            status.text = "Showing patch notes."
            return null
        }
        if (!Files.exists(requestedLog)) {
            status.text = "$label not found."
            return activeLog
        }
        pane.text = renderLogHtml(requestedLog)
        scrollToTop(pane, scrollPane)
        status.text = "Showing $label."
        return requestedLog
    }

    private fun renderLogHtml(path: Path, maxChars: Int = 200_000): String {
        val content = try {
            Files.readString(path)
        } catch (_: Exception) {
            return "<html><body><p>Unable to read ${escapeHtml(path.toAbsolutePath().toString())}.</p></body></html>"
        }
        val trimmed = if (content.length > maxChars) content.takeLast(maxChars) else content
        val notice = if (content.length > maxChars) {
            "<p><b>Showing last $maxChars characters.</b></p>"
        } else {
            ""
        }
        return "<html><head><style>" +
            "body{font-family:Serif;font-size:12px;color:#f3e8cc;background:transparent;margin:0;padding:4px;}" +
            "h2{font-family:Serif;font-size:14px;margin:0 0 4px 0;}" +
            "p{font-family:Serif;margin:0 0 6px 0;}" +
            "pre{margin:0;white-space:pre-wrap;word-wrap:break-word;}" +
            "</style></head><body>" +
            "<h2>${escapeHtml(path.fileName.toString())}</h2>" +
            notice +
            "<pre>${escapeHtml(trimmed)}</pre>" +
            "</body></html>"
    }

    private fun scrollToTop(pane: JEditorPane, scrollPane: JScrollPane) {
        javax.swing.SwingUtilities.invokeLater {
            pane.caretPosition = 0
            scrollPane.viewport.viewPosition = java.awt.Point(0, 0)
        }
    }

    private fun resolveUpdateLogPath(installRoot: Path): Path? {
        val found = findVelopackLog(installRoot)
        if (found != null) {
            return found
        }
        val logs = logsRoot()
        val candidates = listOf(
            logs.resolve("Velopack.log"),
            logs.resolve("velopack.log"),
            logs.resolve("velopack.txt")
        )
        return candidates.firstOrNull { Files.exists(it) }
    }

    private fun clearLogs() {
        val logs = listLogFiles()
        var cleared = 0
        var failed = 0
        for (path in logs) {
            try {
                if (!Files.exists(path)) continue
                Files.writeString(path, "", StandardOpenOption.TRUNCATE_EXISTING)
                cleared++
            } catch (_: Exception) {
                failed++
            }
        }
        log("Clear logs requested. Cleared=$cleared Failed=$failed")
    }

    private fun listLogFiles(): List<Path> {
        val root = installRoot()
        val logsDir = root.resolve("logs")
        val result = mutableListOf<Path>()
        if (Files.isDirectory(logsDir)) {
            try {
                Files.list(logsDir).use { stream ->
                    stream
                        .filter { Files.isRegularFile(it) }
                        .filter { isLogFile(it) }
                        .forEach { result.add(it) }
                }
            } catch (_: Exception) {
                // Ignore.
            }
        }
        val rootCandidates = listOf(
            root.resolve("Velopack.log"),
            root.resolve("velopack.log"),
            root.resolve("velopack.txt")
        )
        rootCandidates.filterTo(result) { Files.exists(it) }
        return result.distinct()
    }

    private fun isLogFile(path: Path): Boolean {
        val name = path.fileName.toString().lowercase()
        return name.endsWith(".log") || name == "velopack.txt"
    }

    private fun buildPatchNotesView(): PatchNotesView {
        val source = loadPatchNotesSource()
        val meta = loadPatchNotesMeta(source.path, source.markdown)
        val body = extractBulletOnlyPatchNotes(source.markdown)
        val versionText = meta.version?.let { "v$it" } ?: "Version unknown"
        val dateText = meta.date ?: "Date unknown"
        val title = "Patch Notes - $versionText ($dateText)"
        return PatchNotesView(title = title, html = markdownToHtml(body))
    }

    private fun loadPatchNotesSource(): PatchNotesSource {
        val overridePath = System.getenv("GOK_PATCH_NOTES_PATH")
            ?: System.getenv("GOK_RELEASE_NOTES_PATH")
        val payload = payloadRoot()
        val root = installRoot(payload)
        val candidates = listOf(
            payload.resolve("patch_notes.md"),
            root.resolve("patch_notes.md"),
            payload.resolve("release_notes.md"),
            root.resolve("release_notes.md")
        )
        val notesPath = when {
            !overridePath.isNullOrBlank() -> Paths.get(overridePath)
            else -> candidates.firstOrNull { Files.exists(it) }
        }
        if (notesPath != null && Files.exists(notesPath)) {
            val text = try {
                val text = Files.readString(notesPath).trim()
                if (text.isNotEmpty()) text else "Patch notes unavailable."
            } catch (_: Exception) {
                "Patch notes unavailable."
            }
            return PatchNotesSource(notesPath, text)
        }
        return PatchNotesSource(
            path = null,
            markdown = "- Patch notes will appear after updates are installed."
        )
    }

    private fun loadPatchNotesMeta(notesPath: Path?, markdown: String): PatchNotesMeta {
        val payload = payloadRoot()
        val root = installRoot(payload)
        var version = readMetaValue(payload.resolve("patch_notes_meta.txt"), "version")
            ?: readMetaValue(root.resolve("patch_notes_meta.txt"), "version")
        var date = readMetaValue(payload.resolve("patch_notes_meta.txt"), "date")
            ?: readMetaValue(root.resolve("patch_notes_meta.txt"), "date")

        if (version == null) {
            val regex = Regex("^#\\s+.*?v([0-9A-Za-z._-]+)\\s*$")
            markdown.replace("\uFEFF", "").lineSequence().forEach { raw ->
                if (version != null) return@forEach
                val match = regex.find(raw.trim())
                if (match != null) {
                    version = match.groupValues[1]
                }
            }
        }
        if (date == null) {
            val regex = Regex("^Release Date:\\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\\s*$", RegexOption.IGNORE_CASE)
            markdown.replace("\uFEFF", "").lineSequence().forEach { raw ->
                if (date != null) return@forEach
                val match = regex.find(raw.trim())
                if (match != null) {
                    date = match.groupValues[1]
                }
            }
        }
        if (version == null) {
            version = readSqVersion(payload) ?: readSqVersion(root.resolve("current")) ?: readSqVersion(root)
        }
        if (date == null && notesPath != null && Files.exists(notesPath)) {
            try {
                date = Files.getLastModifiedTime(notesPath)
                    .toInstant()
                    .atZone(ZoneId.systemDefault())
                    .toLocalDate()
                    .toString()
            } catch (_: Exception) {
                // Ignore.
            }
        }
        return PatchNotesMeta(version = version, date = date)
    }

    private fun readMetaValue(metaPath: Path, key: String): String? {
        if (!Files.exists(metaPath)) return null
        return try {
            Files.readAllLines(metaPath).asSequence()
                .map { it.trim() }
                .filter { it.isNotBlank() }
                .mapNotNull { line ->
                    val separator = when {
                        line.contains("=") -> "="
                        line.contains(":") -> ":"
                        else -> return@mapNotNull null
                    }
                    val parts = line.split(separator, limit = 2)
                    if (parts.size != 2) return@mapNotNull null
                    val foundKey = parts[0].trim().lowercase()
                    val foundValue = parts[1].trim()
                    if (foundKey == key.lowercase() && foundValue.isNotBlank()) foundValue else null
                }
                .firstOrNull()
        } catch (_: Exception) {
            null
        }
    }

    private fun readSqVersion(root: Path): String? {
        val path = root.resolve("sq.version")
        if (!Files.exists(path)) return null
        return try {
            val text = Files.readString(path)
            val match = Regex("([0-9]+\\.[0-9]+\\.[0-9]+(?:[.-][0-9A-Za-z]+)?)").find(text)
            match?.groupValues?.get(1)
        } catch (_: Exception) {
            null
        }
    }

    private fun extractBulletOnlyPatchNotes(markdown: String): String {
        val cleaned = markdown.replace("\uFEFF", "")
        val bullets = cleaned.lineSequence()
            .map { it.trimEnd() }
            .filter { it.trimStart().startsWith("- ") }
            .toList()
        return if (bullets.isNotEmpty()) {
            bullets.joinToString("\n")
        } else {
            "- Patch notes unavailable."
        }
    }

    private fun markdownToHtml(markdown: String): String {
        val cleaned = markdown.replace("\uFEFF", "")
        val lines = cleaned.replace("\r\n", "\n").split("\n")
        val sb = StringBuilder()
        sb.append(
            "<html><head><style>" +
                "body{font-family:Serif;font-size:13px;color:#f3e8cc;background:transparent;margin:0;padding:4px;}" +
                "h1{font-size:18px;font-weight:700;margin:0 0 6px 0;}" +
                "h2{font-size:16px;font-weight:600;margin:10px 0 4px 0;}" +
                "h3{font-size:14px;font-weight:600;margin:8px 0 4px 0;}" +
                "p{margin:0 0 6px 0;}" +
                "ul{margin:0 0 6px 18px;padding:0;}" +
                "li{margin:0 0 4px 0;}" +
                "code{background:rgba(0,0,0,0.35);padding:1px 3px;border-radius:3px;font-family:Serif;}" +
                "</style></head><body>"
        )
        var inList = false
        for (raw in lines) {
            val line = raw.trim()
            if (line.isEmpty()) {
                if (inList) {
                    sb.append("</ul>")
                    inList = false
                }
                continue
            }
            when {
                line.startsWith("### ") -> {
                    if (inList) { sb.append("</ul>"); inList = false }
                    sb.append("<h3>").append(inlineMarkdown(line.substring(4))).append("</h3>")
                }
                line.startsWith("## ") -> {
                    if (inList) { sb.append("</ul>"); inList = false }
                    sb.append("<h2>").append(inlineMarkdown(line.substring(3))).append("</h2>")
                }
                line.startsWith("# ") -> {
                    if (inList) { sb.append("</ul>"); inList = false }
                    sb.append("<h1>").append(inlineMarkdown(line.substring(2))).append("</h1>")
                }
                line.startsWith("- ") -> {
                    if (!inList) {
                        sb.append("<ul>")
                        inList = true
                    }
                    sb.append("<li>").append(inlineMarkdown(line.substring(2))).append("</li>")
                }
                else -> {
                    if (inList) { sb.append("</ul>"); inList = false }
                    sb.append("<p>").append(inlineMarkdown(line)).append("</p>")
                }
            }
        }
        if (inList) sb.append("</ul>")
        sb.append("</body></html>")
        return sb.toString()
    }

    private fun inlineMarkdown(text: String): String {
        var out = escapeHtml(text)
        out = out.replace(Regex("\\*\\*(.+?)\\*\\*")) { "<b>${it.groupValues[1]}</b>" }
        out = out.replace(Regex("`(.+?)`")) { "<code>${it.groupValues[1]}</code>" }
        return out
    }

    private fun escapeHtml(text: String): String {
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    }

    private fun log(message: String, throwable: Throwable? = null) {
        val logDir = logsRoot()
        val logFile = logDir.resolve("launcher.log")
        val timestamp = Instant.now().toString()
        val entry = buildString {
            append("[").append(timestamp).append("] ").append(message)
            if (throwable != null) {
                append("\n").append(throwable.stackTraceToString())
            }
            append("\n")
        }
        try {
            Files.createDirectories(logDir)
            Files.writeString(
                logFile,
                entry,
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND
            )
        } catch (_: Exception) {
            // Logging must never crash the launcher.
        }
    }

    private fun payloadRoot(): Path {
        val userDir = Paths.get(System.getProperty("user.dir")).toAbsolutePath()
        val envRoot = System.getenv("VELOPACK_APPROOT")?.takeIf { it.isNotBlank() }?.let { Paths.get(it).toAbsolutePath() }
        val localAppData = System.getenv("LOCALAPPDATA")?.takeIf { it.isNotBlank() }?.let {
            Paths.get(it, "GardensOfKaraxas").toAbsolutePath()
        }
        val homeAppData = System.getProperty("user.home")?.let {
            Paths.get(it, "AppData", "Local", "GardensOfKaraxas").toAbsolutePath()
        }
        val javaHome = System.getProperty("java.home")?.let { Paths.get(it).toAbsolutePath() }
        val fromJavaHome = javaHome?.let { home ->
            if (home.fileName.toString().equals("runtime", ignoreCase = true)) home.parent else home.parent
        }
        val codeSource = LauncherMain::class.java.protectionDomain.codeSource?.location
        val jarPath = try {
            codeSource?.toURI()?.let { Paths.get(it).toAbsolutePath() }
        } catch (_: Exception) {
            null
        }
        val jarDir = jarPath?.parent
        val fromCodeSource = when {
            jarDir != null && jarDir.fileName.toString() == "app" -> jarDir.parent
            jarDir != null -> jarDir
            else -> null
        }
        val candidates = listOfNotNull(envRoot, localAppData, homeAppData, fromCodeSource, fromJavaHome, userDir)
        val withGame = candidates.firstOrNull { Files.exists(it.resolve("game")) }
        val withApp = candidates.firstOrNull { Files.exists(it.resolve("app")) }
        return withGame ?: withApp ?: fromCodeSource ?: fromJavaHome ?: userDir
    }

    private fun installRoot(payloadRoot: Path): Path {
        val name = payloadRoot.fileName?.toString()?.lowercase()
        return if (name == "current") {
            payloadRoot.parent ?: payloadRoot
        } else {
            payloadRoot
        }
    }

    private fun loadIconImages(): List<java.awt.Image>? {
        LauncherMain::class.java.getResource("/game_icon.png")?.let {
            return listOf(ImageIcon(it).image)
        }
        return null
    }

    private fun applyTaskbarIcon(images: List<java.awt.Image>) {
        try {
            if (images.isEmpty()) return
            val taskbar = java.awt.Taskbar.getTaskbar()
            taskbar.iconImage = images.first()
        } catch (_: Exception) {
            // Ignore if not supported.
        }
    }

    private fun applyDialogIcon(images: List<java.awt.Image>) {
        try {
            if (images.isEmpty()) return
            UIManager.put("OptionPane.icon", ImageIcon(images.first()))
        } catch (_: Exception) {
            // Ignore if not supported.
        }
    }

    private fun buildUpdateFailureMessage(exitCode: Int, installRoot: Path, output: String = ""): String {
        val logPath = findVelopackLog(installRoot)
        if (logPath == null) {
            return "Update failed (exit $exitCode). No Velopack log found in ${installRoot.toAbsolutePath()}."
        }
        val tail = readLogTail(logPath)
        val combined = listOf(output, tail).joinToString("\n")
        val hint = when {
            combined.contains("401") || combined.contains("403") ||
                combined.contains("Unauthorized", ignoreCase = true) ||
                combined.contains("Forbidden", ignoreCase = true) ->
                "Authentication failed. Check VELOPACK_TOKEN."
            combined.contains("404") || combined.contains("Not Found", ignoreCase = true) ->
                "Release feed not found."
            combined.contains("429") || combined.contains("rate limit", ignoreCase = true) ->
                "Rate limited by GitHub."
            combined.contains("timeout", ignoreCase = true) ||
                combined.contains("timed out", ignoreCase = true) ->
                "Network timeout."
            combined.contains("failed to remove directory", ignoreCase = true) ||
                combined.contains("access is denied", ignoreCase = true) ->
                "Files are in use. Close the launcher/game and retry."
            else -> null
        }
        val base = "Update failed (exit $exitCode)."
        return if (hint != null) {
            "$base $hint See Velopack log for details."
        } else {
            "$base See Velopack log for details."
        }
    }

    private fun findVelopackLog(installRoot: Path): Path? {
        val logsDir = installRoot.resolve("logs")
        val candidates = listOf(
            logsDir.resolve("Velopack.log"),
            logsDir.resolve("velopack.log"),
            logsDir.resolve("velopack.txt"),
            installRoot.resolve("Velopack.log"),
            installRoot.resolve("velopack.log"),
            installRoot.resolve("velopack.txt")
        )
        return candidates.firstOrNull { Files.exists(it) }
    }

    private fun readLogTail(path: Path, maxChars: Int = 4000): String {
        return try {
            val content = Files.readString(path)
            if (content.length <= maxChars) content else content.takeLast(maxChars)
        } catch (_: Exception) {
            ""
        }
    }

    private fun setUpdatingState(progress: JProgressBar, controls: List<JButton>, updating: Boolean) {
        progress.isVisible = updating
        progress.minimum = 0
        progress.maximum = 100
        progress.value = 0
        progress.isIndeterminate = updating
        progress.string = if (updating) "Checking for updates..." else ""
        controls.forEach { it.isEnabled = !updating }
    }

    private fun handleUpdateHelperLine(line: String, status: JLabel, progress: JProgressBar) {
        when {
            line.startsWith("DOWNLOAD_MODE:DELTA:") -> javax.swing.SwingUtilities.invokeLater {
                val count = line.substringAfter("DOWNLOAD_MODE:DELTA:").substringBefore(":").toIntOrNull() ?: 0
                status.text = if (count > 0) {
                    "Delta update available (${count} package${if (count == 1) "" else "s"})."
                } else {
                    "Delta update available."
                }
            }

            line.startsWith("DOWNLOAD_MODE:FULL:") -> javax.swing.SwingUtilities.invokeLater {
                status.text = "Full update package required for this version."
            }

            line == "STATUS:CHECKING" -> javax.swing.SwingUtilities.invokeLater {
                progress.isIndeterminate = true
                progress.string = "Checking for updates..."
                status.text = "Checking for updates..."
            }

            line == "STATUS:DOWNLOADING" -> javax.swing.SwingUtilities.invokeLater {
                progress.isIndeterminate = false
                progress.value = 0
                progress.string = "Downloading update... 0%"
                status.text = "Downloading update..."
            }

            line.startsWith("PROGRESS:") -> {
                val payload = line.substringAfter(':').trim()
                val parts = payload.split(':')
                val percent = parts.firstOrNull()?.toIntOrNull()?.coerceIn(0, 100) ?: return
                val speedBps = parts.getOrNull(1)?.toLongOrNull()?.coerceAtLeast(0L)
                val speedText = formatSpeed(speedBps)
                javax.swing.SwingUtilities.invokeLater {
                    progress.isIndeterminate = false
                    progress.value = percent
                    progress.string = if (speedText != null) {
                        "Downloading update... ${percent}% (${speedText})"
                    } else {
                        "Downloading update... ${percent}%"
                    }
                    status.text = if (percent >= 100) {
                        "Preparing update..."
                    } else if (speedText != null) {
                        "Downloading update... ${percent}% (${speedText})"
                    } else {
                        "Downloading update... ${percent}%"
                    }
                }
            }

            line == "STATUS:APPLYING" -> javax.swing.SwingUtilities.invokeLater {
                progress.isIndeterminate = true
                progress.string = "Applying update..."
                status.text = "Applying update..."
            }
        }
    }

    private fun resolveUpdateToken(payloadRoot: Path, installRoot: Path): String? {
        val env = System.getenv("VELOPACK_TOKEN")
            ?: System.getenv("VELOPACK_GITHUB_TOKEN")
        if (!env.isNullOrBlank()) return env.trim()

        val candidates = listOf(
            payloadRoot.resolve("update_token.txt"),
            installRoot.resolve("update_token.txt")
        )
        for (path in candidates) {
            if (!Files.exists(path)) continue
            val token = try {
                Files.readString(path).trim()
            } catch (_: Exception) {
                ""
            }
            if (token.isNotBlank()) return token
        }
        return null
    }

    private fun formatSpeed(bytesPerSecond: Long?): String? {
        if (bytesPerSecond == null || bytesPerSecond <= 0L) return null
        val kb = 1024.0
        val mb = kb * 1024.0
        val gb = mb * 1024.0
        val value = bytesPerSecond.toDouble()
        return when {
            value >= gb -> String.format("%.2f GB/s", value / gb)
            value >= mb -> String.format("%.2f MB/s", value / mb)
            value >= kb -> String.format("%.1f KB/s", value / kb)
            else -> "${bytesPerSecond} B/s"
        }
    }

    private fun buildUpdateRootCandidates(payloadRoot: Path): List<Path> {
        val roots = mutableListOf<Path>()
        roots.add(installRoot(payloadRoot))
        roots.add(payloadRoot)
        System.getenv("VELOPACK_APPROOT")?.takeIf { it.isNotBlank() }?.let { roots.add(Paths.get(it)) }
        System.getenv("LOCALAPPDATA")?.takeIf { it.isNotBlank() }?.let {
            roots.add(Paths.get(it, "GardensOfKaraxas"))
        }
        System.getProperty("user.home")?.let {
            roots.add(Paths.get(it, "AppData", "Local", "GardensOfKaraxas"))
        }
        return roots.distinct()
    }

    private fun findUpdateExe(payloadRoot: Path): Path? {
        val roots = buildUpdateRootCandidates(payloadRoot)
        return roots.firstOrNull { Files.exists(it.resolve("Update.exe")) }?.resolve("Update.exe")
    }

    private fun findUpdateHelper(payloadRoot: Path): Path? {
        val helper = payloadRoot.resolve("UpdateHelper.exe")
        return helper.takeIf { Files.exists(it) }
    }

    private fun launcherPrefsPath(): Path {
        return installRoot(payloadRoot()).resolve("launcher_prefs.properties")
    }

    private fun loadLauncherPrefs(): LauncherPrefs {
        val path = launcherPrefsPath()
        if (!Files.exists(path)) return LauncherPrefs()
        return try {
            val properties = Properties()
            Files.newInputStream(path).use { input ->
                properties.load(input)
            }
            val enabled = properties.getProperty("auto_login_enabled", "false").equals("true", ignoreCase = true)
            LauncherPrefs(
                lastEmail = properties.getProperty("last_email", "").trim(),
                autoLoginEnabled = enabled,
                autoLoginRefreshToken = if (enabled) {
                    properties.getProperty("auto_login_refresh_token", "").trim()
                } else {
                    ""
                }
            )
        } catch (_: Exception) {
            LauncherPrefs()
        }
    }

    private fun saveLauncherPrefs(prefs: LauncherPrefs) {
        val path = launcherPrefsPath()
        try {
            val properties = Properties()
            val refreshToken = if (prefs.autoLoginEnabled) prefs.autoLoginRefreshToken else ""
            properties.setProperty("last_email", prefs.lastEmail)
            properties.setProperty("auto_login_enabled", prefs.autoLoginEnabled.toString())
            properties.setProperty("auto_login_refresh_token", refreshToken)
            Files.createDirectories(path.parent)
            Files.newOutputStream(
                path,
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING,
                StandardOpenOption.WRITE
            ).use { output ->
                properties.store(output, "Gardens of Karaxas launcher preferences")
            }
        } catch (ex: Exception) {
            log("Failed to save launcher preferences.", ex)
        }
    }

    private fun logsRoot(): Path {
        val root = installRoot(payloadRoot())
        val dir = root.resolve("logs")
        try {
            Files.createDirectories(dir)
        } catch (_: Exception) {
            // Ignore.
        }
        return dir
    }
}
