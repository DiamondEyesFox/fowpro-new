"""
Choice Dialogs for FoWPro
=========================

PyQt6 dialogs for player choices during gameplay:
- Target selection
- Modal choices ("Choose one")
- X value selection
- Yes/No prompts
- Card selection from list
"""

from typing import List, Optional, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QButtonGroup, QRadioButton,
    QCheckBox, QSpinBox, QDialogButtonBox, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap

from .styles import Colors


class ChoiceDialog(QDialog):
    """Base class for choice dialogs"""

    def __init__(self, title: str, prompt: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(16, 16, 16, 16)

        # Prompt label
        self._prompt_label = QLabel(prompt)
        self._prompt_label.setWordWrap(True)
        self._prompt_label.setFont(QFont("Segoe UI", 11))
        self._prompt_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self._layout.addWidget(self._prompt_label)

        # Content area (subclasses add their content here)
        self._content_frame = QFrame()
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(0, 8, 0, 8)
        self._layout.addWidget(self._content_frame)

        # Button box
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._layout.addWidget(self._button_box)

        # Styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_DARK};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_SECONDARY};
            }}
        """)

        self.result_value = None


class TargetSelectionDialog(ChoiceDialog):
    """Dialog for selecting targets from valid options"""

    def __init__(self, prompt: str, valid_targets: List,
                 min_targets: int = 1, max_targets: int = 1,
                 get_card_display: Callable = None, parent=None):
        super().__init__("Select Target", prompt, parent)

        self.valid_targets = valid_targets
        self.min_targets = min_targets
        self.max_targets = max_targets
        self.selected_targets = []
        self.get_card_display = get_card_display or (lambda c: c.data.name if c.data else str(c))

        # Selection info
        self._selection_label = QLabel(f"Select {min_targets}" +
                                       (f"-{max_targets}" if max_targets > min_targets else "") +
                                       " target(s)")
        self._selection_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._content_layout.addWidget(self._selection_label)

        # Scroll area for targets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)

        scroll_widget = QWidget()
        self._targets_layout = QGridLayout(scroll_widget)
        self._targets_layout.setSpacing(8)
        scroll.setWidget(scroll_widget)
        self._content_layout.addWidget(scroll)

        # Add target buttons
        self._target_buttons = []
        for i, target in enumerate(valid_targets):
            btn = self._create_target_button(target, i)
            row, col = divmod(i, 3)
            self._targets_layout.addWidget(btn, row, col)
            self._target_buttons.append(btn)

        self._update_ok_button()

    def _create_target_button(self, target, index: int) -> QPushButton:
        """Create a button for a target"""
        display_text = self.get_card_display(target)

        # Add zone/controller info if available
        extra_info = []
        if hasattr(target, 'controller'):
            extra_info.append(f"P{target.controller + 1}")
        if hasattr(target, 'zone'):
            extra_info.append(str(target.zone.name))

        if extra_info:
            display_text += f"\n({', '.join(extra_info)})"

        btn = QPushButton(display_text)
        btn.setCheckable(True)
        btn.setMinimumSize(120, 60)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Get attribute color if available
        attr_color = Colors.ACCENT
        if hasattr(target, 'data') and target.data and hasattr(target.data, 'attribute'):
            attr = str(target.data.attribute).upper()
            attr_colors = {
                'LIGHT': "#ffd700",
                'FIRE': "#ff4500",
                'WATER': "#1e90ff",
                'WIND': "#32cd32",
                'DARKNESS': "#9932cc",
            }
            attr_color = attr_colors.get(attr, Colors.ACCENT)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                text-align: center;
            }}
            QPushButton:hover {{
                border-color: {attr_color};
            }}
            QPushButton:checked {{
                background-color: {attr_color};
                color: white;
                border-color: {attr_color};
            }}
        """)

        btn.clicked.connect(lambda checked, t=target: self._on_target_clicked(t, checked))
        return btn

    def _on_target_clicked(self, target, checked: bool):
        if checked:
            if target not in self.selected_targets:
                # If at max, uncheck the oldest selection
                if len(self.selected_targets) >= self.max_targets:
                    old_target = self.selected_targets.pop(0)
                    idx = self.valid_targets.index(old_target)
                    self._target_buttons[idx].setChecked(False)
                self.selected_targets.append(target)
        else:
            if target in self.selected_targets:
                self.selected_targets.remove(target)

        self._selection_label.setText(f"Selected: {len(self.selected_targets)}/{self.max_targets}")
        self._update_ok_button()

    def _update_ok_button(self):
        ok_btn = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(len(self.selected_targets) >= self.min_targets)

    def get_result(self) -> List:
        return self.selected_targets


