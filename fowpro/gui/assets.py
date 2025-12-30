"""
FoWPro Asset Manager
====================
Handles textures, backgrounds, card images, and skin management.
Similar to EDOPro's ImageManager.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Set
from dataclasses import dataclass, field
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal


@dataclass
class SkinConfig:
    """Configuration for a skin/theme"""
    name: str = "default"
    backgrounds: Dict[str, str] = field(default_factory=dict)
    colors: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> 'SkinConfig':
        """Load skin config from JSON file"""
        config_file = path / "skin.json"
        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return cls(**data)
        return cls(name=path.name)

    def save(self, path: Path):
        """Save skin config to JSON file"""
        config_file = path / "skin.json"
        with open(config_file, 'w') as f:
            json.dump({
                'name': self.name,
                'backgrounds': self.backgrounds,
                'colors': self.colors,
            }, f, indent=2)


class ImageDownloader(QThread):
    """Background thread for downloading card images"""

    image_ready = pyqtSignal(str, str)  # card_code, local_path

    CARD_IMAGE_URL = "https://fowsim.s3.amazonaws.com/media/cards/{}.jpg"

    def __init__(self, card_code: str, save_path: Path):
        super().__init__()
        self.card_code = card_code
        self.save_path = save_path

    def run(self):
        url = self.CARD_IMAGE_URL.format(self.card_code)
        try:
            # Create request with user agent
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'FoWPro/1.0'}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read()
                self.save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.save_path, 'wb') as f:
                    f.write(data)
                self.image_ready.emit(self.card_code, str(self.save_path))
        except Exception as e:
            print(f"Failed to download {self.card_code}: {e}")


class AssetManager:
    """
    Manages all game assets including:
    - Background images (menu, deck editor, duel)
    - Card images and thumbnails
    - UI textures
    - Skin/theme management
    """

    # Default gradient colors for generated backgrounds
    GRADIENT_PRESETS = {
        'menu': [('#1a1a2e', 0.0), ('#16213e', 0.5), ('#0f3460', 1.0)],
        'deck': [('#1a1a2e', 0.0), ('#2d132c', 0.5), ('#801336', 1.0)],
        'duel': [('#0d1b2a', 0.0), ('#1b263b', 0.5), ('#415a77', 1.0)],
        'settings': [('#1a1a2e', 0.0), ('#16213e', 0.5), ('#1e3a5f', 1.0)],
    }

    CARD_IMAGE_URL = "https://fowsim.s3.amazonaws.com/media/cards/{}.jpg"

    def __init__(self, base_path: str = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to project textures directory
            self.base_path = Path(__file__).parent.parent.parent / "textures"

        self.skins_path = self.base_path.parent / "skins"
        self.current_skin = "default"
        self.skin_config = SkinConfig()

        # Caches
        self._background_cache: Dict[str, QPixmap] = {}
        self._card_cache: Dict[str, QPixmap] = {}
        self._ui_cache: Dict[str, QPixmap] = {}

        # Custom background paths (user-configured)
        self.custom_backgrounds: Dict[str, str] = {}

        # Track pending downloads to avoid duplicates
        self._pending_downloads: Set[str] = set()
        self._download_threads: list = []

        # Initialize
        self._ensure_directories()
        self._load_skin_config()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.base_path / "backgrounds",
            self.base_path / "cards",
            self.base_path / "ui",
            self.skins_path / "default",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _load_skin_config(self):
        """Load current skin configuration"""
        skin_path = self.skins_path / self.current_skin
        if skin_path.exists():
            self.skin_config = SkinConfig.load(skin_path)
            self.custom_backgrounds = self.skin_config.backgrounds.copy()

    def set_skin(self, skin_name: str):
        """Switch to a different skin"""
        skin_path = self.skins_path / skin_name
        if skin_path.exists():
            self.current_skin = skin_name
            self._load_skin_config()
            self.clear_cache()

    def get_available_skins(self) -> list[str]:
        """Get list of available skins"""
        if not self.skins_path.exists():
            return ["default"]
        return [d.name for d in self.skins_path.iterdir() if d.is_dir()]

    def clear_cache(self):
        """Clear all cached images"""
        self._background_cache.clear()
        self._card_cache.clear()
        self._ui_cache.clear()

    # =========================================================================
    # BACKGROUND MANAGEMENT
    # =========================================================================

    def get_background(self, screen: str, size: QSize) -> QPixmap:
        """
        Get background for a screen (menu, deck, duel, settings).

        Priority:
        1. Custom user-set background
        2. Skin-specific background
        3. Default texture file
        4. Generated gradient
        """
        cache_key = f"{screen}_{size.width()}x{size.height()}"

        if cache_key in self._background_cache:
            return self._background_cache[cache_key]

        pixmap = None

        # Try custom background
        if screen in self.custom_backgrounds:
            custom_path = Path(self.custom_backgrounds[screen])
            if custom_path.exists():
                pixmap = self._load_and_scale(custom_path, size)

        # Try skin background
        if pixmap is None:
            skin_bg = self.skins_path / self.current_skin / "backgrounds" / f"{screen}.png"
            if skin_bg.exists():
                pixmap = self._load_and_scale(skin_bg, size)

        # Try default texture
        if pixmap is None:
            default_bg = self.base_path / "backgrounds" / f"{screen}.png"
            if default_bg.exists():
                pixmap = self._load_and_scale(default_bg, size)

        # Generate gradient as fallback
        if pixmap is None:
            pixmap = self._generate_gradient_background(screen, size)

        self._background_cache[cache_key] = pixmap
        return pixmap

    def set_custom_background(self, screen: str, path: str):
        """Set a custom background for a screen"""
        self.custom_backgrounds[screen] = path

        # Update skin config
        self.skin_config.backgrounds[screen] = path
        skin_path = self.skins_path / self.current_skin
        self.skin_config.save(skin_path)

        # Clear cache for this screen
        keys_to_remove = [k for k in self._background_cache if k.startswith(screen)]
        for k in keys_to_remove:
            del self._background_cache[k]

    def _load_and_scale(self, path: Path, size: QSize) -> Optional[QPixmap]:
        """Load an image and scale it to fit the size"""
        try:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap.scaled(
                    size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
        except Exception:
            pass
        return None

    def _generate_gradient_background(self, screen: str, size: QSize) -> QPixmap:
        """Generate a gradient background"""
        pixmap = QPixmap(size)
        painter = QPainter(pixmap)

        # Get gradient colors for this screen
        colors = self.GRADIENT_PRESETS.get(screen, self.GRADIENT_PRESETS['menu'])

        gradient = QLinearGradient(0, 0, size.width(), size.height())
        for color_hex, position in colors:
            gradient.setColorAt(position, QColor(color_hex))

        painter.fillRect(pixmap.rect(), QBrush(gradient))

        # Add subtle pattern overlay
        self._add_pattern_overlay(painter, size)

        painter.end()
        return pixmap

    def _add_pattern_overlay(self, painter: QPainter, size: QSize):
        """Add a subtle pattern overlay to backgrounds"""
        # Create a subtle grid pattern
        painter.setPen(QColor(255, 255, 255, 8))

        spacing = 50
        for x in range(0, size.width(), spacing):
            painter.drawLine(x, 0, x, size.height())
        for y in range(0, size.height(), spacing):
            painter.drawLine(0, y, size.width(), y)

    # =========================================================================
    # CARD IMAGE MANAGEMENT
    # =========================================================================

    def get_card_image(self, card_code: str, size: QSize = None) -> QPixmap:
        """Get card image by code - downloads from web if not cached locally"""
        if size is None:
            size = QSize(177, 254)  # Standard card size

        cache_key = f"{card_code}_{size.width()}x{size.height()}"

        if cache_key in self._card_cache:
            return self._card_cache[cache_key]

        # Try to find card image locally
        for ext in ['.png', '.jpg', '.jpeg']:
            card_path = self.base_path / "cards" / f"{card_code}{ext}"
            if card_path.exists():
                pixmap = self._load_and_scale(card_path, size)
                if pixmap:
                    self._card_cache[cache_key] = pixmap
                    return pixmap

        # Try to download synchronously (blocking but ensures image is shown)
        downloaded = self._download_card_image_sync(card_code)
        if downloaded:
            pixmap = self._load_and_scale(downloaded, size)
            if pixmap:
                self._card_cache[cache_key] = pixmap
                return pixmap

        # Return placeholder if download failed
        pixmap = self._generate_card_placeholder(card_code, size)
        self._card_cache[cache_key] = pixmap
        return pixmap

    def _download_card_image_sync(self, card_code: str) -> Optional[Path]:
        """Download card image synchronously, returns path if successful"""
        save_path = self.base_path / "cards" / f"{card_code}.jpg"
        if save_path.exists():
            return save_path

        url = self.CARD_IMAGE_URL.format(card_code)
        try:
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'FoWPro/1.0'}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read()
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(data)
                return save_path
        except Exception as e:
            print(f"Failed to download {card_code}: {e}")
            return None

    def prefetch_card_images(self, card_codes: list):
        """Start background download of multiple card images"""
        for code in card_codes:
            if code in self._pending_downloads:
                continue

            save_path = self.base_path / "cards" / f"{code}.jpg"
            if save_path.exists():
                continue

            self._pending_downloads.add(code)
            thread = ImageDownloader(code, save_path)
            thread.image_ready.connect(self._on_image_downloaded)
            thread.finished.connect(lambda t=thread: self._cleanup_thread(t))
            self._download_threads.append(thread)
            thread.start()

    def _on_image_downloaded(self, card_code: str, local_path: str):
        """Handle downloaded image"""
        self._pending_downloads.discard(card_code)
        # Clear any cached placeholder for this card
        keys_to_remove = [k for k in self._card_cache if k.startswith(card_code)]
        for k in keys_to_remove:
            del self._card_cache[k]

    def _cleanup_thread(self, thread):
        """Clean up finished download thread"""
        if thread in self._download_threads:
            self._download_threads.remove(thread)

    def get_card_thumbnail(self, card_code: str) -> QPixmap:
        """Get card thumbnail (44x64)"""
        return self.get_card_image(card_code, QSize(44, 64))

    def _generate_card_placeholder(self, card_code: str, size: QSize) -> QPixmap:
        """Generate a placeholder for missing card images"""
        pixmap = QPixmap(size)
        painter = QPainter(pixmap)

        # Dark background
        painter.fillRect(pixmap.rect(), QColor('#2a2a3a'))

        # Border
        painter.setPen(QColor('#4a4a5a'))
        painter.drawRect(0, 0, size.width() - 1, size.height() - 1)

        # Card code text
        painter.setPen(QColor('#888888'))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, card_code)

        painter.end()
        return pixmap

    # =========================================================================
    # UI TEXTURE MANAGEMENT
    # =========================================================================

    def get_ui_texture(self, name: str) -> Optional[QPixmap]:
        """Get a UI texture by name"""
        if name in self._ui_cache:
            return self._ui_cache[name]

        # Try skin path first
        for ext in ['.png', '.jpg']:
            skin_path = self.skins_path / self.current_skin / "ui" / f"{name}{ext}"
            if skin_path.exists():
                pixmap = QPixmap(str(skin_path))
                if not pixmap.isNull():
                    self._ui_cache[name] = pixmap
                    return pixmap

        # Try default path
        for ext in ['.png', '.jpg']:
            default_path = self.base_path / "ui" / f"{name}{ext}"
            if default_path.exists():
                pixmap = QPixmap(str(default_path))
                if not pixmap.isNull():
                    self._ui_cache[name] = pixmap
                    return pixmap

        return None

    def get_card_back(self, size: QSize = None) -> QPixmap:
        """Get card back image"""
        if size is None:
            size = QSize(177, 254)

        # Try to load card back texture
        back = self.get_ui_texture("card_back")
        if back:
            return back.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)

        # Generate default card back
        return self._generate_default_card_back(size)

    def _generate_default_card_back(self, size: QSize) -> QPixmap:
        """Generate default card back design"""
        pixmap = QPixmap(size)
        painter = QPainter(pixmap)

        # Dark purple gradient
        gradient = QLinearGradient(0, 0, size.width(), size.height())
        gradient.setColorAt(0.0, QColor('#1a0a2e'))
        gradient.setColorAt(0.5, QColor('#2d1b4e'))
        gradient.setColorAt(1.0, QColor('#1a0a2e'))
        painter.fillRect(pixmap.rect(), QBrush(gradient))

        # Pattern
        painter.setPen(QColor(255, 255, 255, 30))
        center_x, center_y = size.width() // 2, size.height() // 2
        for r in range(20, max(size.width(), size.height()), 20):
            painter.drawEllipse(center_x - r, center_y - r, r * 2, r * 2)

        # Border
        painter.setPen(QColor('#6a4a8a'))
        painter.drawRect(2, 2, size.width() - 5, size.height() - 5)
        painter.drawRect(5, 5, size.width() - 11, size.height() - 11)

        # FoW text
        painter.setPen(QColor('#9a7aba'))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "FoW")

        painter.end()
        return pixmap


# Global asset manager instance
_asset_manager: Optional[AssetManager] = None


def get_asset_manager() -> AssetManager:
    """Get the global asset manager instance"""
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetManager()
    return _asset_manager


def init_asset_manager(base_path: str = None) -> AssetManager:
    """Initialize the global asset manager with a custom path"""
    global _asset_manager
    _asset_manager = AssetManager(base_path)
    return _asset_manager
