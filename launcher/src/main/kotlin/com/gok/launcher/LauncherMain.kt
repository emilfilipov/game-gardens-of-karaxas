package com.gok.launcher

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import java.awt.BorderLayout
import java.awt.CardLayout
import java.awt.Color
import java.awt.Component
import java.awt.Dimension
import java.awt.AlphaComposite
import java.awt.EventQueue
import java.awt.Font
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.GradientPaint
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import java.awt.GridLayout
import java.awt.Insets
import java.awt.Rectangle
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
import javax.swing.JScrollPane
import javax.swing.JTextArea
import javax.swing.JTextField
import javax.swing.JToggleButton
import javax.swing.SwingConstants
import javax.swing.ToolTipManager
import javax.swing.Timer
import javax.swing.UIManager
import javax.swing.Box
import javax.swing.AbstractAction
import javax.swing.border.TitledBorder
import javax.swing.plaf.basic.BasicButtonUI
import javax.swing.plaf.basic.BasicComboBoxUI
import javax.swing.plaf.basic.BasicMenuItemUI
import javax.swing.plaf.basic.BasicScrollBarUI
import javax.net.ssl.SSLException

object LauncherMain {
    private const val THEME_FONT_FAMILY = "Serif"
    private val THEME_TEXT_COLOR = Color(244, 230, 197)
    private const val THEME_TEXT_HEX = "#f4e6c5"

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