class ModalChoiceDialog(ChoiceDialog):
    """Dialog for modal choices ('Choose one', 'Choose two', etc.)"""

    def __init__(self, prompt: str, modes: List[Dict],
                 select_count: int = 1, parent=None):
        super().__init__("Choose Mode", prompt, parent)

        self.modes = modes
        self.select_count = select_count
        self.selected_modes = []

        # Info label
        if select_count > 1:
            info = f"Select {select_count} mode(s)"
        else:
            info = "Select one"
        info_label = QLabel(info)
        info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._content_layout.addWidget(info_label)

        # Mode buttons/checkboxes
        self._mode_widgets = []

        if select_count == 1:
            # Use radio buttons for single selection
            self._button_group = QButtonGroup(self)
            for i, mode in enumerate(modes):
                radio = QRadioButton(f"{mode.get('name', f'Mode {i+1}')}")
                if mode.get('description'):
                    radio.setToolTip(mode['description'])
                radio.setStyleSheet(f"""
                    QRadioButton {{
                        color: {Colors.TEXT_PRIMARY};
                        padding: 8px;
                    }}
                    QRadioButton::indicator {{
                        width: 16px;
                        height: 16px;
                    }}
                """)
                self._button_group.addButton(radio, i)
                self._content_layout.addWidget(radio)
                self._mode_widgets.append(radio)

            self._button_group.buttonClicked.connect(self._on_radio_clicked)
        else:
            # Use checkboxes for multi-selection
            for i, mode in enumerate(modes):
                cb = QCheckBox(f"{mode.get('name', f'Mode {i+1}')}")
                if mode.get('description'):
                    cb.setToolTip(mode['description'])
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        color: {Colors.TEXT_PRIMARY};
                        padding: 8px;
                    }}
                """)
                cb.stateChanged.connect(lambda state, idx=i: self._on_checkbox_changed(idx, state))
                self._content_layout.addWidget(cb)
                self._mode_widgets.append(cb)

        self._update_ok_button()

    def _on_radio_clicked(self, btn):
        self.selected_modes = [self._button_group.id(btn)]
        self._update_ok_button()

    def _on_checkbox_changed(self, index: int, state: int):
        if state == Qt.CheckState.Checked.value:
            if index not in self.selected_modes:
                self.selected_modes.append(index)
        else:
            if index in self.selected_modes:
                self.selected_modes.remove(index)
        self._update_ok_button()

    def _update_ok_button(self):
        ok_btn = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(len(self.selected_modes) >= self.select_count)

    def get_result(self) -> List[int]:
        return sorted(self.selected_modes)


class YesNoDialog(ChoiceDialog):
    """Dialog for yes/no choices ('You may...')"""

    def __init__(self, prompt: str, yes_text: str = "Yes", no_text: str = "No",
                 mandatory: bool = False, parent=None):
        super().__init__("Choose", prompt, parent)

        self.choice = None

        # Replace button box with custom yes/no buttons
        self._layout.removeWidget(self._button_box)
        self._button_box.deleteLater()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        self._yes_btn = QPushButton(yes_text)
        self._yes_btn.setMinimumWidth(100)
        self._yes_btn.clicked.connect(self._on_yes)
        btn_layout.addWidget(self._yes_btn)

        if not mandatory:
            self._no_btn = QPushButton(no_text)
            self._no_btn.setMinimumWidth(100)
            self._no_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_MEDIUM};
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {Colors.BORDER};
                }}
                QPushButton:hover {{
                    background-color: {Colors.BG_LIGHT};
                }}
            """)
            self._no_btn.clicked.connect(self._on_no)
            btn_layout.addWidget(self._no_btn)

        self._layout.addLayout(btn_layout)

    def _on_yes(self):
        self.choice = True
        self.accept()

    def _on_no(self):
        self.choice = False
        self.accept()

    def get_result(self) -> bool:
        return self.choice


