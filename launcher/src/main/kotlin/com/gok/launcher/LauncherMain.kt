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
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardOpenOption
import java.time.Instant
import java.time.ZoneId
import javax.imageio.ImageIO
import javax.swing.BorderFactory
import javax.swing.ImageIcon
import javax.swing.JButton
import javax.swing.JComboBox
import javax.swing.JList
import javax.swing.JOptionPane
import javax.swing.JPasswordField
import javax.swing.JEditorPane
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.JProgressBar
import javax.swing.JScrollPane
import javax.swing.JTextArea
import javax.swing.JTextField
import javax.swing.SwingConstants
import javax.swing.UIManager
import javax.swing.DefaultListModel
import javax.swing.plaf.basic.BasicProgressBarUI

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

    private data class CharacterArtOption(
        val key: String,
        val label: String,
        val image: BufferedImage?
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
        frame.minimumSize = Dimension(960, 640)
        frame.preferredSize = Dimension(1280, 720)

        val backgroundImage = loadUiImage("/ui/main_menu_background.png")
        val rectangularButtonImage = loadUiImage("/ui/button_rec_no_flame.png")
        val launcherCanvasImage = loadUiImage("/ui/launcher_canvas.png")

        val rootPanel = BackgroundPanel(backgroundImage).apply {
            layout = BorderLayout()
            border = BorderFactory.createEmptyBorder(10, 10, 10, 10)
        }
        val screenTitle = JLabel("Gardens of Karaxas", SwingConstants.CENTER).apply {
            foreground = Color(244, 230, 197)
            font = Font("Serif", Font.BOLD, 56)
            border = BorderFactory.createEmptyBorder(8, 0, 6, 0)
        }
        val contentPanel = JPanel(GridBagLayout()).apply {
            isOpaque = false
        }
        val menuLayout = GridLayout(8, 1, 0, 6)
        val menuPanel = JPanel().apply {
            isOpaque = false
            layout = menuLayout
            preferredSize = Dimension(340, 460)
        }
        val loginMenu = buildMenuButton("Login", rectangularButtonImage, Dimension(360, 54), 24f)
        val registerMenu = buildMenuButton("Register", rectangularButtonImage, Dimension(360, 54), 24f)
        val lobbyMenu = buildMenuButton("Account Lobby", rectangularButtonImage, Dimension(360, 54), 22f)
        val createCharacterMenu = buildMenuButton("Create Character", rectangularButtonImage, Dimension(360, 54), 21f)
        val selectCharacterMenu = buildMenuButton("Select Character", rectangularButtonImage, Dimension(360, 54), 21f)
        val updateMenu = buildMenuButton("Update", rectangularButtonImage, Dimension(360, 54), 24f)
        val playMenu = buildMenuButton("In Game", rectangularButtonImage, Dimension(360, 54), 24f)
        val exit = buildMenuButton("Exit", rectangularButtonImage, Dimension(360, 54), 24f)

        val boxBody = JPanel().apply {
            isOpaque = false
            layout = BorderLayout()
            preferredSize = Dimension(690, 440)
        }
        val menuBox = MenuContentBoxPanel(launcherCanvasImage ?: rectangularButtonImage).apply {
            layout = BorderLayout()
            border = BorderFactory.createEmptyBorder(0, 0, 0, 0)
            preferredSize = Dimension(760, 460)
            minimumSize = Dimension(420, 320)
            isVisible = true
            add(boxBody, BorderLayout.CENTER)
        }
        val menuBoxContainer = JPanel(BorderLayout()).apply {
            isOpaque = false
        }
        menuBoxContainer.add(menuBox, BorderLayout.NORTH)
        val menuConstraints = GridBagConstraints().apply {
            gridx = 0
            gridy = 0
            anchor = GridBagConstraints.NORTHWEST
            fill = GridBagConstraints.NONE
            weightx = 0.0
            weighty = 0.0
            insets = Insets(0, 0, 0, 8)
        }
        val boxConstraints = GridBagConstraints().apply {
            gridx = 1
            gridy = 0
            anchor = GridBagConstraints.NORTHWEST
            fill = GridBagConstraints.HORIZONTAL
            weightx = 1.0
            weighty = 0.0
        }
        contentPanel.add(menuPanel, menuConstraints)
        contentPanel.add(menuBoxContainer, boxConstraints)

        val backendClient = KaraxasBackendClient.fromEnvironment()
        var authSession: AuthSession? = null
        var activeChannel: ChannelView? = null

        fun defaultClientVersion(): String {
            val source = loadPatchNotesSource()
            val meta = loadPatchNotesMeta(source.path, source.markdown)
            return meta.version ?: "0.0.0"
        }

        val patchNotesPane = JEditorPane().apply {
            contentType = "text/html"
            isEditable = false
            putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, true)
            isOpaque = false
            background = Color(0, 0, 0, 0)
            foreground = Color(245, 232, 206)
            font = Font("Serif", Font.PLAIN, 13)
            border = BorderFactory.createEmptyBorder(0, 0, 0, 0)
        }
        val patchNotes = JScrollPane(patchNotesPane).apply {
            border = BorderFactory.createEmptyBorder(0, 0, 0, 0)
            viewportBorder = BorderFactory.createEmptyBorder(0, 0, 0, 0)
            preferredSize = Dimension(680, 410)
            isOpaque = false
            viewport.isOpaque = false
            background = Color(0, 0, 0, 0)
            viewport.background = Color(0, 0, 0, 0)
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
        val launcherButtons = JPanel(GridLayout(3, 2, 8, 8)).apply {
            isOpaque = false
            add(checkUpdates)
            add(showPatchNotesButton)
            add(launcherLogButton)
            add(gameLogButton)
            add(updateLogButton)
            add(clearLogsButton)
        }
        val buildVersionLabel = JLabel("", SwingConstants.LEFT).apply {
            foreground = Color(246, 233, 201)
            font = Font("Serif", Font.BOLD, 18)
            border = BorderFactory.createEmptyBorder(0, 0, 6, 0)
        }
        val updateContent = UiScaffold.contentPanel().apply {
            layout = BorderLayout(0, 8)
            isOpaque = false
            add(buildVersionLabel, BorderLayout.NORTH)
            add(patchNotes, BorderLayout.CENTER)
            add(JPanel(BorderLayout(0, 8)).apply {
                isOpaque = false
                add(progress, BorderLayout.NORTH)
                add(launcherButtons, BorderLayout.CENTER)
            }, BorderLayout.SOUTH)
        }

        val cardsLayout = CardLayout()
        val menuCards = JPanel(cardsLayout).apply {
            isOpaque = false
        }

        val loginEmail = UiScaffold.textField()
        val loginPassword = JPasswordField(24).apply {
            preferredSize = UiScaffold.fieldSize
            minimumSize = UiScaffold.fieldSize
            maximumSize = UiScaffold.fieldSize
            font = UiScaffold.bodyFont
        }
        val loginVersion = UiScaffold.textField().apply { text = defaultClientVersion() }
        val loginStatus = JLabel("Ready.")
        val loginSubmit = buildMenuButton("Login", rectangularButtonImage, Dimension(206, 42), 14f)

        val registerEmail = UiScaffold.textField()
        val registerName = UiScaffold.textField()
        val registerPassword = JPasswordField(24).apply {
            preferredSize = UiScaffold.fieldSize
            minimumSize = UiScaffold.fieldSize
            maximumSize = UiScaffold.fieldSize
            font = UiScaffold.bodyFont
        }
        val registerStatus = JLabel("Ready.")
        val registerSubmit = buildMenuButton("Create Account", rectangularButtonImage, Dimension(220, 42), 14f)

        val userStatus = JLabel("Not authenticated.")
        val lobbyStatus = JLabel("Lobby ready.")
        val characterSummary = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            text = "No characters loaded."
        }
        val refreshLobbyButton = buildMenuButton("Refresh Lobby", rectangularButtonImage, Dimension(170, 38), 13f)
        val openCreateFromLobby = buildMenuButton("Create Character", rectangularButtonImage, Dimension(170, 38), 13f)
        val openSelectFromLobby = buildMenuButton("Select Character", rectangularButtonImage, Dimension(170, 38), 13f)
        val openGameFromLobby = buildMenuButton("Enter Game", rectangularButtonImage, Dimension(170, 38), 13f)
        val openUpdateFromLobby = buildMenuButton("Updater", rectangularButtonImage, Dimension(150, 38), 13f)
        val logoutButton = buildMenuButton("Logout", rectangularButtonImage, Dimension(140, 38), 13f)

        val characterModel = DefaultListModel<CharacterView>()
        val characterList = JList(characterModel)

        val createName = UiScaffold.textField()
        val createPoints = UiScaffold.textField().apply { text = "20" }
        val statStrength = UiScaffold.textField().apply { text = "0" }
        val statAgility = UiScaffold.textField().apply { text = "0" }
        val statIntellect = UiScaffold.textField().apply { text = "0" }
        val skillAlchemy = UiScaffold.textField().apply { text = "0" }
        val skillSword = UiScaffold.textField().apply { text = "0" }
        val createStatus = JLabel("Allocate points to scaffold your first build.")
        val createSubmit = buildMenuButton("Create Character", rectangularButtonImage, Dimension(220, 42), 14f)
        val createRefresh = buildMenuButton("Refresh List", rectangularButtonImage, Dimension(180, 42), 14f)
        val createAppearancePreview = JLabel("No art loaded", SwingConstants.CENTER).apply {
            preferredSize = Dimension(230, 250)
            minimumSize = Dimension(230, 250)
            border = BorderFactory.createLineBorder(Color(172, 132, 87), 1)
            foreground = Color(245, 232, 206)
            font = Font("Serif", Font.BOLD, 14)
        }

        val selectStatus = JLabel("Choose an active character.")
        val selectRefresh = buildMenuButton("Refresh Characters", rectangularButtonImage, Dimension(220, 42), 14f)
        val selectSubmit = buildMenuButton("Set Active", rectangularButtonImage, Dimension(180, 42), 14f)
        val selectCharacterDetails = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            text = "Pick a character to view details."
        }

        val channelModel = DefaultListModel<ChannelView>()
        val channelList = JList(channelModel)
        val chatArea = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = Font("Monospaced", Font.PLAIN, 12)
        }
        val guildArea = JTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = UiScaffold.bodyFont
            text = "Guild data appears in-game."
        }
        val messageInput = UiScaffold.textField(26)
        val sendMessageButton = buildMenuButton("Send", rectangularButtonImage, Dimension(120, 38), 13f)
        val refreshGameButton = buildMenuButton("Refresh Game", rectangularButtonImage, Dimension(160, 38), 13f)
        val refreshChatButton = buildMenuButton("Refresh Chat", rectangularButtonImage, Dimension(160, 38), 13f)
        val launchRuntimeButton = buildMenuButton("Launch Runtime", rectangularButtonImage, Dimension(180, 38), 13f)
        val gameStatus = JLabel("Log in and select a character to enter game features.")

        val playStatus = JLabel("Game screen hosts in-session social features.")
        var selectedCharacterId: Int? = null
        var selectedCharacterName: String? = null

        fun parsePoints(text: String): Int = text.trim().toIntOrNull()?.coerceAtLeast(0) ?: 0

        fun loadCharacterArtOptions(): List<CharacterArtOption> {
            val options = mutableListOf<CharacterArtOption>()
            val roots = mutableListOf<Path>()
            System.getenv("GOK_CHARACTER_ART_DIR")
                ?.takeIf { it.isNotBlank() }
                ?.let { roots.add(Paths.get(it)) }
            roots.add(Paths.get(System.getProperty("user.dir")).resolve("assets").resolve("characters"))

            val imageExtensions = setOf("png", "jpg", "jpeg", "webp")
            for (root in roots.distinct()) {
                if (!Files.isDirectory(root)) continue
                try {
                    Files.list(root).use { stream ->
                        stream
                            .filter { Files.isRegularFile(it) }
                            .sorted()
                            .forEach { path ->
                                val ext = path.fileName.toString().substringAfterLast('.', "").lowercase()
                                if (ext !in imageExtensions) return@forEach
                                val image = try {
                                    ImageIO.read(path.toFile())
                                } catch (_: Exception) {
                                    null
                                }
                                if (image != null) {
                                    val rawName = path.fileName.toString().substringBeforeLast('.')
                                    val label = rawName.replace('_', ' ').replace('-', ' ')
                                    options.add(CharacterArtOption(key = rawName, label = label, image = image))
                                }
                            }
                    }
                } catch (_: Exception) {
                    // Ignore invalid art directories.
                }
            }
            return options
        }

        val appearanceOptions = loadCharacterArtOptions()
        val appearanceCombo = JComboBox<CharacterArtOption>().apply {
            preferredSize = UiScaffold.fieldSize
            minimumSize = UiScaffold.fieldSize
            maximumSize = Dimension(300, UiScaffold.fieldSize.height)
            font = UiScaffold.bodyFont
            if (appearanceOptions.isEmpty()) {
                addItem(CharacterArtOption("default", "Default (No Art Yet)", null))
            } else {
                appearanceOptions.forEach { addItem(it) }
            }
        }

        fun applySelectedAppearancePreview() {
            val option = appearanceCombo.selectedItem as? CharacterArtOption
            val image = option?.image
            if (image == null) {
                createAppearancePreview.icon = null
                createAppearancePreview.text = "No art loaded"
                return
            }
            val scaled = scaleImage(image, createAppearancePreview.width.coerceAtLeast(180), createAppearancePreview.height.coerceAtLeast(220))
            createAppearancePreview.icon = ImageIcon(scaled)
            createAppearancePreview.text = ""
        }

        fun withSession(onMissing: () -> Unit = {}, block: (AuthSession) -> Unit) {
            val session = authSession
            if (session == null) {
                onMissing()
                return
            }
            block(session)
        }

        fun runTask(
            statusLabel: JLabel,
            startText: String,
            successText: String,
            onFailure: (String) -> Unit = { statusLabel.text = it },
            work: () -> Unit,
        ) {
            statusLabel.text = startText
            Thread {
                try {
                    work()
                    javax.swing.SwingUtilities.invokeLater { statusLabel.text = successText }
                } catch (ex: Exception) {
                    javax.swing.SwingUtilities.invokeLater {
                        onFailure(ex.message ?: "Operation failed")
                    }
                }
            }.start()
        }

        fun refreshCharacters(statusLabel: JLabel) {
            withSession(onMissing = { statusLabel.text = "Please login first." }) { session ->
                runTask(statusLabel, "Loading characters...", "Characters loaded.") {
                    val characters = backendClient.listCharacters(session.accessToken, loginVersion.text.trim())
                    javax.swing.SwingUtilities.invokeLater {
                        characterModel.clear()
                        characters.forEach { characterModel.addElement(it) }
                        val active = characters.firstOrNull { it.isSelected }
                        selectedCharacterId = active?.id
                        selectedCharacterName = active?.name
                        if (active != null) {
                            selectCharacterDetails.text = "Active Character\n\nName: ${active.name}\nPoints: ${active.statPointsUsed}/${active.statPointsTotal}\n\nThis character unlocks in-game chat/guild tools."
                        } else {
                            selectCharacterDetails.text = "Pick a character to view details."
                        }
                    }
                }
            }
        }

        fun refreshChannels(statusLabel: JLabel) {
            withSession(onMissing = { statusLabel.text = "Please login first." }) { session ->
                runTask(statusLabel, "Loading channels...", "Channels loaded.") {
                    val channels = backendClient.listChannels(session.accessToken, loginVersion.text.trim())
                    javax.swing.SwingUtilities.invokeLater {
                        channelModel.clear()
                        channels.forEach { channelModel.addElement(it) }
                        if (channels.isNotEmpty()) {
                            channelList.selectedIndex = 0
                            activeChannel = channels.first()
                        }
                    }
                }
            }
        }

        fun refreshLobby() {
            withSession(onMissing = { lobbyStatus.text = "Please login first." }) { session ->
                runTask(lobbyStatus, "Refreshing lobby...", "Lobby refreshed.") {
                    val characters = backendClient.listCharacters(session.accessToken, loginVersion.text.trim())
                    javax.swing.SwingUtilities.invokeLater {
                        userStatus.text = "Logged in as ${session.displayName} (${session.email})"
                        characterModel.clear()
                        characters.forEach { characterModel.addElement(it) }
                        val active = characters.firstOrNull { it.isSelected }
                        selectedCharacterId = active?.id
                        selectedCharacterName = active?.name
                        characterSummary.text = if (characters.isEmpty()) {
                            "No characters created yet.\nUse Create Character to start."
                        } else {
                            val lines = characters.map { c ->
                                val marker = if (c.isSelected) " [ACTIVE]" else ""
                                "${c.name} (${c.statPointsUsed}/${c.statPointsTotal})$marker"
                            }
                            lines.joinToString("\n")
                        }
                    }
                }
            }
        }

        fun refreshGameSocial() {
            withSession(onMissing = { gameStatus.text = "Please login first." }) { session ->
                val selectedId = selectedCharacterId
                if (selectedId == null) {
                    gameStatus.text = "Select a character before entering game features."
                    return@withSession
                }
                runTask(gameStatus, "Refreshing game social data...", "Game social refreshed.") {
                    val overview = backendClient.lobbyOverview(session.accessToken, loginVersion.text.trim())
                    val channels = backendClient.listChannels(session.accessToken, loginVersion.text.trim())
                    javax.swing.SwingUtilities.invokeLater {
                        guildArea.text = if (overview.guilds.isEmpty()) {
                            "No guild membership yet."
                        } else {
                            overview.guilds.joinToString("\n")
                        }
                        channelModel.clear()
                        channels.forEach { channelModel.addElement(it) }
                        if (channels.isNotEmpty()) {
                            channelList.selectedIndex = 0
                            activeChannel = channels.first()
                        } else {
                            activeChannel = null
                        }
                    }
                }
            }
        }

        fun refreshMessages() {
            withSession(onMissing = { gameStatus.text = "Please login first." }) { session ->
                if (selectedCharacterId == null) {
                    gameStatus.text = "Select a character first."
                    return@withSession
                }
                val channel = activeChannel
                if (channel == null) {
                    gameStatus.text = "Select a channel first."
                    return@withSession
                }
                runTask(gameStatus, "Loading messages...", "Messages loaded.") {
                    val messages = backendClient.listMessages(session.accessToken, loginVersion.text.trim(), channel.id)
                    val rendered = messages.joinToString("\n") {
                        "[${it.createdAt}] ${it.senderDisplayName}: ${it.content}"
                    }
                    javax.swing.SwingUtilities.invokeLater {
                        chatArea.text = rendered.ifBlank { "No messages yet." }
                        chatArea.caretPosition = 0
                    }
                }
            }
        }

        val loginPanel = UiScaffold.contentPanel().apply {
            layout = GridBagLayout()
            add(UiScaffold.sectionLabel("Login"), UiScaffold.gbc(0))
            add(UiScaffold.titledLabel("Email"), UiScaffold.gbc(1))
            add(loginEmail, UiScaffold.gbc(2))
            add(UiScaffold.titledLabel("Password"), UiScaffold.gbc(3))
            add(loginPassword, UiScaffold.gbc(4))
            add(UiScaffold.titledLabel("Client Version"), UiScaffold.gbc(5))
            add(loginVersion, UiScaffold.gbc(6))
            add(loginSubmit, UiScaffold.gbc(7))
            add(loginStatus, UiScaffold.gbc(8))
        }

        val registerPanel = UiScaffold.contentPanel().apply {
            layout = GridBagLayout()
            add(UiScaffold.sectionLabel("Registration"), UiScaffold.gbc(0))
            add(UiScaffold.titledLabel("Display Name"), UiScaffold.gbc(1))
            add(registerName, UiScaffold.gbc(2))
            add(UiScaffold.titledLabel("Email"), UiScaffold.gbc(3))
            add(registerEmail, UiScaffold.gbc(4))
            add(UiScaffold.titledLabel("Password"), UiScaffold.gbc(5))
            add(registerPassword, UiScaffold.gbc(6))
            add(registerSubmit, UiScaffold.gbc(7))
            add(registerStatus, UiScaffold.gbc(8))
        }

        val lobbyPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(JPanel(BorderLayout(8, 8)).apply {
                isOpaque = false
                add(userStatus, BorderLayout.WEST)
                add(JPanel(GridLayout(1, 6, 6, 0)).apply {
                    isOpaque = false
                    add(refreshLobbyButton)
                    add(openCreateFromLobby)
                    add(openSelectFromLobby)
                    add(openGameFromLobby)
                    add(openUpdateFromLobby)
                    add(logoutButton)
                }, BorderLayout.EAST)
            }, BorderLayout.NORTH)
            add(JScrollPane(characterSummary).apply {
                border = BorderFactory.createTitledBorder("Account Characters")
                preferredSize = Dimension(780, 340)
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
                    border = BorderFactory.createTitledBorder("Character Art Preview")
                    add(createAppearancePreview, BorderLayout.CENTER)
                }, BorderLayout.WEST)
                add(JPanel(GridBagLayout()).apply {
                    isOpaque = false
                    add(UiScaffold.titledLabel("Name"), UiScaffold.gbc(0))
                    add(createName, UiScaffold.gbc(1))
                    add(UiScaffold.titledLabel("Appearance"), UiScaffold.gbc(2))
                    add(appearanceCombo, UiScaffold.gbc(3))
                    add(UiScaffold.titledLabel("Total Skill/Stat Points"), UiScaffold.gbc(4))
                    add(createPoints, UiScaffold.gbc(5))
                    add(UiScaffold.titledLabel("Stats (Strength / Agility / Intellect)"), UiScaffold.gbc(6))
                    add(JPanel(GridLayout(1, 3, 6, 0)).apply {
                        isOpaque = false
                        add(statStrength)
                        add(statAgility)
                        add(statIntellect)
                    }, UiScaffold.gbc(7))
                    add(UiScaffold.titledLabel("Skills (Alchemy / Sword Mastery)"), UiScaffold.gbc(8))
                    add(JPanel(GridLayout(1, 2, 6, 0)).apply {
                        isOpaque = false
                        add(skillAlchemy)
                        add(skillSword)
                    }, UiScaffold.gbc(9))
                    add(JPanel(GridLayout(1, 2, 6, 0)).apply {
                        isOpaque = false
                        add(createSubmit)
                        add(createRefresh)
                    }, UiScaffold.gbc(10))
                    add(createStatus, UiScaffold.gbc(11))
                }, BorderLayout.CENTER)
            }, BorderLayout.CENTER)
        }

        val selectCharacterPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(10, 8)
            add(UiScaffold.sectionLabel("Character Selection"), BorderLayout.NORTH)
            add(JScrollPane(characterList), BorderLayout.CENTER)
            add(JScrollPane(selectCharacterDetails).apply {
                border = BorderFactory.createTitledBorder("Selection Details")
                preferredSize = Dimension(260, 220)
            }, BorderLayout.EAST)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = false
                add(JPanel(GridLayout(1, 2, 6, 0)).apply {
                    isOpaque = false
                    add(selectRefresh)
                    add(selectSubmit)
                }, BorderLayout.NORTH)
                add(selectStatus, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }

        val playPanel = UiScaffold.contentPanel().apply {
            layout = BorderLayout(8, 8)
            add(UiScaffold.sectionLabel("In-Game Social"), BorderLayout.NORTH)
            add(JPanel(BorderLayout(8, 8)).apply {
                isOpaque = false
                add(JScrollPane(channelList).apply {
                    border = BorderFactory.createTitledBorder("Channels")
                    preferredSize = Dimension(220, 300)
                }, BorderLayout.WEST)
                add(JPanel(BorderLayout(6, 6)).apply {
                    isOpaque = false
                    add(JScrollPane(chatArea).apply { border = BorderFactory.createTitledBorder("Chat") }, BorderLayout.CENTER)
                    add(JPanel(BorderLayout(6, 0)).apply {
                        isOpaque = false
                        add(messageInput, BorderLayout.CENTER)
                        add(sendMessageButton, BorderLayout.EAST)
                    }, BorderLayout.SOUTH)
                }, BorderLayout.CENTER)
                add(JScrollPane(guildArea).apply {
                    border = BorderFactory.createTitledBorder("Guild Overview")
                    preferredSize = Dimension(260, 220)
                }, BorderLayout.EAST)
            }, BorderLayout.CENTER)
            add(JPanel(BorderLayout(6, 0)).apply {
                isOpaque = false
                add(JPanel(GridLayout(1, 4, 6, 0)).apply {
                    isOpaque = false
                    add(refreshGameButton)
                    add(refreshChatButton)
                    add(launchRuntimeButton)
                }, BorderLayout.NORTH)
                add(JPanel(GridLayout(2, 1)).apply {
                    isOpaque = false
                    add(gameStatus)
                    add(playStatus)
                }, BorderLayout.SOUTH)
            }, BorderLayout.SOUTH)
        }

        menuCards.add(loginPanel, "login")
        menuCards.add(registerPanel, "register")
        menuCards.add(lobbyPanel, "lobby")
        menuCards.add(createCharacterPanel, "create_character")
        menuCards.add(selectCharacterPanel, "select_character")
        menuCards.add(updateContent, "update")
        menuCards.add(playPanel, "play")
        boxBody.add(menuCards, BorderLayout.CENTER)

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

        fun showCard(card: String) {
            if (card == "lobby" || card == "create_character" || card == "select_character" || card == "play") {
                if (authSession == null) {
                    JOptionPane.showMessageDialog(frame, "Please login first.", "Not Authenticated", JOptionPane.WARNING_MESSAGE)
                    cardsLayout.show(menuCards, "login")
                    return
                }
            }
            if (card == "play" && selectedCharacterId == null) {
                JOptionPane.showMessageDialog(frame, "Select a character before entering game features.", "Character Required", JOptionPane.WARNING_MESSAGE)
                cardsLayout.show(menuCards, "select_character")
                return
            }
            if (card == "update") {
                buildVersionLabel.text = "Build Version: v${defaultClientVersion()} (${Instant.now().atZone(ZoneId.systemDefault()).toLocalDate()})"
                activeLog = null
                applyPatchNotesView(patchNotesPane, patchNotes)
                updateStatus.text = "Ready."
            }
            if (card == "play") {
                refreshGameSocial()
                playStatus.text = "In-game social ready for ${selectedCharacterName ?: "selected character"}."
            }
            cardsLayout.show(menuCards, card)
        }

        loginSubmit.addActionListener {
            val email = loginEmail.text.trim()
            val password = String(loginPassword.password)
            val version = loginVersion.text.trim().ifBlank { "0.0.0" }
            if (email.isBlank() || password.isBlank()) {
                loginStatus.text = "Email and password are required."
                return@addActionListener
            }
            loginStatus.text = "Logging in..."
            Thread {
                try {
                    val session = backendClient.login(email, password, version)
                    authSession = session
                    javax.swing.SwingUtilities.invokeLater {
                        loginStatus.text = "Welcome ${session.displayName}"
                        refreshLobby()
                        showCard("lobby")
                    }
                } catch (ex: Exception) {
                    javax.swing.SwingUtilities.invokeLater {
                        loginStatus.text = ex.message ?: "Login failed."
                    }
                }
            }.start()
        }

        registerSubmit.addActionListener {
            val email = registerEmail.text.trim()
            val displayName = registerName.text.trim()
            val password = String(registerPassword.password)
            val version = loginVersion.text.trim().ifBlank { "0.0.0" }
            if (email.isBlank() || displayName.isBlank() || password.isBlank()) {
                registerStatus.text = "All fields are required."
                return@addActionListener
            }
            registerStatus.text = "Creating account..."
            Thread {
                try {
                    val session = backendClient.register(email, password, displayName, version)
                    authSession = session
                    javax.swing.SwingUtilities.invokeLater {
                        registerStatus.text = "Account created."
                        refreshLobby()
                        showCard("lobby")
                    }
                } catch (ex: Exception) {
                    javax.swing.SwingUtilities.invokeLater {
                        registerStatus.text = ex.message ?: "Registration failed."
                    }
                }
            }.start()
        }

        refreshLobbyButton.addActionListener { refreshLobby() }
        openCreateFromLobby.addActionListener { showCard("create_character") }
        openSelectFromLobby.addActionListener { showCard("select_character") }
        openGameFromLobby.addActionListener { showCard("play") }
        refreshChatButton.addActionListener { refreshMessages() }
        refreshGameButton.addActionListener { refreshGameSocial() }
        openUpdateFromLobby.addActionListener { showCard("update") }
        appearanceCombo.addActionListener { applySelectedAppearancePreview() }
        applySelectedAppearancePreview()
        channelList.addListSelectionListener {
            val selected = channelList.selectedValue ?: return@addListSelectionListener
            activeChannel = selected
            refreshMessages()
        }
        characterList.addListSelectionListener {
            val selected = characterList.selectedValue ?: return@addListSelectionListener
            selectCharacterDetails.text =
                "Character\n\nName: ${selected.name}\nAllocated: ${selected.statPointsUsed}/${selected.statPointsTotal}\nActive: ${if (selected.isSelected) "Yes" else "No"}"
        }

        sendMessageButton.addActionListener {
            val content = messageInput.text.trim()
            if (content.isBlank()) {
                gameStatus.text = "Message cannot be empty."
                return@addActionListener
            }
            withSession(onMissing = { gameStatus.text = "Please login first." }) { session ->
                if (selectedCharacterId == null) {
                    gameStatus.text = "Select a character first."
                    return@withSession
                }
                val channel = activeChannel
                if (channel == null) {
                    gameStatus.text = "Select a channel first."
                    return@withSession
                }
                runTask(gameStatus, "Sending message...", "Message sent.") {
                    backendClient.sendMessage(session.accessToken, loginVersion.text.trim(), channel.id, content)
                    javax.swing.SwingUtilities.invokeLater {
                        messageInput.text = ""
                    }
                    refreshMessages()
                }
            }
        }

        createSubmit.addActionListener {
            withSession(onMissing = { createStatus.text = "Please login first." }) { session ->
                val name = createName.text.trim()
                if (name.isBlank()) {
                    createStatus.text = "Character name is required."
                    return@withSession
                }
                val totalPoints = parsePoints(createPoints.text)
                val stats = mapOf(
                    "strength" to parsePoints(statStrength.text),
                    "agility" to parsePoints(statAgility.text),
                    "intellect" to parsePoints(statIntellect.text),
                )
                val skills = mapOf(
                    "alchemy" to parsePoints(skillAlchemy.text),
                    "sword_mastery" to parsePoints(skillSword.text),
                )
                runTask(createStatus, "Creating character...", "Character created.") {
                    backendClient.createCharacter(
                        accessToken = session.accessToken,
                        clientVersion = loginVersion.text.trim(),
                        name = name,
                        totalPoints = totalPoints,
                        stats = stats,
                        skills = skills,
                    )
                    refreshCharacters(createStatus)
                    refreshLobby()
                }
            }
        }
        createRefresh.addActionListener { refreshCharacters(createStatus) }

        selectRefresh.addActionListener { refreshCharacters(selectStatus) }
        selectSubmit.addActionListener {
            val selected = characterList.selectedValue
            if (selected == null) {
                selectStatus.text = "Select a character first."
                return@addActionListener
            }
            withSession(onMissing = { selectStatus.text = "Please login first." }) { session ->
                runTask(selectStatus, "Applying selection...", "Character selected.") {
                    backendClient.selectCharacter(session.accessToken, loginVersion.text.trim(), selected.id)
                    refreshCharacters(selectStatus)
                    selectedCharacterId = selected.id
                    selectedCharacterName = selected.name
                }
            }
        }

        logoutButton.addActionListener {
            val session = authSession
            authSession = null
            if (session != null) {
                Thread {
                    try {
                        backendClient.logout(session.accessToken, loginVersion.text.trim())
                    } catch (_: Exception) {
                        // best effort logout
                    }
                }.start()
            }
            userStatus.text = "Not authenticated."
            guildArea.text = ""
            characterSummary.text = ""
            channelModel.clear()
            characterModel.clear()
            chatArea.text = ""
            selectedCharacterId = null
            selectedCharacterName = null
            lobbyStatus.text = "Logged out."
            gameStatus.text = "Logged out."
            showCard("login")
        }

        launchRuntimeButton.addActionListener {
            playStatus.text = "Launching local runtime..."
            launchGame(playStatus)
        }

        loginMenu.addActionListener { showCard("login") }
        registerMenu.addActionListener { showCard("register") }
        lobbyMenu.addActionListener { showCard("lobby") }
        createCharacterMenu.addActionListener { showCard("create_character") }
        selectCharacterMenu.addActionListener { showCard("select_character") }
        updateMenu.addActionListener { showCard("update") }
        playMenu.addActionListener { showCard("play") }
        exit.addActionListener {
            log("Exit selected from main menu.")
            frame.dispose()
            kotlin.system.exitProcess(0)
        }

        val mainButtons = listOf(loginMenu, registerMenu, lobbyMenu, createCharacterMenu, selectCharacterMenu, updateMenu, playMenu, exit)
        val toolButtons = listOf(checkUpdates, showPatchNotesButton, launcherLogButton, gameLogButton, updateLogButton, clearLogsButton)

        fun applyResponsiveLayout() {
            val availableW = contentPanel.width.coerceAtLeast(1)
            val availableH = contentPanel.height.coerceAtLeast(1)

            var menuWidth = (availableW * 0.27).toInt().coerceIn(250, 420)
            var columnGap = (availableW * 0.012).toInt().coerceIn(6, 18)
            if (menuWidth + columnGap > availableW - 320) {
                menuWidth = (availableW - 320 - columnGap).coerceAtLeast(220)
            }

            var buttonHeight = (availableH * 0.11).toInt().coerceIn(40, 64)
            var gap = (buttonHeight * 0.12f).toInt().coerceIn(4, 10)
            val rows = mainButtons.size
            var stackHeight = (rows * buttonHeight) + ((rows - 1) * gap)
            if (stackHeight > availableH) {
                buttonHeight = ((availableH - ((rows - 1) * gap)) / rows).coerceAtLeast(34)
                gap = (buttonHeight * 0.1f).toInt().coerceIn(3, 8)
                stackHeight = (rows * buttonHeight) + ((rows - 1) * gap)
            }

            menuLayout.vgap = gap
            menuPanel.preferredSize = Dimension(menuWidth, stackHeight)
            val mainFontSize = (buttonHeight * 0.42f).coerceIn(16f, 28f)
            mainButtons.forEach { resizeThemedButton(it, menuWidth, buttonHeight, mainFontSize) }

            menuConstraints.insets = Insets(0, 0, 0, columnGap)
            val boxWidth = (availableW - menuWidth - columnGap).coerceAtLeast(320)
            val boxHeight = stackHeight
            menuBox.preferredSize = Dimension(boxWidth, boxHeight)

            val insetLeft = (boxWidth * 0.115f).toInt().coerceIn(30, 150)
            val insetRight = (boxWidth * 0.115f).toInt().coerceIn(30, 150)
            val insetTop = (boxHeight * 0.17f).toInt().coerceIn(36, 130)
            val insetBottom = (boxHeight * 0.13f).toInt().coerceIn(28, 110)
            menuBox.border = BorderFactory.createEmptyBorder(insetTop, insetLeft, insetBottom, insetRight)

            val innerWidth = (boxWidth - insetLeft - insetRight).coerceAtLeast(240)
            val innerHeight = (boxHeight - insetTop - insetBottom).coerceAtLeast(180)
            val versionHeight = (buttonHeight * 0.8f).toInt().coerceIn(24, 46)
            buildVersionLabel.font = Font("Serif", Font.BOLD, (buttonHeight * 0.36f).toInt().coerceIn(14, 24))
            buildVersionLabel.preferredSize = Dimension(innerWidth, versionHeight)

            val toolButtonHeight = (buttonHeight * 0.76f).toInt().coerceIn(30, 48)
            val toolGap = (toolButtonHeight * 0.18f).toInt().coerceIn(6, 10)
            val toolButtonWidth = ((innerWidth - toolGap) / 2).coerceAtLeast(120)
            val toolFontSize = (toolButtonHeight * 0.35f).coerceIn(11f, 16f)
            toolButtons.forEach { resizeThemedButton(it, toolButtonWidth, toolButtonHeight, toolFontSize) }
            launcherButtons.preferredSize = Dimension(
                innerWidth,
                (toolButtonHeight * 3) + (toolGap * 2)
            )

            val progressHeight = (toolButtonHeight * 0.4f).toInt().coerceIn(12, 20)
            progress.preferredSize = Dimension(innerWidth, progressHeight)
            val patchHeight = (innerHeight - versionHeight - launcherButtons.preferredSize.height - progressHeight - 16).coerceAtLeast(100)
            patchNotes.preferredSize = Dimension(innerWidth, patchHeight)

            contentPanel.revalidate()
            contentPanel.repaint()
        }

        menuPanel.add(loginMenu)
        menuPanel.add(registerMenu)
        menuPanel.add(lobbyMenu)
        menuPanel.add(createCharacterMenu)
        menuPanel.add(selectCharacterMenu)
        menuPanel.add(updateMenu)
        menuPanel.add(playMenu)
        menuPanel.add(exit)

        rootPanel.add(screenTitle, BorderLayout.NORTH)
        rootPanel.add(contentPanel, BorderLayout.CENTER)
        frame.contentPane.add(rootPanel, BorderLayout.CENTER)
        loadIconImages()?.let { images ->
            frame.iconImages = images
            frame.iconImage = images.first()
            applyTaskbarIcon(images)
            applyDialogIcon(images)
        }
        frame.pack()
        frame.setLocationRelativeTo(null)
        frame.isVisible = true
        applyResponsiveLayout()
        showCard("login")
        frame.addComponentListener(object : ComponentAdapter() {
            override fun componentResized(e: ComponentEvent?) {
                applyResponsiveLayout()
            }
        })
        frame.addWindowListener(object : WindowAdapter() {
            override fun windowClosing(e: WindowEvent?) {
                authSession = null
            }
        })
        if (autoPlay) {
            javax.swing.SwingUtilities.invokeLater {
                playStatus.text = "Launching game..."
                launchGame(playStatus)
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

    private fun buildMenuButton(text: String, background: BufferedImage?, size: Dimension, fontSize: Float = 25f): JButton {
        val button = JButton(text).apply {
            alignmentX = Component.CENTER_ALIGNMENT
            horizontalTextPosition = SwingConstants.CENTER
            verticalTextPosition = SwingConstants.CENTER
            foreground = Color(247, 236, 209)
            isFocusPainted = false
            margin = Insets(0, 0, 0, 0)
            putClientProperty("bgImage", background)
        }
        resizeThemedButton(button, size.width, size.height, fontSize)
        return button
    }

    private fun resizeThemedButton(button: JButton, width: Int, height: Int, fontSize: Float) {
        val size = Dimension(width, height)
        button.preferredSize = size
        button.maximumSize = size
        button.minimumSize = size
        button.font = Font("Serif", Font.BOLD, fontSize.toInt())
        val background = button.getClientProperty("bgImage") as? BufferedImage
        if (background != null) {
            val icon = scaleImage(background, width, height)
            button.icon = ImageIcon(icon)
            button.rolloverIcon = ImageIcon(icon)
            button.pressedIcon = ImageIcon(icon)
            button.disabledIcon = ImageIcon(icon)
            button.isRolloverEnabled = false
            button.border = BorderFactory.createEmptyBorder()
            button.isContentAreaFilled = false
            button.isBorderPainted = false
            button.isOpaque = false
        } else {
            button.background = Color(32, 39, 46)
            button.foreground = Color.WHITE
            button.border = BorderFactory.createLineBorder(Color(170, 170, 170), 1)
            button.isContentAreaFilled = true
            button.isBorderPainted = true
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

    private class MenuContentBoxPanel(private val frameTexture: BufferedImage?) : JPanel() {
        private val sourceBounds: Rectangle = computeOpaqueBounds(frameTexture)

        init {
            isOpaque = false
        }

        override fun paintComponent(graphics: Graphics) {
            val g2 = graphics.create() as Graphics2D
            try {
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
                if (frameTexture != null) {
                    g2.drawImage(
                        frameTexture,
                        0,
                        0,
                        width,
                        height,
                        sourceBounds.x,
                        sourceBounds.y,
                        sourceBounds.x + sourceBounds.width,
                        sourceBounds.y + sourceBounds.height,
                        null
                    )
                } else {
                    g2.color = Color(52, 39, 32)
                    g2.fillRect(0, 0, width, height)
                }
            } finally {
                g2.dispose()
            }
            super.paintComponent(graphics)
        }

        private fun computeOpaqueBounds(image: BufferedImage?): Rectangle {
            if (image == null) return Rectangle(0, 0, 1, 1)
            var minX = image.width
            var minY = image.height
            var maxX = -1
            var maxY = -1
            for (y in 0 until image.height) {
                for (x in 0 until image.width) {
                    val alpha = image.getRGB(x, y).ushr(24) and 0xFF
                    if (alpha > 8) {
                        if (x < minX) minX = x
                        if (y < minY) minY = y
                        if (x > maxX) maxX = x
                        if (y > maxY) maxY = y
                    }
                }
            }
            if (maxX < minX || maxY < minY) return Rectangle(0, 0, image.width, image.height)
            return Rectangle(minX, minY, (maxX - minX + 1), (maxY - minY + 1))
        }
    }

    private fun runUpdate(
        status: JLabel,
        patchNotesPane: JEditorPane,
        patchNotesPaneScroll: JScrollPane,
        progress: JProgressBar,
        controls: List<JButton>
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
                            if (outputLines.any { it == "UPDATE_APPLYING" }) {
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
        scrollPane.border = BorderFactory.createEmptyBorder(0, 0, 0, 0)
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
        scrollPane.border = BorderFactory.createEmptyBorder(0, 0, 0, 0)
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
