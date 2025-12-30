"""
FoWPro Deck Editor
==================
Professional deck builder with card browser, similar to YGOPro/EDOPro.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QSpinBox,
    QSplitter, QGridLayout, QGroupBox, QFileDialog, QMessageBox,
    QSizePolicy, QGraphicsDropShadowEffect, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QDrag, QMouseEvent, QFont,
    QDragEnterEvent, QDropEvent
)

from .styles import Colors, Fonts
from .assets import get_asset_manager


# =============================================================================
# DECK DATA
# =============================================================================

@dataclass
class Deck:
    """Represents a complete deck"""
    name: str = "New Deck"
    ruler_code: Optional[str] = None
    main_deck: List[str] = field(default_factory=list)  # Card codes
    stone_deck: List[str] = field(default_factory=list)
    side_deck: List[str] = field(default_factory=list)

    def is_valid(self) -> tuple[bool, str]:
        """Check if deck is valid for play"""
        errors = []

        if not self.ruler_code:
            errors.append("No ruler selected")

        if len(self.main_deck) < 40:
            errors.append(f"Main deck needs at least 40 cards (has {len(self.main_deck)})")
        if len(self.main_deck) > 60:
            errors.append(f"Main deck cannot exceed 60 cards (has {len(self.main_deck)})")

        if len(self.stone_deck) < 10:
            errors.append(f"Stone deck needs at least 10 cards (has {len(self.stone_deck)})")
        if len(self.stone_deck) > 20:
            errors.append(f"Stone deck cannot exceed 20 cards (has {len(self.stone_deck)})")

        if len(self.side_deck) > 15:
            errors.append(f"Side deck cannot exceed 15 cards (has {len(self.side_deck)})")

        return (len(errors) == 0, "\n".join(errors))

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'ruler': self.ruler_code,
            'main': self.main_deck,
            'stones': self.stone_deck,
            'side': self.side_deck,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Deck':
        return cls(
            name=data.get('name', 'Imported Deck'),
            ruler_code=data.get('ruler'),
            main_deck=data.get('main', []),
            stone_deck=data.get('stones', []),
            side_deck=data.get('side', []),
        )

    def save(self, path: Path):
        """Save deck to file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'Deck':
        """Load deck from file"""
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


# =============================================================================
# CARD WIDGETS
# =============================================================================

class DeckCardWidget(QFrame):
    """Small card widget for deck display - shows card image"""

    clicked = pyqtSignal(str)  # card_code
    double_clicked = pyqtSignal(str)
    right_clicked = pyqtSignal(str)

    ATTRIBUTE_COLORS = {
        'Light': "#ffd700",
        'Fire': "#ff4500",
        'Water': "#1e90ff",
        'Wind': "#32cd32",
        'Darkness': "#9932cc",
        'Void': "#808080",
    }

    def __init__(self, card_code: str = None, card_data=None, parent=None):
        super().__init__(parent)
        self.card_code = card_code
        self.card_data = card_data
        self._selected = False

        self.setFixedSize(70, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(False)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the card UI"""
        self.setStyleSheet(f"""
            DeckCardWidget {{
                background-color: {Colors.BG_MEDIUM};
                border: 2px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
            }}
            DeckCardWidget:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Card image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, stretch=1)

        self._update_display()

    def _update_display(self):
        """Update card display"""
        if not self.card_code:
            self.image_label.setText("???")
            self.image_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
            return

        # Check if image exists locally first (fast)
        assets = get_asset_manager()
        card_path = assets.base_path / "cards" / f"{self.card_code}.jpg"

        if card_path.exists():
            # Image exists locally - load it
            pixmap = assets.get_card_image(self.card_code, QSize(66, 94))
            self.image_label.setPixmap(pixmap)
        else:
            # Show card code as placeholder - don't block to download
            name = self.card_data.name if self.card_data else self.card_code
            short_name = name[:8] + "..." if len(name) > 8 else name
            self.image_label.setText(short_name)
            self.image_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent; font-size: 8px;")

        # Border color based on attribute
        if self.card_data:
            attr_name = self.card_data.attribute.name if self.card_data.attribute else 'Void'
            color = self.ATTRIBUTE_COLORS.get(attr_name, Colors.BORDER_MEDIUM)
        else:
            color = Colors.BORDER_MEDIUM

        self.setStyleSheet(f"""
            DeckCardWidget {{
                background-color: {Colors.BG_MEDIUM};
                border: 2px solid {color};
                border-radius: 4px;
            }}
            DeckCardWidget:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """)

    def set_card(self, card_code: str, card_data):
        """Set the card to display"""
        self.card_code = card_code
        self.card_data = card_data
        self._update_display()

    def set_selected(self, selected: bool):
        """Set selection state"""
        self._selected = selected
        border_color = Colors.ACCENT if selected else Colors.BORDER_MEDIUM
        self.setStyleSheet(self.styleSheet().replace(
            f"border: 2px solid {Colors.BORDER_MEDIUM}",
            f"border: 2px solid {border_color}"
        ))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.card_code)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.card_code)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.card_code)
        super().mouseDoubleClickEvent(event)


