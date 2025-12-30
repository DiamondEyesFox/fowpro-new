"""
FoWPro Styles & Theming
=======================
Professional dark theme styling for the application.
"""

from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication


# =============================================================================
# COLOR SCHEME
# =============================================================================

class Colors:
    """Application color palette"""

    # Primary colors
    PRIMARY = "#e94560"
    PRIMARY_DARK = "#c73e54"
    PRIMARY_LIGHT = "#ff6b81"

    # Secondary colors
    SECONDARY = "#0f3460"
    SECONDARY_DARK = "#0a2647"
    SECONDARY_LIGHT = "#16537e"

    # Accent colors
    ACCENT = "#ffd700"
    ACCENT_DARK = "#b8860b"

    # Background colors
    BG_DARKEST = "#0a0a14"
    BG_DARKER = "#12121e"
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#252540"
    BG_LIGHT = "#2d2d4a"

    # Surface colors
    SURFACE = "#1e1e32"
    SURFACE_HOVER = "#2a2a44"
    SURFACE_ACTIVE = "#3a3a5a"

    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0c0"
    TEXT_MUTED = "#606080"
    TEXT_DISABLED = "#404060"

    # Card attribute colors
    ATTR_LIGHT = "#ffd700"
    ATTR_FIRE = "#ff4500"
    ATTR_WATER = "#1e90ff"
    ATTR_WIND = "#32cd32"
    ATTR_DARKNESS = "#9932cc"
    ATTR_VOID = "#808080"

    # Status colors
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    ERROR = "#dc3545"
    INFO = "#17a2b8"

    # Border colors
    BORDER_DARK = "#2a2a44"
    BORDER_MEDIUM = "#3a3a5a"
    BORDER_LIGHT = "#4a4a6a"
    BORDER_FOCUS = "#e94560"


# =============================================================================
# FONTS
# =============================================================================

class Fonts:
    """Application fonts"""

    @staticmethod
    def title() -> QFont:
        font = QFont("Segoe UI", 28)
        font.setBold(True)
        return font

    @staticmethod
    def heading() -> QFont:
        font = QFont("Segoe UI", 18)
        font.setBold(True)
        return font

    @staticmethod
    def subheading() -> QFont:
        font = QFont("Segoe UI", 14)
        font.setBold(True)
        return font

    @staticmethod
    def body() -> QFont:
        return QFont("Segoe UI", 11)

    @staticmethod
    def small() -> QFont:
        return QFont("Segoe UI", 9)

    @staticmethod
    def monospace() -> QFont:
        return QFont("Consolas", 10)

    @staticmethod
    def card_name() -> QFont:
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        return font

    @staticmethod
    def card_stats() -> QFont:
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        return font


# =============================================================================
# STYLESHEET
# =============================================================================