class XValueDialog(ChoiceDialog):
    """Dialog for choosing X value"""

    def __init__(self, prompt: str, min_x: int = 0, max_x: int = 20,
                 description: str = "", parent=None):
        super().__init__("Choose X", prompt, parent)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            self._content_layout.addWidget(desc_label)

        # Spinbox with range
        spin_layout = QHBoxLayout()

        spin_label = QLabel("X = ")
        spin_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        spin_label.setStyleSheet(f"color: {Colors.ACCENT};")
        spin_layout.addWidget(spin_label)

        self._spinbox = QSpinBox()
        self._spinbox.setRange(min_x, max_x)
        self._spinbox.setValue(min_x)
        self._spinbox.setFont(QFont("Segoe UI", 14))
        self._spinbox.setMinimumWidth(80)
        self._spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                background-color: {Colors.BG_LIGHT};
            }}
        """)
        spin_layout.addWidget(self._spinbox)

        spin_layout.addStretch()
        self._content_layout.addLayout(spin_layout)

        # Range info
        range_label = QLabel(f"(Range: {min_x} - {max_x})")
        range_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._content_layout.addWidget(range_label)

    def get_result(self) -> int:
        return self._spinbox.value()


class CardListDialog(ChoiceDialog):
    """Dialog for selecting cards from a list (search results, etc.)"""

    def __init__(self, prompt: str, cards: List,
                 select_count: int = 1, select_up_to: bool = False,
                 get_card_display: Callable = None, parent=None):
        super().__init__("Select Card", prompt, parent)

        self.cards = cards
        self.select_count = select_count
        self.select_up_to = select_up_to
        self.selected_cards = []
        self.get_card_display = get_card_display or (lambda c: c.data.name if c.data else str(c))

        # Selection info
        if select_up_to:
            info = f"Select up to {select_count} card(s)"
        else:
            info = f"Select {select_count} card(s)"
        self._selection_label = QLabel(info)
        self._selection_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._content_layout.addWidget(self._selection_label)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)

        scroll_widget = QWidget()
        self._cards_layout = QVBoxLayout(scroll_widget)
        self._cards_layout.setSpacing(4)
        scroll.setWidget(scroll_widget)
        self._content_layout.addWidget(scroll)

        # Add card items
        self._card_widgets = []
        for i, card in enumerate(cards):
            widget = self._create_card_item(card, i)
            self._cards_layout.addWidget(widget)
            self._card_widgets.append(widget)

        self._update_ok_button()

    def _create_card_item(self, card, index: int) -> QFrame:
        """Create a selectable card item"""
        frame = QFrame()
        frame.setProperty("index", index)
        frame.setProperty("selected", False)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)

        # Card name
        name_label = QLabel(self.get_card_display(card))
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(name_label)

        # Card type/stats
        info_parts = []
        if hasattr(card, 'data') and card.data:
            if card.data.card_type:
                info_parts.append(str(card.data.card_type.name))
            if card.data.atk is not None:
                info_parts.append(f"{card.data.atk}/{card.data.defense}")

        if info_parts:
            info_label = QLabel(" | ".join(info_parts))
            info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            layout.addWidget(info_label)

        layout.addStretch()

        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_MEDIUM};
                border: 2px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QFrame:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)

        # Make clickable
        frame.mousePressEvent = lambda e, f=frame, c=card: self._on_card_clicked(f, c)

        return frame

    def _on_card_clicked(self, frame: QFrame, card):
        is_selected = frame.property("selected")

        if is_selected:
            # Deselect
            frame.setProperty("selected", False)
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BG_MEDIUM};
                    border: 2px solid {Colors.BORDER};
                    border-radius: 4px;
                }}
            """)
            if card in self.selected_cards:
                self.selected_cards.remove(card)
        else:
            # Select
            if len(self.selected_cards) >= self.select_count:
                if not self.select_up_to:
                    # Deselect oldest
                    old_card = self.selected_cards.pop(0)
                    for w in self._card_widgets:
                        if self.cards[w.property("index")] == old_card:
                            w.setProperty("selected", False)
                            w.setStyleSheet(f"""
                                QFrame {{
                                    background-color: {Colors.BG_MEDIUM};
                                    border: 2px solid {Colors.BORDER};
                                    border-radius: 4px;
                                }}
                            """)
                            break
                else:
                    return  # Can't select more

            frame.setProperty("selected", True)
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.ACCENT};
                    border: 2px solid {Colors.ACCENT};
                    border-radius: 4px;
                }}
            """)
            self.selected_cards.append(card)

        self._selection_label.setText(f"Selected: {len(self.selected_cards)}/{self.select_count}")
        self._update_ok_button()

    def _update_ok_button(self):
        ok_btn = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        if self.select_up_to:
            ok_btn.setEnabled(True)  # Can always confirm with 0 or more
        else:
            ok_btn.setEnabled(len(self.selected_cards) >= self.select_count)

    def get_result(self) -> List:
        return self.selected_cards


class AttributeChoiceDialog(ChoiceDialog):
    """Dialog for choosing an attribute"""

    ATTRIBUTE_COLORS = {
        'Light': "#ffd700",
        'Fire': "#ff4500",
        'Water': "#1e90ff",
        'Wind': "#32cd32",
        'Darkness': "#9932cc",
    }

    def __init__(self, prompt: str, attributes: List[str] = None, parent=None):
        super().__init__("Choose Attribute", prompt, parent)

        self.attributes = attributes or ['Light', 'Fire', 'Water', 'Wind', 'Darkness']
        self.selected_attribute = None

        # Attribute buttons in a row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._attr_buttons = []
        for attr in self.attributes:
            btn = QPushButton(attr)
            btn.setMinimumSize(80, 50)
            color = self.ATTRIBUTE_COLORS.get(attr, Colors.ACCENT)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: 2px solid {color};
                    border-radius: 6px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
                QPushButton:checked {{
                    border: 3px solid white;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, a=attr: self._on_attr_clicked(a))
            btn_layout.addWidget(btn)
            self._attr_buttons.append(btn)

        self._content_layout.addLayout(btn_layout)
        self._update_ok_button()

    def _on_attr_clicked(self, attr: str):
        self.selected_attribute = attr
        # Uncheck others
        for btn in self._attr_buttons:
            if btn.text() != attr:
                btn.setChecked(False)
        self._update_ok_button()

    def _update_ok_button(self):
        ok_btn = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(self.selected_attribute is not None)

    def get_result(self) -> str:
        return self.selected_attribute
