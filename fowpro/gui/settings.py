"""
FoWPro Settings Screen
======================
Settings with background/texture customization like YGOPro/DevPro.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTabWidget, QGroupBox, QFileDialog,
    QSlider, QCheckBox, QComboBox, QLineEdit, QSpinBox,
    QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap

from .styles import Colors, Fonts
from .assets import get_asset_manager


class BackgroundSelector(QFrame):
    """Widget for selecting a background image"""

    changed = pyqtSignal(str, str)  # screen_name, path

    def __init__(self, screen_name: str, display_name: str, parent=None):
        super().__init__(parent)
        self.screen_name = screen_name
        self.current_path = ""

        self.setStyleSheet(f"""
            BackgroundSelector {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Preview
        self.preview = QLabel()
        self.preview.setFixedSize(160, 90)
        self.preview.setStyleSheet(f"""
            background-color: {Colors.BG_MEDIUM};
            border: 1px solid {Colors.BORDER_DARK};
            border-radius: 4px;
        """)
        self.preview.setScaledContents(True)
        layout.addWidget(self.preview)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_label = QLabel(display_name)
        name_label.setFont(Fonts.subheading())
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        info_layout.addWidget(name_label)

        self.path_label = QLabel("Default gradient")
        self.path_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        self.path_label.setWordWrap(True)
        info_layout.addWidget(self.path_label)

        info_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        btn_layout.addWidget(browse_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(reset_btn)

        info_layout.addLayout(btn_layout)
        layout.addLayout(info_layout, stretch=1)

        self._update_preview()

    def _browse(self):
        """Browse for a background image"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Background for {self.screen_name}",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )

        if path:
            self.current_path = path
            self.path_label.setText(path)

            # Update asset manager
            assets = get_asset_manager()
            assets.set_custom_background(self.screen_name, path)

            self._update_preview()
            self.changed.emit(self.screen_name, path)

    def _reset(self):
        """Reset to default background"""
        self.current_path = ""
        self.path_label.setText("Default gradient")

        # Clear from asset manager
        assets = get_asset_manager()
        if self.screen_name in assets.custom_backgrounds:
            del assets.custom_backgrounds[self.screen_name]
        assets.clear_cache()

        self._update_preview()
        self.changed.emit(self.screen_name, "")

    def _update_preview(self):
        """Update the preview image"""
        assets = get_asset_manager()
        pixmap = assets.get_background(self.screen_name, QSize(160, 90))
        self.preview.setPixmap(pixmap)


class SettingsScreen(QWidget):
    """Settings screen with customization options"""

    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._background: QPixmap = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)

        # Header
        header = QHBoxLayout()

        back_btn = QPushButton("< Back")
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)

        title = QLabel("Settings")
        title.setFont(Fonts.heading())
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)

        header.addStretch()
        content_layout.addLayout(header)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {Colors.SURFACE}dd;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

        # Appearance tab
        appearance_tab = self._create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")

        # Game tab
        game_tab = self._create_game_tab()
        tabs.addTab(game_tab, "Game")

        # Audio tab
        audio_tab = self._create_audio_tab()
        tabs.addTab(audio_tab, "Audio")

        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")

        content_layout.addWidget(tabs, stretch=1)

        layout.addWidget(content)

    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Backgrounds section
        bg_group = QGroupBox("Background Images")
        bg_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.BG_DARK}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        bg_layout = QVBoxLayout(bg_group)
        bg_layout.setSpacing(12)

        # Background selectors
        screens = [
            ('menu', 'Main Menu'),
            ('deck', 'Deck Editor'),
            ('duel', 'Duel Screen'),
            ('settings', 'Settings'),
        ]

        for screen_name, display_name in screens:
            selector = BackgroundSelector(screen_name, display_name)
            selector.changed.connect(self._on_background_changed)
            bg_layout.addWidget(selector)

        layout.addWidget(bg_group)

        # Theme section
        theme_group = QGroupBox("Theme")
        theme_group.setStyleSheet(bg_group.styleSheet())
        theme_layout = QGridLayout(theme_group)
        theme_layout.setSpacing(12)

        # Skin selector
        theme_layout.addWidget(QLabel("Skin:"), 0, 0)
        self.skin_combo = QComboBox()
        self.skin_combo.addItems(get_asset_manager().get_available_skins())
        self.skin_combo.currentTextChanged.connect(self._on_skin_changed)
        theme_layout.addWidget(self.skin_combo, 0, 1)

        # Card size
        theme_layout.addWidget(QLabel("Card Size:"), 1, 0)
        self.card_size_combo = QComboBox()
        self.card_size_combo.addItems(["Small", "Medium", "Large"])
        self.card_size_combo.setCurrentText("Medium")
        theme_layout.addWidget(self.card_size_combo, 1, 1)

        layout.addWidget(theme_group)

        layout.addStretch()
        return tab

    def _create_game_tab(self) -> QWidget:
        """Create the game settings tab"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Gameplay section
        gameplay_group = QGroupBox("Gameplay")
        gameplay_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.BG_DARK}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        gameplay_layout = QGridLayout(gameplay_group)
        gameplay_layout.setSpacing(12)

        # Auto-pass priority
        self.auto_pass_check = QCheckBox("Auto-pass priority when no actions available")
        self.auto_pass_check.setChecked(True)
        self.auto_pass_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        gameplay_layout.addWidget(self.auto_pass_check, 0, 0, 1, 2)

        # Show card tooltips
        self.tooltips_check = QCheckBox("Show card tooltips on hover")
        self.tooltips_check.setChecked(True)
        self.tooltips_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        gameplay_layout.addWidget(self.tooltips_check, 1, 0, 1, 2)

        # Animation speed
        gameplay_layout.addWidget(QLabel("Animation Speed:"), 2, 0)
        self.anim_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.anim_speed_slider.setMinimum(0)
        self.anim_speed_slider.setMaximum(100)
        self.anim_speed_slider.setValue(50)
        gameplay_layout.addWidget(self.anim_speed_slider, 2, 1)

        layout.addWidget(gameplay_group)

        # Default deck section
        default_group = QGroupBox("Default Deck")
        default_group.setStyleSheet(gameplay_group.styleSheet())
        default_layout = QHBoxLayout(default_group)
        default_layout.setSpacing(12)

        self.default_deck_path = QLineEdit()
        self.default_deck_path.setPlaceholderText("No default deck set")
        self.default_deck_path.setReadOnly(True)
        default_layout.addWidget(self.default_deck_path, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_default_deck)
        default_layout.addWidget(browse_btn)

        layout.addWidget(default_group)

        layout.addStretch()
        return tab

    def _create_audio_tab(self) -> QWidget:
        """Create the audio settings tab"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Volume section
        volume_group = QGroupBox("Volume")
        volume_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.BG_DARK}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        volume_layout = QGridLayout(volume_group)
        volume_layout.setSpacing(12)

        # Master volume
        volume_layout.addWidget(QLabel("Master Volume:"), 0, 0)
        self.master_volume = QSlider(Qt.Orientation.Horizontal)
        self.master_volume.setMinimum(0)
        self.master_volume.setMaximum(100)
        self.master_volume.setValue(80)
        volume_layout.addWidget(self.master_volume, 0, 1)
        self.master_vol_label = QLabel("80%")
        self.master_vol_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self.master_volume.valueChanged.connect(
            lambda v: self.master_vol_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.master_vol_label, 0, 2)

        # Music volume
        volume_layout.addWidget(QLabel("Music Volume:"), 1, 0)
        self.music_volume = QSlider(Qt.Orientation.Horizontal)
        self.music_volume.setMinimum(0)
        self.music_volume.setMaximum(100)
        self.music_volume.setValue(60)
        volume_layout.addWidget(self.music_volume, 1, 1)
        self.music_vol_label = QLabel("60%")
        self.music_vol_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self.music_volume.valueChanged.connect(
            lambda v: self.music_vol_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.music_vol_label, 1, 2)

        # SFX volume
        volume_layout.addWidget(QLabel("Sound Effects:"), 2, 0)
        self.sfx_volume = QSlider(Qt.Orientation.Horizontal)
        self.sfx_volume.setMinimum(0)
        self.sfx_volume.setMaximum(100)
        self.sfx_volume.setValue(70)
        volume_layout.addWidget(self.sfx_volume, 2, 1)
        self.sfx_vol_label = QLabel("70%")
        self.sfx_vol_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self.sfx_volume.valueChanged.connect(
            lambda v: self.sfx_vol_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.sfx_vol_label, 2, 2)

        layout.addWidget(volume_group)

        # Audio options
        options_group = QGroupBox("Audio Options")
        options_group.setStyleSheet(volume_group.styleSheet())
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(8)

        self.enable_music = QCheckBox("Enable background music")
        self.enable_music.setChecked(True)
        self.enable_music.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        options_layout.addWidget(self.enable_music)

        self.enable_sfx = QCheckBox("Enable sound effects")
        self.enable_sfx.setChecked(True)
        self.enable_sfx.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        options_layout.addWidget(self.enable_sfx)

        layout.addWidget(options_group)

        layout.addStretch()
        return tab

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Paths section
        paths_group = QGroupBox("Paths")
        paths_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.BG_DARK}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        paths_layout = QGridLayout(paths_group)
        paths_layout.setSpacing(12)

        # Database path
        paths_layout.addWidget(QLabel("Database:"), 0, 0)
        self.db_path = QLineEdit()
        self.db_path.setPlaceholderText("data/cards.db")
        self.db_path.setReadOnly(True)
        paths_layout.addWidget(self.db_path, 0, 1)
        db_browse = QPushButton("...")
        db_browse.setFixedWidth(40)
        db_browse.clicked.connect(self._browse_database)
        paths_layout.addWidget(db_browse, 0, 2)

        # Decks folder
        paths_layout.addWidget(QLabel("Decks Folder:"), 1, 0)
        self.decks_path = QLineEdit()
        self.decks_path.setPlaceholderText("decks/")
        self.decks_path.setReadOnly(True)
        paths_layout.addWidget(self.decks_path, 1, 1)
        decks_browse = QPushButton("...")
        decks_browse.setFixedWidth(40)
        paths_layout.addWidget(decks_browse, 1, 2)

        # Textures folder
        paths_layout.addWidget(QLabel("Textures Folder:"), 2, 0)
        self.textures_path = QLineEdit()
        self.textures_path.setPlaceholderText("textures/")
        self.textures_path.setReadOnly(True)
        paths_layout.addWidget(self.textures_path, 2, 1)
        textures_browse = QPushButton("...")
        textures_browse.setFixedWidth(40)
        paths_layout.addWidget(textures_browse, 2, 2)

        layout.addWidget(paths_group)

        # Cache section
        cache_group = QGroupBox("Cache")
        cache_group.setStyleSheet(paths_group.styleSheet())
        cache_layout = QVBoxLayout(cache_group)
        cache_layout.setSpacing(12)

        cache_info = QLabel("Clear cached images and textures to free memory or apply changes.")
        cache_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        cache_info.setWordWrap(True)
        cache_layout.addWidget(cache_info)

        clear_cache_btn = QPushButton("Clear Image Cache")
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(clear_cache_btn)

        layout.addWidget(cache_group)

        # Import section
        import_group = QGroupBox("Import Cards")
        import_group.setStyleSheet(paths_group.styleSheet())
        import_layout = QVBoxLayout(import_group)
        import_layout.setSpacing(12)

        import_info = QLabel("Import Grimm Cluster cards from Force of Wind. This may take 10-15 minutes.")
        import_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        import_info.setWordWrap(True)
        import_layout.addWidget(import_info)

        import_btn = QPushButton("Import Grimm Cluster Cards")
        import_btn.clicked.connect(self._import_cards)
        import_layout.addWidget(import_btn)

        layout.addWidget(import_group)

        layout.addStretch()
        return tab

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def _on_background_changed(self, screen: str, path: str):
        """Handle background change"""
        # Invalidate any cached backgrounds in other screens
        pass

    def _on_skin_changed(self, skin_name: str):
        """Handle skin change"""
        assets = get_asset_manager()
        assets.set_skin(skin_name)

    def _browse_default_deck(self):
        """Browse for default deck"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Default Deck",
            str(Path(__file__).parent.parent.parent / "decks"),
            "FoWPro Deck (*.fdk);;All Files (*)"
        )
        if path:
            self.default_deck_path.setText(path)

    def _browse_database(self):
        """Browse for database file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Card Database",
            str(Path(__file__).parent.parent.parent / "data"),
            "SQLite Database (*.db);;All Files (*)"
        )
        if path:
            self.db_path.setText(path)
            if self.main_window:
                self.main_window.load_database(path)

    def _clear_cache(self):
        """Clear image cache"""
        assets = get_asset_manager()
        assets.clear_cache()
        self._background = None
        self.update()

    def _import_cards(self):
        """Start card import process"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Import Cards",
            "Card import will start. This may take 10-15 minutes.\n\n"
            "Run 'python import_grimm.py' from the terminal for best results."
        )

    # =========================================================================
    # SCREEN EVENTS
    # =========================================================================

    def paintEvent(self, event):
        """Paint the background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self._background is None or self._background.size() != self.size():
            assets = get_asset_manager()
            self._background = assets.get_background('settings', self.size())

        if self._background:
            painter.drawPixmap(0, 0, self._background)

        # Overlay
        overlay = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay)

        painter.end()

    def on_show(self):
        """Called when screen is shown"""
        pass

    def on_resize(self, size: QSize):
        """Called when window is resized"""
        self._background = None
        self.update()