MAIN_STYLESHEET = f"""
/* ==========================================================================
   GLOBAL STYLES
   ========================================================================== */

QWidget {{
    background-color: {Colors.BG_DARK};
    color: {Colors.TEXT_PRIMARY};
    font-family: "Segoe UI", sans-serif;
    font-size: 11px;
}}

QMainWindow {{
    background-color: {Colors.BG_DARKEST};
}}

/* ==========================================================================
   BUTTONS
   ========================================================================== */

QPushButton {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 12px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {Colors.SURFACE_HOVER};
    border-color: {Colors.PRIMARY};
}}

QPushButton:pressed {{
    background-color: {Colors.SURFACE_ACTIVE};
    border-color: {Colors.PRIMARY_DARK};
}}

QPushButton:disabled {{
    background-color: {Colors.BG_MEDIUM};
    color: {Colors.TEXT_DISABLED};
    border-color: {Colors.BORDER_DARK};
}}

/* Primary Button */
QPushButton[class="primary"] {{
    background-color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY_DARK};
}}

QPushButton[class="primary"]:hover {{
    background-color: {Colors.PRIMARY_LIGHT};
}}

/* Large Menu Button */
QPushButton[class="menu-button"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {Colors.SURFACE}, stop:1 {Colors.BG_MEDIUM});
    border: 2px solid {Colors.BORDER_MEDIUM};
    border-radius: 8px;
    padding: 16px 48px;
    font-size: 16px;
    font-weight: bold;
    min-width: 280px;
    min-height: 32px;
}}

QPushButton[class="menu-button"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {Colors.SURFACE_HOVER}, stop:1 {Colors.SURFACE});
    border-color: {Colors.PRIMARY};
    color: {Colors.PRIMARY_LIGHT};
}}

QPushButton[class="menu-button"]:pressed {{
    background: {Colors.SURFACE_ACTIVE};
    border-color: {Colors.PRIMARY_DARK};
}}

/* Icon Button */
QPushButton[class="icon-button"] {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
    min-width: 32px;
    min-height: 32px;
}}

QPushButton[class="icon-button"]:hover {{
    background-color: {Colors.SURFACE_HOVER};
}}

/* ==========================================================================
   INPUT FIELDS
   ========================================================================== */

QLineEdit {{
    background-color: {Colors.BG_MEDIUM};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: {Colors.PRIMARY};
}}

QLineEdit:focus {{
    border-color: {Colors.PRIMARY};
    background-color: {Colors.SURFACE};
}}

QLineEdit:disabled {{
    background-color: {Colors.BG_DARK};
    color: {Colors.TEXT_DISABLED};
}}

QTextEdit {{
    background-color: {Colors.BG_MEDIUM};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 8px;
}}

QTextEdit:focus {{
    border-color: {Colors.PRIMARY};
}}

/* ==========================================================================
   COMBO BOX
   ========================================================================== */

QComboBox {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {Colors.PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER_MEDIUM};
    selection-background-color: {Colors.PRIMARY};
}}

/* ==========================================================================
   SCROLL BARS
   ========================================================================== */

QScrollBar:vertical {{
    background-color: {Colors.BG_DARKER};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {Colors.BORDER_MEDIUM};
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Colors.BORDER_LIGHT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {Colors.BG_DARKER};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {Colors.BORDER_MEDIUM};
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Colors.BORDER_LIGHT};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ==========================================================================
   LIST & TABLE WIDGETS
   ========================================================================== */

QListWidget {{
    background-color: {Colors.BG_MEDIUM};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 4px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {Colors.SURFACE_HOVER};
}}

QListWidget::item:selected {{
    background-color: {Colors.PRIMARY};
}}

QTableWidget {{
    background-color: {Colors.BG_MEDIUM};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 4px;
    gridline-color: {Colors.BORDER_DARK};
}}

QTableWidget::item {{
    padding: 8px;
}}

QTableWidget::item:selected {{
    background-color: {Colors.PRIMARY};
}}

QHeaderView::section {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_PRIMARY};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {Colors.BORDER_DARK};
    font-weight: bold;
}}

/* ==========================================================================
   TAB WIDGET
   ========================================================================== */

QTabWidget::pane {{
    background-color: {Colors.BG_DARK};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 4px;
    padding: 8px;
}}

QTabBar::tab {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_SECONDARY};
    padding: 10px 20px;
    border: 1px solid {Colors.BORDER_DARK};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}

QTabBar::tab:hover {{
    background-color: {Colors.SURFACE_HOVER};
    color: {Colors.TEXT_PRIMARY};
}}

QTabBar::tab:selected {{
    background-color: {Colors.BG_DARK};
    color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

/* ==========================================================================
   GROUP BOX
   ========================================================================== */

QGroupBox {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 6px;
    margin-top: 12px;
    padding: 16px;
    padding-top: 24px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: {Colors.TEXT_SECONDARY};
}}

/* ==========================================================================
   LABELS
   ========================================================================== */

QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background-color: transparent;
}}

QLabel[class="title"] {{
    font-size: 28px;
    font-weight: bold;
    color: {Colors.TEXT_PRIMARY};
}}

QLabel[class="subtitle"] {{
    font-size: 14px;
    color: {Colors.TEXT_SECONDARY};
}}

QLabel[class="heading"] {{
    font-size: 18px;
    font-weight: bold;
}}

QLabel[class="muted"] {{
    color: {Colors.TEXT_MUTED};
}}

/* ==========================================================================
   FRAMES
   ========================================================================== */

QFrame[class="panel"] {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 8px;
}}

QFrame[class="card"] {{
    background-color: {Colors.BG_MEDIUM};
    border: 2px solid {Colors.BORDER_MEDIUM};
    border-radius: 6px;
}}

QFrame[class="card"]:hover {{
    border-color: {Colors.PRIMARY};
}}

QFrame[class="separator"] {{
    background-color: {Colors.BORDER_DARK};
    max-height: 1px;
}}

/* ==========================================================================
   SLIDERS
   ========================================================================== */

QSlider::groove:horizontal {{
    background-color: {Colors.BG_MEDIUM};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {Colors.PRIMARY};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px 0;
}}

QSlider::handle:horizontal:hover {{
    background-color: {Colors.PRIMARY_LIGHT};
}}

QSlider::sub-page:horizontal {{
    background-color: {Colors.PRIMARY};
    border-radius: 3px;
}}

/* ==========================================================================
   CHECK BOX & RADIO BUTTON
   ========================================================================== */

QCheckBox {{
    spacing: 8px;
    color: {Colors.TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    background-color: {Colors.BG_MEDIUM};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.PRIMARY};
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

QRadioButton {{
    spacing: 8px;
    color: {Colors.TEXT_PRIMARY};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {Colors.BORDER_MEDIUM};
    border-radius: 9px;
    background-color: {Colors.BG_MEDIUM};
}}

QRadioButton::indicator:hover {{
    border-color: {Colors.PRIMARY};
}}

QRadioButton::indicator:checked {{
    background-color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

/* ==========================================================================
   SPIN BOX
   ========================================================================== */

QSpinBox, QDoubleSpinBox {{
    background-color: {Colors.BG_MEDIUM};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 6px 12px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {Colors.PRIMARY};
}}

/* ==========================================================================
   MENU
   ========================================================================== */

QMenuBar {{
    background-color: {Colors.BG_DARKER};
    color: {Colors.TEXT_PRIMARY};
    border-bottom: 1px solid {Colors.BORDER_DARK};
    padding: 4px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {Colors.SURFACE_HOVER};
}}

QMenu {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {Colors.PRIMARY};
}}

QMenu::separator {{
    height: 1px;
    background-color: {Colors.BORDER_DARK};
    margin: 4px 8px;
}}

/* ==========================================================================
   TOOL TIP
   ========================================================================== */

QToolTip {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_MEDIUM};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ==========================================================================
   PROGRESS BAR
   ========================================================================== */

QProgressBar {{
    background-color: {Colors.BG_MEDIUM};
    border: 1px solid {Colors.BORDER_DARK};
    border-radius: 4px;
    height: 20px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {Colors.PRIMARY};
    border-radius: 3px;
}}

/* ==========================================================================
   STATUS BAR
   ========================================================================== */

QStatusBar {{
    background-color: {Colors.BG_DARKER};
    color: {Colors.TEXT_SECONDARY};
    border-top: 1px solid {Colors.BORDER_DARK};
}}

QStatusBar::item {{
    border: none;
}}

/* ==========================================================================
   SPLITTER
   ========================================================================== */

QSplitter::handle {{
    background-color: {Colors.BORDER_DARK};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {Colors.PRIMARY};
}}
"""


def apply_theme(app: QApplication):
    """Apply the dark theme to the application"""
    app.setStyleSheet(MAIN_STYLESHEET)

    # Set application-wide palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_MEDIUM))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_PRIMARY))

    app.setPalette(palette)
