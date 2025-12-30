"""
FoWPro - PyQt6 GUI
==================
Complete graphical interface for Force of Will simulator.
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter, QGroupBox,
    QMessageBox, QInputDialog, QDialog, QDialogButtonBox, QComboBox,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QFileDialog, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread
from PyQt6.QtGui import (
    QColor, QPalette, QFont, QAction, QPainter, QBrush, QPen,
    QLinearGradient, QPixmap
)

from .models import (
    Card, CardData, CardType, Attribute, Zone, Phase, CombatStep,
    Keyword, WillCost, WillPool
)
from .engine import GameEngine, EventType, GameEvent
from .database import CardDatabase


# =============================================================================
# CUSTOM WIDGETS
# =============================================================================

class CardWidget(QFrame):
    """Widget representing a single card"""

    clicked = pyqtSignal(object)  # Emits Card
    double_clicked = pyqtSignal(object)

    ATTRIBUTE_COLORS = {
        Attribute.LIGHT: "#FFD700",
        Attribute.FIRE: "#FF4500",
        Attribute.WATER: "#1E90FF",
        Attribute.WIND: "#32CD32",
        Attribute.DARKNESS: "#8B008B",
        Attribute.VOID: "#808080",
        Attribute.NONE: "#C0C0C0",
    }

    def __init__(self, card: Optional[Card] = None, face_down: bool = False,
                 small: bool = False, parent=None):
        super().__init__(parent)
        self.card = card
        self.face_down = face_down
        self.small = small
        self.selected = False

        self._setup_ui()
        self.update_display()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)

        if self.small:
            self.setFixedSize(80, 112)
        else:
            self.setFixedSize(120, 168)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Name label
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(8 if self.small else 10)
        font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)

        # Type label
        self.type_label = QLabel()
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font2 = QFont()
        font2.setPointSize(6 if self.small else 8)
        self.type_label.setFont(font2)
        layout.addWidget(self.type_label)

        layout.addStretch()

        # Stats label (ATK/DEF)
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font3 = QFont()
        font3.setPointSize(10 if self.small else 12)
        font3.setBold(True)
        self.stats_label.setFont(font3)
        layout.addWidget(self.stats_label)

        # Status indicators
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font4 = QFont()
        font4.setPointSize(6 if self.small else 8)
        self.status_label.setFont(font4)
        layout.addWidget(self.status_label)

    def update_display(self):
        if self.face_down or not self.card:
            self.name_label.setText("???")
            self.type_label.setText("")
            self.stats_label.setText("")
            self.status_label.setText("")
            self.setStyleSheet("background-color: #2F4F4F; border: 2px solid #696969;")
            return

        card = self.card
        data = card.data

        # Set name
        name = data.name
        if len(name) > 15 and self.small:
            name = name[:12] + "..."
        self.name_label.setText(name)

        # Set type
        type_str = data.card_type.value
        if len(type_str) > 15:
            type_str = type_str[:12] + "..."
        self.type_label.setText(type_str)

        # Set stats
        if data.atk or data.defense:
            self.stats_label.setText(f"{card.effective_atk}/{card.effective_def}")
        else:
            self.stats_label.setText("")

        # Set status
        status_parts = []
        if card.is_rested:
            status_parts.append("Rested")
        if card.damage > 0:
            status_parts.append(f"Dmg:{card.damage}")
        self.status_label.setText(" ".join(status_parts))

        # Set background color based on attribute
        color = self.ATTRIBUTE_COLORS.get(data.attribute, "#C0C0C0")
        border_color = "#FFD700" if self.selected else "#404040"
        border_width = 3 if self.selected else 2

        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {color};
                border: {border_width}px solid {border_color};
                border-radius: 5px;
            }}
        """)

    def set_card(self, card: Optional[Card]):
        self.card = card
        self.update_display()

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.card)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.card)
        super().mouseDoubleClickEvent(event)


