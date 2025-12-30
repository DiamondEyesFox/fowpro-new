"""
FoWPro Main Menu Screen
=======================
Professional main menu with YGOPro/DevPro style.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPixmap, QFont, QColor, QPalette

from .styles import Colors, Fonts
from .assets import get_asset_manager


class MenuButton(QPushButton):
    """Styled menu button with hover effects"""

    def __init__(self, text: str, icon_text: str = None, parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setProperty("class", "menu-button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(320, 56)
        self.setMaximumWidth(400)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)


class MainMenuScreen(QWidget):
    """Main menu screen with game options"""

    # Signals
    start_game_clicked = pyqtSignal()
    deck_editor_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._background: QPixmap = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main menu UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content container
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(60, 60, 60, 60)

        # Top spacer
        content_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main title
        title = QLabel("FoWPro")
        title.setFont(Fonts.title())
        title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 64px;
            font-weight: bold;
            background: transparent;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add glow effect to title
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(30)
        title_shadow.setXOffset(0)
        title_shadow.setYOffset(0)
        title_shadow.setColor(QColor(Colors.PRIMARY))
        title.setGraphicsEffect(title_shadow)

        title_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Force of Will Simulator")
        subtitle.setFont(Fonts.subheading())
        subtitle.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 18px;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle)

        # Version
        version = QLabel("Grimm Cluster Edition")
        version.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 12px;
            background: transparent;
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(version)

        content_layout.addWidget(title_container)

        # Spacer
        content_layout.addSpacerItem(
            QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # Menu buttons container
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background: transparent;")
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(16)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Menu buttons
        self.start_btn = MenuButton("Start Game")
        self.start_btn.clicked.connect(self.start_game_clicked.emit)
        buttons_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.deck_btn = MenuButton("Deck Editor")
        self.deck_btn.clicked.connect(self.deck_editor_clicked.emit)
        buttons_layout.addWidget(self.deck_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.settings_btn = MenuButton("Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        buttons_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Separator
        separator = QFrame()
        separator.setFixedSize(200, 1)
        separator.setStyleSheet(f"background-color: {Colors.BORDER_DARK};")
        buttons_layout.addWidget(separator, alignment=Qt.AlignmentFlag.AlignCenter)

        self.exit_btn = MenuButton("Exit")
        self.exit_btn.clicked.connect(self.exit_clicked.emit)
        buttons_layout.addWidget(self.exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(buttons_container)

        # Bottom spacer
        content_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Footer
        footer = QLabel("A fan project for educational purposes")
        footer.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 10px;
            background: transparent;
            padding: 10px;
        """)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(footer)

        layout.addWidget(content)

    def paintEvent(self, event):
        """Paint the background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Get or generate background
        if self._background is None or self._background.size() != self.size():
            assets = get_asset_manager()
            self._background = assets.get_background('menu', self.size())

        # Draw background
        if self._background:
            painter.drawPixmap(0, 0, self._background)

        # Draw overlay for better text readability
        overlay = QColor(0, 0, 0, 120)
        painter.fillRect(self.rect(), overlay)

        painter.end()

    def on_show(self):
        """Called when screen is shown"""
        # Could add entrance animations here
        pass

    def on_resize(self, size: QSize):
        """Called when window is resized"""
        # Invalidate background cache
        self._background = None
        self.update()
