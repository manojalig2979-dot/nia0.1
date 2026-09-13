"""
bot3d_widget.py — NiaBot3DWidget
A QWebEngineView-based wrapper that renders the Three.js 3D bot avatar
and exposes a set_state() interface identical to HoloAvatarWidget.
"""

import os

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    _WEB_ENGINE_AVAILABLE = True
except ImportError:
    _WEB_ENGINE_AVAILABLE = False

# ── Asset path ────────────────────────────────────────────
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_HTML   = os.path.join(BASE_DIR, "nia_bot.html")


class NiaBot3DWidget(QWidget):
    """
    3D Animated Nia Bot Avatar.

    Drop-in replacement for HoloAvatarWidget.  Renders the Three.js
    WebGL scene inside a transparent QWebEngineView.

    Public API (matches HoloAvatarWidget):
        set_state(state: str)  — 'idle' | 'speaking' | 'working'
        set_voice_engine(voice_engine)  — accepted but unused (kept for compat)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self._voice_engine = None
        self._ready = False
        self._pending_state = None

        # Fixed size matching nia_bot.html canvas (W=280, H=360)
        self.setFixedSize(280, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        if not _WEB_ENGINE_AVAILABLE:
            # Graceful fallback: just a transparent placeholder
            self._view = None
            return

        self._view = QWebEngineView(self)
        self._view.setFixedSize(280, 360)
        self._view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._view.setStyleSheet("background: transparent;")

        # Configure WebEngine page settings
        page = self._view.page()
        settings = page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)

        # Transparent background
        page.setBackgroundColor(Qt.GlobalColor.transparent)

        # Load the HTML scene
        url = QUrl.fromLocalFile(BOT_HTML)
        self._view.load(url)
        self._view.loadFinished.connect(self._on_load_finished)

        lay.addWidget(self._view)

    # ── Internal ──────────────────────────────────────────

    def _on_load_finished(self, ok: bool):
        if ok:
            self._ready = True
            # Apply any state that was set before the page finished loading
            if self._pending_state:
                self._js_set_state(self._pending_state)
                self._pending_state = None
        else:
            print("[NiaBot3DWidget] Warning: 3D bot HTML failed to load.")

    def _js_set_state(self, state: str):
        """Send setState() call to the Three.js scene."""
        if self._view and self._ready:
            self._view.page().runJavaScript(f"setState('{state}');")

    # ── Public API (mirrors HoloAvatarWidget) ─────────────

    def set_state(self, state: str):
        """Switch the 3D avatar animation state."""
        self._state = state
        if self._ready:
            self._js_set_state(state)
        else:
            # Queue it — page hasn't finished loading yet
            self._pending_state = state

    def set_avatar_model(self, model_file: str):
        """Switch to another GLB stored in the local 3d-agent directory."""
        if self._view and self._ready:
            safe_name = os.path.basename(model_file)
            self._view.page().runJavaScript(
                f"setAvatarModel({safe_name!r});"
            )

    def set_voice_engine(self, voice_engine):
        """Kept for API compatibility with HoloAvatarWidget. Not needed for 3D bot."""
        self._voice_engine = voice_engine


def make_3d_bot_widget(parent=None) -> QWidget:
    """
    Factory that returns NiaBot3DWidget if WebEngine is available,
    otherwise falls back to HoloAvatarWidget so Nia always has an avatar.
    """
    if _WEB_ENGINE_AVAILABLE and os.path.exists(BOT_HTML):
        return NiaBot3DWidget(parent)

    # Fallback to original procedural widget
    try:
        from nia_gui import HoloAvatarWidget, AVATAR_PATH
        return HoloAvatarWidget(AVATAR_PATH, parent)
    except Exception as e:
        print(f"[NiaBot3D] Fallback also failed: {e}")
        placeholder = QWidget(parent)
        placeholder.setFixedSize(240, 320)
        placeholder.setStyleSheet("background: transparent;")
        placeholder.set_state = lambda s: None
        placeholder.set_voice_engine = lambda v: None
        return placeholder
