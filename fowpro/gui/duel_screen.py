"""
FoWPro Duel Screen
==================
Professional duel interface with YGOPro-quality appearance.
"""

import json
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QGridLayout, QTextEdit,
    QSizePolicy, QGraphicsDropShadowEffect, QMessageBox, QComboBox,
    QDialog, QDialogButtonBox, QMenu, QLineEdit, QStackedWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QRectF, QMimeData, QPoint
from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QFont, QLinearGradient, QBrush, QPen, QTransform,
    QKeySequence, QShortcut, QDrag
)

from .styles import Colors, Fonts
from .assets import get_asset_manager
from .choice_dialogs import (
    TargetSelectionDialog, ModalChoiceDialog, YesNoDialog,
    XValueDialog, CardListDialog, AttributeChoiceDialog
)


# =============================================================================
# CARD WIDGETS
# =============================================================================

class DuelCardWidget(QFrame):
    """Card widget for the duel field - shows actual card image"""

    clicked = pyqtSignal(object)  # Card
    double_clicked = pyqtSignal(object)
    hovered = pyqtSignal(object)  # Card - for preview on hover
    context_menu_requested = pyqtSignal(object, object)  # Card, QPoint (global pos)

    ATTRIBUTE_COLORS = {
        'LIGHT': "#ffd700",
        'FIRE': "#ff4500",
        'WATER': "#1e90ff",
        'WIND': "#32cd32",
        'DARKNESS': "#9932cc",
        'VOID': "#808080",
        'NONE': "#606060",
    }

    def __init__(self, card=None, face_down: bool = False, small: bool = False, draggable: bool = False, parent=None):
        super().__init__(parent)
        self.card = card
        self.face_down = face_down
        self.small = small
        self.draggable = draggable
        self._selected = False
        self._drag_start_pos = None
        self._did_drag = False  # Track if drag occurred (don't emit click)
        self.setMouseTracking(True)

        # Store base dimensions - INCREASED SIZES
        if small:
            self._base_w, self._base_h = 90, 126  # Small cards (stones, hand)
        else:
            self._base_w, self._base_h = 120, 168  # Normal cards (resonators)

        self._update_size()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _update_size(self):
        """Update widget size based on rested state"""
        is_rested = self.card.is_rested if self.card else False
        if is_rested:
            # Swap dimensions for sideways card
            self.setFixedSize(self._base_h, self._base_w)
        else:
            self.setFixedSize(self._base_w, self._base_h)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Card image label (primary display)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, stretch=1)

        self._update_display()

    def _update_display(self):
        # Get size for image
        img_w = self.width() - 4
        img_h = self.height() - 4

        if self.face_down:
            # Show card back
            self.image_label.setText("???")
            self.image_label.setStyleSheet(f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.PRIMARY}40, stop:1 {Colors.BG_DARK});
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                border-radius: 3px;
            """)
            self.setStyleSheet(f"""
                DuelCardWidget {{
                    background-color: {Colors.BG_MEDIUM};
                    border: 2px solid {Colors.BORDER_MEDIUM};
                    border-radius: 4px;
                }}
            """)
            return

        if not self.card:
            self.image_label.setText("")
            self.setStyleSheet(f"""
                DuelCardWidget {{
                    background-color: {Colors.BG_MEDIUM};
                    border: 2px solid {Colors.BORDER_MEDIUM};
                    border-radius: 4px;
                }}
            """)
            return

        # Try to load card image
        assets = get_asset_manager()
        card_path = assets.base_path / "cards" / f"{self.card.data.code}.jpg"

        # Check if card is rested (tapped) - need to rotate 90 degrees
        is_rested = self.card.is_rested if self.card else False

        if card_path.exists():
            # Load pixmap at appropriate size
            if is_rested:
                # For rested cards, swap dimensions and rotate
                pixmap = assets.get_card_image(self.card.data.code, QSize(img_h, img_w))
                # Rotate 90 degrees clockwise
                transform = QTransform().rotate(90)
                pixmap = pixmap.transformed(transform)
            else:
                pixmap = assets.get_card_image(self.card.data.code, QSize(img_w, img_h))
            self.image_label.setPixmap(pixmap)
            self.image_label.setStyleSheet("background: transparent;")
        else:
            # Fallback to text display
            name = self.card.data.name
            max_len = 6 if self.small else 8
            if len(name) > max_len:
                name = name[:max_len-1] + "…"
            display_text = f"[R] {name}" if is_rested else name
            self.image_label.setText(display_text)
            self.image_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 8px; background: transparent;")

        # Border color based on attribute and selection
        attr = self.card.data.attribute.name if self.card.data.attribute else 'VOID'
        attr_color = self.ATTRIBUTE_COLORS.get(attr, Colors.BORDER_MEDIUM)
        border_color = Colors.ACCENT if self._selected else attr_color

        # Rested cards get a dimmed background
        bg_extra = ""
        if is_rested:
            bg_extra = f"background-color: {Colors.BG_DARK}60;"

        self.setStyleSheet(f"""
            DuelCardWidget {{
                {bg_extra}
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
        """)

    def set_card(self, card):
        self.card = card
        self._update_size()
        self._update_display()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._did_drag = False
            # Don't emit clicked here - wait for release to allow drag
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.draggable or not self.card or self.face_down:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self._drag_start_pos:
            return

        # Check if we've moved enough to start a drag
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        # Mark that we're dragging (don't emit click on release)
        self._did_drag = True

        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        # Store card UID for identification
        mime_data.setText(f"card:{self.card.uid}")
        drag.setMimeData(mime_data)

        # Create a pixmap of the card for the drag image
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(72, 100, Qt.AspectRatioMode.KeepAspectRatio))
        drag.setHotSpot(QPoint(36, 50))

        # Execute drag
        drag.exec(Qt.DropAction.MoveAction)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only emit clicked if we didn't drag
            if not self._did_drag and self._drag_start_pos is not None:
                self.clicked.emit(self.card)
        self._drag_start_pos = None
        self._did_drag = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.card)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        """Emit hovered signal when mouse enters card"""
        if self.card and not self.face_down:
            self.hovered.emit(self.card)
        super().enterEvent(event)

    def contextMenuEvent(self, event):
        """Emit context menu signal for right-click"""
        if self.card and not self.face_down:
            self.context_menu_requested.emit(self.card, event.globalPos())
        event.accept()


class ZoneWidget(QFrame):
    """Widget for a game zone"""

    card_clicked = pyqtSignal(object)
    card_hovered = pyqtSignal(object)
    card_context_menu = pyqtSignal(object, object)  # Card, QPoint
    card_dropped = pyqtSignal(str, int)  # card_uid, drop_index (-1 for end)
    card_reordered = pyqtSignal(str, int)  # card_uid, new_index

    def __init__(self, zone_name: str, horizontal: bool = True, max_cards: int = 10,
                 show_label: bool = True, centered: bool = False,
                 accept_drops: bool = False, draggable_cards: bool = False,
                 peek_from_top: bool = False, small_cards: bool = True, parent=None):
        super().__init__(parent)
        self.zone_name = zone_name
        self.horizontal = horizontal
        self.max_cards = max_cards
        self.show_label = show_label and not peek_from_top  # No label when peeking
        self.centered = centered
        self.accept_drops_flag = accept_drops
        self.draggable_cards = draggable_cards
        self.peek_from_top = peek_from_top
        self.small_cards = small_cards
        self.cards = []
        self._widgets: List[DuelCardWidget] = []

        self._setup_ui()

        if accept_drops:
            self.setAcceptDrops(True)

    def _setup_ui(self):
        if self.peek_from_top:
            # Minimal styling for peek mode - cards extend upward out of frame
            self.setStyleSheet("background: transparent; border: none;")
        else:
            self.setStyleSheet(f"""
                ZoneWidget {{
                    background-color: {Colors.SURFACE}40;
                    border: 1px solid {Colors.BORDER_DARK};
                    border-radius: 6px;
                }}
            """)

        layout = QVBoxLayout(self)

        if self.peek_from_top:
            # Cards at top, extend downward (clipped) - shows tops of cards peeking in
            layout.setContentsMargins(6, 0, 6, 0)
        else:
            layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Zone label (optional)
        self.label = QLabel(self.zone_name)
        self.label.setFont(Fonts.small())
        self.label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        if self.show_label:
            layout.addWidget(self.label)

        # Cards container
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")

        if self.horizontal:
            self.cards_layout = QHBoxLayout(self.cards_container)
        else:
            self.cards_layout = QVBoxLayout(self.cards_container)

        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(4)
        if self.centered:
            self.cards_layout.addStretch()  # Left stretch for centering
        self.cards_layout.addStretch()  # Right stretch

        if self.peek_from_top:
            # Cards at top, bottoms extend down and get clipped
            layout.addWidget(self.cards_container, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
            layout.addStretch()  # Push everything to top
        else:
            layout.addWidget(self.cards_container, stretch=1)

    def set_cards(self, cards: list, face_down: bool = False):
        """Update the cards in this zone"""
        self.cards = cards

        # Clear old widgets
        for widget in self._widgets:
            widget.setParent(None)
            widget.deleteLater()
        self._widgets.clear()

        # Add new widgets
        for card in cards[:self.max_cards]:
            widget = DuelCardWidget(card, face_down=face_down, small=self.small_cards,
                                   draggable=self.draggable_cards)
            widget.clicked.connect(self.card_clicked.emit)
            widget.hovered.connect(self.card_hovered.emit)
            widget.context_menu_requested.connect(self.card_context_menu.emit)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, widget)
            self._widgets.append(widget)

        self.label.setText(f"{self.zone_name} ({len(cards)})")

    def dragEnterEvent(self, event):
        """Accept card drags"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("card:"):
                event.acceptProposedAction()
                # Highlight zone
                self.setStyleSheet(f"""
                    ZoneWidget {{
                        background-color: {Colors.PRIMARY}40;
                        border: 2px solid {Colors.PRIMARY};
                        border-radius: 6px;
                    }}
                """)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Remove highlight when drag leaves"""
        self.setStyleSheet(f"""
            ZoneWidget {{
                background-color: {Colors.SURFACE}40;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

    def dropEvent(self, event):
        """Handle card drop"""
        self.setStyleSheet(f"""
            ZoneWidget {{
                background-color: {Colors.SURFACE}40;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("card:"):
                card_uid = text.split(":", 1)[1]

                # Calculate drop index based on position
                drop_index = -1
                drop_pos = event.position().toPoint()
                for i, widget in enumerate(self._widgets):
                    widget_center = widget.pos().x() + widget.width() // 2
                    if drop_pos.x() < widget_center:
                        drop_index = i
                        break

                # Check if this is a reorder (card from same zone) or external drop
                is_reorder = any(w.card and w.card.uid == card_uid for w in self._widgets)
                if is_reorder:
                    self.card_reordered.emit(card_uid, drop_index)
                else:
                    self.card_dropped.emit(card_uid, drop_index)

                event.acceptProposedAction()
                return
        event.ignore()


class WillOrbWidget(QWidget):
    """Single will orb - a colored circle"""

    WILL_COLORS = {
        'light': "#ffd700",
        'fire': "#ff4500",
        'water': "#1e90ff",
        'wind': "#32cd32",
        'darkness': "#9932cc",
        'void': "#808080",
    }

    def __init__(self, will_type: str, parent=None):
        super().__init__(parent)
        self.will_type = will_type
        self.setFixedSize(20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(self.WILL_COLORS.get(self.will_type, "#808080"))

        # Draw orb with gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(150))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawEllipse(1, 1, self.width() - 2, self.height() - 2)


class WillPoolWidget(QFrame):
    """Widget displaying will pool as colored orbs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._orbs = []
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            WillPoolWidget {{
                background-color: {Colors.SURFACE}60;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
            }}
        """)
        self.setMinimumHeight(32)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(4)
        self.layout.addStretch()

    def set_will_pool(self, pool):
        """Update will pool display with orbs"""
        # Clear existing orbs
        for orb in self._orbs:
            orb.setParent(None)
            orb.deleteLater()
        self._orbs.clear()

        # Add orbs for each will type (in order: L, R, U, G, B, V)
        will_counts = [
            ('light', pool.light),
            ('fire', pool.fire),
            ('water', pool.water),
            ('wind', pool.wind),
            ('darkness', pool.darkness),
            ('void', pool.void),
        ]

        for will_type, count in will_counts:
            for _ in range(count):
                orb = WillOrbWidget(will_type)
                self.layout.insertWidget(self.layout.count() - 1, orb)
                self._orbs.append(orb)


class FieldDropZone(QFrame):
    """Drop zone for playing cards onto the field"""

    card_dropped = pyqtSignal(str)  # card_uid

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._default_style = f"background-color: {Colors.SURFACE}30; border-radius: 4px;"
        self.setStyleSheet(self._default_style)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("card:"):
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                    background-color: {Colors.SUCCESS}40;
                    border: 2px dashed {Colors.SUCCESS};
                    border-radius: 4px;
                """)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event):
        self.setStyleSheet(self._default_style)
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("card:"):
                card_uid = text.split(":", 1)[1]
                self.card_dropped.emit(card_uid)
                event.acceptProposedAction()
                return
        event.ignore()


class PlayerAreaWidget(QFrame):
    """Widget for one player's game area"""

    card_clicked = pyqtSignal(object, str)  # card, zone
    card_hovered = pyqtSignal(object)  # card - for preview
    card_context_menu = pyqtSignal(object, str, object)  # card, zone, QPoint
    ruler_tapped = pyqtSignal()  # for calling stones
    hand_reordered = pyqtSignal(str, int)  # card_uid, new_index
    card_dropped_on_field = pyqtSignal(str)  # card_uid - for playing cards by drag

    def __init__(self, player_index: int, is_opponent: bool = False, parent=None):
        super().__init__(parent)
        self.player_index = player_index
        self.is_opponent = is_opponent
        self._stone_widgets = []
        self._resonator_widgets = []

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            PlayerAreaWidget {{
                background-color: {Colors.BG_DARK}80;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        if self.is_opponent:
            layout.setContentsMargins(8, 0, 8, 4)  # No top margin - hand touches top edge
        else:
            layout.setContentsMargins(8, 4, 8, 0)  # No bottom margin - hand touches bottom edge
        layout.setSpacing(4)

        # Hand zone for opponent (peeks from top - only bottom portion visible)
        if self.is_opponent:
            self.hand_zone = ZoneWidget("Hand", horizontal=True, max_cards=10, centered=True,
                                        peek_from_top=True, show_label=False)
            self.hand_zone.card_clicked.connect(lambda c: self.card_clicked.emit(c, "hand"))
            self.hand_zone.card_hovered.connect(self.card_hovered.emit)
            self.hand_zone.card_context_menu.connect(
                lambda c, pos: self.card_context_menu.emit(c, "hand", pos))
            self.hand_zone.setFixedHeight(50)  # Only show bottom ~40% of cards (126px cards)
            layout.addWidget(self.hand_zone)

        # Info bar with BIGGER life total
        info_bar = QHBoxLayout()

        self.name_label = QLabel(f"Player {self.player_index + 1}")
        self.name_label.setFont(Fonts.subheading())
        self.name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        info_bar.addWidget(self.name_label)

        # Life label - MUCH BIGGER (use stylesheet font-size to override global)
        self.life_label = QLabel("4000")
        self.life_label.setStyleSheet(f"""
            color: {Colors.ERROR};
            background: transparent;
            min-width: 80px;
            font-size: 32px;
            font-weight: bold;
        """)
        info_bar.addWidget(self.life_label)

        info_bar.addStretch()

        self.deck_label = QLabel("Deck: 0")
        self.deck_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        info_bar.addWidget(self.deck_label)

        self.stone_deck_label = QLabel("Stone Deck: 0")
        self.stone_deck_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        info_bar.addWidget(self.stone_deck_label)

        layout.addLayout(info_bar)

        # Main field area: Ruler on left, field rows on right
        field_area = QHBoxLayout()
        field_area.setSpacing(8)

        # Ruler column
        ruler_frame = QFrame()
        ruler_frame.setStyleSheet(f"""
            background-color: {Colors.SURFACE}40;
            border: 1px solid {Colors.BORDER_DARK};
            border-radius: 4px;
        """)
        ruler_layout = QVBoxLayout(ruler_frame)
        ruler_layout.setContentsMargins(4, 4, 4, 4)
        ruler_layout.setSpacing(4)

        self.ruler_widget = DuelCardWidget(small=False)
        self.ruler_widget.clicked.connect(self._on_ruler_clicked)
        self.ruler_widget.hovered.connect(self.card_hovered.emit)
        self.ruler_widget.context_menu_requested.connect(
            lambda c, pos: self.card_context_menu.emit(c, "ruler", pos))
        ruler_layout.addWidget(self.ruler_widget)
        ruler_layout.addStretch()

        field_area.addWidget(ruler_frame)

        # Field rows container (stones back, resonators front)
        field_rows = QVBoxLayout()
        field_rows.setSpacing(8)  # Space between resonator and stone rows

        # Front row: Resonators (centered, closer to opponent)
        # Use FieldDropZone for player to accept card drops
        if self.is_opponent:
            self.resonators_container = QWidget()
            self.resonators_container.setStyleSheet(f"background-color: {Colors.SURFACE}30; border-radius: 4px;")
            # Opponent zones are smaller - just for viewing
            self.resonators_container.setFixedHeight(100)
        else:
            self.resonators_container = FieldDropZone()
            self.resonators_container.card_dropped.connect(self.card_dropped_on_field.emit)
            # Player zones need full height for interaction
            self.resonators_container.setFixedHeight(176)  # 168 + padding
        self.resonators_layout = QHBoxLayout(self.resonators_container)
        self.resonators_layout.setContentsMargins(4, 4, 4, 4)
        self.resonators_layout.setSpacing(4)
        self.resonators_layout.addStretch()
        self.resonators_layout.addStretch()
        field_rows.addWidget(self.resonators_container)

        # Back row: Stones with will pool in bottom-left
        self.stones_container = QWidget()
        self.stones_container.setStyleSheet(f"background-color: {Colors.SURFACE}20; border-radius: 4px;")
        if self.is_opponent:
            self.stones_container.setFixedHeight(80)  # Smaller for opponent
        else:
            self.stones_container.setFixedHeight(134)  # 126 + padding for player
        stones_outer_layout = QHBoxLayout(self.stones_container)
        stones_outer_layout.setContentsMargins(4, 4, 4, 4)
        stones_outer_layout.setSpacing(8)

        # Will pool on the left
        self.will_pool_widget = WillPoolWidget()
        stones_outer_layout.addWidget(self.will_pool_widget, alignment=Qt.AlignmentFlag.AlignBottom)

        # Stones in the center (with stretches for centering)
        self.stones_layout = QHBoxLayout()
        self.stones_layout.setSpacing(4)
        self.stones_layout.addStretch()
        self.stones_layout.addStretch()
        stones_outer_layout.addLayout(self.stones_layout, stretch=1)

        field_rows.addWidget(self.stones_container)

        field_area.addLayout(field_rows, stretch=1)
        layout.addLayout(field_area, stretch=1)

        # Hand zone (centered) - only for player, opponent's hand is at top
        if not self.is_opponent:
            self.hand_zone = ZoneWidget("Hand", horizontal=True, max_cards=10, centered=True,
                                        accept_drops=True, draggable_cards=True, small_cards=False)
            self.hand_zone.card_clicked.connect(lambda c: self.card_clicked.emit(c, "hand"))
            self.hand_zone.card_hovered.connect(self.card_hovered.emit)
            self.hand_zone.card_context_menu.connect(
                lambda c, pos: self.card_context_menu.emit(c, "hand", pos))
            self.hand_zone.card_reordered.connect(self._on_hand_reordered)
            self.hand_zone.setMinimumHeight(185)  # Cards 168px + label + padding
            layout.addWidget(self.hand_zone, stretch=1)  # Can expand if space available

    def _on_ruler_clicked(self, card):
        """Handle ruler click - call stone if ruler is untapped, show context menu if tapped"""
        self.card_clicked.emit(card, "ruler")
        if card:
            if not card.is_rested:
                # Untapped ruler = call stone
                self.ruler_tapped.emit()
            else:
                # Tapped ruler = show context menu for abilities
                pos = self.ruler_widget.mapToGlobal(self.ruler_widget.rect().center())
                self.card_context_menu.emit(card, "ruler", pos)

    def _set_field_cards(self, stones: list, resonators: list):
        """Update field with separate stone and resonator rows"""
        # Clear stones
        for widget in self._stone_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self._stone_widgets.clear()

        # Clear resonators
        for widget in self._resonator_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self._resonator_widgets.clear()

        # Add stone widgets (centered)
        insert_pos = 1  # After first stretch
        for card in stones:
            widget = DuelCardWidget(card, small=True)
            widget.clicked.connect(lambda checked=False, c=card: self.card_clicked.emit(c, "stone"))
            widget.hovered.connect(self.card_hovered.emit)
            widget.context_menu_requested.connect(
                lambda c, pos: self.card_context_menu.emit(c, "stone", pos))
            self.stones_layout.insertWidget(insert_pos, widget)
            self._stone_widgets.append(widget)
            insert_pos += 1

        # Add resonator widgets (centered)
        insert_pos = 1
        for card in resonators:
            widget = DuelCardWidget(card, small=True)
            widget.clicked.connect(lambda checked=False, c=card: self.card_clicked.emit(c, "resonator"))
            widget.hovered.connect(self.card_hovered.emit)
            widget.context_menu_requested.connect(
                lambda c, pos: self.card_context_menu.emit(c, "resonator", pos))
            self.resonators_layout.insertWidget(insert_pos, widget)
            self._resonator_widgets.append(widget)
            insert_pos += 1

    def update_from_state(self, player_state, hide_hand: bool = False):
        """Update display from player state"""
        self.life_label.setText(str(player_state.life))
        self.deck_label.setText(f"Deck: {len(player_state.main_deck)}")
        self.stone_deck_label.setText(f"Stone Deck: {len(player_state.stone_deck)}")

        self.will_pool_widget.set_will_pool(player_state.will_pool)

        # Ruler
        if player_state.j_ruler:
            self.ruler_widget.set_card(player_state.j_ruler)
        elif player_state.ruler:
            self.ruler_widget.set_card(player_state.ruler)
        else:
            self.ruler_widget.set_card(None)

        # Separate field into stones and resonators
        from ..models import CardType
        stones = [c for c in player_state.field if c.data.is_stone()]
        resonators = [c for c in player_state.field if c.data.card_type == CardType.RESONATOR]
        other = [c for c in player_state.field if not c.data.is_stone() and c.data.card_type != CardType.RESONATOR]
        # Add other permanents to resonator row for now
        resonators.extend(other)

        self._set_field_cards(stones, resonators)

        # Hand
        self.hand_zone.set_cards(player_state.hand, face_down=hide_hand)

    def _on_hand_reordered(self, card_uid: str, new_index: int):
        """Forward hand reorder to parent"""
        self.hand_reordered.emit(card_uid, new_index)


# =============================================================================
# MAIN DUEL SCREEN
# =============================================================================

class DuelScreen(QWidget):
    """Main duel screen"""

    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.engine = None
        self.human_player = 0
        self.selected_card = None
        self._background: QPixmap = None
        self._game_over_shown = False
        self._pending_will = []  # Track will produced for undo: [(attribute, amount, stone_card), ...]

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main content
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 0, 8, 0)  # No top/bottom margin - zones touch edges
        content_layout.setSpacing(0)  # No spacing - game_area fills vertically

        # Main game area (surrender button moved to info panel)
        game_area = QHBoxLayout()

        # Left side - game field
        field_area = QVBoxLayout()
        field_area.setSpacing(2)  # Minimal spacing between areas

        # Opponent area (smaller - just for viewing)
        self.opponent_area = PlayerAreaWidget(1, is_opponent=True)
        self.opponent_area.card_clicked.connect(self._on_opponent_card_clicked)
        self.opponent_area.card_hovered.connect(self._on_card_hovered)
        field_area.addWidget(self.opponent_area, stretch=1)

        # CENTER ZONE - Turn info, phase, combat indicator, chase, buttons
        center_zone = self._create_center_zone()
        center_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        field_area.addWidget(center_zone)

        # Player area (larger - has hand zone, needs more space)
        self.player_area = PlayerAreaWidget(0)
        self.player_area.card_clicked.connect(self._on_player_card_clicked)
        self.player_area.card_hovered.connect(self._on_card_hovered)
        self.player_area.ruler_tapped.connect(self._on_call_stone)
        self.player_area.card_context_menu.connect(self._show_card_context_menu)
        self.player_area.card_dropped_on_field.connect(self._on_card_dropped_to_field)
        self.player_area.hand_reordered.connect(self._on_hand_reordered)
        field_area.addWidget(self.player_area, stretch=3)  # Player gets 3x opponent space

        game_area.addLayout(field_area, stretch=3)

        # Right side - info panel
        info_panel = self._create_info_panel()
        game_area.addWidget(info_panel)

        content_layout.addLayout(game_area, stretch=1)

        layout.addWidget(content)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts - MTGO style"""
        # Spacebar = Pass priority (F2 equivalent)
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self._pass_priority)

        # N = Next phase (skip remaining priority passes)
        # Note: Enter removed to allow chat input to work
        n_shortcut = QShortcut(QKeySequence(Qt.Key.Key_N), self)
        n_shortcut.activated.connect(self._on_next_phase)

    def _pass_priority(self):
        """Pass priority (spacebar) - MTGO F2 equivalent"""
        if not self.engine or self.engine.game_over:
            return

        if self.engine.priority_player != self.human_player:
            self._log("Not your priority", Colors.WARNING)
            return

        # pass_priority returns True if both players have now passed
        both_passed = self.engine.pass_priority(self.human_player)
        self._log("Priority passed", Colors.TEXT_SECONDARY)

        if both_passed:
            # Both passed - advance phase
            self.engine.advance_phase()

        self._update_display()

    def _create_center_zone(self) -> QWidget:
        """Create the center zone with turn info on left, chase on right"""
        zone = QFrame()
        zone.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE}40;
                border-radius: 8px;
            }}
        """)

        # Horizontal layout: info/buttons centered, chase on right
        main_layout = QHBoxLayout(zone)
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(12)

        # Left side: Turn info and buttons (all on one line, centered)
        left_side = QHBoxLayout()
        left_side.setSpacing(16)

        # Turn info - BIG (use stylesheet font-size to override global)
        self.turn_label = QLabel("Turn 1")
        self.turn_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; font-size: 16px; font-weight: bold;")

        self.turn_player_label = QLabel("Your Turn")
        self.turn_player_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent; font-size: 16px; font-weight: bold;")

        # Phase - prominent
        self.phase_label = QLabel("MAIN")
        self.phase_label.setStyleSheet(f"color: {Colors.ACCENT}; background: transparent; font-size: 14px; font-weight: bold;")

        # Combat indicator (hidden by default) - BIG AND PROMINENT
        self.combat_indicator = QLabel("⚔ COMBAT ⚔")
        self.combat_indicator.setStyleSheet(f"""
            color: {Colors.ERROR};
            background-color: {Colors.ERROR}40;
            padding: 6px 16px;
            border-radius: 6px;
            border: 2px solid {Colors.ERROR};
            font-size: 24px;
            font-weight: bold;
        """)
        self.combat_indicator.setVisible(False)

        # Priority indicator
        self.priority_label = QLabel("Your Priority")
        self.priority_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; font-size: 12px;")

        # Buttons
        self.pass_btn = QPushButton("Pass [Space]")
        self.pass_btn.setToolTip("Pass priority - both passing advances phase")
        self.pass_btn.clicked.connect(self._on_pass)

        self.next_btn = QPushButton("Next [N]")
        self.next_btn.setToolTip("Skip to next phase")
        self.next_btn.clicked.connect(self._on_next_phase)

        self.resolve_btn = QPushButton("Resolve")
        self.resolve_btn.setToolTip("Resolve top of chase")
        self.resolve_btn.clicked.connect(self._on_resolve)

        # Add all to horizontal layout, centered
        left_side.addStretch()
        left_side.addWidget(self.turn_label)
        left_side.addWidget(self.turn_player_label)
        left_side.addWidget(self.phase_label)
        left_side.addWidget(self.combat_indicator)
        left_side.addWidget(self.priority_label)
        left_side.addSpacing(20)
        left_side.addWidget(self.pass_btn)
        left_side.addWidget(self.next_btn)
        left_side.addWidget(self.resolve_btn)
        left_side.addStretch()

        main_layout.addLayout(left_side, stretch=1)

        # Right side: Chase zone (vertical, 3 cards wide)
        chase_frame = QFrame()
        chase_frame.setFixedWidth(240)  # ~3 small cards wide
        chase_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE}30;
                border: 1px dashed {Colors.BORDER_DARK};
                border-radius: 4px;
            }}
        """)
        chase_layout = QVBoxLayout(chase_frame)
        chase_layout.setContentsMargins(4, 4, 4, 4)

        chase_label = QLabel("Chase")
        chase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chase_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        chase_layout.addWidget(chase_label)

        self.chase_zone = ZoneWidget("", horizontal=True, max_cards=3, show_label=False, centered=True)
        self.chase_zone.setMaximumHeight(90)
        self.chase_zone.card_hovered.connect(self._on_card_hovered)
        chase_layout.addWidget(self.chase_zone)

        main_layout.addWidget(chase_frame)

        return zone

    def _create_info_panel(self) -> QWidget:
        """Create the side info panel"""
        panel = QFrame()
        panel.setFixedWidth(320)  # Wide enough for 300px card + padding
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Card preview - MUCH LARGER for legibility
        self.card_preview = QLabel()
        self.card_preview.setFixedSize(300, 420)  # Large enough to read text
        self.card_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_preview.setStyleSheet(f"""
            background-color: {Colors.BG_MEDIUM};
            border: 2px solid {Colors.BORDER_MEDIUM};
            border-radius: 6px;
        """)
        layout.addWidget(self.card_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Card info - compact, no label
        self.card_info = QLabel("Select a card")
        self.card_info.setWordWrap(True)
        self.card_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; font-size: 11px;")
        layout.addWidget(self.card_info)

        # Ability text - expands to fill space
        self.card_ability_text = QTextEdit()
        self.card_ability_text.setReadOnly(True)
        self.card_ability_text.setMinimumHeight(80)
        self.card_ability_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 11px;
                padding: 6px;
            }}
        """)
        layout.addWidget(self.card_ability_text, stretch=1)

        # Tab buttons for switching panel content
        tab_row = QHBoxLayout()
        tab_row.setSpacing(2)

        tab_style = f"""
            QPushButton {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_MEDIUM};
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """

        self.log_tab_btn = QPushButton("Log")
        self.log_tab_btn.setCheckable(True)
        self.log_tab_btn.setChecked(True)
        self.log_tab_btn.setStyleSheet(tab_style)
        self.log_tab_btn.clicked.connect(lambda: self._switch_panel_tab(0))
        tab_row.addWidget(self.log_tab_btn)

        self.chat_tab_btn = QPushButton("Chat")
        self.chat_tab_btn.setCheckable(True)
        self.chat_tab_btn.setStyleSheet(tab_style)
        self.chat_tab_btn.clicked.connect(lambda: self._switch_panel_tab(1))
        tab_row.addWidget(self.chat_tab_btn)

        self.settings_tab_btn = QPushButton("Settings")
        self.settings_tab_btn.setCheckable(True)
        self.settings_tab_btn.setStyleSheet(tab_style)
        self.settings_tab_btn.clicked.connect(lambda: self._switch_panel_tab(2))
        tab_row.addWidget(self.settings_tab_btn)

        self._panel_tab_buttons = [self.log_tab_btn, self.chat_tab_btn, self.settings_tab_btn]
        layout.addLayout(tab_row)

        # Stacked widget for tab content
        self.panel_stack = QStackedWidget()
        self.panel_stack.setMinimumHeight(100)

        # Tab 0: Game Log
        self.game_log = QTextEdit()
        self.game_log.setReadOnly(True)
        self.game_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                font-family: "Consolas", monospace;
                font-size: 10px;
            }}
        """)
        self.panel_stack.addWidget(self.game_log)

        # Tab 1: Chat (placeholder for multiplayer)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setStyleSheet(self.game_log.styleSheet())
        self.chat_log.setPlaceholderText("Chat messages will appear here...")
        chat_layout.addWidget(self.chat_log, stretch=1)
        chat_input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.setStyleSheet(f"background-color: {Colors.BG_MEDIUM}; border: 1px solid {Colors.BORDER_DARK}; border-radius: 4px; padding: 4px; color: {Colors.TEXT_PRIMARY};")
        self.chat_input.returnPressed.connect(self._send_chat)
        chat_input_row.addWidget(self.chat_input)
        chat_layout.addLayout(chat_input_row)
        self.panel_stack.addWidget(chat_widget)

        # Tab 2: Settings
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(4, 4, 4, 4)
        settings_layout.setSpacing(8)

        self.auto_pass_check = QCheckBox("Auto-pass when no plays")
        self.auto_pass_check.setChecked(True)
        self.auto_pass_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        settings_layout.addWidget(self.auto_pass_check)

        self.auto_yield_check = QCheckBox("Auto-yield to opponent")
        self.auto_yield_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        settings_layout.addWidget(self.auto_yield_check)

        self.show_hints_check = QCheckBox("Show play hints")
        self.show_hints_check.setChecked(True)
        self.show_hints_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        settings_layout.addWidget(self.show_hints_check)

        settings_layout.addStretch()
        self.panel_stack.addWidget(settings_widget)

        layout.addWidget(self.panel_stack, stretch=2)

        # Bottom buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        surrender_btn = QPushButton("Surrender")
        surrender_btn.clicked.connect(self._on_surrender)
        surrender_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ERROR}40;
                border: 1px solid {Colors.ERROR};
                border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.ERROR}80;
            }}
        """)
        btn_row.addWidget(surrender_btn)

        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self._on_exit_game)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_MEDIUM};
            }}
        """)
        btn_row.addWidget(exit_btn)

        layout.addLayout(btn_row)

        return panel


    # =========================================================================
    # GAME LOGIC
    # =========================================================================

    def start_new_game(self):
        """Start a new game"""
        if not self.main_window:
            return

        db = self.main_window.get_database()
        if not db:
            return

        from ..engine import GameEngine, EventType
        from ..models import CardType

        # Try to load player deck from config/default
        p0_deck, p0_stones, p0_ruler = self._load_player_deck(db)

        if not p0_deck or not p0_stones or not p0_ruler:
            QMessageBox.warning(self, "No Deck",
                "No deck found. Please create a deck in the Deck Editor and set it as default.")
            return

        # Build AI opponent deck (random from available cards)
        all_cards = db.get_all_cards()
        rulers = [c for c in all_cards if c.card_type == CardType.RULER]
        resonators = [c for c in all_cards if c.card_type == CardType.RESONATOR]
        stones = [c for c in all_cards if c.is_stone()]

        if not rulers:
            QMessageBox.warning(self, "No Cards", "Not enough cards in database.")
            return

        # Pick a different ruler for AI if possible
        p1_ruler = rulers[0]
        for r in rulers:
            if r.code != p0_ruler.code:
                p1_ruler = r
                break

        p1_deck = (resonators * 10)[:40] if resonators else []
        p1_stones = (stones * 5)[:10] if stones else []

        # Create engine
        self.engine = GameEngine(db)
        self.engine.subscribe(self._on_game_event)

        # Enhance with CR-compliant rules engine
        self._setup_rules_engine()

        # Setup and start
        self.engine.setup_game(p0_deck, p0_stones, p0_ruler, p1_deck, p1_stones, p1_ruler)
        self.engine.shuffle_decks()
        self.engine.start_game(0)

        self.game_log.clear()
        self._log("Game started!", Colors.SUCCESS)
        self._log(f"Your ruler: {p0_ruler.name}", Colors.INFO)
        self._update_display()

    def _setup_rules_engine(self):
        """Set up the CR-compliant rules engine with UI callbacks"""
        try:
            from ..rules import enhance_engine
            self.rules_engine = enhance_engine(self.engine)
            self.engine._rules_engine = self.rules_engine

            # Set up choice callback for human player
            self.rules_engine.choices.set_ui_callback(self._handle_choice_request)
        except ImportError:
            # Rules engine not available, continue without it
            self.rules_engine = None

    def _handle_choice_request(self, choice):
        """Handle choice requests from the rules engine via UI dialogs"""
        from ..rules import ChoiceType

        if choice.player != self.human_player:
            # AI choice - let default handler work
            return None

        result = None

        if choice.choice_type == ChoiceType.TARGET:
            dialog = TargetSelectionDialog(
                choice.prompt,
                choice.valid_targets,
                choice.min_targets,
                choice.max_targets,
                lambda c: c.data.name if c.data else str(c),
                self
            )
            if dialog.exec():
                result = dialog.get_result()

        elif choice.choice_type == ChoiceType.MODAL:
            modes = []
            if choice.modal_choice:
                for mode in choice.modal_choice.modes:
                    modes.append({
                        'name': mode.name,
                        'description': mode.description
                    })
            dialog = ModalChoiceDialog(
                choice.prompt,
                modes,
                choice.modal_choice.choose_count if choice.modal_choice else 1,
                self
            )
            if dialog.exec():
                result = dialog.get_result()

        elif choice.choice_type == ChoiceType.YES_NO:
            dialog = YesNoDialog(
                choice.prompt,
                mandatory=choice.is_mandatory,
                parent=self
            )
            if dialog.exec():
                result = dialog.get_result()

        elif choice.choice_type == ChoiceType.X_VALUE:
            dialog = XValueDialog(
                choice.prompt,
                choice.min_x,
                choice.max_x,
                choice.x_description,
                self
            )
            if dialog.exec():
                result = dialog.get_result()

        elif choice.choice_type == ChoiceType.CARD_FROM_LIST:
            dialog = CardListDialog(
                choice.prompt,
                choice.card_list,
                choice.select_count,
                choice.select_up_to,
                lambda c: c.data.name if c.data else str(c),
                self
            )
            if dialog.exec():
                result = dialog.get_result()

        elif choice.choice_type == ChoiceType.ATTRIBUTE:
            dialog = AttributeChoiceDialog(
                choice.prompt,
                choice.attribute_options,
                self
            )
            if dialog.exec():
                result = dialog.get_result()

        return result

    def _request_targets_for_spell(self, card) -> list:
        """Request target selection for a spell that needs targets"""
        # Get script for card
        script = self.engine.get_script(card)
        if not script:
            return []

        # Check if script defines target requirements
        if hasattr(script, 'get_target_requirements'):
            requirements = script.get_target_requirements(self.engine, card)
            if requirements:
                # Gather valid targets
                valid_targets = []
                for req in requirements:
                    if req.filter:
                        for p in self.engine.players:
                            for field_card in p.field:
                                if req.filter.matches(field_card, field_card.controller, self.human_player):
                                    if field_card not in valid_targets:
                                        valid_targets.append(field_card)

                if valid_targets:
                    min_targets = sum(r.count for r in requirements if not getattr(r, 'up_to', False))
                    max_targets = sum(r.count for r in requirements)

                    dialog = TargetSelectionDialog(
                        f"Choose target(s) for {card.data.name}",
                        valid_targets,
                        min_targets,
                        max_targets,
                        lambda c: c.data.name if c.data else str(c),
                        self
                    )
                    if dialog.exec():
                        return dialog.get_result()
                    else:
                        return None  # Cancelled

        return []

    def _load_player_deck(self, db):
        """Load player's deck from default or config"""
        base_path = Path(__file__).parent.parent.parent

        # Check config for default deck path
        config_path = base_path / "config.json"
        deck_path = None

        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    if 'default_deck' in config:
                        deck_path = Path(config['default_deck'])
            except:
                pass

        # Fallback to decks/default.fdk
        if not deck_path or not deck_path.exists():
            deck_path = base_path / "decks" / "default.fdk"

        if not deck_path.exists():
            # Try any .fdk file in decks folder
            decks_dir = base_path / "decks"
            if decks_dir.exists():
                fdk_files = list(decks_dir.glob("*.fdk"))
                if fdk_files:
                    deck_path = fdk_files[0]

        if not deck_path or not deck_path.exists():
            return None, None, None

        try:
            with open(deck_path) as f:
                deck_data = json.load(f)

            # Load ruler
            ruler_code = deck_data.get('ruler')
            ruler = db.get_card(ruler_code) if ruler_code else None

            # Load main deck cards
            main_codes = deck_data.get('main', [])
            main_deck = []
            for code in main_codes:
                card = db.get_card(code)
                if card:
                    main_deck.append(card)

            # Load stone deck cards
            stone_codes = deck_data.get('stones', [])
            stone_deck = []
            for code in stone_codes:
                card = db.get_card(code)
                if card:
                    stone_deck.append(card)

            if ruler and main_deck and stone_deck:
                return main_deck, stone_deck, ruler

        except Exception as e:
            print(f"Error loading deck: {e}")

        return None, None, None

    def _on_game_event(self, event):
        """Handle game events"""
        from ..engine import EventType

        msg = f"[{event.event_type.name}]"
        if event.card:
            msg += f" {event.card.data.name}"
        if event.data:
            msg += f" {event.data}"

        color = Colors.TEXT_SECONDARY
        if event.event_type == EventType.DAMAGE_DEALT:
            color = Colors.ERROR
        elif event.event_type == EventType.CARD_DRAWN:
            color = Colors.INFO
        elif event.event_type == EventType.PHASE_CHANGE:
            color = Colors.SUCCESS

        self._log(msg, color)
        QTimer.singleShot(10, self._update_display)

    def _update_display(self):
        """Update all display elements"""
        if not self.engine:
            return

        # Check for game over
        if self.engine.game_over and not self._game_over_shown:
            self._game_over_shown = True
            self._show_game_over()
            return

        try:
            # Update turn info
            phase_name = self.engine.current_phase.name
            print(f"[DEBUG GUI] turn={self.engine.turn_number}, player={self.engine.turn_player}, phase={phase_name}", flush=True)

            self.turn_label.setText(f"Turn {self.engine.turn_number}")
            self.phase_label.setText(phase_name.upper())

            # Update turn player indicator
            if self.engine.turn_player == self.human_player:
                self.turn_player_label.setText("Your Turn")
                self.turn_player_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent; font-size: 16px; font-weight: bold;")
            else:
                self.turn_player_label.setText("Opponent's Turn")
                self.turn_player_label.setStyleSheet(f"color: {Colors.WARNING}; background: transparent; font-size: 16px; font-weight: bold;")

            # Show/hide combat indicator based on battle state
            is_combat = self.engine.battle.in_battle if hasattr(self.engine, 'battle') else False
            self.combat_indicator.setVisible(is_combat)
            if is_combat:
                # Show combat step in the indicator
                step_name = self.engine.battle.step.name.replace("_", " ").title()
                self.combat_indicator.setText(f"⚔ {step_name} ⚔")
                self.phase_label.setStyleSheet(f"color: {Colors.ERROR}; background: transparent; font-size: 14px; font-weight: bold;")
            else:
                self.combat_indicator.setText("⚔ COMBAT ⚔")
                self.phase_label.setStyleSheet(f"color: {Colors.ACCENT}; background: transparent; font-size: 14px; font-weight: bold;")

        except Exception as e:
            print(f"[DEBUG GUI] ERROR in _update_display: {e}", flush=True)
            import traceback
            traceback.print_exc()

        # Priority indicator
        if self.engine.priority_player == self.human_player:
            self.priority_label.setText("Your Priority")
            self.priority_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent; font-size: 12px;")
        else:
            self.priority_label.setText("Opponent's Priority")
            self.priority_label.setStyleSheet(f"color: {Colors.WARNING}; background: transparent; font-size: 12px;")

        # Update player areas
        self.player_area.update_from_state(self.engine.players[self.human_player], hide_hand=False)
        self.opponent_area.update_from_state(self.engine.players[1 - self.human_player], hide_hand=True)

        # Update chase
        chase_cards = [item.source for item in self.engine.chase]
        self.chase_zone.set_cards(chase_cards)

        # Update button states
        self._update_buttons()

        # Auto-pass logic (MTGO F8 style)
        if self.engine.priority_player != self.human_player:
            # AI's turn - auto-pass for them
            QTimer.singleShot(300, self._ai_auto_pass)
        else:
            # Human's turn - auto-pass in phases with no actions
            QTimer.singleShot(150, self._try_human_auto_pass)

    def _ai_auto_pass(self):
        """Auto-pass for AI opponent"""
        if not self.engine:
            return
        if self.engine.priority_player == self.human_player:
            return  # Already passed back to human

        ai_player = 1 - self.human_player

        # AI passes priority
        if self.engine.pass_priority(ai_player):
            # Both passed - phase advances
            self.engine.advance_phase()
            self._log("Opponent passes", Colors.TEXT_MUTED)
        else:
            # Just passed priority back
            self._log("Opponent passes priority", Colors.TEXT_MUTED)

        self._update_display()

    def _should_auto_pass(self) -> bool:
        """Check if we should auto-pass for the human player (MTGO F8 style)"""
        if not self.engine or self.engine.game_over:
            return False
        if self.engine.priority_player != self.human_player:
            return False

        # Get legal actions
        legal_actions = self.engine.get_legal_actions(self.human_player)
        action_types = {a["type"] for a in legal_actions}

        # Only filter out truly meaningless actions:
        # - pass_priority: always available, doesn't count
        # - produce_will: tapping for mana alone isn't meaningful
        meaningful_actions = action_types - {"pass_priority", "produce_will"}

        # If we have meaningful actions, don't auto-pass
        if meaningful_actions:
            return False

        # Check if we could play cards by tapping stones (Arena-style potential)
        # If we have untapped stones AND cards in hand, check if any card could be played
        if "produce_will" in action_types:
            p = self.engine.players[self.human_player]
            if p.hand:
                # Check if any card could potentially be played with available stones
                if self._could_play_any_card():
                    return False

        return True

    def _could_play_any_card(self) -> bool:
        """Check if any card in hand could be played with current will + untapped stones"""
        from ..models import Attribute
        if not self.engine:
            return False

        p = self.engine.players[self.human_player]

        # Start with will already in pool
        available_colors = {
            Attribute.LIGHT: p.will_pool.light,
            Attribute.FIRE: p.will_pool.fire,
            Attribute.WATER: p.will_pool.water,
            Attribute.WIND: p.will_pool.wind,
            Attribute.DARKNESS: p.will_pool.darkness,
        }
        total_will = p.will_pool.total

        # Add untapped stones
        for card in p.field:
            if card.data.is_stone() and not card.is_rested:
                total_will += 1
                colors = self.engine.get_will_colors(card)
                for color in colors:
                    available_colors[color] = available_colors.get(color, 0) + 1

        if total_will == 0:
            return False

        # Check each card in hand
        for card in p.hand:
            cost = card.data.cost
            if cost.total > total_will:
                continue  # Not enough will total

            # Check if we can produce the required colors
            can_pay = True
            color_requirements = {
                Attribute.LIGHT: cost.light,
                Attribute.FIRE: cost.fire,
                Attribute.WATER: cost.water,
                Attribute.WIND: cost.wind,
                Attribute.DARKNESS: cost.darkness,
            }

            for attr, needed in color_requirements.items():
                if needed > 0 and available_colors.get(attr, 0) < needed:
                    can_pay = False
                    break

            if can_pay:
                return True

        return False

    def _try_human_auto_pass(self):
        """Auto-pass for human if they have no actions (MTGO F8 style)"""
        if self._should_auto_pass():
            phase = self.engine.current_phase.name
            both_passed = self.engine.pass_priority(self.human_player)
            self._log(f"Auto-pass ({phase})", Colors.TEXT_MUTED)
            if both_passed:
                self.engine.advance_phase()
            # Schedule next update
            QTimer.singleShot(100, self._update_display)

    def _update_buttons(self):
        """Update button enabled states"""
        if not self.engine:
            return

        legal_actions = self.engine.get_legal_actions(self.human_player)
        action_types = {a["type"] for a in legal_actions}

        is_my_priority = self.engine.priority_player == self.human_player

        self.pass_btn.setEnabled("pass_priority" in action_types)
        # stone_btn removed - ruler tap calls stones
        # judgment_btn removed - use right-click on ruler
        self.next_btn.setEnabled(is_my_priority)
        self.resolve_btn.setEnabled(is_my_priority and len(self.engine.chase) > 0)

    def _show_game_over(self):
        """Display game over message"""
        from PyQt6.QtWidgets import QMessageBox

        if self.engine.winner == self.human_player:
            title = "Victory!"
            message = "You won the game!"
            self._log("YOU WIN!", Colors.SUCCESS)
        elif self.engine.winner == -1:
            title = "Draw"
            message = "The game ended in a draw."
            self._log("DRAW", Colors.WARNING)
        else:
            title = "Defeat"
            message = "You lost the game."
            self._log("YOU LOSE", Colors.ERROR)

        # Show message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def _log(self, message: str, color: str = None):
        """Add message to game log"""
        # Also print to file log
        print(f"[GAME] {message}", flush=True)
        if color:
            self.game_log.append(f'<span style="color: {color}">{message}</span>')
        else:
            self.game_log.append(message)
        self.game_log.verticalScrollBar().setValue(
            self.game_log.verticalScrollBar().maximum()
        )

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def _on_player_card_clicked(self, card, zone: str):
        """Handle click on player's card"""
        self.selected_card = card
        self._update_card_preview(card)

        if not card:
            self._log(f"Clicked empty {zone}", Colors.TEXT_MUTED)
            return
        if not self.engine:
            self._log("No game in progress", Colors.ERROR)
            return

        self._log(f"Clicked: {card.data.name} in {zone}", Colors.TEXT_SECONDARY)
        print(f"[DEBUG] Card clicked: {card.data.name} in {zone}, is_stone={card.data.is_stone()}, is_resonator={card.data.is_resonator()}", flush=True)

        # Try actions based on zone
        if zone == "hand":
            self._try_play_card(card)
        elif zone == "stone":
            # Stone card - tap for will
            if card.is_rested:
                self._log(f"{card.data.name} is already rested", Colors.WARNING)
            else:
                self._try_produce_will(card)
        elif zone == "resonator" or zone == "field":
            # Resonator or other field card
            if card.data.is_stone():
                if card.is_rested:
                    self._log(f"{card.data.name} is already rested", Colors.WARNING)
                else:
                    self._try_produce_will(card)
            elif card.data.is_resonator() or card.data.card_type.value == "J-Ruler":
                # Check if this resonator can produce will (like Elvish Priest)
                script = self.engine.get_script(card)
                will_colors = script.get_will_colors(self.engine, card)

                if card.is_rested:
                    self._log(f"{card.data.name} is already rested", Colors.WARNING)
                    return

                # Check if can attack
                can_attack = self._can_creature_attack(card)

                if will_colors and can_attack:
                    # Can both produce will AND attack - show choice popup
                    self._show_mana_attack_picker(card, will_colors)
                elif will_colors:
                    # Can only produce will
                    self._try_produce_will(card)
                elif can_attack:
                    # Can only attack
                    self._try_attack(card)
                else:
                    self._log(f"{card.data.name} has summoning sickness", Colors.WARNING)
            else:
                self._log(f"No action for {card.data.card_type.value}", Colors.TEXT_MUTED)
        elif zone == "ruler":
            # Ruler click handled by ruler_tapped signal for stone calling
            # Judgment is done via the Judgment button (requires deliberate action)
            pass

    def _on_opponent_card_clicked(self, card, zone: str):
        """Handle click on opponent's card"""
        self._update_card_preview(card)

    def _on_card_hovered(self, card):
        """Handle mouse hover over a card - update preview"""
        self._update_card_preview(card)

    def _show_card_context_menu(self, card, zone: str, pos):
        """Show context menu for a card based on its zone"""
        try:
            if not card or not self.engine:
                return

            # Validate card has required attributes
            if not hasattr(card, 'data') or not card.data:
                return

            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {Colors.SURFACE};
                    border: 1px solid {Colors.BORDER_MEDIUM};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    color: {Colors.TEXT_PRIMARY};
                }}
                QMenu::item:selected {{
                    background-color: {Colors.PRIMARY};
                }}
                QMenu::item:disabled {{
                    color: {Colors.TEXT_MUTED};
                }}
            """)

            player = self.engine.players[self.human_player]
            is_my_turn = self.engine.turn_player == self.human_player
            has_priority = self.engine.priority_player == self.human_player

            if zone == "hand":
                # Hand cards: Play
                can_play = has_priority and self.engine.can_play_card(self.human_player, card)
                play_action = menu.addAction(f"Play {card.data.name}")
                play_action.setEnabled(can_play)
                play_action.triggered.connect(lambda: self._try_play_card(card))

            elif zone == "stone":
                # Field stones: Tap for will (show all colors), Undo
                if not card.is_rested:
                    # Get actual will colors from script
                    will_colors = self.engine.get_will_colors(card)
                    if will_colors:
                        if len(will_colors) == 1:
                            # Single color stone
                            attr = will_colors[0]
                            tap_action = menu.addAction(f"Tap for {attr.name.title()} will")
                            tap_action.setEnabled(has_priority)
                            tap_action.triggered.connect(lambda: self._try_produce_will(card))
                        else:
                            # Multi-color stone - show each option
                            for attr in will_colors:
                                tap_action = menu.addAction(f"Tap for {attr.name.title()} will")
                                tap_action.setEnabled(has_priority)
                                # Capture attr in closure
                                tap_action.triggered.connect(
                                    lambda checked=False, c=card, a=attr: self._produce_will_with_color(c, a))
                    else:
                        no_will = menu.addAction("(Cannot produce will)")
                        no_will.setEnabled(False)
                else:
                    # Stone is already tapped - offer undo if pending
                    if self._pending_will and self._pending_will[-1][2] == card:
                        undo_action = menu.addAction("Undo (return will)")
                        undo_action.triggered.connect(lambda: self._undo_will_production(card))
                    else:
                        rest_label = menu.addAction("(Already rested)")
                        rest_label.setEnabled(False)

                # Some magic stones have special abilities beyond producing will
                self._add_abilities_to_menu(menu, card, has_priority)

            elif zone == "resonator":
                # Field resonators: Attack, Rest/Recover, Abilities
                if not card.is_rested:
                    # Can attack if it's battle phase and has valid targets
                    attack_action = menu.addAction("Attack")
                    can_attack = (has_priority and
                                  self.engine.current_phase.name == "BATTLE" and
                                  not card.is_rested)
                    attack_action.setEnabled(can_attack)
                    attack_action.triggered.connect(lambda: self._try_attack(card))

                    # Rest (tap without attacking)
                    rest_action = menu.addAction("Rest")
                    rest_action.setEnabled(has_priority)
                    rest_action.triggered.connect(lambda: self._rest_card(card))
                else:
                    recover_action = menu.addAction("(Rested - recovers next turn)")
                    recover_action.setEnabled(False)

                # Activated abilities
                self._add_abilities_to_menu(menu, card, has_priority)

            elif zone == "ruler":
                # Ruler: Call Stone, Judgment, Abilities
                ruler = card

                # Call Stone (if ruler is untapped)
                if not ruler.is_rested:
                    call_action = menu.addAction("Call Stone")
                    can_call = has_priority and len(player.stone_deck) > 0 and not player.called_stone_this_turn
                    call_action.setEnabled(can_call)
                    call_action.triggered.connect(self._on_call_stone)

                # Judgment (if ruler has judgment cost and isn't already J-Ruler)
                if hasattr(ruler.data, 'judgment_cost') and ruler.data.judgment_cost:
                    judgment_action = menu.addAction("Judgment")
                    can_judge = has_priority and not player.j_ruler
                    judgment_action.setEnabled(can_judge)
                    judgment_action.triggered.connect(self._try_judgment)

                # Activated abilities
                self._add_abilities_to_menu(menu, ruler, has_priority)

            # Only show menu if it has items
            if menu.actions():
                menu.exec(pos)

        except Exception as e:
            print(f"[ERROR] Context menu failed: {e}", flush=True)
            import traceback
            traceback.print_exc()

    def _add_abilities_to_menu(self, menu, card, has_priority: bool):
        """Add activated abilities from a card's script to the context menu"""
        if not self.engine:
            return

        script = self.engine.get_script(card)
        if not script:
            return

        abilities = script.get_activated_abilities(self.engine, card)
        if not abilities:
            return

        menu.addSeparator()
        player = self.engine.players[self.human_player]

        for i, ability in enumerate(abilities):
            # Build ability name from description or text
            name = ability.description if ability.description else f"Ability {i + 1}"

            # Build cost string
            cost_parts = []
            if ability.tap_cost:
                cost_parts.append("Rest")
            if ability.will_cost:
                cost_parts.append(str(ability.will_cost))
            cost_str = ", ".join(cost_parts) if cost_parts else ""

            # Build menu label
            if cost_str:
                label = f"{name} ({cost_str})"
            else:
                label = name

            action = menu.addAction(label)

            # Check if ability can be activated
            can_activate = has_priority
            if ability.will_cost and not player.will_pool.can_pay(ability.will_cost):
                can_activate = False
            if ability.tap_cost and card.is_rested:
                can_activate = False
            # Summoning sickness check for resonators
            if ability.tap_cost and card.data.is_resonator():
                from ..models import Keyword
                if (card.entered_turn == self.engine.turn_number and
                    not card.has_keyword(Keyword.SWIFTNESS)):
                    can_activate = False

            action.setEnabled(can_activate)
            # Capture the index in closure
            action.triggered.connect(lambda checked=False, c=card, idx=i: self._activate_ability(c, idx))

    def _activate_ability(self, card, ability_index: int):
        """Activate an ability on a card"""
        if not self.engine:
            return

        if self.engine.activate_ability(self.human_player, card, ability_index):
            script = self.engine.get_script(card)
            if script:
                abilities = script.get_activated_abilities(self.engine, card)
                if ability_index < len(abilities):
                    desc = abilities[ability_index].description or f"Ability {ability_index + 1}"
                    self._log(f"Activated {desc} on {card.data.name}", Colors.SUCCESS)
        else:
            self._log(f"Could not activate ability on {card.data.name}", Colors.ERROR)

        self._update_display()

    def _produce_will_from_stone(self, card):
        """Produce will from a stone and track for undo"""
        if not self.engine or card.is_rested:
            return

        attr = card.data.attribute
        attr_name = attr.name.lower() if attr else "void"

        # Rest the stone
        card.is_rested = True

        # Add will to pool
        player = self.engine.players[self.human_player]
        if attr_name == "light":
            player.will_pool.light += 1
        elif attr_name == "fire":
            player.will_pool.fire += 1
        elif attr_name == "water":
            player.will_pool.water += 1
        elif attr_name == "wind":
            player.will_pool.wind += 1
        elif attr_name == "darkness":
            player.will_pool.darkness += 1
        else:
            player.will_pool.void += 1

        # Track for undo
        self._pending_will.append((attr_name, 1, card))

        self._log(f"Produced 1 {attr_name} will from {card.data.name}", Colors.SUCCESS)
        self._update_display()

    def _undo_will_production(self, card):
        """Undo the last will production from a stone"""
        if not self._pending_will:
            return

        # Find and remove the will entry for this card
        for i in range(len(self._pending_will) - 1, -1, -1):
            attr_name, amount, stone = self._pending_will[i]
            if stone == card:
                # Remove will from pool
                player = self.engine.players[self.human_player]
                if attr_name == "light":
                    player.will_pool.light -= amount
                elif attr_name == "fire":
                    player.will_pool.fire -= amount
                elif attr_name == "water":
                    player.will_pool.water -= amount
                elif attr_name == "wind":
                    player.will_pool.wind -= amount
                elif attr_name == "darkness":
                    player.will_pool.darkness -= amount
                else:
                    player.will_pool.void -= amount

                # Unrest the stone
                card.is_rested = False

                # Remove from pending
                self._pending_will.pop(i)

                self._log(f"Undid {amount} {attr_name} will from {card.data.name}", Colors.WARNING)
                self._update_display()
                break

    def _rest_card(self, card):
        """Rest a card without any other effect"""
        if not card.is_rested:
            card.is_rested = True
            self._log(f"Rested {card.data.name}", Colors.TEXT_SECONDARY)
            self._update_display()

    def _update_card_preview(self, card):
        """Update card preview panel"""
        if not card:
            self.card_info.setText("Select a card")
            self.card_ability_text.setText("")
            return

        data = card.data
        info = f"<b>{data.name}</b><br>"
        info += f"Type: {data.card_type.value}<br>"
        info += f"Attribute: {data.attribute.name}<br>"
        info += f"Cost: {data.cost}<br>"
        if data.atk or data.defense:
            info += f"ATK/DEF: {card.effective_atk}/{card.effective_def}<br>"

        self.card_info.setText(info)
        self.card_ability_text.setText(data.ability_text or "No ability text.")

        # Card image - large for legibility
        assets = get_asset_manager()
        pixmap = assets.get_card_image(data.code, QSize(300, 420))
        self.card_preview.setPixmap(pixmap)

    def _try_play_card(self, card):
        """Try to play a card from hand"""
        # Check phase - instant speed cards (Quickcast, Chant-Instant) can be played anytime
        is_instant = card.data.is_instant()
        if not is_instant and self.engine.current_phase.name not in ["MAIN", "MAIN_2"]:
            self._log(f"Can only play {card.data.name} during Main phase", Colors.WARNING)
            return

        # Non-instant cards can only be played on your turn
        if not is_instant and self.engine.turn_player != self.human_player:
            self._log(f"Can only play {card.data.name} on your turn", Colors.WARNING)
            return

        p = self.engine.players[self.human_player]
        cost = card.data.cost

        # Auto-tap stones if we don't have enough will (Arena-style with hand lookahead)
        if not p.will_pool.can_pay(cost):
            if not self._auto_tap_for_cost(cost, card_being_played=card):
                self._log(f"Not enough will for {card.data.name} (need {cost})", Colors.WARNING)
                return

        # Check if this spell needs targets
        targets = None
        if card.data.is_spell():
            targets = self._request_targets_for_spell(card)
            if targets is None:
                # User cancelled target selection
                self._log(f"Cancelled {card.data.name}", Colors.INFO)
                return

        if self.engine.play_card(self.human_player, card, targets):
            self._log(f"Played {card.data.name}", Colors.SUCCESS)
            # Clear pending will - can't undo after spending
            self._pending_will.clear()
        else:
            self._log(f"Cannot play {card.data.name}", Colors.ERROR)
        self._update_display()

    def _on_card_dropped_to_field(self, card_uid: str):
        """Handle card dropped from hand to field (play it)"""
        if not self.engine:
            return

        # Find the card by UID
        p = self.engine.players[self.human_player]
        card = None
        for c in p.hand:
            if c.uid == card_uid:
                card = c
                break

        if card:
            self._try_play_card(card)

    def _on_hand_reordered(self, card_uid: str, new_index: int):
        """Handle card reordered in hand"""
        if not self.engine:
            return

        p = self.engine.players[self.human_player]

        # Find the card and its current index
        card = None
        old_index = -1
        for i, c in enumerate(p.hand):
            if c.uid == card_uid:
                card = c
                old_index = i
                break

        if card is None or old_index == -1:
            return

        # Remove from old position and insert at new position
        p.hand.pop(old_index)
        if new_index == -1 or new_index >= len(p.hand):
            p.hand.append(card)
        else:
            # Adjust index if we removed before the target
            if old_index < new_index:
                new_index -= 1
            p.hand.insert(new_index, card)

        self._update_display()

    def _auto_tap_for_cost(self, cost, card_being_played=None) -> bool:
        """Auto-tap mana sources to pay for a cost (Arena-style with hand lookahead)."""
        from ..models import Attribute

        p = self.engine.players[self.human_player]

        # Already have enough?
        if p.will_pool.can_pay(cost):
            return True

        # Only auto-tap stones, never creatures
        mana_sources = []
        available_colors = {}  # Track what colors we CAN produce
        for card in p.field:
            if card.is_rested:
                continue
            if not card.data.is_stone():
                continue
            will_colors = self.engine.get_will_colors(card)
            if will_colors:
                mana_sources.append(card)
                for color in will_colors:
                    available_colors[color] = available_colors.get(color, 0) + 1

        if not mana_sources:
            return False

        # PRE-CHECK: Verify we can actually pay the colored costs before tapping anything
        # Check each colored requirement
        color_requirements = {
            Attribute.LIGHT: cost.light,
            Attribute.FIRE: cost.fire,
            Attribute.WATER: cost.water,
            Attribute.WIND: cost.wind,
            Attribute.DARKNESS: cost.darkness,
        }
        for attr, needed in color_requirements.items():
            already_have = getattr(p.will_pool, attr.name.lower(), 0)
            still_need = max(0, needed - already_have)
            if still_need > 0 and available_colors.get(attr, 0) < still_need:
                # Can't produce enough of this color - don't tap anything
                return False

        # Also check total mana is sufficient
        total_available = len(mana_sources) + p.will_pool.total
        if total_available < cost.total:
            return False

        # Analyze what colors other cards in hand need (lookahead)
        colors_needed_by_hand = {}  # Attribute -> count of cards needing it
        for hand_card in p.hand:
            if card_being_played and hand_card.uid == card_being_played.uid:
                continue  # Skip the card we're playing
            hc = hand_card.data.cost
            if hc.light > 0:
                colors_needed_by_hand[Attribute.LIGHT] = colors_needed_by_hand.get(Attribute.LIGHT, 0) + 1
            if hc.fire > 0:
                colors_needed_by_hand[Attribute.FIRE] = colors_needed_by_hand.get(Attribute.FIRE, 0) + 1
            if hc.water > 0:
                colors_needed_by_hand[Attribute.WATER] = colors_needed_by_hand.get(Attribute.WATER, 0) + 1
            if hc.wind > 0:
                colors_needed_by_hand[Attribute.WIND] = colors_needed_by_hand.get(Attribute.WIND, 0) + 1
            if hc.darkness > 0:
                colors_needed_by_hand[Attribute.DARKNESS] = colors_needed_by_hand.get(Attribute.DARKNESS, 0) + 1

        # Sort stones by priority:
        # 1. Stones that DON'T produce colors needed by other cards (tap first)
        # 2. Single-color stones before multi-color (preserve flexibility)
        # 3. Stones producing less-needed colors before more-needed
        def stone_priority(stone):
            colors = self.engine.get_will_colors(stone)
            # How many other cards in hand need colors this stone produces?
            hand_overlap = sum(colors_needed_by_hand.get(c, 0) for c in colors)
            # Flexibility (fewer colors = tap first)
            flexibility = len(colors) if colors else 999
            return (hand_overlap, flexibility)

        mana_sources.sort(key=stone_priority)

        # Calculate what colors we need for current spell
        def get_needed():
            return {
                Attribute.LIGHT: max(0, cost.light - p.will_pool.light),
                Attribute.FIRE: max(0, cost.fire - p.will_pool.fire),
                Attribute.WATER: max(0, cost.water - p.will_pool.water),
                Attribute.WIND: max(0, cost.wind - p.will_pool.wind),
                Attribute.DARKNESS: max(0, cost.darkness - p.will_pool.darkness),
            }

        def get_generic_needed():
            pool = p.will_pool
            remaining = (
                max(0, pool.light - cost.light) +
                max(0, pool.fire - cost.fire) +
                max(0, pool.water - cost.water) +
                max(0, pool.wind - cost.wind) +
                max(0, pool.darkness - cost.darkness) +
                pool.void
            )
            return max(0, cost.void - remaining)

        # Tap mana sources until we can pay
        for source in mana_sources:
            if p.will_pool.can_pay(cost):
                break

            available_colors = self.engine.get_will_colors(source)
            if not available_colors:
                continue

            needed = get_needed()
            chosen = None

            # First: colors we specifically need for this spell
            for attr in available_colors:
                if needed.get(attr, 0) > 0:
                    chosen = attr
                    break

            # Second: for generic cost, prefer colors NOT needed by hand
            if not chosen and get_generic_needed() > 0:
                # Sort available colors by how much hand needs them (least needed first)
                sorted_colors = sorted(available_colors,
                    key=lambda c: colors_needed_by_hand.get(c, 0))
                chosen = sorted_colors[0]

            # Third: if we still need something, just tap (least needed by hand)
            if not chosen and not p.will_pool.can_pay(cost):
                sorted_colors = sorted(available_colors,
                    key=lambda c: colors_needed_by_hand.get(c, 0))
                chosen = sorted_colors[0]

            if chosen:
                if self.engine.produce_will(self.human_player, source, chosen):
                    self._log(f"Auto-tapped {source.data.name} for {chosen.name.title()}", Colors.TEXT_MUTED)

        return p.will_pool.can_pay(cost)

    def _try_produce_will(self, card):
        """Try to produce will from a stone or mana creature using the script system"""
        from ..models import Attribute, Keyword

        # Check summoning sickness for resonators (not stones)
        if card.data.is_resonator():
            if card.entered_turn == self.engine.turn_number:
                if not card.has_keyword(Keyword.SWIFTNESS):
                    self._log(f"{card.data.name} has summoning sickness", Colors.WARNING)
                    return

        # Get available colors from the card's script via engine
        available_colors = self.engine.get_will_colors(card)

        if not available_colors:
            self._log(f"{card.data.name} cannot produce will", Colors.ERROR)
            self._update_display()
            return

        if len(available_colors) > 1:
            # Multiple colors - show Arena-style color picker
            self._show_will_color_picker(card, available_colors)
            return

        # Single color - use it directly
        chosen_attr = available_colors[0]
        if self.engine.produce_will(self.human_player, card, chosen_attr):
            self._log(f"Tapped {card.data.name} for {chosen_attr.name.title()} will", Colors.ACCENT)
        else:
            self._log(f"Cannot tap {card.data.name}", Colors.ERROR)
        self._update_display()

    def _produce_will_with_color(self, card, chosen_attr):
        """Produce will of a specific color from a stone (used by context menu)"""
        if not self.engine or card.is_rested:
            return

        if self.engine.produce_will(self.human_player, card, chosen_attr):
            self._log(f"Tapped {card.data.name} for {chosen_attr.name.title()} will", Colors.ACCENT)
        else:
            self._log(f"Cannot tap {card.data.name}", Colors.ERROR)
        self._update_display()

    def _show_will_color_picker(self, card, available_colors):
        """Show Arena-style inline color picker with colored orbs"""
        from ..models import Attribute

        # Color mapping for will types
        WILL_COLORS = {
            Attribute.LIGHT: ("#ffd700", "L"),      # Gold
            Attribute.FIRE: ("#ff4500", "F"),       # Red-orange
            Attribute.WATER: ("#1e90ff", "W"),      # Blue
            Attribute.WIND: ("#32cd32", "G"),       # Green
            Attribute.DARKNESS: ("#9932cc", "D"),   # Purple
            Attribute.VOID: ("#808080", "V"),       # Gray
        }

        # Create popup widget
        picker = QFrame(self)
        picker.setWindowFlags(Qt.WindowType.Popup)
        picker.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_DARK};
                border: 2px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(picker)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        def make_choice(attr):
            def on_click():
                picker.close()
                if self.engine.produce_will(self.human_player, card, attr):
                    self._log(f"Tapped {card.data.name} for {attr.name.title()} will", Colors.ACCENT)
                else:
                    self._log(f"Cannot tap {card.data.name}", Colors.ERROR)
                self._update_display()
            return on_click

        # Create colored orb buttons for each available color
        for attr in available_colors:
            color, letter = WILL_COLORS.get(attr, ("#808080", "?"))

            orb = QPushButton(letter)
            orb.setFixedSize(48, 48)
            orb.setCursor(Qt.CursorShape.PointingHandCursor)
            orb.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid {color};
                    border-radius: 24px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 1px 1px 2px black;
                }}
                QPushButton:hover {{
                    border: 3px solid white;
                    background-color: {color}dd;
                }}
            """)
            orb.setToolTip(f"{attr.name.title()} Will")
            orb.clicked.connect(make_choice(attr))
            layout.addWidget(orb)

        # Position near cursor
        picker.adjustSize()
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        picker.move(cursor_pos.x() - picker.width() // 2, cursor_pos.y() - picker.height() - 10)
        picker.show()

    def _can_creature_attack(self, card) -> bool:
        """Check if a creature can attack (without side effects)"""
        from ..models import Keyword

        if self.engine.current_phase.name != "MAIN":
            return False
        if self.engine.turn_player != self.human_player:
            return False
        if self.engine.priority_player != self.human_player:
            return False
        if self.engine.chase:  # Can't attack while chase has items
            return False
        if self.engine.battle.in_battle:  # Can't start new attack during battle
            return False
        if card.is_rested:
            return False
        # Check summoning sickness
        if card.entered_turn == self.engine.turn_number:
            if not card.has_keyword(Keyword.SWIFTNESS):
                return False
        return True

    def _show_mana_attack_picker(self, card, will_colors):
        """Show picker for mana dorks that can both produce will and attack"""
        from ..models import Attribute

        # Color mapping for will types
        WILL_COLORS = {
            Attribute.LIGHT: ("#ffd700", "L"),      # Gold
            Attribute.FIRE: ("#ff4500", "F"),       # Red-orange
            Attribute.WATER: ("#1e90ff", "W"),      # Blue
            Attribute.WIND: ("#32cd32", "G"),       # Green
            Attribute.DARKNESS: ("#9932cc", "D"),   # Purple
            Attribute.VOID: ("#808080", "V"),       # Gray
        }

        # Create popup widget
        picker = QFrame(self)
        picker.setWindowFlags(Qt.WindowType.Popup)
        picker.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_DARK};
                border: 2px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(picker)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        def make_will_choice(attr):
            def on_click():
                picker.close()
                if self.engine.produce_will(self.human_player, card, attr):
                    self._log(f"Tapped {card.data.name} for {attr.name.title()} will", Colors.ACCENT)
                else:
                    self._log(f"Cannot tap {card.data.name}", Colors.ERROR)
                self._update_display()
            return on_click

        def make_attack_choice():
            def on_click():
                picker.close()
                self._try_attack(card)
            return on_click

        # Create colored orb buttons for each available mana color
        for attr in will_colors:
            color, letter = WILL_COLORS.get(attr, ("#808080", "?"))

            orb = QPushButton(letter)
            orb.setFixedSize(48, 48)
            orb.setCursor(Qt.CursorShape.PointingHandCursor)
            orb.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid {color};
                    border-radius: 24px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 1px 1px 2px black;
                }}
                QPushButton:hover {{
                    border: 3px solid white;
                    background-color: {color}dd;
                }}
            """)
            orb.setToolTip(f"Tap for {attr.name.title()} Will")
            orb.clicked.connect(make_will_choice(attr))
            layout.addWidget(orb)

        # Add attack button - black with white text, red border
        attack_btn = QPushButton("ATK")
        attack_btn.setFixedSize(48, 48)
        attack_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        attack_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 3px solid #cc3333;
                border-radius: 24px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 3px solid #ff4444;
                background-color: #2a2a2a;
            }}
        """)
        attack_btn.setToolTip("Attack")
        attack_btn.clicked.connect(make_attack_choice())
        layout.addWidget(attack_btn)

        # Position near cursor
        picker.adjustSize()
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        picker.move(cursor_pos.x() - picker.width() // 2, cursor_pos.y() - picker.height() - 10)
        picker.show()

    def _try_attack(self, card):
        """Try to attack with a card - attacks happen during Main phase"""
        from ..models import Keyword

        print(f"[DEBUG] _try_attack: {card.data.name}, phase={self.engine.current_phase.name}, rested={card.is_rested}", flush=True)

        if self.engine.current_phase.name != "MAIN":
            self._log(f"Can only attack during Main phase (current: {self.engine.current_phase.name})", Colors.WARNING)
            return

        if card.is_rested:
            self._log(f"{card.data.name} is rested and cannot attack", Colors.WARNING)
            return

        # Check summoning sickness
        if card.entered_turn == self.engine.turn_number:
            if not card.has_keyword(Keyword.SWIFTNESS):
                self._log(f"{card.data.name} has summoning sickness", Colors.WARNING)
                return

        # Check if chase is empty (required for battle initiation)
        if self.engine.chase:
            self._log("Cannot attack while chase has items", Colors.WARNING)
            return

        print(f"[DEBUG] _try_attack: calling declare_attack", flush=True)
        if self.engine.declare_attack(self.human_player, card, target_player=1 - self.human_player):
            self._log(f"{card.data.name} attacks!", Colors.ERROR)
        else:
            self._log(f"{card.data.name} cannot attack (engine rejected)", Colors.WARNING)
        self._update_display()

    def _try_judgment(self):
        """Try to perform Judgment"""
        p = self.engine.players[self.human_player]
        ruler = p.ruler
        if not ruler or not ruler.data.judgment_cost:
            self._log("No Judgment cost on ruler", Colors.WARNING)
            return

        if not p.will_pool.can_pay(ruler.data.judgment_cost):
            self._log(f"Not enough will for Judgment (need {ruler.data.judgment_cost})", Colors.WARNING)
            return

        if self.engine.perform_judgment(self.human_player):
            self._log("Judgment!", Colors.ACCENT)
        else:
            self._log("Cannot perform Judgment", Colors.ERROR)
        self._update_display()

    def _on_pass(self):
        """Pass priority"""
        if self.engine and self.engine.pass_priority(self.human_player):
            self.engine.advance_phase()
        self._update_display()

    def _on_call_stone(self):
        """Call a magic stone"""
        if self.engine and self.engine.call_stone(self.human_player):
            self._log("Called a magic stone", Colors.SUCCESS)
        self._update_display()

    def _on_judgment(self):
        """Perform judgment"""
        self._try_judgment()

    def _on_next_phase(self):
        """Advance to next phase"""
        if self.engine:
            self.engine.advance_phase()
        self._update_display()

    def _on_resolve(self):
        """Resolve the chase"""
        if self.engine:
            self.engine.resolve_full_chase()
        self._update_display()

    def _on_surrender(self):
        """Surrender the game"""
        reply = QMessageBox.question(
            self,
            "Surrender",
            "Are you sure you want to surrender?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.back_clicked.emit()

    def _on_exit_game(self):
        """Exit the game (with confirmation if game in progress)"""
        if self.engine and not self.engine.game_over:
            reply = QMessageBox.question(
                self,
                "Exit Game",
                "Game in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.back_clicked.emit()

    def _switch_panel_tab(self, index: int):
        """Switch the info panel tab"""
        # Update button states
        for i, btn in enumerate(self._panel_tab_buttons):
            btn.setChecked(i == index)
        # Switch content
        self.panel_stack.setCurrentIndex(index)

    def _send_chat(self):
        """Send a chat message"""
        text = self.chat_input.text().strip()
        if text:
            # Add to chat log (local echo for now - multiplayer would send to server)
            self.chat_log.append(f"<b>You:</b> {text}")
            self.chat_input.clear()

    # =========================================================================
    # SCREEN EVENTS
    # =========================================================================

    def paintEvent(self, event):
        """Paint the background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self._background is None or self._background.size() != self.size():
            assets = get_asset_manager()
            self._background = assets.get_background('duel', self.size())

        if self._background:
            painter.drawPixmap(0, 0, self._background)

        painter.end()

    def on_show(self):
        """Called when screen is shown"""
        pass

    def on_resize(self, size: QSize):
        """Called when window is resized"""
        self._background = None
        self.update()