class ZoneWidget(QFrame):
    """Widget representing a game zone (hand, field, etc.)"""

    card_clicked = pyqtSignal(object)  # Card
    card_double_clicked = pyqtSignal(object)

    def __init__(self, zone_name: str, horizontal: bool = True,
                 max_cards: int = 10, small_cards: bool = False, parent=None):
        super().__init__(parent)
        self.zone_name = zone_name
        self.horizontal = horizontal
        self.max_cards = max_cards
        self.small_cards = small_cards
        self.cards: list[Card] = []
        self.card_widgets: list[CardWidget] = []

        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Zone label
        self.label = QLabel(self.zone_name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        main_layout.addWidget(self.label)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded if self.horizontal
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff if self.horizontal
            else Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        container = QWidget()
        if self.horizontal:
            self.cards_layout = QHBoxLayout(container)
        else:
            self.cards_layout = QVBoxLayout(container)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(5)
        self.cards_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def set_cards(self, cards: list[Card], face_down: bool = False):
        """Update the cards displayed in this zone"""
        self.cards = cards

        # Remove old widgets
        for widget in self.card_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.card_widgets.clear()

        # Add new widgets
        for card in cards[:self.max_cards]:
            widget = CardWidget(card, face_down=face_down, small=self.small_cards)
            widget.clicked.connect(self._on_card_clicked)
            widget.double_clicked.connect(self._on_card_double_clicked)

            # Insert before stretch
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, widget)
            self.card_widgets.append(widget)

        # Update label with count
        self.label.setText(f"{self.zone_name} ({len(cards)})")

    def _on_card_clicked(self, card: Card):
        self.card_clicked.emit(card)

    def _on_card_double_clicked(self, card: Card):
        self.card_double_clicked.emit(card)


class WillPoolWidget(QFrame):
    """Widget displaying a player's will pool"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.will_pool = WillPool()
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.will_labels = {}
        colors = [
            ("Light", "#FFD700", "light"),
            ("Fire", "#FF4500", "fire"),
            ("Water", "#1E90FF", "water"),
            ("Wind", "#32CD32", "wind"),
            ("Dark", "#8B008B", "darkness"),
            ("Void", "#808080", "void"),
        ]

        for name, color, attr in colors:
            label = QLabel(f"{name[0]}: 0")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            layout.addWidget(label)
            self.will_labels[attr] = label

    def set_will_pool(self, pool: WillPool):
        self.will_pool = pool
        self.will_labels["light"].setText(f"L: {pool.light}")
        self.will_labels["fire"].setText(f"R: {pool.fire}")
        self.will_labels["water"].setText(f"U: {pool.water}")
        self.will_labels["wind"].setText(f"G: {pool.wind}")
        self.will_labels["darkness"].setText(f"B: {pool.darkness}")
        self.will_labels["void"].setText(f"V: {pool.void}")


class PlayerAreaWidget(QFrame):
    """Widget representing one player's game area"""

    card_clicked = pyqtSignal(object, str)  # Card, zone_name

    def __init__(self, player_index: int, is_opponent: bool = False, parent=None):
        super().__init__(parent)
        self.player_index = player_index
        self.is_opponent = is_opponent
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Player info bar
        info_bar = QHBoxLayout()

        self.name_label = QLabel(f"Player {self.player_index + 1}")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.name_label.setFont(font)
        info_bar.addWidget(self.name_label)

        self.life_label = QLabel("Life: 4000")
        self.life_label.setStyleSheet("color: #FF0000; font-weight: bold; font-size: 14px;")
        info_bar.addWidget(self.life_label)

        info_bar.addStretch()

        self.deck_label = QLabel("Deck: 0")
        info_bar.addWidget(self.deck_label)

        self.stone_deck_label = QLabel("Stones: 0")
        info_bar.addWidget(self.stone_deck_label)

        layout.addLayout(info_bar)

        # Will pool
        self.will_pool_widget = WillPoolWidget()
        layout.addWidget(self.will_pool_widget)

        # Ruler area
        ruler_layout = QHBoxLayout()
        ruler_layout.addWidget(QLabel("Ruler:"))
        self.ruler_widget = CardWidget(small=True)
        self.ruler_widget.clicked.connect(lambda c: self.card_clicked.emit(c, "ruler"))
        ruler_layout.addWidget(self.ruler_widget)
        ruler_layout.addStretch()
        layout.addLayout(ruler_layout)

        # Field
        self.field_zone = ZoneWidget("Field", horizontal=True, small_cards=True)
        self.field_zone.card_clicked.connect(lambda c: self.card_clicked.emit(c, "field"))
        layout.addWidget(self.field_zone)

        # Hand (hidden for opponent)
        self.hand_zone = ZoneWidget("Hand", horizontal=True, small_cards=True)
        self.hand_zone.card_clicked.connect(lambda c: self.card_clicked.emit(c, "hand"))
        layout.addWidget(self.hand_zone)

    def update_from_state(self, player_state, hide_hand: bool = False):
        """Update display from player state"""
        self.life_label.setText(f"Life: {player_state.life}")
        self.deck_label.setText(f"Deck: {len(player_state.main_deck)}")
        self.stone_deck_label.setText(f"Stones: {len(player_state.stone_deck)}")

        self.will_pool_widget.set_will_pool(player_state.will_pool)

        # Ruler
        if player_state.j_ruler:
            self.ruler_widget.set_card(player_state.j_ruler)
        elif player_state.ruler:
            self.ruler_widget.set_card(player_state.ruler)
        else:
            self.ruler_widget.set_card(None)

        # Field
        self.field_zone.set_cards(player_state.field)

        # Hand
        self.hand_zone.set_cards(player_state.hand, face_down=hide_hand)