    private data class RuntimeContentState(
        val bootstrap: ContentBootstrapView,
        val validSnapshot: Boolean,
        val source: String,
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

    private data class LevelTileAsset(
        val key: String,
        val label: String,
        val defaultLayer: Int,
        val collidable: Boolean,
        val image: BufferedImage?,
    )

    private data class SkillTooltipTemplate(
        val fullName: String,
        val manaCost: String,
        val energyCost: String,
        val lifeCost: String,
        val effects: String,
        val damage: String,
        val cooldown: String,
        val skillTypeTag: String,
        val description: String,
    )

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
        val textColor = THEME_TEXT_COLOR

        val rootPanel = BackgroundPanel(backgroundImage).apply {
            layout = BorderLayout()
            border = BorderFactory.createEmptyBorder(8, 12, 8, 12)
        }

        val screenTitle = JLabel("Gardens of Karaxas", SwingConstants.CENTER).apply {
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 56)
            border = BorderFactory.createEmptyBorder(4, 0, 4, 0)
        }
        val settingsButton = JButton("\u2699").apply {
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 20)
            preferredSize = Dimension(42, 42)
            toolTipText = "Menu"
            margin = Insets(0, 0, 0, 0)
            horizontalAlignment = SwingConstants.CENTER
            verticalAlignment = SwingConstants.CENTER
        }
        applyThemedButtonStyle(settingsButton, 20f, compactPadding = true)
        settingsButton.border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
        val headerPanel = JPanel(BorderLayout()).apply {
            isOpaque = false
            add(Box.createHorizontalStrut(42), BorderLayout.WEST)
            add(screenTitle, BorderLayout.CENTER)
            add(JPanel(GridBagLayout()).apply {
                isOpaque = false
                add(settingsButton)
            }, BorderLayout.EAST)
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

        val embeddedBootstrap = embeddedContentBootstrap()
        val cachedBootstrap = loadCachedContentBootstrap()
        var runtimeContentState = RuntimeContentState(
            bootstrap = cachedBootstrap ?: embeddedBootstrap,
            validSnapshot = cachedBootstrap != null,
            source = if (cachedBootstrap != null) "cache" else "embedded",
        )
        try {
            val fetched = backendClient.fetchContentBootstrap(defaultClientVersion())
            if (isUsableContentBootstrap(fetched)) {
                runtimeContentState = RuntimeContentState(
                    bootstrap = fetched,
                    validSnapshot = true,
                    source = "network",
                )
                saveCachedContentBootstrap(fetched)
                log("Loaded content bootstrap from backend version=${fetched.contentVersionKey}")
            } else {
                log("Fetched content bootstrap was invalid; keeping ${runtimeContentState.source} snapshot.")
            }
        } catch (ex: Exception) {
            log("Content bootstrap fetch failed; using ${runtimeContentState.source} snapshot.", ex)
        }
        var runtimeContent = runtimeContentState.bootstrap
        var hasValidContentSnapshot = runtimeContentState.validSnapshot
        var contentSnapshotSource = runtimeContentState.source
        fun contentText(textKey: String, fallback: String): String {
            val value = runtimeContent.uiText[textKey]?.trim().orEmpty()
            return if (value.isNotBlank()) value else fallback
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
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 12)
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
        val menuFg = THEME_TEXT_COLOR
        val panelBg = Color(42, 31, 25)
        val panelBorder = Color(172, 132, 87)
        fun stylePopupItem(item: JMenuItem) {
            item.font = Font(THEME_FONT_FAMILY, Font.BOLD, 15)
            item.foreground = menuFg
            item.background = menuBg
            item.isOpaque = true
            item.isBorderPainted = false
            item.border = BorderFactory.createEmptyBorder(8, 14, 8, 14)
            item.setUI(object : BasicMenuItemUI() {
                override fun installDefaults() {
                    super.installDefaults()
                    selectionBackground = menuHover
                    selectionForeground = menuFg
                    disabledForeground = Color(149, 125, 96)
                }
            })
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
            border = BorderFactory.createEmptyBorder(24, 28, 24, 28)
            preferredSize = Dimension(1360, 820)
            minimumSize = Dimension(1180, 700)
        }
        val gameSceneContainer = JPanel(BorderLayout()).apply {
            isOpaque = true
            background = Color(12, 10, 9)
            isVisible = false
            border = BorderFactory.createEmptyBorder(20, 20, 20, 20)
        }
        val levelSceneContainer = JPanel(BorderLayout()).apply {
            isOpaque = true
            background = Color(12, 10, 9)
            isVisible = false
            border = BorderFactory.createEmptyBorder(12, 12, 12, 12)
        }
        UIManager.put("ToolTip.background", Color(31, 24, 20))
        UIManager.put("ToolTip.foreground", THEME_TEXT_COLOR)
        UIManager.put("ToolTip.border", BorderFactory.createLineBorder(Color(172, 132, 87), 1))
        UIManager.put("ToolTip.font", Font(THEME_FONT_FAMILY, Font.PLAIN, 12))
        ToolTipManager.sharedInstance().initialDelay = 120
        ToolTipManager.sharedInstance().reshowDelay = 0
        ToolTipManager.sharedInstance().dismissDelay = 30_000
        val authStandaloneContainer = JPanel(GridBagLayout()).apply {
            isOpaque = false
            isVisible = false
        }
        centeredContent.add(shellPanel)
        centeredContent.add(gameSceneContainer)
        centeredContent.add(levelSceneContainer)
        centeredContent.add(authStandaloneContainer)
        rootPanel.add(centeredContent, BorderLayout.CENTER)

        val patchNotesPane = JEditorPane().apply {
            contentType = "text/html"
            isEditable = false
            putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, true)
            isOpaque = false
            background = Color(0, 0, 0, 0)
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 13)
            border = BorderFactory.createEmptyBorder(8, 10, 8, 10)
        }
        val patchNotes = ThemedScrollPane(patchNotesPane, transparent = true).apply {
            border = BorderFactory.createEmptyBorder(6, 8, 6, 8)
            viewportBorder = BorderFactory.createEmptyBorder(0, 0, 0, 0)
            preferredSize = Dimension(680, 410)
            verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_NEVER
            horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_NEVER
            verticalScrollBar.preferredSize = Dimension(0, 0)
            horizontalScrollBar.preferredSize = Dimension(0, 0)
            setWheelScrollingEnabled(true)
        }
        val updateStatus = JLabel(" ", SwingConstants.CENTER).apply {
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 13)
            border = BorderFactory.createEmptyBorder(4, 0, 8, 0)
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
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 18)
            border = BorderFactory.createEmptyBorder(4, 8, 8, 8)
        }
        val updateContent = UiScaffold.contentPanel().apply {
            layout = BorderLayout(0, 8)
            isOpaque = true
            background = Color(24, 18, 15)
            border = BorderFactory.createEmptyBorder(6, 10, 6, 10)
            add(buildVersionLabel, BorderLayout.NORTH)
            add(patchNotes, BorderLayout.CENTER)
            add(JPanel(BorderLayout(0, 10)).apply {
                isOpaque = false
                add(updateStatus, BorderLayout.NORTH)
                add(JPanel(BorderLayout(0, 8)).apply {
                    isOpaque = false
                    add(launcherButtons, BorderLayout.CENTER)
                    add(updateBackButton, BorderLayout.SOUTH)
                }, BorderLayout.CENTER)
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
                titleFont = Font(THEME_FONT_FAMILY, Font.BOLD, 14)
            }
        }

        fun themeStatusLabel(label: JLabel) {
            label.foreground = textColor
            label.font = UiScaffold.bodyFont
        }

        val tabSelect = buildMenuButton("Character List", rectangularButtonImage, Dimension(190, 38), 13f)
        val tabCreate = buildMenuButton("Create Character", rectangularButtonImage, Dimension(190, 38), 13f)
        val tabLevelTool = buildMenuButton("Levels", rectangularButtonImage, Dimension(150, 38), 13f).apply {
            isVisible = false
        }

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
        var availableLevels: List<LevelSummaryView> = emptyList()
        val levelDetailsById = mutableMapOf<Int, LevelDataView>()
        val characterRowsPanel = JPanel().apply {
            layout = javax.swing.BoxLayout(this, javax.swing.BoxLayout.Y_AXIS)
            isOpaque = true
            background = Color(24, 18, 15)
            border = BorderFactory.createEmptyBorder(8, 8, 8, 8)
        }
        val characterRowsScroll = ThemedScrollPane(characterRowsPanel).apply {
            border = themedTitledBorder("Character List")
            horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_NEVER
        }

        val createName = UiScaffold.ghostTextField("Character Name")
        val createIdentityFieldSize = Dimension(190, UiScaffold.fieldSize.height)
        val createStatControlCardSize = Dimension(250, 36)
        val createStatDescriptionCardSize = Dimension(280, 36)
        val createSkillButtonSize = Dimension(74, 74)
        val createStatsPanelSize = Dimension(560, 320)
        val createSkillsPanelSize = Dimension(560, 320)
        val createPreviewRenderSize = Dimension(230, 250)
        val runtimeRaceOptions = runtimeContent.races
            .ifEmpty { embeddedBootstrap.races }
            .filter { it.label.isNotBlank() }
            .distinctBy { it.value.lowercase() }
        val runtimeBackgroundOptions = runtimeContent.backgrounds
            .ifEmpty { embeddedBootstrap.backgrounds }
            .filter { it.label.isNotBlank() }
            .distinctBy { it.value.lowercase() }
        val runtimeAffiliationOptions = runtimeContent.affiliations
            .ifEmpty { embeddedBootstrap.affiliations }
            .filter { it.label.isNotBlank() }
            .distinctBy { it.value.lowercase() }
        val runtimeStatEntries = runtimeContent.stats
            .ifEmpty { embeddedBootstrap.stats }
            .filter { it.key.isNotBlank() && it.label.isNotBlank() }
            .distinctBy { it.key.lowercase() }
        val runtimeSkillEntries = runtimeContent.skills
            .ifEmpty { embeddedBootstrap.skills }
            .filter { it.key.isNotBlank() && it.label.isNotBlank() }
            .distinctBy { it.key.lowercase() }
        val sexChoice = ThemedComboBox<String>().apply {
            addItem("Male")
            addItem("Female")
            preferredSize = createIdentityFieldSize
            minimumSize = createIdentityFieldSize
            maximumSize = createIdentityFieldSize
            font = UiScaffold.bodyFont
        }
        createName.preferredSize = createIdentityFieldSize
        createName.minimumSize = createIdentityFieldSize
        createName.maximumSize = createIdentityFieldSize
        val raceChoice = ThemedComboBox<String>().apply {
            runtimeRaceOptions.forEach { addItem(it.label) }
            preferredSize = createIdentityFieldSize
            minimumSize = createIdentityFieldSize
            maximumSize = createIdentityFieldSize
            font = UiScaffold.bodyFont
            toolTipText = "Race options are loaded from active content."
        }
        val backgroundChoice = ThemedComboBox<String>().apply {
            runtimeBackgroundOptions.forEach { addItem(it.label) }
            preferredSize = createIdentityFieldSize
            minimumSize = createIdentityFieldSize
            maximumSize = createIdentityFieldSize
            font = UiScaffold.bodyFont
            toolTipText = "Background options are loaded from active content."
        }
        val affiliationChoice = ThemedComboBox<String>().apply {
            runtimeAffiliationOptions.forEach { addItem(it.label) }
            preferredSize = createIdentityFieldSize
            minimumSize = createIdentityFieldSize
            maximumSize = createIdentityFieldSize
            font = UiScaffold.bodyFont
            toolTipText = "Affiliation options are loaded from active content."
        }
        val createStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val createSubmit = buildMenuButton("Create Character", rectangularButtonImage, Dimension(220, 42), 14f)
        val createAppearancePreview = JLabel("No art loaded", SwingConstants.CENTER).apply {
            preferredSize = createPreviewRenderSize
            minimumSize = createPreviewRenderSize
            isOpaque = true
            background = Color(31, 24, 20)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            foreground = THEME_TEXT_COLOR
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 14)
        }
        createName.toolTipText = "Enter a unique character name."
        sexChoice.toolTipText = "Choose the visual sex preset for this character."

        val selectStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val selectCharacterDetails = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            foreground = textColor
            background = Color(31, 24, 20)
            border = BorderFactory.createEmptyBorder(10, 10, 10, 10)
            text = "Choose a character row to preview."
        }

        val gameStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val playStatus = JLabel(" ").apply { themeStatusLabel(this) }
        val playBackToLobby = buildMenuButton("Back to Select", rectangularButtonImage, Dimension(180, 42), 14f)
        val levelToolStatus = JLabel(" ").apply { themeStatusLabel(this) }
        var selectedCharacterId: Int? = null
        var selectedCharacterView: CharacterView? = null
        var activeGameCharacterView: CharacterView? = null
        var activeGameLevelId: Int? = null
        var activeGameLevelName: String = "Unassigned"

        fun loadCharacterArtOptions(): List<CharacterArtOption> {
            val options = mutableListOf<CharacterArtOption>()
            val roots = mutableListOf<Path>()
            val femaleToken = Regex("(^|[_-])female([_-]|$)")
            val maleToken = Regex("(^|[_-])male([_-]|$)")
            fun appendCharacterRoots(base: Path) {
                roots.add(base)
                roots.add(base.resolve("assets").resolve("characters"))
                roots.add(base.resolve("game").resolve("assets").resolve("characters"))
            }
            System.getenv("GOK_CHARACTER_ART_DIR")
                ?.takeIf { it.isNotBlank() }
                ?.let { appendCharacterRoots(Paths.get(it).toAbsolutePath().normalize()) }
            appendCharacterRoots(payloadRoot().toAbsolutePath().normalize())
            appendCharacterRoots(installRoot().toAbsolutePath().normalize())
            var cwdProbe: Path? = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize()
            repeat(5) {
                cwdProbe?.let {
                    appendCharacterRoots(it)
                    cwdProbe = it.parent
                }
            }

            val grouped = linkedMapOf<String, MutableMap<String, BufferedImage>>()
            val strictMatcher = Regex("^karaxas_([a-z0-9_]+)_(idle(?:_[0-9]+)?|walk(?:_sheet(?:_4dir_6f)?)?|run(?:_sheet(?:_4dir_6f)?)?)\\.png$")
            val skipTokens = setOf("karaxas", "idle", "walk", "run", "sheet", "4dir", "6f", "32")

            fun normalizeKind(raw: String): String? {
                val lowered = raw.lowercase()
                return when {
                    lowered.startsWith("idle") -> "idle_32"
                    lowered.startsWith("walk") -> "walk_sheet_4dir_6f"
                    lowered.startsWith("run") -> "run_sheet_4dir_6f"
                    else -> null
                }
            }

            fun parseArtDescriptor(fileName: String): Pair<String, String>? {
                val lowered = fileName.lowercase()
                val strict = strictMatcher.matchEntire(lowered)
                if (strict != null) {
                    val key = strict.groupValues[1]
                    val kind = normalizeKind(strict.groupValues[2]) ?: return null
                    return key to kind
                }
                if (!lowered.endsWith(".png")) return null
                val base = lowered.removeSuffix(".png")
                val kind = when {
                    "idle" in base -> "idle_32"
                    "walk" in base -> "walk_sheet_4dir_6f"
                    "run" in base -> "run_sheet_4dir_6f"
                    else -> return null
                }
                val key = when {
                    femaleToken.containsMatchIn(base) -> if ("human" in base) "human_female" else "female"
                    maleToken.containsMatchIn(base) -> if ("human" in base) "human_male" else "male"
                    else -> {
                        val tokens = base.split('_', '-')
                            .filter { it.isNotBlank() && it !in skipTokens }
                        if (tokens.isEmpty()) return null
                        tokens.joinToString("_")
                    }
                }
                return key to kind
            }

            for (root in roots.distinct()) {
                if (!Files.isDirectory(root)) continue
                try {
                    Files.walk(root, 3).use { stream ->
                        stream
                            .filter { Files.isRegularFile(it) }
                            .sorted()
                            .forEach { path ->
                                val descriptor = parseArtDescriptor(path.fileName.toString()) ?: return@forEach
                                val image = try {
                                    ImageIO.read(path.toFile())
                                } catch (_: Exception) {
                                    null
                                }
                                if (image != null) {
                                    val (key, kind) = descriptor
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
            val searched = roots.distinct().joinToString(", ") { it.toAbsolutePath().toString() }
            if (options.isEmpty()) {
                log("Character art discovery found no options. Searched roots: $searched")
            } else {
                val keys = options.joinToString(", ") { it.key }
                log("Character art discovery loaded ${options.size} option(s): $keys")
            }
            return options
        }

        val appearanceOptions = loadCharacterArtOptions()
        val appearanceByKey = appearanceOptions.associateBy { it.key }
        val femaleKeyMatcher = Regex("(^|_)female($|_)")
        val maleKeyMatcher = Regex("(^|_)male($|_)")
        fun resolveAppearanceOption(appearanceKey: String?): CharacterArtOption? {
            if (appearanceOptions.isEmpty()) return null
            val normalized = appearanceKey?.trim()?.lowercase().orEmpty()
            if (normalized.isBlank()) return appearanceOptions.firstOrNull()
            appearanceByKey[normalized]?.let { return it }
            appearanceByKey.entries.firstOrNull { (key, _) ->
                normalized.contains(key) || key.contains(normalized)
            }?.let { return it.value }
            if (femaleKeyMatcher.containsMatchIn(normalized)) {
                appearanceOptions.firstOrNull { femaleKeyMatcher.containsMatchIn(it.key) }?.let { return it }
            } else if (maleKeyMatcher.containsMatchIn(normalized)) {
                appearanceOptions.firstOrNull { maleKeyMatcher.containsMatchIn(it.key) }?.let { return it }
            }
            return appearanceOptions.firstOrNull()
        }
        fun appearanceForSex(isFemale: Boolean): String {
            if (appearanceOptions.isEmpty()) return if (isFemale) "human_female" else "human_male"
            if (isFemale && appearanceByKey.containsKey("human_female")) return "human_female"
            if (!isFemale && appearanceByKey.containsKey("human_male")) return "human_male"
            val matched = if (isFemale) {
                appearanceOptions.firstOrNull { femaleKeyMatcher.containsMatchIn(it.key) }
            } else {
                appearanceOptions.firstOrNull { maleKeyMatcher.containsMatchIn(it.key) }
            }
            return matched?.key ?: appearanceOptions.first().key
        }
        var createAppearanceKey = when {
            appearanceByKey.containsKey("human_male") -> "human_male"
            appearanceOptions.isNotEmpty() -> appearanceOptions.first().key
            else -> "human_male"
        }

        fun loadLevelTileAssets(): Map<String, LevelTileAsset> {
            data class TileSpec(
                val key: String,
                val label: String,
                val defaultLayer: Int,
                val collidable: Boolean,
                val fileNames: List<String>,
            )

            val specs = listOf(
                TileSpec(
                    key = "grass_tile",
                    label = "Grass",
                    defaultLayer = 0,
                    collidable = false,
                    fileNames = listOf("karaxas_grass_tile_32.png", "grass_tile.png"),
                ),
                TileSpec(
                    key = "wall_block",
                    label = "Wall",
                    defaultLayer = 1,
                    collidable = true,
                    fileNames = listOf("karaxas_wall_block_32.png", "wall_block.png"),
                ),
                TileSpec(
                    key = "tree_oak",
                    label = "Tree",
                    defaultLayer = 1,
                    collidable = true,
                    fileNames = listOf("karaxas_tree_oak_32.png", "tree_oak.png"),
                ),
                TileSpec(
                    key = "cloud_soft",
                    label = "Cloud",
                    defaultLayer = 2,
                    collidable = false,
                    fileNames = listOf("karaxas_cloud_soft_32.png", "cloud_soft.png"),
                ),
            )

            val roots = mutableListOf<Path>()
            fun appendTileRoots(base: Path) {
                roots.add(base)
                roots.add(base.resolve("assets").resolve("tiles"))
                roots.add(base.resolve("game").resolve("assets").resolve("tiles"))
            }

            System.getenv("GOK_LEVEL_ART_DIR")
                ?.takeIf { it.isNotBlank() }
                ?.let { appendTileRoots(Paths.get(it).toAbsolutePath().normalize()) }
            appendTileRoots(payloadRoot().toAbsolutePath().normalize())
            appendTileRoots(installRoot().toAbsolutePath().normalize())
            var cwdProbe: Path? = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize()
            repeat(5) {
                cwdProbe?.let {
                    appendTileRoots(it)
                    cwdProbe = it.parent
                }
            }

            val normalizedRoots = roots.distinct()
            fun findTileImage(fileNames: List<String>): BufferedImage? {
                for (root in normalizedRoots) {
                    if (!Files.exists(root)) continue
                    for (fileName in fileNames) {
                        val candidate = root.resolve(fileName)
                        if (!Files.isRegularFile(candidate)) continue
                        val image = try {
                            ImageIO.read(candidate.toFile())
                        } catch (_: Exception) {
                            null
                        }
                        if (image != null) {
                            return image
                        }
                    }
                }
                return null
            }

            val assets = linkedMapOf<String, LevelTileAsset>()
            specs.forEach { spec ->
                assets[spec.key] = LevelTileAsset(
                    key = spec.key,
                    label = spec.label,
                    defaultLayer = spec.defaultLayer,
                    collidable = spec.collidable,
                    image = findTileImage(spec.fileNames),
                )
            }
            val loaded = assets.values.filter { it.image != null }.joinToString(", ") { it.key }
            if (loaded.isBlank()) {
                log("Level tile discovery found no themed tile art. Falling back to painted tiles.")
            } else {
                log("Level tile discovery loaded: $loaded")
            }
            return assets
        }

        val levelTileAssets = loadLevelTileAssets()
        val levelTileImageCache = mutableMapOf<Pair<String, Int>, BufferedImage>()
        val collidableTileKeys = levelTileAssets.values.filter { it.collidable }.map { it.key }.toSet()
        val defaultLayerForTile = levelTileAssets.values.associate { it.key to it.defaultLayer }
        val reservedLayerIds = listOf(0, 1, 2)
        fun resolveLevelTileAsset(assetKey: String?): LevelTileAsset? {
            val normalized = assetKey?.trim()?.lowercase().orEmpty()
            return levelTileAssets[normalized]
        }
        fun resolveLevelTileImage(assetKey: String, drawSize: Int): BufferedImage? {
            val cacheKey = assetKey to drawSize
            levelTileImageCache[cacheKey]?.let { return it }
            val source = resolveLevelTileAsset(assetKey)?.image ?: return null
            val scaled = scaleImage(source, drawSize, drawSize)
            levelTileImageCache[cacheKey] = scaled
            return scaled
        }

        val selectAppearancePreview = JLabel("No preview", SwingConstants.CENTER).apply {
            preferredSize = Dimension(180, 190)
            minimumSize = Dimension(180, 190)
            isOpaque = true
            background = Color(31, 24, 20)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            foreground = THEME_TEXT_COLOR
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 14)
        }
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

        fun normalizePreviewSprite(source: BufferedImage): BufferedImage {
            val canvasSize = 32
            val canvas = BufferedImage(canvasSize, canvasSize, BufferedImage.TYPE_INT_ARGB)
            val graphics = canvas.createGraphics()
            try {
                graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR)
                val scale = kotlin.math.min(
                    canvasSize.toDouble() / source.width.coerceAtLeast(1),
                    canvasSize.toDouble() / source.height.coerceAtLeast(1)
                )
                val drawW = (source.width * scale).toInt().coerceAtLeast(1)
                val drawH = (source.height * scale).toInt().coerceAtLeast(1)
                val drawX = ((canvasSize - drawW) / 2).coerceAtLeast(0)
                val drawY = ((canvasSize - drawH) / 2).coerceAtLeast(0)
                graphics.drawImage(source, drawX, drawY, drawW, drawH, null)
            } finally {
                graphics.dispose()
            }
            return canvas
        }

        fun applyCreateAppearancePreview() {
            val option = resolveAppearanceOption(createAppearanceKey)
            val image = option?.let { renderArtFrame(it, "Idle", 0, 0) }
            if (image == null) {
                createAppearancePreview.icon = null
                createAppearancePreview.text = if (appearanceOptions.isEmpty()) "No art loaded" else "Preview unavailable"
                if (appearanceOptions.isNotEmpty()) {
                    val keys = appearanceOptions.joinToString(",") { it.key }
                    log("Create preview missing for key '$createAppearanceKey'. Loaded keys=$keys")
                }
                return
            }
            val normalized = normalizePreviewSprite(image)
            val scaled = scaleImage(
                normalized,
                createAppearancePreview.preferredSize.width.coerceAtLeast(180),
                createAppearancePreview.preferredSize.height.coerceAtLeast(220)
            )
            createAppearancePreview.icon = ImageIcon(scaled)
            createAppearancePreview.text = ""
        }

        fun applySelectionPreview(character: CharacterView?) {
            if (character == null) {
                selectAppearancePreview.icon = null
                selectAppearancePreview.text = "No preview"
                return
            }
            val option = resolveAppearanceOption(character.appearanceKey)
            val image = if (option != null) renderArtFrame(option, "Idle", 0, 0) else null
            if (image == null) {
                selectAppearancePreview.icon = null
                selectAppearancePreview.text = "No art loaded"
                return
            }
            val normalized = normalizePreviewSprite(image)
            val scaled = scaleImage(normalized, selectAppearancePreview.width.coerceAtLeast(140), selectAppearancePreview.height.coerceAtLeast(160))
            selectAppearancePreview.icon = ImageIcon(scaled)
            selectAppearancePreview.text = ""
        }

        var levelEditorCols = 100_000
        var levelEditorRows = 100_000
        val levelEditorCell = 20
        var levelEditorSpawn = 1 to 1
        val levelEditorLayerCells = mutableMapOf<Int, MutableMap<Pair<Int, Int>, String>>()
        reservedLayerIds.forEach { layerId ->
            levelEditorLayerCells[layerId] = mutableMapOf()
        }
        val levelEditorLayerVisibility = mutableMapOf<Int, Boolean>().apply {
            reservedLayerIds.forEach { put(it, true) }
        }
        var levelEditorTool = "paint"
        var levelEditorBrushKey = "wall_block"
        var levelEditorActiveLayer = defaultLayerForTile[levelEditorBrushKey] ?: 1
        var levelEditorViewX = 0
        var levelEditorViewY = 0
        val levelEditorName = UiScaffold.ghostTextField("Level Name")
        val levelGridWidthField = UiScaffold.ghostTextField("Grid Width").apply {
            text = levelEditorCols.toString()
            horizontalAlignment = JTextField.CENTER
            preferredSize = Dimension(90, UiScaffold.fieldSize.height)
            minimumSize = preferredSize
            maximumSize = preferredSize
        }
        val levelGridHeightField = UiScaffold.ghostTextField("Grid Height").apply {
            text = levelEditorRows.toString()
            horizontalAlignment = JTextField.CENTER
            preferredSize = Dimension(90, UiScaffold.fieldSize.height)
            minimumSize = preferredSize
            maximumSize = preferredSize
        }
        val levelViewXField = UiScaffold.ghostTextField("View X").apply {
            text = levelEditorViewX.toString()
            horizontalAlignment = JTextField.CENTER
            preferredSize = Dimension(90, UiScaffold.fieldSize.height)
            minimumSize = preferredSize
            maximumSize = preferredSize
        }
        val levelViewYField = UiScaffold.ghostTextField("View Y").apply {
            text = levelEditorViewY.toString()
            horizontalAlignment = JTextField.CENTER
            preferredSize = Dimension(90, UiScaffold.fieldSize.height)
            minimumSize = preferredSize
            maximumSize = preferredSize
        }
        val levelLoadCombo = ThemedComboBox<Any>().apply {
            preferredSize = Dimension(170, 32)
            minimumSize = preferredSize
            maximumSize = preferredSize
            font = UiScaffold.bodyFont
        }
        val levelToolResizeButton = buildMenuButton("Resize", rectangularButtonImage, Dimension(88, 30), 12f)
        val levelToolViewButton = buildMenuButton("Pan", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolSpawnButton = buildMenuButton("Spawn", rectangularButtonImage, Dimension(78, 30), 12f)
        val levelToolGrassButton = buildMenuButton("Grass", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolWallButton = buildMenuButton("Wall", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolTreeButton = buildMenuButton("Tree", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolCloudButton = buildMenuButton("Cloud", rectangularButtonImage, Dimension(78, 30), 12f)
        val levelToolLoadButton = buildMenuButton("Load", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolSaveButton = buildMenuButton("Save", rectangularButtonImage, Dimension(72, 30), 12f)
        val levelToolClearButton = buildMenuButton("Clear Layer", rectangularButtonImage, Dimension(110, 30), 12f)
        val levelToolBackButton = buildMenuButton("Back", rectangularButtonImage, Dimension(86, 30), 12f)
        val levelActiveLayerCombo = ThemedComboBox<Any>().apply {
            preferredSize = Dimension(120, 32)
            minimumSize = preferredSize
            maximumSize = preferredSize
            font = UiScaffold.bodyFont
            model = javax.swing.DefaultComboBoxModel(arrayOf("Layer 0", "Layer 1", "Layer 2"))
            selectedIndex = levelEditorActiveLayer
        }
        val levelShowLayer0 = JCheckBox("L0", true).apply {
            isOpaque = false
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 13)
            toolTipText = "Show/hide layer 0 (ground/foliage)."
        }
        val levelShowLayer1 = JCheckBox("L1", true).apply {
            isOpaque = false
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 13)
            toolTipText = "Show/hide layer 1 (gameplay entities/obstacles)."
        }
        val levelShowLayer2 = JCheckBox("L2", true).apply {
            isOpaque = false
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 13)
            toolTipText = "Show/hide layer 2 (ambient/weather overlays)."
        }
        var levelGridViewportPanel: JPanel? = null
        lateinit var levelEditorCanvas: JPanel

        fun setLevelToolMode(mode: String, brushKey: String? = null) {
            levelEditorTool = mode
            if (brushKey != null) {
                levelEditorBrushKey = brushKey
                val defaultLayer = defaultLayerForTile[brushKey] ?: levelEditorActiveLayer
                levelEditorActiveLayer = defaultLayer.coerceIn(0, 2)
                levelActiveLayerCombo.selectedIndex = levelEditorActiveLayer
            }
            val spawnActive = mode == "spawn"
            levelToolSpawnButton.putClientProperty("gokActiveTab", spawnActive)
            levelToolGrassButton.putClientProperty("gokActiveTab", !spawnActive && levelEditorBrushKey == "grass_tile")
            levelToolWallButton.putClientProperty("gokActiveTab", !spawnActive && levelEditorBrushKey == "wall_block")
            levelToolTreeButton.putClientProperty("gokActiveTab", !spawnActive && levelEditorBrushKey == "tree_oak")
            levelToolCloudButton.putClientProperty("gokActiveTab", !spawnActive && levelEditorBrushKey == "cloud_soft")
            levelToolSpawnButton.repaint()
            levelToolGrassButton.repaint()
            levelToolWallButton.repaint()
            levelToolTreeButton.repaint()
            levelToolCloudButton.repaint()
        }

        fun levelLayerCells(layerId: Int): MutableMap<Pair<Int, Int>, String> {
            return levelEditorLayerCells.getOrPut(layerId) { mutableMapOf() }
        }

        fun removeCollidableCellAtSpawn(spawnCell: Pair<Int, Int>) {
            for ((_, layerCells) in levelEditorLayerCells) {
                val key = layerCells[spawnCell] ?: continue
                if (collidableTileKeys.contains(key)) {
                    layerCells.remove(spawnCell)
                }
            }
        }

        fun drawEditorTileCell(g2: Graphics2D, drawX: Int, drawY: Int, drawSize: Int, layerId: Int, assetKey: String) {
            val image = resolveLevelTileImage(assetKey, drawSize)
            if (image != null) {
                g2.drawImage(image, drawX, drawY, null)
                return
            }
            val fallback = when (assetKey) {
                "grass_tile" -> Color(72, 104, 63)
                "tree_oak" -> Color(46, 92, 54)
                "cloud_soft" -> Color(176, 178, 181, 200)
                else -> Color(104, 77, 53)
            }
            g2.color = fallback
            g2.fillRect(drawX, drawY, drawSize, drawSize)
            g2.color = when (layerId) {
                0 -> Color(89, 124, 70)
                1 -> Color(172, 132, 87)
                else -> Color(194, 194, 194)
            }
            g2.drawRect(drawX, drawY, drawSize, drawSize)
        }

        fun visibleLevelEditorCols(): Int = (levelEditorCanvas.width / levelEditorCell).coerceAtLeast(1)
        fun visibleLevelEditorRows(): Int = (levelEditorCanvas.height / levelEditorCell).coerceAtLeast(1)
        fun syncLevelGridFields() {
            val width = levelEditorCols.toString()
            val height = levelEditorRows.toString()
            if (levelGridWidthField.text.trim() != width) levelGridWidthField.text = width
            if (levelGridHeightField.text.trim() != height) levelGridHeightField.text = height
            val viewX = levelEditorViewX.toString()
            val viewY = levelEditorViewY.toString()
            if (levelViewXField.text.trim() != viewX) levelViewXField.text = viewX
            if (levelViewYField.text.trim() != viewY) levelViewYField.text = viewY
        }
        fun clampLevelEditorView() {
            val maxViewX = (levelEditorCols - visibleLevelEditorCols()).coerceAtLeast(0)
            val maxViewY = (levelEditorRows - visibleLevelEditorRows()).coerceAtLeast(0)
            levelEditorViewX = levelEditorViewX.coerceIn(0, maxViewX)
            levelEditorViewY = levelEditorViewY.coerceIn(0, maxViewY)
            levelGridViewportPanel?.border = themedTitledBorder(
                "Level Grid ${levelEditorCols}x${levelEditorRows} | View ${levelEditorViewX},${levelEditorViewY}"
            )
            syncLevelGridFields()
        }

        levelEditorCanvas = object : JPanel() {
            init {
                isOpaque = true
                background = Color(24, 18, 15)
                border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
                preferredSize = Dimension(1180, 560)
                minimumSize = Dimension(640, 320)
            }

            override fun paintComponent(graphics: Graphics) {
                super.paintComponent(graphics)
                val g2 = graphics.create() as Graphics2D
                try {
                    clampLevelEditorView()
                    val visCols = visibleLevelEditorCols()
                    val visRows = visibleLevelEditorRows()
                    g2.color = Color(39, 31, 25)
                    g2.fillRect(0, 0, width, height)
                    g2.color = Color(66, 54, 44)
                    for (x in 0..visCols) {
                        val px = x * levelEditorCell
                        g2.drawLine(px, 0, px, height)
                    }
                    for (y in 0..visRows) {
                        val py = y * levelEditorCell
                        g2.drawLine(0, py, width, py)
                    }
                    reservedLayerIds.forEach layerLoop@{ layerId ->
                        if (levelEditorLayerVisibility[layerId] != true) {
                            return@layerLoop
                        }
                        levelLayerCells(layerId).forEach cellLoop@{ (cell, assetKey) ->
                            val cellX = cell.first
                            val cellY = cell.second
                            if (cellX !in levelEditorViewX until (levelEditorViewX + visCols)) return@cellLoop
                            if (cellY !in levelEditorViewY until (levelEditorViewY + visRows)) return@cellLoop
                            val drawX = (cellX - levelEditorViewX) * levelEditorCell + 1
                            val drawY = (cellY - levelEditorViewY) * levelEditorCell + 1
                            val drawSize = (levelEditorCell - 2).coerceAtLeast(2)
                            drawEditorTileCell(g2, drawX, drawY, drawSize, layerId, assetKey)
                        }
                    }
                    val (spawnX, spawnY) = levelEditorSpawn
                    val drawSpawnX = spawnX - levelEditorViewX
                    val drawSpawnY = spawnY - levelEditorViewY
                    if (drawSpawnX !in 0 until visCols || drawSpawnY !in 0 until visRows) return
                    val spawnSprite = resolveAppearanceOption(selectedCharacterView?.appearanceKey ?: createAppearanceKey)
                        ?.let { renderArtFrame(it, "Idle", 0, 0) }
                    if (spawnSprite != null) {
                        val spriteSize = (levelEditorCell - 2).coerceAtLeast(2)
                        val sprite = scaleImage(spawnSprite, spriteSize, spriteSize)
                        g2.drawImage(
                            sprite,
                            drawSpawnX * levelEditorCell + 1,
                            drawSpawnY * levelEditorCell + 1,
                            null
                        )
                    } else {
                        val markerSize = (levelEditorCell - 4).coerceAtLeast(2)
                        val offset = ((levelEditorCell - markerSize) / 2).coerceAtLeast(1)
                        g2.color = Color(201, 170, 114)
                        g2.fillOval(
                            drawSpawnX * levelEditorCell + offset,
                            drawSpawnY * levelEditorCell + offset,
                            markerSize,
                            markerSize
                        )
                    }
                } finally {
                    g2.dispose()
                }
            }
        }

        fun resizeLevelEditorCanvas() {
            clampLevelEditorView()
            levelEditorCanvas.repaint()
        }

        fun applyLevelGridSize(cols: Int, rows: Int) {
            levelEditorCols = cols.coerceIn(8, 100_000)
            levelEditorRows = rows.coerceIn(8, 100_000)
            levelEditorSpawn = levelEditorSpawn.first.coerceIn(0, levelEditorCols - 1) to
                levelEditorSpawn.second.coerceIn(0, levelEditorRows - 1)
            levelEditorLayerCells.values.forEach { layerMap ->
                layerMap.keys.removeIf { (x, y) -> x !in 0 until levelEditorCols || y !in 0 until levelEditorRows }
            }
            resizeLevelEditorCanvas()
        }

        fun levelCellAt(mouseX: Int, mouseY: Int): Pair<Int, Int>? {
            if (mouseX < 0 || mouseY < 0) return null
            val localCellX = mouseX / levelEditorCell
            val localCellY = mouseY / levelEditorCell
            val cellX = levelEditorViewX + localCellX
            val cellY = levelEditorViewY + localCellY
            if (cellX !in 0 until levelEditorCols || cellY !in 0 until levelEditorRows) return null
            return cellX to cellY
        }

        fun applyLevelToolPlacement(mouseX: Int, mouseY: Int, erase: Boolean) {
            val cell = levelCellAt(mouseX, mouseY) ?: return
            val layerMap = levelLayerCells(levelEditorActiveLayer)
            if (erase) {
                layerMap.remove(cell)
                levelEditorCanvas.repaint()
                return
            }
            if (levelEditorTool == "spawn") {
                levelEditorSpawn = cell
                removeCollidableCellAtSpawn(cell)
            } else {
                if (cell == levelEditorSpawn && collidableTileKeys.contains(levelEditorBrushKey)) {
                    levelToolStatus.text = "Spawn cell cannot contain collidable tiles."
                    return
                }
                layerMap[cell] = levelEditorBrushKey
            }
            levelEditorCanvas.repaint()
        }

        var levelEditorDragging = false
        var levelEditorPanning = false
        var levelEditorPanStartViewX = 0
        var levelEditorPanStartViewY = 0
        var levelEditorPanStartMouseX = 0
        var levelEditorPanStartMouseY = 0
        levelEditorCanvas.addMouseListener(object : java.awt.event.MouseAdapter() {
            override fun mousePressed(event: java.awt.event.MouseEvent) {
                if (event.button == java.awt.event.MouseEvent.BUTTON2 || event.isAltDown) {
                    levelEditorPanning = true
                    levelEditorPanStartViewX = levelEditorViewX
                    levelEditorPanStartViewY = levelEditorViewY
                    levelEditorPanStartMouseX = event.x
                    levelEditorPanStartMouseY = event.y
                    return
                }
                levelEditorDragging = true
                applyLevelToolPlacement(event.x, event.y, erase = javax.swing.SwingUtilities.isRightMouseButton(event))
            }

            override fun mouseReleased(event: java.awt.event.MouseEvent) {
                levelEditorDragging = false
                levelEditorPanning = false
            }
        })
        levelEditorCanvas.addMouseMotionListener(object : java.awt.event.MouseMotionAdapter() {
            override fun mouseDragged(event: java.awt.event.MouseEvent) {
                if (levelEditorPanning) {
                    val deltaCellsX = (levelEditorPanStartMouseX - event.x) / levelEditorCell
                    val deltaCellsY = (levelEditorPanStartMouseY - event.y) / levelEditorCell
                    levelEditorViewX = levelEditorPanStartViewX + deltaCellsX
                    levelEditorViewY = levelEditorPanStartViewY + deltaCellsY
                    resizeLevelEditorCanvas()
                    return
                }
                if (!levelEditorDragging) return
                applyLevelToolPlacement(event.x, event.y, erase = javax.swing.SwingUtilities.isRightMouseButton(event))
            }
        })
        levelEditorCanvas.addMouseWheelListener { event ->
            val step = if (event.isControlDown) 20 else 6
            if (event.isShiftDown) {
                levelEditorViewX += event.wheelRotation * step
            } else {
                levelEditorViewY += event.wheelRotation * step
            }
            resizeLevelEditorCanvas()
        }
        levelEditorCanvas.addComponentListener(object : ComponentAdapter() {
            override fun componentResized(event: ComponentEvent) {
                resizeLevelEditorCanvas()
            }
        })
        setLevelToolMode("paint", levelEditorBrushKey)
        resizeLevelEditorCanvas()

        val buildPointBudget = runtimeContent.pointBudget.coerceAtLeast(1)
        val maxPerStat = runtimeContent.maxPerStat.coerceAtLeast(0)
        var pointsRemaining = buildPointBudget
        val createPointsRemainingLabel = JLabel("${buildPointBudget}/${buildPointBudget} points left").apply {
            foreground = textColor
            font = Font(THEME_FONT_FAMILY, Font.BOLD, 15)
        }
        val statEntries = runtimeStatEntries
        val statAllocations = linkedMapOf<String, Int>().apply {
            statEntries.forEach { entry -> put(entry.key, 0) }
        }
        val skillEntries = runtimeSkillEntries
        val skillAllocations = linkedMapOf<String, Int>().apply {
            skillEntries.forEach { entry -> put(entry.key, 0) }
        }
        val statValueLabels = mutableMapOf<String, JLabel>()
        val skillToggleButtons = mutableMapOf<String, JToggleButton>()
        val statTooltips = statEntries.associate { entry ->
            entry.key to entry.tooltip.ifBlank { "No tooltip text configured." }
        }
        val statDescriptions = statEntries.associate { entry ->
            entry.key to entry.description.ifBlank { "No description configured." }
        }
        fun formatContentNumber(value: Double): String {
            return if (value % 1.0 == 0.0) value.toInt().toString() else String.format("%.1f", value)
        }
        val skillTooltipTemplates = skillEntries.associate { entry ->
            entry.key to SkillTooltipTemplate(
                fullName = entry.label,
                manaCost = formatContentNumber(entry.manaCost),
                energyCost = formatContentNumber(entry.energyCost),
                lifeCost = formatContentNumber(entry.lifeCost),
                effects = entry.effects.ifBlank { "No effects configured." },
                damage = entry.damageText.ifBlank {
                    "${formatContentNumber(entry.damageBase)} base, INT x${formatContentNumber(entry.intelligenceScale)}"
                },
                cooldown = "${formatContentNumber(entry.cooldownSeconds)}s",
                skillTypeTag = entry.skillType.ifBlank { "Skill" },
                description = entry.description.ifBlank { "No description configured." },
            )
        }

        fun renderSkillTooltip(template: SkillTooltipTemplate): String {
            val title = escapeHtml(template.fullName)
            val mana = escapeHtml(template.manaCost)
            val energy = escapeHtml(template.energyCost)
            val life = escapeHtml(template.lifeCost)
            val effects = escapeHtml(template.effects)
            val damage = escapeHtml(template.damage)
            val cooldown = escapeHtml(template.cooldown)
            val typeTag = escapeHtml(template.skillTypeTag)
            val description = escapeHtml(template.description)
            return (
                "<html><body style='margin:0;padding:0;background:#1f1814;font-family:$THEME_FONT_FAMILY;color:$THEME_TEXT_HEX;'>" +
                    "<div style='width:320px;background:#1f1814;border:1px solid #ac8457;padding:8px;'>" +
                    "<div style='font-size:14px;font-weight:bold;margin-bottom:6px;'>$title</div>" +
                    "<div style='font-size:12px;margin-bottom:6px;'><b>Cost</b>: Mana $mana | Energy $energy | Life $life</div>" +
                    "<div style='font-size:12px;margin-bottom:6px;'><b>Effects</b><br/>$effects</div>" +
                    "<div style='font-size:12px;margin-bottom:6px;'><b>Damage / Cooldown</b><br/>$damage<br/>Cooldown: $cooldown</div>" +
                    "<div style='font-size:12px;margin-bottom:6px;'><b>Type</b>: " +
                    "<span style='border:1px solid #ac8457;padding:1px 6px;background:#2a2019;'>$typeTag</span></div>" +
                    "<div style='font-size:12px;border:1px solid #6b513b;background:#18120f;padding:6px;'>" +
                    "<b>Description</b><br/>$description</div>" +
                    "</div></body></html>"
                )
        }

        fun updatePointUi() {
            createPointsRemainingLabel.text = "${pointsRemaining}/${buildPointBudget} points left"
            statAllocations.forEach { (key, value) -> statValueLabels[key]?.text = value.toString() }
            skillAllocations.forEach { (key, value) -> skillToggleButtons[key]?.isSelected = value > 0 }
        }

        fun adjustStatAllocation(key: String, delta: Int) {
            val current = statAllocations[key] ?: 0
            if (delta > 0 && pointsRemaining <= 0) return
            if (delta < 0 && current <= 0) return
            if (delta > 0 && current >= maxPerStat) return
            statAllocations[key] = current + delta
            pointsRemaining -= delta
            updatePointUi()
        }

        fun statAllocationRow(entry: ContentStatEntryView): JPanel {
            val key = entry.key
            val statButtonSize = Dimension(30, 30)
            val minus = JButton("-").apply {
                preferredSize = statButtonSize
                minimumSize = statButtonSize
                maximumSize = statButtonSize
            }
            applyThemedButtonStyle(minus, 15f, compactPadding = true)
            val plus = JButton("+").apply {
                preferredSize = statButtonSize
                minimumSize = statButtonSize
                maximumSize = statButtonSize
            }
            applyThemedButtonStyle(plus, 15f, compactPadding = true)
            val value = JLabel("0", SwingConstants.CENTER).apply {
                preferredSize = Dimension(36, statButtonSize.height)
                foreground = textColor
                font = Font(THEME_FONT_FAMILY, Font.BOLD, 16)
            }
            statValueLabels[key] = value
            minus.toolTipText = statTooltips[key]
            plus.toolTipText = statTooltips[key]
            minus.addActionListener { adjustStatAllocation(key, -1) }
            plus.addActionListener { adjustStatAllocation(key, 1) }
            val label = UiScaffold.titledLabel(entry.label).apply {
                toolTipText = statTooltips[key]
            }
            return JPanel(BorderLayout(8, 0)).apply {
                isOpaque = true
                background = Color(31, 24, 20)
                border = BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                    BorderFactory.createEmptyBorder(2, 8, 2, 8)
                )
                preferredSize = createStatControlCardSize
                minimumSize = createStatControlCardSize
                maximumSize = createStatControlCardSize
                add(label, BorderLayout.CENTER)
                add(JPanel(GridLayout(1, 3, 4, 0)).apply {
                    isOpaque = false
                    add(minus)
                    add(value)
                    add(plus)
                }, BorderLayout.EAST)
            }
        }

        fun statDescriptionCard(entry: ContentStatEntryView): JPanel {
            val key = entry.key
            val description = UiScaffold.titledLabel(statDescriptions[key] ?: "Placeholder stat effect.").apply {
                horizontalAlignment = SwingConstants.LEFT
                toolTipText = statTooltips[key]
            }
            return JPanel(BorderLayout()).apply {
                isOpaque = true
                background = Color(31, 24, 20)
                border = BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                    BorderFactory.createEmptyBorder(2, 8, 2, 8)
                )
                preferredSize = createStatDescriptionCardSize
                minimumSize = createStatDescriptionCardSize
                maximumSize = createStatDescriptionCardSize
                add(description, BorderLayout.CENTER)
            }
        }

        fun toggleSkillSelection(key: String) {
            val current = skillAllocations[key] ?: 0
            if (current > 0) {
                skillAllocations[key] = 0
                pointsRemaining += 1
                updatePointUi()
                return
            }
            if (pointsRemaining <= 0) {
                updatePointUi()
                return
            }
            skillAllocations[key] = 1
            pointsRemaining -= 1
            updatePointUi()
        }

        fun skillSelectionButton(key: String, title: String): JToggleButton {
            val tooltipTemplate = skillTooltipTemplates[key]
            val button = JToggleButton(title).apply {
                preferredSize = createSkillButtonSize
                minimumSize = createSkillButtonSize
                maximumSize = createSkillButtonSize
                horizontalAlignment = SwingConstants.CENTER
                margin = Insets(0, 4, 0, 4)
                verticalAlignment = SwingConstants.CENTER
                toolTipText = tooltipTemplate?.let { renderSkillTooltip(it) }
            }
            applyThemedToggleStyle(button, 11f)
            ToolTipManager.sharedInstance().registerComponent(button)
            button.addActionListener { toggleSkillSelection(key) }
            skillToggleButtons[key] = button
            return button
        }

        fun disabledSkillPlaceholder(): JToggleButton {
            return JToggleButton(" ").apply {
                isEnabled = false
                preferredSize = createSkillButtonSize
                minimumSize = createSkillButtonSize
                maximumSize = createSkillButtonSize
                margin = Insets(0, 4, 0, 4)
            }.also {
                applyThemedToggleStyle(it, 11f)
            }
        }

        val gameTileSize = 64f
        val gameMovementSpeed = runtimeContent.movementSpeed.coerceAtLeast(1.0)
        var gameWorldWidth = 2400f
        var gameWorldHeight = 1600f
        var gameLevelWidthCells = 40
        var gameLevelHeightCells = 24
        var gameSpawnCellX = 1
        var gameSpawnCellY = 1
        var gameWallCells = emptySet<Pair<Int, Int>>()
        var gameLayerCells = emptyMap<Int, List<LevelLayerCellView>>()
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

        fun setPlayerToSpawn() {
            gamePlayerX = ((gameSpawnCellX.toFloat() + 0.5f) * gameTileSize).coerceIn(spriteHalf, gameWorldWidth - spriteHalf)
            gamePlayerY = ((gameSpawnCellY.toFloat() + 0.5f) * gameTileSize).coerceIn(spriteHalf, gameWorldHeight - spriteHalf)
        }

        fun collidesWithWall(nextX: Float, nextY: Float): Boolean {
            if (gameWallCells.isEmpty()) return false
            val left = (nextX - spriteHalf).coerceAtLeast(0f)
            val right = (nextX + spriteHalf).coerceAtMost(gameWorldWidth - 1f)
            val top = (nextY - spriteHalf).coerceAtLeast(0f)
            val bottom = (nextY + spriteHalf).coerceAtMost(gameWorldHeight - 1f)
            val minX = kotlin.math.floor(left / gameTileSize).toInt()
            val maxX = kotlin.math.floor(right / gameTileSize).toInt()
            val minY = kotlin.math.floor(top / gameTileSize).toInt()
            val maxY = kotlin.math.floor(bottom / gameTileSize).toInt()
            for (cellY in minY..maxY) {
                for (cellX in minX..maxX) {
                    if (gameWallCells.contains(cellX to cellY)) {
                        return true
                    }
                }
            }
            return false
        }

        fun resetPlayerPosition(savedX: Int?, savedY: Int?) {
            if (savedX != null && savedY != null) {
                gamePlayerX = savedX.toFloat().coerceIn(spriteHalf, gameWorldWidth - spriteHalf)
                gamePlayerY = savedY.toFloat().coerceIn(spriteHalf, gameWorldHeight - spriteHalf)
                if (collidesWithWall(gamePlayerX, gamePlayerY)) {
                    setPlayerToSpawn()
                }
            } else {
                setPlayerToSpawn()
            }
            gameDirection = 0
            gameAnimationFrame = 0
            gameAnimationCarryMs = 0.0
        }

        fun clampPlayerToWorld() {
            gamePlayerX = gamePlayerX.coerceIn(spriteHalf, gameWorldWidth - spriteHalf)
            gamePlayerY = gamePlayerY.coerceIn(spriteHalf, gameWorldHeight - spriteHalf)
        }

        val gameWorldPanel = object : JPanel() {
            init {
                isOpaque = true
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
                    g2.color = Color(63, 78, 65)
                    g2.fillRect(worldScreenX, worldScreenY, worldW, worldH)

                    g2.color = Color(74, 90, 76)
                    val grid = gameTileSize.toInt().coerceAtLeast(16)
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
                    fun drawLayerTile(layerId: Int, cell: LevelLayerCellView) {
                        val drawX = worldScreenX + (cell.x * grid)
                        val drawY = worldScreenY + (cell.y * grid)
                        if (drawX + grid < 0 || drawY + grid < 0 || drawX > width || drawY > height) {
                            return
                        }
                        val image = resolveLevelTileImage(cell.assetKey, grid)
                        val previousComposite = g2.composite
                        if (layerId == 2) {
                            g2.composite = AlphaComposite.getInstance(AlphaComposite.SRC_OVER, 0.78f)
                        }
                        if (image != null) {
                            g2.drawImage(image, drawX, drawY, null)
                        } else {
                            g2.color = when (cell.assetKey) {
                                "grass_tile" -> Color(73, 105, 63)
                                "tree_oak" -> Color(44, 92, 53)
                                "cloud_soft" -> Color(178, 182, 187)
                                else -> Color(52, 40, 31)
                            }
                            g2.fillRect(drawX, drawY, grid, grid)
                        }
                        g2.composite = previousComposite
                        if (layerId == 1 && collidableTileKeys.contains(cell.assetKey)) {
                            g2.color = Color(173, 130, 86)
                            g2.drawRect(drawX, drawY, grid, grid)
                        }
                    }

                    gameLayerCells[0].orEmpty().forEach { drawLayerTile(0, it) }
                    gameLayerCells[1].orEmpty().forEach { drawLayerTile(1, it) }

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
                    g2.font = Font(THEME_FONT_FAMILY, Font.BOLD, 15)
                    g2.drawString(gameCharacterName, playerDrawX - 4, playerDrawY - 8)
                    gameLayerCells[2].orEmpty().forEach { drawLayerTile(2, it) }
                    g2.font = Font(THEME_FONT_FAMILY, Font.PLAIN, 14)
                    g2.drawString("WASD to move. Level: $activeGameLevelName", 12, 22)
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
                val speed = gameMovementSpeed
                val nx = dx / length
                val ny = dy / length
                val nextX = (gamePlayerX + (nx * speed * dt).toFloat()).coerceIn(spriteHalf, gameWorldWidth - spriteHalf)
                val nextY = (gamePlayerY + (ny * speed * dt).toFloat()).coerceIn(spriteHalf, gameWorldHeight - spriteHalf)
                if (!collidesWithWall(nextX, gamePlayerY)) {
                    gamePlayerX = nextX
                }
                if (!collidesWithWall(gamePlayerX, nextY)) {
                    gamePlayerY = nextY
                }
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

        fun applyGameLevel(level: LevelDataView?) {
            if (level == null) {
                activeGameLevelId = null
                activeGameLevelName = "Default"
                gameLevelWidthCells = 40
                gameLevelHeightCells = 24
                gameSpawnCellX = 1
                gameSpawnCellY = 1
                gameWorldWidth = gameLevelWidthCells * gameTileSize
                gameWorldHeight = gameLevelHeightCells * gameTileSize
                gameWallCells = emptySet()
                gameLayerCells = emptyMap()
                return
            }
            activeGameLevelId = level.id
            activeGameLevelName = level.name
            gameLevelWidthCells = level.width.coerceAtLeast(8)
            gameLevelHeightCells = level.height.coerceAtLeast(8)
            gameSpawnCellX = level.spawnX.coerceIn(0, gameLevelWidthCells - 1)
            gameSpawnCellY = level.spawnY.coerceIn(0, gameLevelHeightCells - 1)
            gameWorldWidth = gameLevelWidthCells * gameTileSize
            gameWorldHeight = gameLevelHeightCells * gameTileSize
            val rawLayers = if (level.layers.isNotEmpty()) {
                level.layers
            } else {
                mapOf(
                    1 to level.wallCells.map { wall ->
                        LevelLayerCellView(layer = 1, x = wall.x, y = wall.y, assetKey = "wall_block")
                    }
                )
            }
            val normalizedLayers = linkedMapOf<Int, MutableList<LevelLayerCellView>>()
            rawLayers.keys.sorted().forEach { layerId ->
                val cells = rawLayers[layerId].orEmpty()
                val normalized = cells.mapNotNull { cell ->
                    val cellX = cell.x.coerceIn(0, gameLevelWidthCells - 1)
                    val cellY = cell.y.coerceIn(0, gameLevelHeightCells - 1)
                    val key = cell.assetKey.trim().lowercase().ifBlank { "decor" }
                    if (cellX == gameSpawnCellX && cellY == gameSpawnCellY && collidableTileKeys.contains(key)) {
                        null
                    } else {
                        LevelLayerCellView(layer = layerId, x = cellX, y = cellY, assetKey = key)
                    }
                }
                normalizedLayers[layerId] = normalized.toMutableList()
            }
            gameLayerCells = normalizedLayers
            gameWallCells = normalizedLayers[1]
                .orEmpty()
                .filter { collidableTileKeys.contains(it.assetKey) }
                .map { it.x to it.y }
                .toSet()
        }

        fun enterGameWithCharacter(character: CharacterView, level: LevelDataView?, forceSpawn: Boolean = false) {
            activeGameCharacterView = character
            gameCharacterName = character.name
            gameCharacterAppearance = resolveAppearanceOption(character.appearanceKey)
            applyGameLevel(level)
            resetPlayerPosition(
                if (forceSpawn) null else character.locationX,
                if (forceSpawn) null else character.locationY
            )
            clampPlayerToWorld()
            gameStatus.text = " "
            val levelName = level?.name ?: "Default"
            playStatus.text = if (!forceSpawn && character.locationX != null && character.locationY != null) {
                "Loaded $levelName at (${character.locationX}, ${character.locationY})."
            } else {
                "Loaded $levelName at spawn."
            }
            gameWorldPanel.requestFocusInWindow()
        }

        fun persistCurrentCharacterLocation() {
            val session = authSession ?: return
            val character = activeGameCharacterView ?: selectedCharacterView ?: return
            val locationX = kotlin.math.round(gamePlayerX).toInt().coerceAtLeast(0)
            val locationY = kotlin.math.round(gamePlayerY).toInt().coerceAtLeast(0)
            val levelId = activeGameLevelId ?: character.levelId
            Thread {
                try {
                    backendClient.updateCharacterLocation(
                        accessToken = session.accessToken,
                        clientVersion = clientVersion,
                        characterId = character.id,
                        levelId = levelId,
                        locationX = locationX,
                        locationY = locationY,
                    )
                } catch (ex: Exception) {
                    log("Character location save failed against ${backendClient.endpoint()}", ex)
                }
            }.start()

            selectedCharacterView = character.copy(
                levelId = levelId,
                locationX = locationX,
                locationY = locationY,
            )
            activeGameCharacterView = selectedCharacterView
            loadedCharacters = loadedCharacters.map { existing ->
                if (existing.id == character.id) {
                    existing.copy(
                        levelId = levelId,
                        locationX = locationX,
                        locationY = locationY,
                    )
                } else {
                    existing
                }
            }
        }

        fun withSession(onMissing: () -> Unit = {}, block: (AuthSession) -> Unit) {
            val session = authSession
            if (session == null) {
                onMissing()
                return
            }
            block(session)
        }

        fun isAdminAccount(): Boolean {
            return authSession?.isAdmin == true
        }

        fun formatServiceError(ex: Exception, fallback: String): String {
            val chain = generateSequence<Throwable>(ex) { it.cause }
            if (chain.any { it is UnknownHostException }) return "No internet connection. Check your network."
            if (chain.any { it is ConnectException }) return "Servers are currently unavailable. Please try again."
            if (chain.any { it is HttpTimeoutException || it is SocketTimeoutException }) return "Connection timed out. Please try again."
            if (chain.any { it is SSLException }) return "Secure connection failed. Please try again."
            val message = ex.message?.trim().orEmpty()
            val code = Regex("^(\\d{3}):").find(message)?.groupValues?.getOrNull(1)?.toIntOrNull()
            if (code == 401 || code == 403 || message.contains("invalid token", ignoreCase = true)) {
                return "Session expired or invalid token. Please log in again."
            }
            if (message.contains(":")) {
                val detail = message.substringAfter(":").trim()
                if (detail.isNotBlank()) return detail
            }
            return if (message.isNotBlank()) message else fallback
        }

        lateinit var showCard: (String) -> Unit
        lateinit var populateCharacterViewsFn: (List<CharacterView>) -> Unit

        fun playWithCharacter(character: CharacterView, overrideLevelId: Int? = null) {
            if (!hasValidContentSnapshot) {
                selectStatus.text = contentText(
                    "ui.content.blocked_play",
                    "Content unavailable. Reconnect to sync gameplay data.",
                )
                return
            }
            withSession(onMissing = { authStatus.text = "Please login first." }) { session ->
                Thread {
                    try {
                        backendClient.selectCharacter(session.accessToken, clientVersion, character.id)
                        val requestedLevelId = overrideLevelId ?: character.levelId
                        val selectedLevel = requestedLevelId?.let { levelId ->
                            levelDetailsById[levelId] ?: backendClient.getLevel(session.accessToken, clientVersion, levelId).also {
                                levelDetailsById[levelId] = it
                            }
                        }
                        val gameplayCharacter = if (overrideLevelId != null) {
                            character.copy(levelId = overrideLevelId, locationX = null, locationY = null)
                        } else {
                            character
                        }
                        javax.swing.SwingUtilities.invokeLater {
                            if (selectedLevel != null) {
                                activeGameLevelId = selectedLevel.id
                            }
                            enterGameWithCharacter(gameplayCharacter, selectedLevel, forceSpawn = overrideLevelId != null)
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
            fun characterLocationLabel(character: CharacterView): String {
                val area = character.levelId?.let { levelId ->
                    availableLevels.firstOrNull { it.id == levelId }?.name
                    ?: levelDetailsById[levelId]?.name
                    ?: "Level #$levelId"
                } ?: "Default"
                val x = character.locationX
                val y = character.locationY
                return if (x != null && y != null) "$area ($x, $y)" else area
            }

            characterRowsPanel.removeAll()
            if (characters.isEmpty()) {
                characterRowsPanel.add(JLabel("No characters yet. Create your first character.").apply {
                    foreground = textColor
                    font = UiScaffold.bodyFont
                    border = BorderFactory.createEmptyBorder(12, 6, 12, 6)
                })
            } else {
                val adminMode = isAdminAccount()
                characters.forEach { character ->
                    val playButton = buildMenuButton("Play", rectangularButtonImage, Dimension(95, 30), 12f)
                    val deleteButton = buildMenuButton("Delete", rectangularButtonImage, Dimension(95, 30), 12f)
                    val row = object : JPanel(BorderLayout(8, 0)) {
                        override fun getPreferredSize(): Dimension = Dimension(0, if (adminMode) 86 else 72)
                        override fun getMinimumSize(): Dimension = Dimension(0, if (adminMode) 86 else 72)
                        override fun getMaximumSize(): Dimension = Dimension(Int.MAX_VALUE, if (adminMode) 86 else 72)
                    }.apply {
                        isOpaque = true
                        background = if (selectedCharacterId == character.id) Color(57, 42, 31) else Color(39, 29, 24)
                        border = BorderFactory.createCompoundBorder(
                            BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                            BorderFactory.createEmptyBorder(8, 10, 8, 10)
                        )
                    }
                    val locationLabel = characterLocationLabel(character)
                    val info = JLabel("${character.name}  |  Level ${character.level}  |  XP ${character.experience} (next ${character.experienceToNextLevel})  |  Location: $locationLabel").apply {
                        foreground = textColor
                        font = Font(THEME_FONT_FAMILY, Font.BOLD, 14)
                    }
                    var playLevelOverrideCombo: ThemedComboBox<Any>? = null
                    val actions = if (adminMode) {
                        val levelCombo = ThemedComboBox<Any>().apply {
                            preferredSize = Dimension(170, 30)
                            minimumSize = Dimension(170, 30)
                            maximumSize = Dimension(170, 30)
                            font = UiScaffold.bodyFont
                            val values = mutableListOf<Any>("Current Location")
                            values.addAll(availableLevels)
                            model = javax.swing.DefaultComboBoxModel(values.toTypedArray())
                            selectedItem = "Current Location"
                            isEnabled = values.size > 1
                            toolTipText = "Admin override: choose a level to force spawn at that level's spawn point."
                        }
                        playLevelOverrideCombo = levelCombo
                        JPanel(BorderLayout(0, 4)).apply {
                            isOpaque = false
                            add(levelCombo, BorderLayout.NORTH)
                            add(JPanel(GridLayout(1, 2, 4, 0)).apply {
                                isOpaque = false
                                add(playButton)
                                add(deleteButton)
                            }, BorderLayout.SOUTH)
                        }
                    } else {
                        JPanel(GridLayout(1, 2, 6, 0)).apply {
                            isOpaque = false
                            add(playButton)
                            add(deleteButton)
                        }
                    }
                    row.add(info, BorderLayout.CENTER)
                    row.add(actions, BorderLayout.EAST)
                    val rowSelectionHandler = object : java.awt.event.MouseAdapter() {
                        override fun mouseClicked(e: java.awt.event.MouseEvent?) {
                            selectedCharacterId = character.id
                            selectedCharacterView = character
                            selectCharacterDetails.text =
                                "Name: ${character.name}\nLevel: ${character.level}\nExperience: ${character.experience}\nAppearance: ${character.appearanceKey}\nRace: ${character.race}\nBackground: ${character.background}\nAffiliation: ${character.affiliation}\nLocation: $locationLabel"
                            applySelectionPreview(character)
                            renderCharacterRows(loadedCharacters)
                        }
                    }
                    row.addMouseListener(rowSelectionHandler)
                    info.addMouseListener(rowSelectionHandler)
                    playButton.addActionListener {
                        val overrideLevelId = (playLevelOverrideCombo?.selectedItem as? LevelSummaryView)?.id
                        playWithCharacter(character, overrideLevelId)
                    }
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
            selectedCharacterId = null
            selectedCharacterView = null
            selectCharacterDetails.text = "Choose a character row to preview."
            applySelectionPreview(null)
            renderCharacterRows(characters)
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

        fun refreshLevels(
            statusLabel: JLabel,
            onLoaded: ((List<LevelSummaryView>) -> Unit)? = null
        ) {
            withSession(onMissing = { statusLabel.text = "Please login first." }) { session ->
                Thread {
                    try {
                        val levels = backendClient.listLevels(session.accessToken, clientVersion)
                        javax.swing.SwingUtilities.invokeLater {
                            availableLevels = levels
                            val ids = levels.map { it.id }.toSet()
                            val stale = levelDetailsById.keys.filter { it !in ids }
                            stale.forEach { levelDetailsById.remove(it) }
                            if (loadedCharacters.isNotEmpty()) {
                                renderCharacterRows(loadedCharacters)
                            }
                            onLoaded?.invoke(levels)
                        }
                    } catch (ex: Exception) {
                        log("Level list refresh failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            statusLabel.text = formatServiceError(ex, "Unable to load level list.")
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
            tabLevelTool.isVisible = isAdminAccount()
            authStatus.text = "Loading account..."
            resetAuthInputsForMode()
            refreshLevels(selectStatus)
            refreshCharacters(selectStatus) { characters ->
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
            authToggleMode.text = if (registerMode) "Back" else "Create Account"
            authStatus.text = " "
            resetAuthInputsForMode()
            authStandaloneContainer.revalidate()
            authStandaloneContainer.repaint()
            centeredContent.revalidate()
            centeredContent.repaint()
        }

        val authInnerPanel = UiScaffold.contentPanel().apply {
            layout = GridBagLayout()
            add(authDisplayName, UiScaffold.gbc(0).apply { anchor = GridBagConstraints.CENTER })
            add(authEmail, UiScaffold.gbc(1).apply { anchor = GridBagConstraints.CENTER })
            add(authPassword, UiScaffold.gbc(2).apply { anchor = GridBagConstraints.CENTER })
            add(JPanel(GridLayout(1, 2, 8, 0)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                add(authSubmit)
                add(authToggleMode)
            }, UiScaffold.gbc(3).apply { anchor = GridBagConstraints.CENTER })
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
                font = Font(THEME_FONT_FAMILY, Font.PLAIN, 12)
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
                selectStatus.text = " "
            }
        }
        settingsItem.addActionListener { openSettingsDialog() }
        updateSettingsMenuAccess()

        val accountTabButtons = linkedMapOf(
            "select_character" to tabSelect,
            "create_character" to tabCreate,
            "level_tool" to tabLevelTool
        )
        fun setActiveAccountTab(card: String) {
            accountTabButtons.forEach { (name, button) ->
                val isActive = name == card
                if (!button.isVisible) return@forEach
                button.putClientProperty("gokActiveTab", isActive)
                button.isEnabled = true
                button.foreground = textColor
            }
        }
        val accountTabsPanel = JPanel(java.awt.FlowLayout(java.awt.FlowLayout.RIGHT, 8, 0)).apply {
            isOpaque = true
            background = panelBg
            add(tabSelect)
            add(tabCreate)
            add(tabLevelTool)
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
                font = Font(THEME_FONT_FAMILY, Font.BOLD, 18)
            }, BorderLayout.WEST)
            add(accountTabsPanel, BorderLayout.EAST)
            isVisible = false
        }
        shellPanel.add(accountTopBar, BorderLayout.NORTH)

        val createCharacterPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(12, 8)
            add(UiScaffold.sectionLabel("Create Character"), BorderLayout.NORTH)
            add(JPanel(BorderLayout(12, 8)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                add(JPanel(BorderLayout()).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
                    add(createAppearancePreview, BorderLayout.CENTER)
                }, BorderLayout.WEST)
                add(JPanel(BorderLayout(0, 10)).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    add(JPanel(GridLayout(1, 5, 10, 0)).apply {
                        isOpaque = false
                        add(JPanel(GridBagLayout()).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Name"), UiScaffold.gbc(0))
                            add(createName, UiScaffold.gbc(1))
                        })
                        add(JPanel(GridBagLayout()).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Sex"), UiScaffold.gbc(0))
                            add(sexChoice, UiScaffold.gbc(1))
                        })
                        add(JPanel(GridBagLayout()).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Race"), UiScaffold.gbc(0))
                            add(raceChoice, UiScaffold.gbc(1))
                        })
                        add(JPanel(GridBagLayout()).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Background"), UiScaffold.gbc(0))
                            add(backgroundChoice, UiScaffold.gbc(1))
                        })
                        add(JPanel(GridBagLayout()).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Affiliation"), UiScaffold.gbc(0))
                            add(affiliationChoice, UiScaffold.gbc(1))
                        })
                    }, BorderLayout.NORTH)
                    add(JPanel(GridLayout(1, 2, 10, 0)).apply {
                        isOpaque = false
                        add(JPanel(BorderLayout(0, 8)).apply {
                            isOpaque = true
                            background = Color(24, 18, 15)
                            border = themedTitledBorder("Stats")
                            preferredSize = createStatsPanelSize
                            minimumSize = createStatsPanelSize
                            maximumSize = createStatsPanelSize
                            add(JPanel().apply {
                                layout = javax.swing.BoxLayout(this, javax.swing.BoxLayout.Y_AXIS)
                                isOpaque = false
                                statEntries.forEachIndexed { index, entry ->
                                    add(JPanel(BorderLayout(8, 0)).apply {
                                        isOpaque = false
                                        add(statAllocationRow(entry), BorderLayout.WEST)
                                        add(statDescriptionCard(entry), BorderLayout.CENTER)
                                    })
                                    if (index < statEntries.lastIndex) {
                                        add(Box.createVerticalStrut(4))
                                    }
                                }
                            }, BorderLayout.CENTER)
                        })
                        add(JPanel(BorderLayout(0, 8)).apply {
                            isOpaque = true
                            background = Color(24, 18, 15)
                            border = themedTitledBorder("Skills")
                            preferredSize = createSkillsPanelSize
                            minimumSize = createSkillsPanelSize
                            maximumSize = createSkillsPanelSize
                            add(JPanel(BorderLayout()).apply {
                                isOpaque = false
                                add(JPanel().apply {
                                    layout = javax.swing.BoxLayout(this, javax.swing.BoxLayout.Y_AXIS)
                                    isOpaque = false
                                    val visibleSkills = skillEntries.take(12)
                                    val rows = if (visibleSkills.isEmpty()) {
                                        listOf(emptyList(), emptyList())
                                    } else {
                                        val chunked = visibleSkills.chunked(6).toMutableList()
                                        while (chunked.size < 2) {
                                            chunked.add(emptyList())
                                        }
                                        chunked.take(2)
                                    }
                                    rows.forEachIndexed { rowIndex, rowSkills ->
                                        add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                                            isOpaque = false
                                            rowSkills.forEach { entry ->
                                                add(skillSelectionButton(entry.key, entry.label))
                                            }
                                            repeat((6 - rowSkills.size).coerceAtLeast(0)) {
                                                add(disabledSkillPlaceholder())
                                            }
                                        })
                                        if (rowIndex == 0) {
                                            add(Box.createVerticalStrut(6))
                                        }
                                    }
                                }, BorderLayout.NORTH)
                            }, BorderLayout.CENTER)
                        })
                    }, BorderLayout.CENTER)
                    add(JPanel(BorderLayout(8, 0)).apply {
                        isOpaque = false
                        add(createStatus, BorderLayout.CENTER)
                        add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.RIGHT, 8, 0)).apply {
                            isOpaque = false
                            add(createPointsRemainingLabel)
                            add(createSubmit)
                        }, BorderLayout.EAST)
                    }, BorderLayout.SOUTH)
                }, BorderLayout.CENTER)
            }, BorderLayout.CENTER)
        }

        val selectCharacterPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(10, 8)
            add(characterRowsScroll, BorderLayout.CENTER)
            add(JPanel(BorderLayout(0, 8)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                add(selectAppearancePreview, BorderLayout.NORTH)
                add(ThemedScrollPane(selectCharacterDetails).apply {
                    border = themedTitledBorder("Character details")
                    preferredSize = Dimension(260, 220)
                }, BorderLayout.CENTER)
            }, BorderLayout.EAST)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                add(selectStatus, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }

        fun refreshLevelLoadCombo() {
            val options: Array<Any> = if (availableLevels.isEmpty()) {
                arrayOf("No levels")
            } else {
                availableLevels.toTypedArray()
            }
            levelLoadCombo.model = javax.swing.DefaultComboBoxModel(options)
            levelLoadCombo.isEnabled = availableLevels.isNotEmpty()
        }

        fun loadLevelIntoEditor(level: LevelDataView) {
            applyLevelGridSize(level.width, level.height)
            levelEditorName.text = level.name
            levelEditorSpawn = level.spawnX.coerceIn(0, levelEditorCols - 1) to level.spawnY.coerceIn(0, levelEditorRows - 1)
            levelEditorViewX = (levelEditorSpawn.first - 20).coerceAtLeast(0)
            levelEditorViewY = (levelEditorSpawn.second - 12).coerceAtLeast(0)
            levelEditorLayerCells.values.forEach { it.clear() }
            val sourceLayers = if (level.layers.isNotEmpty()) {
                level.layers
            } else {
                mapOf(
                    1 to level.wallCells.map { wall ->
                        LevelLayerCellView(layer = 1, x = wall.x, y = wall.y, assetKey = "wall_block")
                    }
                )
            }
            sourceLayers.forEach layerLoop@{ (layerId, cells) ->
                val clampedLayer = layerId.coerceIn(0, 2)
                val layerMap = levelLayerCells(clampedLayer)
                cells.forEach cellLoop@{ cell ->
                    val x = cell.x.coerceIn(0, levelEditorCols - 1)
                    val y = cell.y.coerceIn(0, levelEditorRows - 1)
                    val assetKey = cell.assetKey.trim().lowercase().ifBlank { "decor" }
                    if (collidableTileKeys.contains(assetKey) && levelEditorSpawn == (x to y)) {
                        return@cellLoop
                    }
                    layerMap[x to y] = assetKey
                }
            }
            levelEditorActiveLayer = 1
            levelActiveLayerCombo.selectedIndex = levelEditorActiveLayer
            setLevelToolMode("paint", levelEditorBrushKey)
            resizeLevelEditorCanvas()
        }

        val levelToolPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(JPanel(BorderLayout(8, 0)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                border = BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                    BorderFactory.createEmptyBorder(6, 8, 6, 8)
                )
                add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                    isOpaque = false
                    add(UiScaffold.titledLabel("Load Existing"))
                    add(levelLoadCombo)
                    add(levelToolLoadButton)
                    add(UiScaffold.titledLabel("Save Level"))
                    add(levelEditorName.apply {
                        preferredSize = Dimension(150, UiScaffold.fieldSize.height)
                        minimumSize = preferredSize
                        maximumSize = preferredSize
                    })
                    add(levelToolSaveButton)
                    add(levelToolBackButton)
                }, BorderLayout.WEST)
                add(UiScaffold.sectionLabel("Level Builder (Admin)").apply {
                    horizontalAlignment = SwingConstants.RIGHT
                }, BorderLayout.EAST)
            }, BorderLayout.NORTH)
            add(JPanel(BorderLayout(8, 8)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                border = BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(172, 132, 87), 1),
                    BorderFactory.createEmptyBorder(6, 6, 6, 6)
                )
                add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    add(JPanel(GridLayout(3, 1, 0, 4)).apply {
                        isOpaque = false
                        add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Tool"))
                            add(levelToolSpawnButton)
                            add(levelToolGrassButton)
                            add(levelToolWallButton)
                            add(levelToolTreeButton)
                            add(levelToolCloudButton)
                            add(levelToolClearButton)
                        })
                        add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Active Layer"))
                            add(levelActiveLayerCombo)
                            add(UiScaffold.titledLabel("Show"))
                            add(levelShowLayer0)
                            add(levelShowLayer1)
                            add(levelShowLayer2)
                        })
                        add(JPanel(java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 6, 0)).apply {
                            isOpaque = false
                            add(UiScaffold.titledLabel("Grid"))
                            add(levelGridWidthField)
                            add(levelGridHeightField)
                            add(levelToolResizeButton)
                            add(UiScaffold.titledLabel("View"))
                            add(levelViewXField)
                            add(levelViewYField)
                            add(levelToolViewButton)
                        })
                    })
                }, BorderLayout.NORTH)
                val gridViewport = JPanel(BorderLayout()).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    border = themedTitledBorder("Level Grid ${levelEditorCols}x${levelEditorRows} | View ${levelEditorViewX},${levelEditorViewY}")
                    add(levelEditorCanvas, BorderLayout.CENTER)
                }
                levelGridViewportPanel = gridViewport
                add(gridViewport, BorderLayout.CENTER)
                add(JPanel(BorderLayout(6, 0)).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    add(UiScaffold.titledLabel("Drag to paint selected layer/asset. Right-drag erases from active layer. Alt+drag or mouse-wheel pans."), BorderLayout.WEST)
                    add(levelToolStatus, BorderLayout.EAST)
                }, BorderLayout.SOUTH)
            }, BorderLayout.CENTER)
        }

        val playPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(UiScaffold.sectionLabel("Game World"), BorderLayout.NORTH)
            add(gameWorldPanel, BorderLayout.CENTER)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = true
                background = Color(24, 18, 15)
                add(playBackToLobby, BorderLayout.NORTH)
                add(JPanel(GridLayout(2, 1)).apply {
                    isOpaque = true
                    background = Color(24, 18, 15)
                    add(gameStatus)
                    add(playStatus)
                }, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }
        gameSceneContainer.add(playPanel, BorderLayout.CENTER)
        levelSceneContainer.add(levelToolPanel, BorderLayout.CENTER)

        menuCards.add(createCharacterPanel, "create_character")
        menuCards.add(selectCharacterPanel, "select_character")
        menuCards.add(updateContent, "update")
        var lastAccountCard = "select_character"

        var activeLog: Path? = null
        val controls = listOf(checkUpdates, launcherLogButton, gameLogButton, updateLogButton, clearLogsButton, showPatchNotesButton)
        checkUpdates.addActionListener {
            updateStatus.text = "Checking for updates..."
            runUpdate(updateStatus, patchNotesPane, patchNotes, controls)
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
            val requiresAuth = card == "create_character" || card == "select_character" || card == "level_tool" || card == "play"
            if (requiresAuth && authSession == null) {
                showCard("auth")
                authStatus.text = " "
                return
            }
            if (card == "level_tool" && !isAdminAccount()) {
                selectStatus.text = "Admin access required."
                showCard("select_character")
                return
            }
            if (card == "auth") {
                shellPanel.isVisible = false
                gameSceneContainer.isVisible = false
                levelSceneContainer.isVisible = false
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
                levelSceneContainer.isVisible = false
                accountTopBar.isVisible = false
            } else if (card == "level_tool") {
                shellPanel.isVisible = false
                gameSceneContainer.isVisible = false
                levelSceneContainer.isVisible = true
                accountTopBar.isVisible = false
            } else {
                shellPanel.isVisible = true
                gameSceneContainer.isVisible = false
                levelSceneContainer.isVisible = false
            }
            if (card == "select_character" || card == "create_character") {
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
            if (card == "play" && !hasValidContentSnapshot) {
                selectStatus.text = contentText(
                    "ui.content.blocked_play",
                    "Content unavailable. Reconnect to sync gameplay data.",
                )
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
                    val level = active.levelId?.let { levelDetailsById[it] }
                    enterGameWithCharacter(active, level)
                }
                gameWorldPanel.requestFocusInWindow()
            } else if (card == "select_character") {
                refreshCharacters(selectStatus)
                if (isAdminAccount()) {
                    refreshLevels(selectStatus) {
                        refreshLevelLoadCombo()
                    }
                }
            } else if (card == "level_tool") {
                refreshLevels(levelToolStatus) {
                    refreshLevelLoadCombo()
                }
            }
            if (card == "select_character" || card == "create_character" || card == "update") {
                cardsLayout.show(menuCards, card)
                menuCards.revalidate()
                menuCards.repaint()
            }
            centeredContent.revalidate()
            centeredContent.repaint()
        }

        quickUpdateItem.addActionListener {
            showCard("update")
            updateStatus.text = "Checking for updates..."
            runUpdate(updateStatus, patchNotesPane, patchNotes, controls, autoRestartOnSuccess = true)
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

        tabCreate.addActionListener { showCard("create_character") }
        tabSelect.addActionListener { showCard("select_character") }
        tabLevelTool.addActionListener { showCard("level_tool") }
        updateBackButton.addActionListener { showCard(lastAccountCard) }
        playBackToLobby.addActionListener {
            persistCurrentCharacterLocation()
            showCard("select_character")
        }
        fun applyRequestedGridSizeFromInputs(): Boolean {
            val cols = levelGridWidthField.text.trim().toIntOrNull()
            val rows = levelGridHeightField.text.trim().toIntOrNull()
            if (cols == null || rows == null) {
                levelToolStatus.text = "Grid width/height must be numeric values."
                return false
            }
            if (cols !in 8..100000 || rows !in 8..100000) {
                levelToolStatus.text = "Grid size must be between 8 and 100000."
                return false
            }
            applyLevelGridSize(cols, rows)
            levelToolStatus.text = "Grid resized to ${levelEditorCols}x${levelEditorRows}."
            return true
        }
        levelToolResizeButton.addActionListener { applyRequestedGridSizeFromInputs() }
        levelGridWidthField.addActionListener { applyRequestedGridSizeFromInputs() }
        levelGridHeightField.addActionListener { applyRequestedGridSizeFromInputs() }
        fun applyRequestedViewportFromInputs() {
            val requestedX = levelViewXField.text.trim().toIntOrNull()
            val requestedY = levelViewYField.text.trim().toIntOrNull()
            if (requestedX == null || requestedY == null) {
                levelToolStatus.text = "View coordinates must be numeric values."
                return
            }
            levelEditorViewX = requestedX
            levelEditorViewY = requestedY
            resizeLevelEditorCanvas()
            levelToolStatus.text = "Viewport moved to ${levelEditorViewX},${levelEditorViewY}."
        }
        levelToolViewButton.addActionListener { applyRequestedViewportFromInputs() }
        levelViewXField.addActionListener { applyRequestedViewportFromInputs() }
        levelViewYField.addActionListener { applyRequestedViewportFromInputs() }
        levelActiveLayerCombo.addActionListener {
            levelEditorActiveLayer = levelActiveLayerCombo.selectedIndex.coerceIn(0, 2)
            resizeLevelEditorCanvas()
        }
        levelShowLayer0.addActionListener {
            levelEditorLayerVisibility[0] = levelShowLayer0.isSelected
            resizeLevelEditorCanvas()
        }
        levelShowLayer1.addActionListener {
            levelEditorLayerVisibility[1] = levelShowLayer1.isSelected
            resizeLevelEditorCanvas()
        }
        levelShowLayer2.addActionListener {
            levelEditorLayerVisibility[2] = levelShowLayer2.isSelected
            resizeLevelEditorCanvas()
        }
        levelToolBackButton.addActionListener { showCard("select_character") }
        levelToolSpawnButton.addActionListener { setLevelToolMode("spawn") }
        levelToolGrassButton.addActionListener { setLevelToolMode("paint", "grass_tile") }
        levelToolWallButton.addActionListener { setLevelToolMode("paint", "wall_block") }
        levelToolTreeButton.addActionListener { setLevelToolMode("paint", "tree_oak") }
        levelToolCloudButton.addActionListener { setLevelToolMode("paint", "cloud_soft") }
        levelToolClearButton.addActionListener {
            levelLayerCells(levelEditorActiveLayer).clear()
            levelEditorCanvas.repaint()
            levelToolStatus.text = "Cleared layer $levelEditorActiveLayer."
        }
        levelToolLoadButton.addActionListener {
            val selected = levelLoadCombo.selectedItem as? LevelSummaryView
            if (selected == null) {
                levelToolStatus.text = "Select a level to load."
                return@addActionListener
            }
            withSession(onMissing = { levelToolStatus.text = "Please login first." }) { session ->
                levelToolStatus.text = "Loading level..."
                Thread {
                    try {
                        val loadedLevel = backendClient.getLevel(session.accessToken, clientVersion, selected.id)
                        levelDetailsById[selected.id] = loadedLevel
                        javax.swing.SwingUtilities.invokeLater {
                            loadLevelIntoEditor(loadedLevel)
                            levelToolStatus.text = "Loaded level '${loadedLevel.name}'."
                        }
                    } catch (ex: Exception) {
                        log("Level load failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            levelToolStatus.text = formatServiceError(ex, "Unable to load level.")
                        }
                    }
                }.start()
            }
        }
        levelToolSaveButton.addActionListener {
            if (!isAdminAccount()) {
                levelToolStatus.text = "Admin access required."
                return@addActionListener
            }
            if (!applyRequestedGridSizeFromInputs()) {
                return@addActionListener
            }
            val levelName = levelEditorName.text.trim()
            if (levelName.isBlank()) {
                levelToolStatus.text = "Level name is required."
                return@addActionListener
            }
            withSession(onMissing = { levelToolStatus.text = "Please login first." }) { session ->
                levelToolStatus.text = "Saving level..."
                val layers = linkedMapOf<Int, List<LevelLayerCellView>>()
                reservedLayerIds.forEach { layerId ->
                    val cells = levelLayerCells(layerId)
                        .entries
                        .sortedWith(compareBy({ it.key.second }, { it.key.first }, { it.value }))
                        .map { entry ->
                            LevelLayerCellView(
                                layer = layerId,
                                x = entry.key.first,
                                y = entry.key.second,
                                assetKey = entry.value,
                            )
                        }
                    if (cells.isNotEmpty()) {
                        layers[layerId] = cells
                    }
                }
                Thread {
                    try {
                        val saved = backendClient.saveLevel(
                            accessToken = session.accessToken,
                            clientVersion = clientVersion,
                            name = levelName,
                            width = levelEditorCols,
                            height = levelEditorRows,
                            spawnX = levelEditorSpawn.first,
                            spawnY = levelEditorSpawn.second,
                            layers = layers,
                        )
                        val levels = backendClient.listLevels(session.accessToken, clientVersion)
                        javax.swing.SwingUtilities.invokeLater {
                            availableLevels = levels
                            levelDetailsById[saved.id] = saved
                            refreshLevelLoadCombo()
                            levelLoadCombo.selectedItem = levels.firstOrNull { it.id == saved.id }
                            if (loadedCharacters.isNotEmpty()) {
                                renderCharacterRows(loadedCharacters)
                            }
                            levelToolStatus.text = "Saved level '${saved.name}'."
                        }
                    } catch (ex: Exception) {
                        log("Level save failed against ${backendClient.endpoint()}", ex)
                        javax.swing.SwingUtilities.invokeLater {
                            levelToolStatus.text = formatServiceError(ex, "Unable to save level.")
                        }
                    }
                }.start()
            }
        }
        sexChoice.addActionListener {
            createAppearanceKey = appearanceForSex(isFemale = sexChoice.selectedIndex == 1)
            applyCreateAppearancePreview()
        }
        applyCreateAppearancePreview()
        updatePointUi()

        createSubmit.addActionListener {
            if (!hasValidContentSnapshot) {
                createStatus.text = contentText(
                    "ui.content.blocked_play",
                    "Content unavailable. Reconnect to sync gameplay data.",
                )
                return@addActionListener
            }
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
                            race = raceChoice.selectedItem?.toString()?.trim().orEmpty(),
                            background = backgroundChoice.selectedItem?.toString()?.trim().orEmpty(),
                            affiliation = affiliationChoice.selectedItem?.toString()?.trim().orEmpty(),
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
                            if (raceChoice.itemCount > 0) raceChoice.selectedIndex = 0
                            if (backgroundChoice.itemCount > 0) backgroundChoice.selectedIndex = 0
                            if (affiliationChoice.itemCount > 0) affiliationChoice.selectedIndex = 0
                            populateCharacterViewsFn(refreshed)
                            createStatus.text = " "
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
            if (gameSceneContainer.isVisible) {
                persistCurrentCharacterLocation()
            }
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
            loadedCharacters = emptyList()
            availableLevels = emptyList()
            levelDetailsById.clear()
            tabLevelTool.isVisible = false
            characterRowsPanel.removeAll()
            characterRowsPanel.revalidate()
            characterRowsPanel.repaint()
            selectedCharacterId = null
            selectedCharacterView = null
            activeGameCharacterView = null
            heldKeys.clear()
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
        if (!hasValidContentSnapshot) {
            authStatus.text = contentText(
                "ui.content.blocked_play",
                "Content unavailable. Reconnect to sync gameplay data.",
            )
        } else if (contentSnapshotSource == "cache") {
            authStatus.text = contentText("ui.content.cached", "Using cached content snapshot.")
        }
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
                if (gameSceneContainer.isVisible) {
                    persistCurrentCharacterLocation()
                }
                authSession = null
            }
        })

        if (autoPlay) {
            javax.swing.SwingUtilities.invokeLater {
                if (authSession != null && selectedCharacterId != null) {
                    showCard("play")
                } else {
                    authStatus.text = " "
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

    private fun applyThemedButtonStyle(button: JButton, fontSize: Float, compactPadding: Boolean = false) {
        button.setUI(BasicButtonUI())
        button.foreground = THEME_TEXT_COLOR
        button.font = Font(THEME_FONT_FAMILY, Font.BOLD, fontSize.toInt())
        button.isFocusPainted = false
        button.isContentAreaFilled = true
        button.isBorderPainted = true
        button.isOpaque = true
        val paddingBorder = if (compactPadding) {
            BorderFactory.createEmptyBorder(2, 6, 2, 6)
        } else {
            BorderFactory.createEmptyBorder(4, 10, 4, 10)
        }
        fun applyButtonVisualState() {
            val activeTab = button.getClientProperty("gokActiveTab") == true
            button.background = when {
                activeTab -> Color(106, 76, 51)
                !button.model.isEnabled -> Color(45, 34, 26)
                button.model.isPressed -> Color(52, 39, 30)
                button.model.isRollover -> Color(84, 62, 45)
                else -> Color(68, 50, 37)
            }
            button.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(if (activeTab) Color(224, 184, 126) else Color(172, 132, 87), 1),
                paddingBorder
            )
        }
        button.border = BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Color(172, 132, 87), 1),
            paddingBorder
        )
        button.isRolloverEnabled = true
        button.model.addChangeListener { applyButtonVisualState() }
        button.addPropertyChangeListener("enabled") { applyButtonVisualState() }
        button.addPropertyChangeListener("gokActiveTab") { applyButtonVisualState() }
        applyButtonVisualState()
    }

    private fun applyThemedToggleStyle(button: JToggleButton, fontSize: Float) {
        button.setUI(BasicButtonUI())
        button.foreground = THEME_TEXT_COLOR
        button.font = Font(THEME_FONT_FAMILY, Font.BOLD, fontSize.toInt())
        button.isFocusPainted = false
        button.isContentAreaFilled = true
        button.isBorderPainted = true
        button.isOpaque = true
        button.isRolloverEnabled = true
        val paddingBorder = BorderFactory.createEmptyBorder(4, 10, 4, 10)
        fun applyToggleVisualState() {
            val selected = button.model.isSelected
            button.background = when {
                !button.model.isEnabled -> Color(45, 34, 26)
                selected -> Color(106, 76, 51)
                button.model.isPressed -> Color(52, 39, 30)
                button.model.isRollover -> Color(84, 62, 45)
                else -> Color(68, 50, 37)
            }
            button.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(if (selected) Color(224, 184, 126) else Color(172, 132, 87), 1),
                paddingBorder
            )
        }
        button.model.addChangeListener { applyToggleVisualState() }
        button.addPropertyChangeListener("enabled") { applyToggleVisualState() }
        applyToggleVisualState()
    }

    private fun buildMenuButton(text: String, buttonTexture: BufferedImage?, size: Dimension, fontSize: Float = 25f): JButton {
        val button = JButton(text).apply {
            alignmentX = Component.CENTER_ALIGNMENT
            horizontalTextPosition = SwingConstants.CENTER
            verticalTextPosition = SwingConstants.CENTER
            margin = Insets(0, 0, 0, 0)
        }
        applyThemedButtonStyle(button, fontSize)
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
        button.font = Font(THEME_FONT_FAMILY, Font.BOLD, fontSize.toInt())
        if (buttonTexture != null) {
            // The launcher intentionally ignores button art in favor of shape-based themed controls.
        }
    }

    private fun scaleImage(source: BufferedImage, width: Int, height: Int): BufferedImage {
        val targetWidth = width.coerceAtLeast(1)
        val targetHeight = height.coerceAtLeast(1)
        val scaled = BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB)
        val safeSourceWidth = source.width.coerceAtLeast(1)
        val safeSourceHeight = source.height.coerceAtLeast(1)
        val scale = kotlin.math.min(
            targetWidth.toDouble() / safeSourceWidth.toDouble(),
            targetHeight.toDouble() / safeSourceHeight.toDouble()
        )
        val drawWidth = (safeSourceWidth * scale).toInt().coerceAtLeast(1)
        val drawHeight = (safeSourceHeight * scale).toInt().coerceAtLeast(1)
        val drawX = ((targetWidth - drawWidth) / 2).coerceAtLeast(0)
        val drawY = ((targetHeight - drawHeight) / 2).coerceAtLeast(0)
        val graphics = scaled.createGraphics()
        try {
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR)
            graphics.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)
            graphics.drawImage(source, drawX, drawY, drawWidth, drawHeight, null)
        } finally {
            graphics.dispose()
        }
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

    private class ThemedComboBox<E> : JComboBox<E>() {
        private val comboBg = Color(58, 42, 33)
        private val comboHover = Color(84, 62, 45)
        private val comboBorder = Color(172, 132, 87)
        private val comboArrowBg = Color(68, 50, 37)

        private fun applyTheme() {
            isEditable = false
            isOpaque = true
            background = comboBg
            foreground = THEME_TEXT_COLOR
            font = Font(THEME_FONT_FAMILY, Font.PLAIN, 14)
            border = BorderFactory.createLineBorder(comboBorder, 1)
            renderer = object : DefaultListCellRenderer() {
                override fun getListCellRendererComponent(
                    list: JList<*>?,
                    value: Any?,
                    index: Int,
                    isSelected: Boolean,
                    cellHasFocus: Boolean
                ): Component {
                    val rendered = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus) as JLabel
                    if (list != null) {
                        list.background = comboBg
                        list.foreground = THEME_TEXT_COLOR
                        list.selectionBackground = comboHover
                        list.selectionForeground = THEME_TEXT_COLOR
                        list.font = Font(THEME_FONT_FAMILY, Font.PLAIN, 14)
                    }
                    rendered.isOpaque = true
                    rendered.foreground = THEME_TEXT_COLOR
                    rendered.background = if (isSelected) comboHover else comboBg
                    rendered.font = Font(THEME_FONT_FAMILY, Font.PLAIN, 14)
                    rendered.border = BorderFactory.createEmptyBorder(3, 8, 3, 8)
                    return rendered
                }
            }
            setUI(object : BasicComboBoxUI() {
                override fun paintCurrentValueBackground(g: Graphics, bounds: Rectangle, hasFocus: Boolean) {
                    g.color = comboBg
                    g.fillRect(bounds.x, bounds.y, bounds.width, bounds.height)
                }

                override fun createArrowButton(): JButton {
                    return JButton("v").apply {
                        setUI(BasicButtonUI())
                        isFocusable = false
                        isBorderPainted = true
                        isOpaque = true
                        background = comboArrowBg
                        foreground = THEME_TEXT_COLOR
                        font = Font(THEME_FONT_FAMILY, Font.BOLD, 12)
                        border = BorderFactory.createLineBorder(comboBorder, 1)
                        margin = Insets(0, 0, 0, 0)
                    }
                }
            })
        }

        override fun updateUI() {
            super.updateUI()
            applyTheme()
        }

        init {
            applyTheme()
        }
    }

    private class ThemedScrollPane(
        view: Component? = null,
        transparent: Boolean = false
    ) : JScrollPane(view) {
        init {
            if (transparent) {
                isOpaque = false
                viewport.isOpaque = false
                background = Color(0, 0, 0, 0)
                viewport.background = Color(0, 0, 0, 0)
                border = BorderFactory.createEmptyBorder()
                viewportBorder = BorderFactory.createEmptyBorder()
            } else {
                val bg = Color(24, 18, 15)
                val borderColor = Color(172, 132, 87)
                isOpaque = true
                viewport.isOpaque = true
                background = bg
                viewport.background = bg
                border = BorderFactory.createLineBorder(borderColor, 1)
                viewportBorder = BorderFactory.createEmptyBorder()
            }
            val track = Color(34, 26, 21)
            val thumb = Color(112, 82, 55)
            val thumbHover = Color(136, 101, 69)
            val borderColor = Color(172, 132, 87)
            fun newScrollBarUi(): BasicScrollBarUI {
                return object : BasicScrollBarUI() {
                    override fun createDecreaseButton(orientation: Int): JButton =
                        JButton().apply {
                            isOpaque = true
                            background = track
                            border = BorderFactory.createLineBorder(borderColor, 1)
                            preferredSize = Dimension(0, 0)
                        }

                    override fun createIncreaseButton(orientation: Int): JButton =
                        JButton().apply {
                            isOpaque = true
                            background = track
                            border = BorderFactory.createLineBorder(borderColor, 1)
                            preferredSize = Dimension(0, 0)
                        }

                    override fun configureScrollBarColors() {
                        trackColor = track
                        thumbColor = thumb
                        thumbDarkShadowColor = borderColor
                        thumbHighlightColor = thumbHover
                        thumbLightShadowColor = thumbHover
                    }
                }
            }
            verticalScrollBar.setUI(newScrollBarUi())
            horizontalScrollBar.setUI(newScrollBarUi())
            verticalScrollBar.unitIncrement = 18
            horizontalScrollBar.unitIncrement = 18
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
        controls: List<JButton>,
        autoRestartOnSuccess: Boolean = false
    ) {
        setUpdatingState(controls, true)
        val payloadRoot = payloadRoot()
        val root = installRoot(payloadRoot)
        val helperExe = findUpdateHelper(payloadRoot)
        if (helperExe == null) {
            status.text = "Updater helper not found. Reinstall from the latest release."
            log("Update helper missing. Checked ${payloadRoot.toAbsolutePath()}")
            setUpdatingState(controls, false)
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
                        handleUpdateHelperLine(line, status)
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
                        2 -> "Game is up to date."
                        else -> buildUpdateFailureMessage(exitCode, root, output)
                    }
                    setUpdatingState(controls, false)
                }
                log("Update finished with exit code $exitCode")
            } catch (ex: Exception) {
                javax.swing.SwingUtilities.invokeLater {
                    status.text = "Update failed: ${ex.message}"
                    setUpdatingState(controls, false)
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
            "body{font-family:$THEME_FONT_FAMILY;font-size:12px;color:$THEME_TEXT_HEX;background:transparent;margin:0;padding:4px;}" +
            "h2{font-family:$THEME_FONT_FAMILY;font-size:14px;margin:0 0 4px 0;}" +
            "p{font-family:$THEME_FONT_FAMILY;margin:0 0 6px 0;}" +
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
                "body{font-family:$THEME_FONT_FAMILY;font-size:13px;color:$THEME_TEXT_HEX;background:transparent;margin:0;padding:4px;}" +
                "h1{font-size:18px;font-weight:700;margin:0 0 6px 0;}" +
                "h2{font-size:16px;font-weight:600;margin:10px 0 4px 0;}" +
                "h3{font-size:14px;font-weight:600;margin:8px 0 4px 0;}" +
                "p{margin:0 0 6px 0;}" +
                "ul{margin:0 0 6px 18px;padding:0;}" +
                "li{margin:0 0 4px 0;}" +
                "code{background:rgba(0,0,0,0.35);padding:1px 3px;border-radius:3px;font-family:$THEME_FONT_FAMILY;}" +
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

    private fun setUpdatingState(controls: List<JButton>, updating: Boolean) {
        controls.forEach { it.isEnabled = !updating }
    }

    private fun handleUpdateHelperLine(line: String, status: JLabel) {
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
                status.text = "Checking for updates..."
            }

            line == "STATUS:DOWNLOADING" -> javax.swing.SwingUtilities.invokeLater {
                status.text = "Downloading update..."
            }

            line.startsWith("PROGRESS:") -> {
                val payload = line.substringAfter(':').trim()
                val parts = payload.split(':')
                val percent = parts.firstOrNull()?.toIntOrNull()?.coerceIn(0, 100) ?: return
                val speedBps = parts.getOrNull(1)?.toLongOrNull()?.coerceAtLeast(0L)
                val speedText = formatSpeed(speedBps)
                javax.swing.SwingUtilities.invokeLater {
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

    private fun embeddedContentBootstrap(): ContentBootstrapView {
        return ContentBootstrapView(
            contentSchemaVersion = 1,
            contentVersionId = 0,
            contentVersionKey = "embedded_v1",
            fetchedAt = Instant.now().toString(),
            pointBudget = 10,
            xpPerLevel = 100,
            maxPerStat = 10,
            races = listOf(
                ContentOptionEntryView("human", "Human", "Balanced origin.", "option.race.human"),
                ContentOptionEntryView("elf", "Elf", "Arcane-leaning origin.", "option.race.elf"),
                ContentOptionEntryView("dwarf", "Dwarf", "Sturdy martial origin.", "option.race.dwarf"),
            ),
            backgrounds = listOf(
                ContentOptionEntryView("drifter", "Drifter", "Survivalist path.", "option.background.drifter"),
                ContentOptionEntryView("scholar", "Scholar", "Knowledge path.", "option.background.scholar"),
                ContentOptionEntryView("soldier", "Soldier", "Military path.", "option.background.soldier"),
            ),
            affiliations = listOf(
                ContentOptionEntryView("unaffiliated", "Unaffiliated", "Independent.", "option.affiliation.unaffiliated"),
                ContentOptionEntryView("order", "Order", "Disciplined faction.", "option.affiliation.order"),
                ContentOptionEntryView("consortium", "Consortium", "Trade faction.", "option.affiliation.consortium"),
            ),
            stats = listOf(
                ContentStatEntryView("strength", "Strength", "Power for heavy melee attacks.", "Increases melee power and carrying force.", "stat.strength"),
                ContentStatEntryView("agility", "Agility", "Speed for movement and recovery.", "Improves movement and action speed.", "stat.agility"),
                ContentStatEntryView("intellect", "Intellect", "Arcane output and spell control.", "Increases spell power and scaling.", "stat.intellect"),
                ContentStatEntryView("vitality", "Vitality", "Base health and toughness.", "Raises health and resilience.", "stat.vitality"),
                ContentStatEntryView("resolve", "Resolve", "Resistance against control effects.", "Improves control resistance.", "stat.resolve"),
                ContentStatEntryView("endurance", "Endurance", "Stamina and sustained effort.", "Improves sustained activity.", "stat.endurance"),
                ContentStatEntryView("dexterity", "Dexterity", "Precision for weapons and tools.", "Improves precision and handling.", "stat.dexterity"),
                ContentStatEntryView("willpower", "Willpower", "Mental focus and channeling.", "Improves focus and control.", "stat.willpower"),
            ),
            skills = listOf(
                ContentSkillEntryView(
                    key = "ember",
                    label = "Ember",
                    textKey = "skill.ember",
                    skillType = "Spell",
                    manaCost = 12.0,
                    energyCost = 0.0,
                    lifeCost = 0.0,
                    effects = "Applies Burn I for 4s.",
                    damageText = "20 fire + INT scaling.",
                    cooldownSeconds = 4.0,
                    damageBase = 20.0,
                    intelligenceScale = 0.6,
                    description = "Starter fire projectile.",
                ),
                ContentSkillEntryView(
                    key = "cleave",
                    label = "Cleave",
                    textKey = "skill.cleave",
                    skillType = "Melee",
                    manaCost = 0.0,
                    energyCost = 18.0,
                    lifeCost = 0.0,
                    effects = "Short frontal arc strike.",
                    damageText = "30 physical.",
                    cooldownSeconds = 5.0,
                    damageBase = 30.0,
                    intelligenceScale = 0.0,
                    description = "Starter wide melee swing.",
                ),
                ContentSkillEntryView(
                    key = "quick_strike",
                    label = "Quick Strike",
                    textKey = "skill.quick_strike",
                    skillType = "Melee",
                    manaCost = 0.0,
                    energyCost = 10.0,
                    lifeCost = 0.0,
                    effects = "Single-target thrust.",
                    damageText = "18 physical.",
                    cooldownSeconds = 2.0,
                    damageBase = 18.0,
                    intelligenceScale = 0.0,
                    description = "Starter fast attack.",
                ),
                ContentSkillEntryView(
                    key = "bandage",
                    label = "Bandage",
                    textKey = "skill.bandage",
                    skillType = "Support",
                    manaCost = 0.0,
                    energyCost = 8.0,
                    lifeCost = 0.0,
                    effects = "Applies Regeneration I for 6s.",
                    damageText = "24 healing over time.",
                    cooldownSeconds = 8.0,
                    damageBase = 0.0,
                    intelligenceScale = 0.0,
                    description = "Starter sustain skill.",
                ),
            ),
            movementSpeed = 220.0,
            attackSpeedBase = 1.0,
            uiText = mapOf(
                "ui.content.blocked_play" to "Content unavailable. Reconnect to sync gameplay data.",
                "ui.content.cached" to "Using cached content snapshot.",
            ),
        )
    }

    private fun contentBootstrapCachePath(): Path {
        return installRoot(payloadRoot()).resolve("content_bootstrap_cache.json")
    }

    private fun isUsableContentBootstrap(bootstrap: ContentBootstrapView): Boolean {
        if (bootstrap.pointBudget <= 0) return false
        if (bootstrap.xpPerLevel <= 0) return false
        if (bootstrap.maxPerStat < 0) return false
        if (bootstrap.races.isEmpty() || bootstrap.backgrounds.isEmpty() || bootstrap.affiliations.isEmpty()) return false
        if (bootstrap.stats.isEmpty() || bootstrap.skills.isEmpty()) return false
        return true
    }

    private fun loadCachedContentBootstrap(): ContentBootstrapView? {
        val path = contentBootstrapCachePath()
        if (!Files.exists(path)) return null
        return try {
            val mapper = jacksonObjectMapper()
            val parsed = mapper.readValue(Files.readString(path), ContentBootstrapView::class.java)
            if (isUsableContentBootstrap(parsed)) {
                parsed
            } else {
                log("Ignoring invalid cached content snapshot at ${path.toAbsolutePath()}")
                null
            }
        } catch (ex: Exception) {
            log("Failed to read cached content snapshot from ${path.toAbsolutePath()}", ex)
            null
        }
    }

    private fun saveCachedContentBootstrap(bootstrap: ContentBootstrapView) {
        if (!isUsableContentBootstrap(bootstrap)) {
            log("Skipping cache write for unusable content snapshot ${bootstrap.contentVersionKey}")
            return
        }
        val path = contentBootstrapCachePath()
        try {
            Files.createDirectories(path.parent)
            val mapper = jacksonObjectMapper()
            val json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(bootstrap)
            Files.writeString(
                path,
                json,
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING,
                StandardOpenOption.WRITE,
            )
        } catch (ex: Exception) {
            log("Failed to persist cached content snapshot to ${path.toAbsolutePath()}", ex)
        }
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