class CardSearchResult(QFrame):
    """Card widget for search results with thumbnail - supports drag to add to deck"""

    add_to_deck = pyqtSignal(object)  # CardData
    clicked = pyqtSignal(object)  # CardData

    def __init__(self, card_data=None, parent=None):
        super().__init__(parent)
        self.card_data = card_data
        self._drag_start_pos = None

        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            CardSearchResult {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
            }}
            CardSearchResult:hover {{
                background-color: {Colors.SURFACE_HOVER};
                border-color: {Colors.PRIMARY};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Card thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(44, 64)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet(f"background: {Colors.BG_MEDIUM}; border-radius: 2px;")
        layout.addWidget(self.thumbnail)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = QLabel()
        self.name_label.setFont(Fonts.card_name())
        self.name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        info_layout.addWidget(self.name_label)

        self.type_label = QLabel()
        self.type_label.setFont(Fonts.small())
        self.type_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        info_layout.addWidget(self.type_label)

        self.cost_label = QLabel()
        self.cost_label.setFont(Fonts.small())
        self.cost_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        info_layout.addWidget(self.cost_label)

        layout.addLayout(info_layout, stretch=1)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setFont(Fonts.card_stats())
        self.stats_label.setStyleSheet(f"color: {Colors.ACCENT}; background: transparent;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.stats_label)

        self._update_display()

    def _update_display(self):
        if not self.card_data:
            return

        self.name_label.setText(self.card_data.name)
        self.type_label.setText(self.card_data.card_type.value if self.card_data.card_type else "")

        # Cost
        cost_str = str(self.card_data.cost) if self.card_data.cost else "Free"
        self.cost_label.setText(cost_str)

        # Stats
        if self.card_data.atk or self.card_data.defense:
            self.stats_label.setText(f"{self.card_data.atk}/{self.card_data.defense}")
        else:
            self.stats_label.setText("")

        # Show placeholder initially - thumbnail loads on demand when clicked
        self.thumbnail.setText(self.card_data.code[:7] if self.card_data.code else "")
        self.thumbnail.setStyleSheet(f"""
            background: {Colors.BG_MEDIUM};
            border-radius: 2px;
            color: {Colors.TEXT_MUTED};
            font-size: 8px;
        """)

    def set_card(self, card_data):
        self.card_data = card_data
        self._update_display()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self.card_data)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Start drag when mouse moves far enough"""
        if not self._drag_start_pos or not self.card_data:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        # Use special prefix to identify search results
        mime_data.setText(f"search:{self.card_data.code}")
        drag.setMimeData(mime_data)

        # Create drag pixmap from thumbnail
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio))
        drag.setHotSpot(QPoint(30, 30))

        drag.exec(Qt.DropAction.CopyAction)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.add_to_deck.emit(self.card_data)
        super().mouseDoubleClickEvent(event)


# =============================================================================
# DECK ZONE WIDGETS (YGOPro-style)
# =============================================================================

class CompactCardWidget(QFrame):
    """Compact card widget with count badge for YGOPro-style deck display"""

    clicked = pyqtSignal(str)  # card_code
    right_clicked = pyqtSignal(str)  # card_code (remove one copy)
    double_clicked = pyqtSignal(str)  # card_code (remove from deck)
    hovered = pyqtSignal(str)  # card_code (for preview on hover)
    drag_started = pyqtSignal(str, int)  # card_code, index in zone

    CARD_WIDTH = 48
    CARD_HEIGHT = 70

    def __init__(self, card_code: str, card_data, count: int = 1, zone_name: str = "", index: int = 0, parent=None):
        super().__init__(parent)
        self.card_code = card_code
        self.card_data = card_data
        self.count = count
        self.zone_name = zone_name
        self.index = index
        self._drag_start_pos = None

        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setMouseTracking(True)  # Enable hover tracking
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        # Attribute colors for border
        attr_colors = {
            'LIGHT': "#ffd700", 'FIRE': "#ff4500", 'WATER': "#1e90ff",
            'WIND': "#32cd32", 'DARKNESS': "#9932cc", 'VOID': "#808080", 'NONE': "#555555"
        }
        attr_name = self.card_data.attribute.name if self.card_data and self.card_data.attribute else "NONE"
        border_color = attr_colors.get(attr_name, "#555555")

        self.setStyleSheet(f"""
            CompactCardWidget {{
                background-color: {Colors.BG_MEDIUM};
                border: 2px solid {border_color};
                border-radius: 3px;
            }}
            CompactCardWidget:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.SURFACE_HOVER};
            }}
        """)

        # Use stacked layout for image + badge overlay
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # Card image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label)

        self._load_image()

    def _load_image(self):
        """Load card image or show placeholder"""
        assets = get_asset_manager()
        card_path = assets.base_path / "cards" / f"{self.card_code}.jpg"

        if card_path.exists():
            pixmap = assets.get_card_image(self.card_code, QSize(self.CARD_WIDTH - 4, self.CARD_HEIGHT - 4))
            self.image_label.setPixmap(pixmap)
        else:
            # Show abbreviated name as placeholder
            name = self.card_data.name if self.card_data else self.card_code
            short = name[:6] if len(name) > 6 else name
            self.image_label.setText(short)
            self.image_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 7px; background: transparent;")

    def paintEvent(self, event):
        """Override to draw count badge"""
        super().paintEvent(event)

        if self.count > 1:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Badge background
            badge_size = 16
            badge_x = self.width() - badge_size - 2
            badge_y = 2

            painter.setBrush(QColor("#e74c3c"))
            painter.setPen(QColor("#ffffff"))
            painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)

            # Badge text
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(badge_x, badge_y, badge_size, badge_size,
                           Qt.AlignmentFlag.AlignCenter, str(self.count))

    def set_count(self, count: int):
        """Update the count badge"""
        self.count = count
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self.card_code)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.card_code)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.card_code)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        """Emit hover signal when mouse enters"""
        self.hovered.emit(self.card_code)
        super().enterEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_pos is None:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        # Format: deck:zone_name:index:card_code
        mime_data.setText(f"deck:{self.zone_name}:{self.index}:{self.card_code}")
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(40, 58, Qt.AspectRatioMode.KeepAspectRatio))
        drag.setHotSpot(QPoint(20, 29))

        # Execute drag - if dropped outside deck zones, remove the card
        result = drag.exec(Qt.DropAction.MoveAction)
        self._drag_start_pos = None

        # If drag ended without valid drop, emit right_clicked to remove
        if result == Qt.DropAction.IgnoreAction:
            self.right_clicked.emit(self.card_code)


class DeckZoneWidget(QFrame):
    """YGOPro-style deck zone with compact cards, count badges, sorting, and drag-drop"""

    card_clicked = pyqtSignal(str)  # card_code
    card_removed = pyqtSignal(str)  # card_code
    card_selected = pyqtSignal(object)  # card_data for preview
    card_double_clicked = pyqtSignal(str)  # card_code (for removal)
    card_hovered = pyqtSignal(object)  # card_data (for hover preview)
    card_dropped_from_search = pyqtSignal(str)  # card_code - request to add from search
    card_dropped_from_zone = pyqtSignal(str, str, int)  # card_code, source_zone, source_index
    card_reordered = pyqtSignal(int, int)  # old_index, new_index
    contents_changed = pyqtSignal()  # emitted when cards added/removed

    # Sort options
    SORT_NAME = "Name"
    SORT_TYPE = "Type"
    SORT_ATTR = "Attribute"
    SORT_COST = "Cost"
    SORT_ATK = "ATK"

    def __init__(self, title: str, min_cards: int = 0, max_cards: int = 60,
                 max_copies: int = 4, parent=None):
        super().__init__(parent)
        self.title = title
        self.min_cards = min_cards
        self.max_cards = max_cards
        self.max_copies = max_copies  # Max copies per unique card
        self.cards: List[tuple[str, object]] = []  # (code, data) - can have duplicates
        self._widgets: List[CompactCardWidget] = []
        self._current_sort = self.SORT_NAME
        self._sort_reverse = False
        self.zone_name = title  # For identifying in drag operations

        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            DeckZoneWidget {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header with title, count, and sort
        header = QHBoxLayout()
        header.setSpacing(8)

        self.title_label = QLabel(self.title)
        self.title_label.setFont(Fonts.subheading())
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(self.title_label)

        # Sort dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([self.SORT_NAME, self.SORT_TYPE, self.SORT_ATTR, self.SORT_COST, self.SORT_ATK])
        self.sort_combo.setFixedWidth(80)
        self.sort_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }}
        """)
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        header.addWidget(self.sort_combo)

        # Sort direction button
        self.sort_dir_btn = QPushButton("↑")
        self.sort_dir_btn.setFixedSize(20, 20)
        self.sort_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{ background: {Colors.SURFACE_HOVER}; }}
        """)
        self.sort_dir_btn.clicked.connect(self._toggle_sort_direction)
        header.addWidget(self.sort_dir_btn)

        header.addStretch()

        # Card count
        self.count_label = QLabel(f"0/{self.min_cards}-{self.max_cards}")
        self.count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        header.addWidget(self.count_label)

        layout.addLayout(header)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {Colors.BG_DARK};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {Colors.PRIMARY}; }}
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(3)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, stretch=1)

    def count_copies(self, card_code: str) -> int:
        """Count how many copies of a card are in the zone"""
        return sum(1 for code, _ in self.cards if code == card_code)

    def can_add_card(self, card_code: str, card_data=None) -> tuple[bool, str]:
        """Check if a card can be added, returns (can_add, reason)"""
        if len(self.cards) >= self.max_cards:
            return False, f"Deck is full ({self.max_cards} cards max)"

        copies = self.count_copies(card_code)
        if copies >= self.max_copies:
            return False, f"Already have {self.max_copies} copies of this card"

        return True, ""

    def add_card(self, card_code: str, card_data) -> bool:
        """Add a card to the zone (respects copy limit)"""
        can_add, reason = self.can_add_card(card_code, card_data)
        if not can_add:
            return False

        self.cards.append((card_code, card_data))
        self._sort_cards()
        self._refresh_display()
        self.contents_changed.emit()
        return True

    def remove_card(self, card_code: str) -> bool:
        """Remove one copy of a card from the zone"""
        for i, (code, data) in enumerate(self.cards):
            if code == card_code:
                self.cards.pop(i)
                self._refresh_display()
                self.contents_changed.emit()
                return True
        return False

    def clear(self):
        """Clear all cards"""
        if self.cards:
            self.cards.clear()
            self._refresh_display()
            self.contents_changed.emit()

    def get_card_codes(self) -> List[str]:
        """Get list of all card codes (with duplicates)"""
        return [code for code, _ in self.cards]

    def get_card_data(self, card_code: str):
        """Get card data for a code"""
        for code, data in self.cards:
            if code == card_code:
                return data
        return None

    def _sort_cards(self):
        """Sort cards by current sort option"""
        def sort_key(item):
            code, data = item
            if not data:
                return ("", 0, "", 0, 0)

            if self._current_sort == self.SORT_NAME:
                return data.name.lower()
            elif self._current_sort == self.SORT_TYPE:
                return (data.card_type.value if data.card_type else "", data.name.lower())
            elif self._current_sort == self.SORT_ATTR:
                return (data.attribute.name if data.attribute else "", data.name.lower())
            elif self._current_sort == self.SORT_COST:
                cost_val = data.cost.total if data.cost else 0
                return (cost_val, data.name.lower())
            elif self._current_sort == self.SORT_ATK:
                return (data.atk or 0, data.name.lower())
            return data.name.lower()

        self.cards.sort(key=sort_key, reverse=self._sort_reverse)

    def _on_sort_changed(self, sort_type: str):
        """Handle sort option change"""
        self._current_sort = sort_type
        self._sort_cards()
        self._refresh_display()

    def _toggle_sort_direction(self):
        """Toggle between ascending and descending sort"""
        self._sort_reverse = not self._sort_reverse
        self.sort_dir_btn.setText("↓" if self._sort_reverse else "↑")
        self._sort_cards()
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the card display - show each card independently"""
        # Clear existing widgets
        for widget in self._widgets:
            widget.setParent(None)
            widget.deleteLater()
        self._widgets.clear()

        # Calculate grid - more cards per row for compact display
        cards_per_row = 10

        # Create compact card widgets for each card (not grouped)
        for i, (code, data) in enumerate(self.cards):
            widget = CompactCardWidget(code, data, count=1,
                                       zone_name=self.zone_name, index=i)
            widget.clicked.connect(self._on_card_clicked)
            widget.right_clicked.connect(self._on_card_right_click)
            widget.double_clicked.connect(self._on_card_double_click)
            widget.hovered.connect(self._on_card_hovered)

            row = i // cards_per_row
            col = i % cards_per_row

            self.cards_layout.addWidget(widget, row, col)
            self._widgets.append(widget)

        # Update count label
        total_count = len(self.cards)
        if self.min_cards <= total_count <= self.max_cards:
            color = Colors.SUCCESS
        else:
            color = Colors.ERROR

        self.count_label.setText(f"{total_count}/{self.min_cards}-{self.max_cards}")
        self.count_label.setStyleSheet(f"color: {color}; background: transparent;")

    def _on_card_clicked(self, card_code: str):
        """Handle card click - emit for preview"""
        self.card_clicked.emit(card_code)
        data = self.get_card_data(card_code)
        if data:
            self.card_selected.emit(data)

    def _on_card_right_click(self, card_code: str):
        """Handle right-click to remove one copy"""
        self.remove_card(card_code)
        self.card_removed.emit(card_code)

    def _on_card_double_click(self, card_code: str):
        """Handle double-click to remove card"""
        self.remove_card(card_code)
        self.card_double_clicked.emit(card_code)

    def _on_card_hovered(self, card_code: str):
        """Handle hover to show preview"""
        data = self.get_card_data(card_code)
        if data:
            self.card_hovered.emit(data)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag if it's a card"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("search:") or text.startswith("deck:"):
                event.acceptProposedAction()
                # Highlight the zone
                self.setStyleSheet(f"""
                    DeckZoneWidget {{
                        background-color: {Colors.PRIMARY}30;
                        border: 2px solid {Colors.PRIMARY};
                        border-radius: 6px;
                    }}
                """)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Remove highlight when drag leaves"""
        self.setStyleSheet(f"""
            DeckZoneWidget {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

    def dropEvent(self, event: QDropEvent):
        """Handle card drop - from search, other zones, or reordering"""
        # Reset style
        self.setStyleSheet(f"""
            DeckZoneWidget {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 6px;
            }}
        """)

        text = event.mimeData().text()

        if text.startswith("search:"):
            # Card from search results - add to deck
            card_code = text.split(":", 1)[1]
            self.card_dropped_from_search.emit(card_code)
            event.acceptProposedAction()

        elif text.startswith("deck:"):
            # Card from a deck zone - could be reorder or transfer
            parts = text.split(":")
            if len(parts) >= 4:
                source_zone = parts[1]
                source_index = int(parts[2])
                card_code = parts[3]

                if source_zone == self.zone_name:
                    # Same zone - reorder
                    drop_index = self._get_drop_index(event.position().toPoint())
                    if drop_index != source_index:
                        self._reorder_card(source_index, drop_index)
                else:
                    # Different zone - transfer
                    self.card_dropped_from_zone.emit(card_code, source_zone, source_index)

            event.acceptProposedAction()
        else:
            event.ignore()

    def _get_drop_index(self, pos: QPoint) -> int:
        """Calculate drop index based on position"""
        cards_per_row = 10
        card_w = CompactCardWidget.CARD_WIDTH + 3  # width + spacing
        card_h = CompactCardWidget.CARD_HEIGHT + 3

        # Account for container offset
        container_pos = self.cards_container.mapFrom(self, pos)

        col = max(0, container_pos.x() // card_w)
        row = max(0, container_pos.y() // card_h)

        index = row * cards_per_row + col
        return min(index, len(self.cards))

    def _reorder_card(self, old_index: int, new_index: int):
        """Reorder a card within this zone"""
        if old_index < 0 or old_index >= len(self.cards):
            return
        if new_index < 0:
            new_index = 0
        if new_index > len(self.cards):
            new_index = len(self.cards)

        # Move the card
        card = self.cards.pop(old_index)
        if new_index > old_index:
            new_index -= 1
        self.cards.insert(new_index, card)

        self._refresh_display()
        self.card_reordered.emit(old_index, new_index)
        self.contents_changed.emit()


# =============================================================================
# MAIN DECK EDITOR
# =============================================================================

class DeckEditorScreen(QWidget):
    """Main deck editor screen"""

    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.deck = Deck()
        self.selected_card = None
        self._all_cards = []
        self._background: QPixmap = None
        self._has_unsaved_changes = False
        self._saved_deck_hash = None  # To track if deck changed

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main content with transparent background
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # Header
        header = self._create_header()
        content_layout.addLayout(header)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER_DARK};
                width: 2px;
            }}
        """)

        # Left panel - Card browser
        left_panel = self._create_card_browser()
        splitter.addWidget(left_panel)

        # Center panel - Deck zones
        center_panel = self._create_deck_panel()
        splitter.addWidget(center_panel)

        # Right panel - Card details
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([350, 600, 300])

        content_layout.addWidget(splitter, stretch=1)

        layout.addWidget(content)

    def _create_header(self) -> QHBoxLayout:
        """Create the header bar"""
        header = QHBoxLayout()

        # Back button
        back_btn = QPushButton("< Back")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self._on_back_clicked)
        header.addWidget(back_btn)

        # Deck name with unsaved indicator
        self.deck_name_edit = QLineEdit(self.deck.name)
        self.deck_name_edit.setFixedWidth(200)
        self.deck_name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        self.deck_name_edit.textChanged.connect(self._on_deck_name_changed)
        header.addWidget(self.deck_name_edit)

        # Unsaved indicator
        self.unsaved_label = QLabel("")
        self.unsaved_label.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold; background: transparent;")
        header.addWidget(self.unsaved_label)

        header.addStretch()

        # Deck stats
        self.deck_stats_label = QLabel("Main: 0 | Stones: 0 | Side: 0")
        self.deck_stats_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        header.addWidget(self.deck_stats_label)

        header.addStretch()

        # Action buttons
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._new_deck)
        header.addWidget(new_btn)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._load_deck)
        header.addWidget(load_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_deck)
        header.addWidget(save_btn)

        default_btn = QPushButton("Set Default")
        default_btn.clicked.connect(self._set_as_default)
        header.addWidget(default_btn)

        # Clear deck button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_deck)
        clear_btn.setStyleSheet(f"QPushButton {{ color: {Colors.ERROR}; }}")
        header.addWidget(clear_btn)

        # Test hand button
        test_btn = QPushButton("Test Hand")
        test_btn.clicked.connect(self._test_hand)
        header.addWidget(test_btn)

        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self._validate_deck)
        header.addWidget(validate_btn)

        return header

    def _create_card_browser(self) -> QWidget:
        """Create the card browser panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Card Browser")
        title.setFont(Fonts.subheading())
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        # Search bar (searches name AND ability text)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name or ability text...")
        self.search_input.textChanged.connect(self._filter_cards)
        layout.addWidget(self.search_input)

        # Row 1: Type and Attribute
        filters1 = QHBoxLayout()

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Ruler", "Resonator", "Spell", "Addition", "Magic Stone"])
        self.type_filter.currentTextChanged.connect(self._filter_cards)
        filters1.addWidget(self.type_filter)

        self.attr_filter = QComboBox()
        self.attr_filter.addItems(["All Attributes", "Light", "Fire", "Water", "Wind", "Darkness", "Void"])
        self.attr_filter.currentTextChanged.connect(self._filter_cards)
        filters1.addWidget(self.attr_filter)

        layout.addLayout(filters1)

        # Row 2: Set and Cost
        filters2 = QHBoxLayout()

        self.set_filter = QComboBox()
        self.set_filter.addItems(["All Sets", "CMF", "TAT", "MPR", "MOA"])
        self.set_filter.currentTextChanged.connect(self._filter_cards)
        filters2.addWidget(self.set_filter)

        self.cost_filter = QComboBox()
        self.cost_filter.addItems(["All Costs", "0", "1", "2", "3", "4", "5+"])
        self.cost_filter.currentTextChanged.connect(self._filter_cards)
        filters2.addWidget(self.cost_filter)

        layout.addLayout(filters2)

        # Row 3: Race and Rarity
        filters3 = QHBoxLayout()

        self.race_filter = QComboBox()
        self.race_filter.addItems(["All Races", "Human", "Fairy Tale", "Dragon", "Beast", "Elf",
                                   "Vampire", "Werewolf", "Wizard", "Knight", "Angel", "Demon",
                                   "Spirit", "Wererabbit", "God", "Machine", "Zombie"])
        self.race_filter.currentTextChanged.connect(self._filter_cards)
        filters3.addWidget(self.race_filter)

        self.rarity_filter = QComboBox()
        self.rarity_filter.addItems(["All Rarities", "Common", "Uncommon", "Rare", "Super Rare"])
        self.rarity_filter.currentTextChanged.connect(self._filter_cards)
        filters3.addWidget(self.rarity_filter)

        layout.addLayout(filters3)

        # Results scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_container.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(4)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll, stretch=1)

        # Result count
        self.result_count_label = QLabel("0 cards")
        self.result_count_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.result_count_label)

        return panel

    def _create_deck_panel(self) -> QWidget:
        """Create the deck zones panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_DARK}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Ruler section
        ruler_section = QHBoxLayout()
        ruler_label = QLabel("Ruler:")
        ruler_label.setFont(Fonts.subheading())
        ruler_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        ruler_section.addWidget(ruler_label)

        self.ruler_widget = DeckCardWidget()
        self.ruler_widget.setFixedSize(90, 126)
        self.ruler_widget.right_clicked.connect(self._remove_ruler)
        ruler_section.addWidget(self.ruler_widget)

        ruler_section.addStretch()
        layout.addLayout(ruler_section)

        # Main deck zone (max 4 copies per card)
        self.main_zone = DeckZoneWidget("Main Deck", min_cards=40, max_cards=60, max_copies=4)
        self.main_zone.card_clicked.connect(self._on_deck_card_clicked)
        self.main_zone.card_selected.connect(self._update_card_details)
        self.main_zone.card_hovered.connect(self._update_card_details)
        self.main_zone.contents_changed.connect(self._mark_unsaved)
        self.main_zone.card_dropped_from_search.connect(
            lambda code: self._add_card_to_zone_by_code(code, self.main_zone))
        self.main_zone.card_dropped_from_zone.connect(
            lambda code, src, idx: self._transfer_card(code, src, idx, self.main_zone))
        layout.addWidget(self.main_zone, stretch=2)

        # Stone deck zone (max 4 copies per card, some basics may allow more)
        self.stone_zone = DeckZoneWidget("Magic Stone Deck", min_cards=10, max_cards=20, max_copies=4)
        self.stone_zone.card_clicked.connect(self._on_deck_card_clicked)
        self.stone_zone.card_selected.connect(self._update_card_details)
        self.stone_zone.card_hovered.connect(self._update_card_details)
        self.stone_zone.contents_changed.connect(self._mark_unsaved)
        self.stone_zone.card_dropped_from_search.connect(
            lambda code: self._add_card_to_zone_by_code(code, self.stone_zone))
        self.stone_zone.card_dropped_from_zone.connect(
            lambda code, src, idx: self._transfer_card(code, src, idx, self.stone_zone))
        layout.addWidget(self.stone_zone, stretch=1)

        # Side deck zone (max 4 copies per card)
        self.side_zone = DeckZoneWidget("Side Deck", min_cards=0, max_cards=15, max_copies=4)
        self.side_zone.card_clicked.connect(self._on_deck_card_clicked)
        self.side_zone.card_selected.connect(self._update_card_details)
        self.side_zone.card_hovered.connect(self._update_card_details)
        self.side_zone.contents_changed.connect(self._mark_unsaved)
        self.side_zone.card_dropped_from_search.connect(
            lambda code: self._add_card_to_zone_by_code(code, self.side_zone))
        self.side_zone.card_dropped_from_zone.connect(
            lambda code, src, idx: self._transfer_card(code, src, idx, self.side_zone))
        layout.addWidget(self.side_zone, stretch=1)

        return panel

    def _create_details_panel(self) -> QWidget:
        """Create the card details panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE}cc;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Title
        title = QLabel("Card Details")
        title.setFont(Fonts.subheading())
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        # Card image placeholder
        self.card_image = QLabel()
        self.card_image.setFixedSize(180, 252)
        self.card_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_image.setStyleSheet(f"""
            background-color: {Colors.BG_MEDIUM};
            border: 2px solid {Colors.BORDER_MEDIUM};
            border-radius: 6px;
        """)
        layout.addWidget(self.card_image, alignment=Qt.AlignmentFlag.AlignCenter)

        # Card info - Name and code
        self.card_name_label = QLabel("Select a card")
        self.card_name_label.setFont(Fonts.subheading())
        self.card_name_label.setWordWrap(True)
        self.card_name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self.card_name_label)

        self.card_code_label = QLabel("")
        self.card_code_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent; font-size: 10px;")
        layout.addWidget(self.card_code_label)

        # Info grid for compact display
        info_grid = QGridLayout()
        info_grid.setSpacing(4)
        info_grid.setColumnStretch(1, 1)

        # Type
        info_grid.addWidget(QLabel("Type:"), 0, 0)
        self.card_type_label = QLabel("")
        self.card_type_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self.card_type_label.setWordWrap(True)
        info_grid.addWidget(self.card_type_label, 0, 1)

        # Attribute with color
        info_grid.addWidget(QLabel("Attribute:"), 1, 0)
        self.card_attr_label = QLabel("")
        self.card_attr_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        info_grid.addWidget(self.card_attr_label, 1, 1)

        # Cost
        info_grid.addWidget(QLabel("Cost:"), 2, 0)
        self.card_cost_label = QLabel("")
        self.card_cost_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        info_grid.addWidget(self.card_cost_label, 2, 1)

        # ATK/DEF
        info_grid.addWidget(QLabel("ATK/DEF:"), 3, 0)
        self.card_stats_label = QLabel("")
        self.card_stats_label.setFont(Fonts.card_stats())
        self.card_stats_label.setStyleSheet(f"color: {Colors.ACCENT}; background: transparent;")
        info_grid.addWidget(self.card_stats_label, 3, 1)

        # Race/Trait
        info_grid.addWidget(QLabel("Race:"), 4, 0)
        self.card_race_label = QLabel("")
        self.card_race_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self.card_race_label.setWordWrap(True)
        info_grid.addWidget(self.card_race_label, 4, 1)

        # Set and Rarity
        info_grid.addWidget(QLabel("Set:"), 5, 0)
        self.card_set_label = QLabel("")
        self.card_set_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        info_grid.addWidget(self.card_set_label, 5, 1)

        # Style the grid labels
        for i in range(info_grid.rowCount()):
            label = info_grid.itemAtPosition(i, 0)
            if label and label.widget():
                label.widget().setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")

        layout.addLayout(info_grid)

        # Ability text
        self.card_ability_text = QTextEdit()
        self.card_ability_text.setReadOnly(True)
        self.card_ability_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
                padding: 8px;
                color: {Colors.TEXT_SECONDARY};
            }}
        """)
        layout.addWidget(self.card_ability_text, stretch=1)

        # Add to deck button
        self.add_btn = QPushButton("Add to Deck")
        self.add_btn.setProperty("class", "primary")
        self.add_btn.clicked.connect(self._add_selected_to_deck)
        self.add_btn.setEnabled(False)
        layout.addWidget(self.add_btn)

        return panel

    # =========================================================================
    # CARD BROWSING
    # =========================================================================

    def _load_cards(self):
        """Load cards from database"""
        if not self.main_window:
            return

        db = self.main_window.get_database()
        if db:
            self._all_cards = db.get_all_cards()
            self._filter_cards()

    def _filter_cards(self):
        """Filter cards based on search and filters"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        attr_filter = self.attr_filter.currentText()
        set_filter = self.set_filter.currentText()
        cost_filter = self.cost_filter.currentText()
        race_filter = self.race_filter.currentText()
        rarity_filter = self.rarity_filter.currentText()

        # Clear results
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = []
        for card in self._all_cards:
            # Search filter (name OR ability text)
            if search_text:
                name_match = search_text in card.name.lower()
                ability_match = card.ability_text and search_text in card.ability_text.lower()
                if not name_match and not ability_match:
                    continue

            # Type filter
            if type_filter != "All Types":
                type_map = {
                    "Ruler": ["Ruler", "J-Ruler"],
                    "Resonator": ["Resonator"],
                    "Spell": ["Spell: Chant", "Spell: Chant-Instant", "Spell: Chant-Standby"],
                    "Addition": ["Addition: Field", "Addition: Resonator", "Addition: Ruler", "Regalia"],
                    "Magic Stone": ["Basic Magic Stone", "Special Magic Stone"],
                }
                allowed_types = type_map.get(type_filter, [])
                if card.card_type and card.card_type.value not in allowed_types:
                    continue

            # Attribute filter
            if attr_filter != "All Attributes":
                if card.attribute and card.attribute.name != attr_filter.upper():
                    continue

            # Set filter
            if set_filter != "All Sets":
                if not card.code or not card.code.startswith(set_filter):
                    continue

            # Cost filter
            if cost_filter != "All Costs":
                total_cost = card.cost.total if card.cost else 0
                if cost_filter == "5+":
                    if total_cost < 5:
                        continue
                else:
                    if total_cost != int(cost_filter):
                        continue

            # Race filter
            if race_filter != "All Races":
                if not card.races or race_filter not in card.races:
                    continue

            # Rarity filter
            if rarity_filter != "All Rarities":
                rarity_map = {
                    "Common": "COMMON",
                    "Uncommon": "UNCOMMON",
                    "Rare": "RARE",
                    "Super Rare": "SUPER_RARE",
                }
                if card.rarity and card.rarity.name != rarity_map.get(rarity_filter):
                    continue

            filtered.append(card)

        # Add results (limit to 100 for performance)
        for card in filtered[:100]:
            widget = CardSearchResult(card)
            widget.clicked.connect(self._on_card_selected)
            widget.add_to_deck.connect(self._add_card_to_deck)
            self.results_layout.insertWidget(self.results_layout.count() - 1, widget)

        self.result_count_label.setText(f"{len(filtered)} cards")

    def _on_card_selected(self, card_data):
        """Handle card selection"""
        self.selected_card = card_data
        self._update_card_details(card_data)
        self.add_btn.setEnabled(True)

    def _update_card_details(self, card_data):
        """Update the card details panel"""
        if not card_data:
            self.card_name_label.setText("Select a card")
            self.card_code_label.setText("")
            self.card_type_label.setText("")
            self.card_attr_label.setText("")
            self.card_cost_label.setText("")
            self.card_stats_label.setText("")
            self.card_race_label.setText("")
            self.card_set_label.setText("")
            self.card_ability_text.setText("")
            return

        # Name and code
        self.card_name_label.setText(card_data.name)
        self.card_code_label.setText(card_data.code)

        # Type
        self.card_type_label.setText(card_data.card_type.value if card_data.card_type else "Unknown")

        # Attribute with color
        attr_colors = {
            'LIGHT': ("#ffd700", "Light"),
            'FIRE': ("#ff4500", "Fire"),
            'WATER': ("#1e90ff", "Water"),
            'WIND': ("#32cd32", "Wind"),
            'DARKNESS': ("#9932cc", "Darkness"),
            'VOID': ("#808080", "Void"),
            'NONE': ("#808080", "None"),
        }
        attr_name = card_data.attribute.name if card_data.attribute else "NONE"
        attr_color, attr_display = attr_colors.get(attr_name, ("#808080", attr_name))
        self.card_attr_label.setText(attr_display)
        self.card_attr_label.setStyleSheet(f"color: {attr_color}; background: transparent; font-weight: bold;")

        # Cost
        self.card_cost_label.setText(str(card_data.cost) if card_data.cost else "Free")

        # ATK/DEF
        if card_data.atk or card_data.defense:
            self.card_stats_label.setText(f"{card_data.atk}/{card_data.defense}")
        else:
            self.card_stats_label.setText("—")

        # Race/Trait
        if card_data.races:
            self.card_race_label.setText(", ".join(card_data.races))
        else:
            self.card_race_label.setText("—")

        # Set and rarity
        rarity_str = card_data.rarity.name.replace("_", " ").title() if card_data.rarity else ""
        set_info = f"{card_data.set_code}" if card_data.set_code else ""
        if rarity_str:
            set_info += f" ({rarity_str})" if set_info else rarity_str
        self.card_set_label.setText(set_info or "—")

        # Ability text
        self.card_ability_text.setText(card_data.ability_text or "No ability text.")

        # Update card image
        assets = get_asset_manager()
        pixmap = assets.get_card_image(card_data.code, QSize(180, 252))
        self.card_image.setPixmap(pixmap)

    # =========================================================================
    # DECK MANAGEMENT
    # =========================================================================

    def _add_card_to_deck(self, card_data):
        """Add a card to the appropriate deck zone"""
        if not card_data:
            return

        # Determine which zone
        card_type = card_data.card_type.value if card_data.card_type else ""

        if card_type in ["Ruler"]:
            self._set_ruler(card_data)
        elif card_type in ["Basic Magic Stone", "Special Magic Stone", "Magic Stone"]:
            # Check if can add
            can_add, reason = self.stone_zone.can_add_card(card_data.code, card_data)
            if can_add:
                self.stone_zone.add_card(card_data.code, card_data)
                self.deck.stone_deck.append(card_data.code)
            else:
                self._show_status_message(reason, error=True)
        else:
            # Check if can add
            can_add, reason = self.main_zone.can_add_card(card_data.code, card_data)
            if can_add:
                self.main_zone.add_card(card_data.code, card_data)
                self.deck.main_deck.append(card_data.code)
            else:
                self._show_status_message(reason, error=True)

        self._update_deck_stats()

    def _add_card_to_zone_by_code(self, card_code: str, target_zone: DeckZoneWidget):
        """Add a card to a specific zone by code (for drag-drop from search)"""
        if not self.db:
            return

        card_data = self.db.get_card(card_code)
        if not card_data:
            return

        can_add, reason = target_zone.can_add_card(card_code, card_data)
        if can_add:
            target_zone.add_card(card_code, card_data)
            # Update the deck model
            if target_zone == self.main_zone:
                self.deck.main_deck.append(card_code)
            elif target_zone == self.stone_zone:
                self.deck.stone_deck.append(card_code)
            elif target_zone == self.side_zone:
                self.deck.side_deck.append(card_code)
            self._update_deck_stats()
        else:
            self._show_status_message(reason, error=True)

    def _transfer_card(self, card_code: str, source_zone_name: str, source_index: int, target_zone: DeckZoneWidget):
        """Transfer a card from one zone to another (for drag-drop between zones)"""
        # Find source zone
        source_zone = None
        source_deck_list = None
        if source_zone_name == "Main Deck":
            source_zone = self.main_zone
            source_deck_list = self.deck.main_deck
        elif source_zone_name == "Magic Stone Deck":
            source_zone = self.stone_zone
            source_deck_list = self.deck.stone_deck
        elif source_zone_name == "Side Deck":
            source_zone = self.side_zone
            source_deck_list = self.deck.side_deck
        else:
            return

        # Get card data from source
        card_data = source_zone.get_card_data(card_code)
        if not card_data:
            return

        # Check if target can accept
        can_add, reason = target_zone.can_add_card(card_code, card_data)
        if not can_add:
            self._show_status_message(reason, error=True)
            return

        # Remove from source
        source_zone.remove_card(card_code)
        if card_code in source_deck_list:
            source_deck_list.remove(card_code)

        # Add to target
        target_zone.add_card(card_code, card_data)
        if target_zone == self.main_zone:
            self.deck.main_deck.append(card_code)
        elif target_zone == self.stone_zone:
            self.deck.stone_deck.append(card_code)
        elif target_zone == self.side_zone:
            self.deck.side_deck.append(card_code)

        self._update_deck_stats()

    def _show_status_message(self, message: str, error: bool = False):
        """Show a temporary status message"""
        # Flash the message in the deck name area or show a tooltip
        color = Colors.ERROR if error else Colors.TEXT_PRIMARY
        self.deck_name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_MEDIUM};
                border: 2px solid {color};
                border-radius: 4px;
                padding: 8px;
                color: {color};
                font-size: 14px;
            }}
        """)
        self.deck_name_edit.setPlaceholderText(message)

        # Reset after a short delay (using a simple approach)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self._reset_status_style)

    def _reset_status_style(self):
        """Reset the status message style"""
        self.deck_name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 4px;
                padding: 8px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
            }}
        """)
        self.deck_name_edit.setPlaceholderText("Deck name...")

    def _add_selected_to_deck(self):
        """Add the selected card to deck"""
        if self.selected_card:
            self._add_card_to_deck(self.selected_card)

    def _set_ruler(self, card_data):
        """Set the deck's ruler"""
        self.deck.ruler_code = card_data.code
        self.ruler_widget.set_card(card_data.code, card_data)

    def _remove_ruler(self, card_code: str):
        """Remove the ruler"""
        self.deck.ruler_code = None
        self.ruler_widget.set_card(None, None)
        self._update_deck_stats()

    def _on_deck_card_clicked(self, card_code: str):
        """Handle clicking a card in the deck"""
        # Find card data
        for card in self._all_cards:
            if card.code == card_code:
                self._on_card_selected(card)
                break

    def _update_deck_stats(self):
        """Update deck statistics display"""
        main_count = len(self.main_zone.cards)
        stone_count = len(self.stone_zone.cards)
        side_count = len(self.side_zone.cards)

        self.deck_stats_label.setText(
            f"Main: {main_count} | Stones: {stone_count} | Side: {side_count}"
        )

    # =========================================================================
    # DECK FILE OPERATIONS
    # =========================================================================

    def _new_deck(self):
        """Create a new deck"""
        if self._has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Create new deck anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.deck = Deck()
        self.deck_name_edit.setText(self.deck.name)
        self.main_zone.clear()
        self.stone_zone.clear()
        self.side_zone.clear()
        self.ruler_widget.set_card(None, None)
        self._update_deck_stats()
        self._mark_saved()

    def _save_deck(self):
        """Save deck to file"""
        # Update deck data from zones
        self.deck.main_deck = self.main_zone.get_card_codes()
        self.deck.stone_deck = self.stone_zone.get_card_codes()
        self.deck.side_deck = self.side_zone.get_card_codes()

        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Deck",
            str(Path(__file__).parent.parent.parent / "decks" / f"{self.deck.name}.fdk"),
            "FoWPro Deck (*.fdk);;JSON (*.json)"
        )

        if path:
            # Ensure extension is added
            if not path.endswith('.fdk') and not path.endswith('.json'):
                path += '.fdk'
            try:
                self.deck.save(Path(path))
                self._mark_saved()
                QMessageBox.information(self, "Saved", f"Deck saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save deck: {e}")

    def _load_deck(self):
        """Load deck from file"""
        if self._has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Load another deck anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        path, _ = QFileDialog.getOpenFileName(
            self, "Load Deck",
            str(Path(__file__).parent.parent.parent / "decks"),
            "All Deck Files (*.fdk *.json *);;FoWPro Deck (*.fdk);;JSON (*.json);;All Files (*)"
        )

        if path:
            try:
                self.deck = Deck.load(Path(path))
                self.deck_name_edit.setText(self.deck.name)

                # Rebuild zones from deck data
                self._rebuild_zones()
                self._update_deck_stats()
                self._mark_saved()

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load deck: {e}")

    def _rebuild_zones(self):
        """Rebuild zone displays from deck data"""
        self.main_zone.clear()
        self.stone_zone.clear()
        self.side_zone.clear()

        # Find card data for each code
        card_map = {card.code: card for card in self._all_cards}

        # Ruler
        if self.deck.ruler_code and self.deck.ruler_code in card_map:
            self._set_ruler(card_map[self.deck.ruler_code])

        # Main deck
        for code in self.deck.main_deck:
            if code in card_map:
                self.main_zone.add_card(code, card_map[code])

        # Stone deck
        for code in self.deck.stone_deck:
            if code in card_map:
                self.stone_zone.add_card(code, card_map[code])

        # Side deck
        for code in self.deck.side_deck:
            if code in card_map:
                self.side_zone.add_card(code, card_map[code])

    def _validate_deck(self):
        """Validate the current deck"""
        # Update deck data
        self.deck.main_deck = self.main_zone.get_card_codes()
        self.deck.stone_deck = self.stone_zone.get_card_codes()
        self.deck.side_deck = self.side_zone.get_card_codes()

        valid, errors = self.deck.is_valid()

        if valid:
            QMessageBox.information(self, "Valid Deck", "This deck is valid for play!")
        else:
            QMessageBox.warning(self, "Invalid Deck", f"Deck validation errors:\n\n{errors}")

    def _set_as_default(self):
        """Set the current deck as the default deck for new games"""
        # Update deck data
        self.deck.main_deck = self.main_zone.get_card_codes()
        self.deck.stone_deck = self.stone_zone.get_card_codes()
        self.deck.side_deck = self.side_zone.get_card_codes()

        # Save to default deck location
        default_path = Path(__file__).parent.parent.parent / "decks" / "default.fdk"
        try:
            default_path.parent.mkdir(parents=True, exist_ok=True)
            self.deck.save(default_path)

            # Also save config to remember default deck
            config_path = Path(__file__).parent.parent.parent / "config.json"
            config = {}
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            config['default_deck'] = str(default_path)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            QMessageBox.information(
                self, "Default Deck Set",
                f"'{self.deck.name}' is now your default deck.\nIt will be used when starting new games."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set default deck: {e}")

    def _clear_deck(self):
        """Clear all cards from the deck"""
        if not self.main_zone.cards and not self.stone_zone.cards and not self.side_zone.cards:
            return  # Nothing to clear

        reply = QMessageBox.question(
            self, "Clear Deck",
            "Are you sure you want to clear all cards from the deck?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.main_zone.clear()
            self.stone_zone.clear()
            self.side_zone.clear()
            self.ruler_widget.set_card(None, None)
            self.deck.ruler_code = None
            self._update_deck_stats()
            self._mark_unsaved()

    def _test_hand(self):
        """Draw a test hand of 5 random cards from the main deck"""
        import random

        cards = self.main_zone.cards.copy()
        if len(cards) < 5:
            QMessageBox.warning(self, "Not Enough Cards",
                f"Need at least 5 cards in main deck to test hand.\nCurrently have {len(cards)} cards.")
            return

        # Shuffle and draw 5
        random.shuffle(cards)
        hand = cards[:5]

        # Display the hand
        hand_text = "Test Hand (5 cards):\n\n"
        for i, (code, data) in enumerate(hand, 1):
            name = data.name if data else code
            cost = str(data.cost) if data and data.cost else "Free"
            hand_text += f"{i}. {name} ({cost})\n"

        QMessageBox.information(self, "Test Hand", hand_text)

    def _on_back_clicked(self):
        """Handle back button click with unsaved changes check"""
        if self._has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Leave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.back_clicked.emit()

    def _on_deck_name_changed(self, name: str):
        """Handle deck name change"""
        self.deck.name = name
        self._mark_unsaved()

    def _mark_unsaved(self):
        """Mark the deck as having unsaved changes"""
        if not self._has_unsaved_changes:
            self._has_unsaved_changes = True
            self.unsaved_label.setText("*")
            self._update_deck_stats()

    def _mark_saved(self):
        """Mark the deck as saved"""
        self._has_unsaved_changes = False
        self.unsaved_label.setText("")

    # =========================================================================
    # SCREEN EVENTS
    # =========================================================================

    def paintEvent(self, event):
        """Paint the background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Get or generate background
        if self._background is None or self._background.size() != self.size():
            assets = get_asset_manager()
            self._background = assets.get_background('deck', self.size())

        if self._background:
            painter.drawPixmap(0, 0, self._background)

        painter.end()

    def on_show(self):
        """Called when screen is shown"""
        self._load_cards()
        self._load_default_deck()

    def _load_default_deck(self):
        """Load the default deck on startup"""
        # Try to get default deck from config
        config_path = Path(__file__).parent.parent.parent / "config.json"
        decks_dir = Path(__file__).parent.parent.parent / "decks"
        deck_path = None

        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                if 'default_deck' in config and config['default_deck']:
                    deck_path = Path(config['default_deck'])
                    if not deck_path.is_absolute():
                        deck_path = decks_dir / deck_path
            except Exception:
                pass

        # Fallback to decks/default.fdk
        if not deck_path or not deck_path.exists():
            deck_path = decks_dir / "default.fdk"

        if deck_path and deck_path.exists():
            try:
                self.deck = Deck.load(deck_path)
                self.deck_name_edit.setText(self.deck.name)
                self._rebuild_zones()
                self._update_deck_stats()
                self._mark_saved()
            except Exception:
                pass  # Silently fail, start with empty deck

    def on_resize(self, size: QSize):
        """Called when window is resized"""
        self._background = None
        self.update()
