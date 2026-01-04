"""
FoWPro Application
===================
Main application window with screen management.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Callable
from enum import Enum, auto

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QCloseEvent, QResizeEvent, QIcon

from .styles import apply_theme, Colors
from .assets import get_asset_manager, init_asset_manager


class Screen(Enum):
    """Available screens in the application"""
    MAIN_MENU = auto()
    DECK_EDITOR = auto()
    DUEL = auto()
    SETTINGS = auto()
    SINGLE_PLAYER = auto()
    REPLAY = auto()


class FoWProApp(QMainWindow):
    """
    Main application window.

    Manages screen transitions and global state, similar to EDOPro's
    visibility-based screen system.
    """

    # Signals
    screen_changed = pyqtSignal(Screen)
    database_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("FoWPro - Force of Will Simulator")
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)

        # Initialize asset manager
        base_path = Path(__file__).parent.parent.parent / "textures"
        init_asset_manager(str(base_path))

        # Database
        self.db = None
        self.db_path: Optional[str] = None

        # Screens (lazy loaded)
        self._screens: Dict[Screen, QWidget] = {}
        self._current_screen: Optional[Screen] = None

        # Setup UI
        self._setup_ui()

        # Show main menu
        QTimer.singleShot(100, lambda: self.show_screen(Screen.MAIN_MENU))

    def _setup_ui(self):
        """Set up the main UI structure"""
        # Central stacked widget for screen management
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pre-create placeholder widgets
        for screen in Screen:
            placeholder = QWidget()
            placeholder.setObjectName(f"placeholder_{screen.name}")
            self.stack.addWidget(placeholder)

    def _get_screen(self, screen: Screen) -> QWidget:
        """Get or create a screen widget (lazy loading)"""
        if screen not in self._screens:
            self._screens[screen] = self._create_screen(screen)

            # Find and replace placeholder
            for i in range(self.stack.count()):
                widget = self.stack.widget(i)
                if widget.objectName() == f"placeholder_{screen.name}":
                    self.stack.removeWidget(widget)
                    widget.deleteLater()
                    break

            self.stack.addWidget(self._screens[screen])

        return self._screens[screen]

    def _create_screen(self, screen: Screen) -> QWidget:
        """Create a screen widget"""
        if screen == Screen.MAIN_MENU:
            from .main_menu import MainMenuScreen
            widget = MainMenuScreen(self)
            widget.start_game_clicked.connect(self._on_start_game)
            widget.deck_editor_clicked.connect(lambda: self.show_screen(Screen.DECK_EDITOR))
            widget.settings_clicked.connect(lambda: self.show_screen(Screen.SETTINGS))
            widget.exit_clicked.connect(self.close)
            return widget

        elif screen == Screen.DECK_EDITOR:
            from .deck_editor import DeckEditorScreen
            widget = DeckEditorScreen(self)
            widget.back_clicked.connect(lambda: self.show_screen(Screen.MAIN_MENU))
            return widget

        elif screen == Screen.SETTINGS:
            from .settings import SettingsScreen
            widget = SettingsScreen(self)
            widget.back_clicked.connect(lambda: self.show_screen(Screen.MAIN_MENU))
            return widget

        elif screen == Screen.DUEL:
            from .duel_screen import DuelScreen
            widget = DuelScreen(self)
            widget.back_clicked.connect(lambda: self.show_screen(Screen.MAIN_MENU))
            return widget

        else:
            # Placeholder for unimplemented screens
            widget = QWidget()
            layout = QVBoxLayout(widget)
            from PyQt6.QtWidgets import QLabel, QPushButton
            label = QLabel(f"{screen.name} - Coming Soon")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

            back_btn = QPushButton("Back to Menu")
            back_btn.clicked.connect(lambda: self.show_screen(Screen.MAIN_MENU))
            layout.addWidget(back_btn)

            return widget

    def show_screen(self, screen: Screen):
        """Show a screen"""
        widget = self._get_screen(screen)

        # Ensure widget is visible and in stack
        if self.stack.indexOf(widget) == -1:
            self.stack.addWidget(widget)

        # Call screen's on_show method if it exists
        if hasattr(widget, 'on_show'):
            widget.on_show()

        self.stack.setCurrentWidget(widget)
        widget.show()
        widget.update()
        self._current_screen = screen
        self.screen_changed.emit(screen)

    def get_current_screen(self) -> Optional[Screen]:
        """Get the current screen"""
        return self._current_screen

    # =========================================================================
    # DATABASE
    # =========================================================================

    def load_database(self, path: str = None) -> bool:
        """Load the card database"""
        if path is None:
            path = str(Path(__file__).parent.parent.parent / "data" / "cards.db")

        try:
            from ..database import CardDatabase
            self.db = CardDatabase(path)
            self.db_path = path

            # Check if database has cards
            if self.db.card_count() == 0:
                self._create_test_cards()

            self.database_loaded.emit(path)
            return True

        except Exception as e:
            QMessageBox.warning(
                self,
                "Database Error",
                f"Failed to load database: {e}"
            )
            return False

    def _create_test_cards(self):
        """Create test cards if database is empty"""
        if not self.db:
            return

        from ..models import CardData, CardType, Attribute, WillCost, Keyword, Rarity

        # Test ruler
        ruler = CardData(
            code="TEST-001",
            name="Grimm, the Fairy Tale Prince",
            card_type=CardType.RULER,
            attribute=Attribute.LIGHT,
            cost=WillCost(),
            ability_text="Continuous: You may pay the attribute cost of Fairy Tale resonators with will of any attribute.",
            rarity=Rarity.RARE,
            set_code="TEST",
            j_ruler_code="TEST-001J",
            judgment_cost=WillCost(light=2, void=1),
        )
        self.db.insert_card(ruler)

        j_ruler = CardData(
            code="TEST-001J",
            name="Grimm, the Avenger",
            card_type=CardType.J_RULER,
            attribute=Attribute.LIGHT,
            cost=WillCost(),
            atk=1000,
            defense=1000,
            rarity=Rarity.RARE,
            set_code="TEST",
            ruler_code="TEST-001",
        )
        self.db.insert_card(j_ruler)

        # Resonators
        resonator_data = [
            ("Tinker Bell, the Spirit", Attribute.WIND, 400, 400, WillCost(wind=1), "Flying"),
            ("Rapunzel, the Long-Haired Princess", Attribute.LIGHT, 600, 600, WillCost(light=2), ""),
            ("Snow White, the Valkyrie of Passion", Attribute.FIRE, 800, 600, WillCost(fire=2), ""),
            ("Cinderella, the Valkyrie of Glass", Attribute.WATER, 500, 700, WillCost(water=2), ""),
            ("Little Red Riding Hood", Attribute.FIRE, 400, 200, WillCost(fire=1), "Swiftness"),
            ("Sleeping Beauty", Attribute.DARKNESS, 700, 700, WillCost(darkness=2, void=1), ""),
            ("Hansel", Attribute.LIGHT, 300, 300, WillCost(light=1), ""),
            ("Gretel", Attribute.LIGHT, 300, 300, WillCost(light=1), ""),
            ("The Wolf", Attribute.DARKNESS, 600, 400, WillCost(darkness=1), ""),
            ("Pied Piper", Attribute.WIND, 500, 500, WillCost(wind=1, void=1), ""),
        ]

        for i, (name, attr, atk, def_, cost, keywords) in enumerate(resonator_data):
            card = CardData(
                code=f"TEST-{100+i:03d}",
                name=name,
                card_type=CardType.RESONATOR,
                attribute=attr,
                cost=cost,
                atk=atk,
                defense=def_,
                ability_text=keywords,
                rarity=Rarity.COMMON,
                set_code="TEST",
            )
            if "Swiftness" in keywords:
                card.keywords = Keyword.SWIFTNESS
            if "Flying" in keywords:
                card.keywords = Keyword.FLYING
            self.db.insert_card(card)

        # Magic Stones
        for i, (name, attr) in enumerate([
            ("Magic Stone of Light", Attribute.LIGHT),
            ("Magic Stone of Flame", Attribute.FIRE),
            ("Magic Stone of Water", Attribute.WATER),
            ("Magic Stone of Wind", Attribute.WIND),
            ("Magic Stone of Darkness", Attribute.DARKNESS),
            ("Magic Stone of Light (2)", Attribute.LIGHT),
            ("Magic Stone of Flame (2)", Attribute.FIRE),
            ("Magic Stone of Water (2)", Attribute.WATER),
            ("Magic Stone of Wind (2)", Attribute.WIND),
            ("Magic Stone of Darkness (2)", Attribute.DARKNESS),
        ]):
            stone = CardData(
                code=f"TEST-{200+i:03d}",
                name=name,
                card_type=CardType.MAGIC_STONE,
                attribute=attr,
                cost=WillCost(),
                rarity=Rarity.COMMON,
                set_code="TEST",
            )
            self.db.insert_card(stone)

        # Spells
        spells = [
            ("Thunder", Attribute.FIRE, WillCost(fire=1), "Deal 500 damage to target resonator."),
            ("Stoning to Death", Attribute.DARKNESS, WillCost(darkness=2), "Destroy target resonator."),
            ("Keen Sense", Attribute.WIND, WillCost(wind=1), "Draw a card."),
        ]

        for i, (name, attr, cost, text) in enumerate(spells):
            spell = CardData(
                code=f"TEST-{300+i:03d}",
                name=name,
                card_type=CardType.SPELL_CHANT,
                attribute=attr,
                cost=cost,
                ability_text=text,
                rarity=Rarity.COMMON,
                set_code="TEST",
            )
            self.db.insert_card(spell)

    def get_database(self):
        """Get the database, loading if necessary"""
        if self.db is None:
            self.load_database()
        return self.db

    # =========================================================================
    # GAME ACTIONS
    # =========================================================================

    def _on_start_game(self):
        """Handle start game request - shows lobby first"""
        # Ensure database is loaded
        if self.db is None:
            self.load_database()

        # Get duel screen and show lobby
        duel_screen = self._get_screen(Screen.DUEL)
        if hasattr(duel_screen, 'show_lobby_and_start'):
            # Show lobby dialog - if user confirms, game starts
            if duel_screen.show_lobby_and_start():
                # Only switch to duel screen if game started successfully
                self.show_screen(Screen.DUEL)
        elif hasattr(duel_screen, 'start_new_game'):
            # Fallback for old behavior
            self.show_screen(Screen.DUEL)
            duel_screen.start_new_game()

    # =========================================================================
    # EVENTS
    # =========================================================================

    def resizeEvent(self, event: QResizeEvent):
        """Handle window resize"""
        super().resizeEvent(event)

        # Notify current screen of resize
        if self._current_screen and self._current_screen in self._screens:
            widget = self._screens[self._current_screen]
            if hasattr(widget, 'on_resize'):
                widget.on_resize(event.size())

    def closeEvent(self, event: QCloseEvent):
        """Handle window close"""
        # Clean up database
        if self.db:
            self.db.close()

        event.accept()


def run_app() -> int:
    """Run the FoWPro application"""
    app = QApplication(sys.argv)
    app.setApplicationName("FoWPro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FoWPro")

    # Apply dark theme
    apply_theme(app)

    # Create and show main window
    window = FoWProApp()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