class GameLogWidget(QTextEdit):
    """Widget for displaying game log"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(150)
        font = QFont("Monospace", 9)
        self.setFont(font)

    def log(self, message: str, color: str = None):
        if color:
            self.append(f'<span style="color: {color}">{message}</span>')
        else:
            self.append(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class ActionButtonsWidget(QFrame):
    """Widget with action buttons"""

    action_triggered = pyqtSignal(str, dict)  # action_type, params

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        self.pass_btn = QPushButton("Pass Priority")
        self.pass_btn.clicked.connect(lambda: self.action_triggered.emit("pass", {}))
        layout.addWidget(self.pass_btn)

        self.stone_btn = QPushButton("Call Stone")
        self.stone_btn.clicked.connect(lambda: self.action_triggered.emit("call_stone", {}))
        layout.addWidget(self.stone_btn)

        self.judgment_btn = QPushButton("Judgment")
        self.judgment_btn.clicked.connect(lambda: self.action_triggered.emit("judgment", {}))
        layout.addWidget(self.judgment_btn)

        self.next_phase_btn = QPushButton("Next Phase")
        self.next_phase_btn.clicked.connect(lambda: self.action_triggered.emit("next_phase", {}))
        layout.addWidget(self.next_phase_btn)

        self.resolve_btn = QPushButton("Resolve Chase")
        self.resolve_btn.clicked.connect(lambda: self.action_triggered.emit("resolve", {}))
        layout.addWidget(self.resolve_btn)

    def update_for_actions(self, legal_actions: list[dict]):
        """Enable/disable buttons based on legal actions"""
        action_types = {a["type"] for a in legal_actions}

        self.pass_btn.setEnabled("pass_priority" in action_types)
        self.stone_btn.setEnabled("call_stone" in action_types)
        self.judgment_btn.setEnabled("judgment" in action_types)


# =============================================================================
# MAIN WINDOW
# =============================================================================

class MainWindow(QMainWindow):
    """Main game window"""

    def __init__(self):
        super().__init__()
        self.engine: Optional[GameEngine] = None
        self.db: Optional[CardDatabase] = None
        self.selected_card: Optional[Card] = None
        self.human_player = 0

        self._setup_ui()
        self._setup_menus()

    def _setup_ui(self):
        self.setWindowTitle("FoWPro - Force of Will Simulator")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Top info bar
        top_bar = QHBoxLayout()
        self.turn_label = QLabel("Turn: 0")
        self.turn_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        top_bar.addWidget(self.turn_label)

        self.phase_label = QLabel("Phase: -")
        self.phase_label.setStyleSheet("font-size: 14px;")
        top_bar.addWidget(self.phase_label)

        self.priority_label = QLabel("Priority: -")
        self.priority_label.setStyleSheet("font-size: 14px;")
        top_bar.addWidget(self.priority_label)

        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # Game areas
        game_area = QSplitter(Qt.Orientation.Vertical)

        # Opponent area (top)
        self.opponent_area = PlayerAreaWidget(1, is_opponent=True)
        self.opponent_area.card_clicked.connect(self._on_opponent_card_clicked)
        game_area.addWidget(self.opponent_area)

        # Chase area (middle)
        self.chase_zone = ZoneWidget("Chase (Stack)", horizontal=True, small_cards=True)
        self.chase_zone.setMaximumHeight(150)
        game_area.addWidget(self.chase_zone)

        # Player area (bottom)
        self.player_area = PlayerAreaWidget(0)
        self.player_area.card_clicked.connect(self._on_player_card_clicked)
        game_area.addWidget(self.player_area)

        main_layout.addWidget(game_area, stretch=1)

        # Action buttons
        self.action_buttons = ActionButtonsWidget()
        self.action_buttons.action_triggered.connect(self._on_action)
        main_layout.addWidget(self.action_buttons)

        # Game log
        self.game_log = GameLogWidget()
        main_layout.addWidget(self.game_log)

        # Card detail panel
        self.card_detail = QLabel("Select a card to see details")
        self.card_detail.setWordWrap(True)
        self.card_detail.setMaximumHeight(100)
        self.card_detail.setStyleSheet("background-color: #F0F0F0; padding: 5px;")
        main_layout.addWidget(self.card_detail)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menus(self):
        menubar = self.menuBar()

        # Game menu
        game_menu = menubar.addMenu("Game")

        new_action = QAction("New Game", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_game)
        game_menu.addAction(new_action)

        load_action = QAction("Load Database", self)
        load_action.triggered.connect(self._load_database)
        game_menu.addAction(load_action)

        game_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        game_menu.addAction(quit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _new_game(self):
        """Start a new game"""
        if not self.db:
            QMessageBox.warning(self, "No Database",
                              "Please load a card database first.")
            return

        # Create test decks (for demo)
        self._create_test_game()

    def _create_test_game(self):
        """Create a test game with sample cards"""
        # Get some cards from database
        all_cards = self.db.get_all_cards()

        if not all_cards:
            QMessageBox.warning(self, "No Cards",
                              "No cards in database. Please import cards first.")
            return

        # Find rulers
        rulers = [c for c in all_cards if c.card_type == CardType.RULER]
        resonators = [c for c in all_cards if c.card_type == CardType.RESONATOR]
        stones = [c for c in all_cards if c.is_stone()]

        if not rulers or not resonators or not stones:
            # Create dummy cards
            rulers = [CardData(
                code="TEST-001", name="Test Ruler",
                card_type=CardType.RULER, attribute=Attribute.LIGHT,
                cost=WillCost(), j_ruler_code="TEST-001J"
            )]
            resonators = [CardData(
                code=f"TEST-{i:03d}", name=f"Test Resonator {i}",
                card_type=CardType.RESONATOR, attribute=Attribute.FIRE,
                cost=WillCost(fire=1), atk=500, defense=500
            ) for i in range(2, 42)]
            stones = [CardData(
                code=f"STONE-{i:03d}", name="Fire Stone",
                card_type=CardType.MAGIC_STONE, attribute=Attribute.FIRE,
                cost=WillCost()
            ) for i in range(1, 11)]

        # Build decks
        p0_deck = resonators[:40] if len(resonators) >= 40 else resonators * (40 // len(resonators) + 1)
        p0_deck = p0_deck[:40]
        p0_stones = stones[:10] if len(stones) >= 10 else stones * (10 // len(stones) + 1)
        p0_stones = p0_stones[:10]
        p0_ruler = rulers[0]

        p1_deck = p0_deck.copy()
        p1_stones = p0_stones.copy()
        p1_ruler = rulers[0] if len(rulers) < 2 else rulers[1]

        # Create engine and set up game
        self.engine = GameEngine(self.db)
        self.engine.subscribe(self._on_game_event)

        self.engine.setup_game(
            p0_deck, p0_stones, p0_ruler,
            p1_deck, p1_stones, p1_ruler
        )
        self.engine.shuffle_decks()
        self.engine.start_game(first_player=0)

        self.game_log.clear()
        self.game_log.log("Game started!", "#00AA00")

        self._update_display()

    def _load_database(self):
        """Load card database"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Card Database", "", "SQLite Database (*.db)"
        )
        if path:
            self.db = CardDatabase(path)
            count = self.db.card_count()
            self.status_bar.showMessage(f"Loaded database with {count} cards")
            self.game_log.log(f"Loaded {count} cards from database")

    def _show_about(self):
        QMessageBox.about(
            self, "About FoWPro",
            "FoWPro - Force of Will Simulator\n\n"
            "A complete Force of Will TCG simulator\n"
            "with all Grimm Cluster sets.\n\n"
            "Version 1.0.0"
        )

    def _on_game_event(self, event: GameEvent):
        """Handle game events"""
        # Log the event
        msg = f"[{event.event_type.name}]"
        if event.card:
            msg += f" {event.card.data.name}"
        if event.data:
            msg += f" {event.data}"

        color = None
        if event.event_type == EventType.DAMAGE_DEALT:
            color = "#FF0000"
        elif event.event_type == EventType.CARD_DRAWN:
            color = "#0000FF"
        elif event.event_type == EventType.PHASE_CHANGE:
            color = "#008800"

        self.game_log.log(msg, color)

        # Update display
        QTimer.singleShot(10, self._update_display)

    def _update_display(self):
        """Update all display elements"""
        if not self.engine:
            return

        # Update turn info
        self.turn_label.setText(f"Turn: {self.engine.turn_number}")
        self.phase_label.setText(f"Phase: {self.engine.current_phase.name}")
        priority_str = f"Priority: Player {self.engine.priority_player + 1}"
        if self.engine.priority_player == self.human_player:
            priority_str += " (YOU)"
        self.priority_label.setText(priority_str)

        # Update player areas
        self.player_area.update_from_state(
            self.engine.players[self.human_player], hide_hand=False
        )
        self.opponent_area.update_from_state(
            self.engine.players[1 - self.human_player], hide_hand=True
        )

        # Update chase
        chase_cards = [item.source for item in self.engine.chase]
        self.chase_zone.set_cards(chase_cards)

        # Update action buttons
        legal_actions = self.engine.get_legal_actions(self.human_player)
        self.action_buttons.update_for_actions(legal_actions)

        # Update status
        if self.engine.game_over:
            winner = "You" if self.engine.winner == self.human_player else "Opponent"
            self.status_bar.showMessage(f"Game Over! {winner} wins!")
        else:
            self.status_bar.showMessage(
                f"Turn {self.engine.turn_number} - {self.engine.current_phase.name}"
            )

    def _on_player_card_clicked(self, card: Card, zone: str):
        """Handle click on player's card"""
        self.selected_card = card
        self._show_card_detail(card)

        if not card:
            return

        # Determine possible actions
        if zone == "hand":
            self._try_play_card(card)
        elif zone == "field":
            if card.data.is_stone() and not card.is_rested:
                self._try_produce_will(card)
            elif (card.data.is_resonator() or
                  card.data.card_type == CardType.J_RULER):
                self._try_attack_with(card)
        elif zone == "ruler":
            self._try_judgment()

    def _on_opponent_card_clicked(self, card: Card, zone: str):
        """Handle click on opponent's card"""
        self._show_card_detail(card)

        # If we have an attacker selected, this might be a target
        if self.selected_card and zone == "field":
            # Could be attack target
            pass

    def _show_card_detail(self, card: Optional[Card]):
        """Show card details in the detail panel"""
        if not card:
            self.card_detail.setText("No card selected")
            return

        data = card.data
        text = f"<b>{data.name}</b> ({data.code})<br>"
        text += f"Type: {data.card_type.value}<br>"
        text += f"Attribute: {data.attribute.name}<br>"
        text += f"Cost: {data.cost}<br>"
        if data.atk or data.defense:
            text += f"ATK/DEF: {card.effective_atk}/{card.effective_def}<br>"
        if data.ability_text:
            text += f"<br><i>{data.ability_text[:200]}...</i>"

        self.card_detail.setText(text)

    def _try_play_card(self, card: Card):
        """Try to play a card from hand"""
        if not self.engine:
            return

        if self.engine.priority_player != self.human_player:
            self.status_bar.showMessage("Not your priority!")
            return

        success = self.engine.play_card(self.human_player, card)
        if success:
            self.game_log.log(f"Played {card.data.name}", "#0000FF")
        else:
            self.status_bar.showMessage(f"Cannot play {card.data.name}")

        self._update_display()

    def _try_produce_will(self, stone: Card):
        """Try to produce will from a stone"""
        if not self.engine:
            return

        success = self.engine.produce_will(self.human_player, stone)
        if success:
            self.game_log.log(f"Produced will from {stone.data.name}", "#FFD700")
        else:
            self.status_bar.showMessage(f"Cannot use {stone.data.name}")

        self._update_display()

    def _try_attack_with(self, card: Card):
        """Try to attack with a creature"""
        if not self.engine:
            return

        if self.engine.priority_player != self.human_player:
            self.status_bar.showMessage("Not your priority!")
            return

        # For now, attack opponent directly
        success = self.engine.declare_attack(
            self.human_player, card, target_player=1 - self.human_player
        )
        if success:
            self.game_log.log(f"{card.data.name} attacks!", "#FF0000")
        else:
            self.status_bar.showMessage(f"{card.data.name} cannot attack")

        self._update_display()

    def _try_judgment(self):
        """Try to perform Judgment"""
        if not self.engine:
            return

        success = self.engine.perform_judgment(self.human_player)
        if success:
            self.game_log.log("Judgment!", "#FFD700")
        else:
            self.status_bar.showMessage("Cannot perform Judgment")

        self._update_display()

    def _on_action(self, action_type: str, params: dict):
        """Handle action button clicks"""
        if not self.engine:
            return

        if action_type == "pass":
            if self.engine.pass_priority(self.human_player):
                self.engine.advance_phase()

        elif action_type == "call_stone":
            self.engine.call_stone(self.human_player)

        elif action_type == "judgment":
            self._try_judgment()

        elif action_type == "next_phase":
            self.engine.advance_phase()

        elif action_type == "resolve":
            self.engine.resolve_full_chase()

        self._update_display()


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_gui():
    """Run the GUI application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Dark palette (optional)
    # palette = QPalette()
    # palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    # app.setPalette(palette)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
