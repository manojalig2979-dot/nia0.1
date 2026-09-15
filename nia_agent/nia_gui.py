"""
nia_gui.py  —  NIA Premium AI Desktop Interface
Futuristic cinematic command-center UI matching the design spec.
"""

import sys
import os
import threading
import math
from datetime import datetime

import psutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QGridLayout, QSpacerItem, QStackedWidget, QTextEdit,
    QSystemTrayIcon, QMenu, QComboBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPoint, QRect, QSize, QPropertyAnimation,
    QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient,
    QPixmap, QPalette, QFontMetrics, QIcon, QPainterPath, QConicalGradient
)

from config_manager import load_config
from gui_views import (
    ChatView, AppsView, WebView, SocialView, FilesView,
    MediaView, AutomationView, MemoryView, SettingsView,
    SmartHomeView
)
from whatsapp_manager import WhatsAppManager
from voice_listener import VoiceListenerThread
from bot3d_widget import make_3d_bot_widget

# ── Asset paths ──────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    STATE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATE_DIR = BASE_DIR
    
AVATAR_PATH = os.path.join(BASE_DIR, "nia_avatar.jpg")

# ── Colours ──────────────────────────────────────────────
C_BG        = "#08091a"       # deep navy
C_PANEL     = "rgba(15,20,50,180)"
C_SIDEBAR   = "rgba(12,16,42,220)"
C_BLUE      = "#3d8ef8"
C_CYAN      = "#00d4ff"
C_PURPLE    = "#9b59b6"
C_ACCENT    = "#1a3a6e"
C_SELECTED  = "#1e4fd8"
C_TEXT      = "#c8d8f8"
C_SUBTEXT   = "#5a6a9a"
C_BORDER    = "rgba(61,142,248,0.25)"
C_GREEN     = "#00e676"


# ══════════════════════════════════════════════════════════
#  Unified Command Execution Router
# ══════════════════════════════════════════════════════════
import re

def clean_command_text(cmd: str) -> str:
    """Cleans command text, strips punctuation, wake words, and common fillers."""
    t = cmd.strip()
    # Remove leading/trailing punctuation
    t = re.sub(r'^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$', '', t)
    
    lower = t.lower()
    # Strip wake word prefixes
    wake_words = ["hey nia", "sun nia", "ok nia", "namaste nia", "hello nia", "nia"]
    for w in wake_words:
        if lower.startswith(w):
            t = t[len(w):].strip()
            t = re.sub(r'^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$', '', t)
            break
            
    return t.strip()

def execute_unified_command(agent, cmd: str) -> str:
    """
    Unified execution router for all command sources:
    GUI chat box, Voice Recognition, and WhatsApp Remote Commands.
    Executes local desktop actions immediately without LLM delay/quota issues.
    """
    if not agent:
        return "Nia systems are warming up. Please try in a moment."

    clean_cmd = clean_command_text(cmd)
    c = clean_cmd.lower().strip()

    if not c:
        return "Haanji, batayein main aapki kya madad kar sakti hoon?"

    # 0. Check custom workflows
    try:
        from workflow_manager import WorkflowManager
        if not hasattr(agent, "workflow_manager"):
            agent.workflow_manager = WorkflowManager(os.path.join(os.path.dirname(__file__), "workflows.json"))
        
        wf = agent.workflow_manager.get_match(c)
        if wf:
            # We found a custom routine! Let's execute its steps.
            actions = wf.get("actions", [])
            if not actions:
                return f"Routine '{wf['name']}' has no actions configured."
            
            # Note: We emit them directly or recursively call. 
            # Recursively calling execute_unified_command for each action.
            results = []
            for act in actions:
                res = execute_unified_command(agent, act)
                results.append(res)
            return f"Executed routine '{wf['name']}':\n" + "\n".join(f"- {r}" for r in results if r)
    except Exception as e:
        pass

    # 1. URL opening
    if c.startswith("open url ") or c.startswith("url "):
        url = clean_cmd.split(None, 2)[-1].strip()
        agent.desktop.open_url(url)
        return f"Opened {url} in your default browser."

    if c in {"check system status", "system status", "check diagnostics", "run diagnostics"}:
        if hasattr(agent, "diagnostics"):
            return agent.diagnostics.get_status_summary()
        return "AI status unavailable."

    # 2. Calculator (English, Hinglish, Hindi)
    calc_keywords = ["calculator", "calc", "कैलकुलेटर", "hisaab", "hisab"]
    if any(k in c for k in calc_keywords):
        agent.desktop.open_application("calculator")
        return "Calculator open kar diya hai."

    # 3. Notepad (English, Hinglish, Hindi)
    notepad_keywords = ["notepad", "note pad", "नोटपैड"]
    if any(k in c for k in notepad_keywords):
        agent.desktop.open_application("notepad")
        return "Notepad open kar diya hai."

    # 4. Google Chrome / Browser
    chrome_keywords = ["chrome", "google chrome", "क्रोम", "browser"]
    if any(k in c for k in chrome_keywords):
        agent.desktop.open_application("chrome")
        return "Google Chrome open kar diya hai."

    # 5. MS Paint
    paint_keywords = ["mspaint", "paint", "पेंट", "drawing"]
    if any(k in c for k in paint_keywords):
        agent.desktop.open_application("mspaint")
        return "MS Paint open kar diya hai."

    # 6. VS Code
    vscode_keywords = ["vs code", "vscode", "visual studio code"]
    if any(k in c for k in vscode_keywords):
        agent.desktop.open_application("code")
        return "Visual Studio Code launch kar diya hai."

    # 7. Task Manager
    taskmgr_keywords = ["taskmgr", "task manager", "टास्क मैनेजर"]
    if any(k in c for k in taskmgr_keywords):
        agent.desktop.open_application("taskmgr")
        return "Task Manager open kar diya hai."

    # 8. File Explorer
    explorer_keywords = ["file explorer", "explorer", "my computer", "this pc"]
    if any(k in c for k in explorer_keywords):
        agent.desktop.open_application("explorer")
        return "File Explorer open kar diya hai."

    # 9. CMD / Terminal
    cmd_keywords = ["command prompt", "terminal", "cmd", "powershell"]
    if any(k in c for k in cmd_keywords):
        agent.desktop.open_application("cmd")
        return "Command Prompt open kar diya hai."

    # 10. Windows Media Player (standalone)
    wmp_keywords = ["windows media player", "media player", "wmplayer", "wmp"]
    if any(k in c for k in wmp_keywords) and not any(k in c for k in ["song", "gana", "play", "bajao"]):
        return agent.desktop.play_in_windows_media_player("")

    # 11. Screenshots
    if any(k in c for k in ("screenshot", "screen shot", "स्क्रीनशॉट", "capture screen")):
        path = agent.desktop.take_screenshot()
        return f"Screenshot saved to Pictures: {os.path.basename(path)}"

    # 12. Music & Songs (Default Windows Media Player, YouTube only if mentioned)
    music_triggers = ["play", "gana", "gaana", "song", "music", "bajao", "bajana", "गाना", "गीत", "संगीत"]
    if any(k in c for k in music_triggers):
        song_query = clean_cmd
        for trig in ["open", "launch", "start", "play", "chalao", "gana bajao", "song bajao", "gana chalao", "song play karo", "bajana", "bajao", "gana", "song", "music", "गाना", "गीत", "संगीत"]:
            song_query = re.sub(rf'\b{trig}\b', '', song_query, flags=re.IGNORECASE).strip()
        
        if "youtube" in c or "यूट्यूब" in c:
            clean = re.sub(r'\b(on youtube|in youtube|youtube|यूट्यूब)\b', '', song_query, flags=re.IGNORECASE).strip()
            return agent.browser.play_song(clean or "popular songs")
        else:
            return agent.desktop.play_in_windows_media_player(song_query.strip())

    # 13. Generic "open <app>" or "<app> kholo / open karo"
    open_triggers = ["open ", "launch ", "start ", "chalao ", "kholo "]
    for trig in open_triggers:
        if c.startswith(trig):
            app_target = clean_cmd[len(trig):].strip()
            app_target = re.sub(r'\b(karo|khol do|chala do|please|app)\b', '', app_target, flags=re.IGNORECASE).strip()
            if app_target:
                return agent.desktop.open_application(app_target)

    if any(c.endswith(s) for s in [" kholo", " open karo", " chalao", " start karo", " launch karo", " khol do"]):
        app_target = re.sub(r'\b(kholo|open karo|chalao|start karo|launch karo|khol do)\b', '', clean_cmd, flags=re.IGNORECASE).strip()
        if app_target:
            return agent.desktop.open_application(app_target)

    # 14. System Power Controls
    if "shutdown" in c or "band karo system" in c or "pc band karo" in c:
        if "cancel" in c or "stop" in c:
            return agent.desktop.system_power_control("cancel")
        return agent.desktop.system_power_control("shutdown")
    elif "restart" in c or "reboot" in c:
        return agent.desktop.system_power_control("restart")

    # 15. Web Search
    if c.startswith("search ") or c.startswith("google ") or c.startswith("khojo "):
        query = clean_cmd.split(None, 1)[-1].strip()
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        agent.desktop.open_url(url)
        return f"Searching Google for: {query}"

    # 16. Common Conversational / Greeting fallbacks (instant, zero LLM needed)
    from datetime import datetime
    user_name = getattr(agent, "user_name", "User")
    if any(w in c for w in ("hello", "hi", "namaste", "hey", "नमस्ते")):
        return f"Namaste {user_name} ji! Main Nia hoon. Main aapki kya madad kar sakti hoon?"
    elif any(w in c for w in ("kaise ho", "kya haal", "how are you")):
        return "Main bilkul theek hoon! Aap batayein, aaj computer me kya kaam karna hai?"
    elif any(w in c for w in ("samay", "time", "date", "tarikh", "din", "waqt")):
        now = datetime.now()
        return f"Abhi samay hai: {now.strftime('%I:%M %p')}, aur date hai: {now.strftime('%d %B %Y')}."
    elif any(w in c for w in ("who are you", "kaun ho", "kya kar sakti ho", "tum kaun ho")):
        return f"Main Nia hoon, {user_name} ji ki personal desktop AI assistant. Main apps khol sakti hoon, gaane chala sakti hoon, WhatsApp handle karti hoon aur computer control karti hoon."

    # 17. Calendar / Reminder / Alarms
    if any(k in c for k in ("remind", "alarm", "timer", "schedule", "yaad dilana")):
        try:
            from reminder_manager import ReminderManager
            
            # Extract time text
            time_str = "in 5 minutes"
            # simple heuristic: everything after 'for', 'at', 'in'
            m = re.search(r'\b(at|in|for)\b\s+(.+)', c, flags=re.IGNORECASE)
            if m:
                time_str = m.group(0).strip()

            # The reminder text
            rem_text = clean_cmd
            for w in ("set alarm", "set a reminder", "set reminder", "remind me to", "remind me", "alarm", "timer", "yaad dilana"):
                rem_text = re.sub(rf'\b{w}\b', '', rem_text, flags=re.IGNORECASE).strip()
            rem_text = re.sub(r'^(for|at|in|to)\s+', '', rem_text, flags=re.IGNORECASE).strip()

            if not hasattr(agent, "reminder_manager"):
                agent.reminder_manager = ReminderManager(os.path.join(os.path.dirname(__file__), "reminders.json"))
                agent.reminder_manager.start()

            success, msg = agent.reminder_manager.add_reminder(rem_text or "Alarm", time_str)
            return msg
        except Exception as e:
            return f"Reminder error: {e}"

    # 18. Computer Vision / Screen Understanding
    if any(k in c for k in ("look at my screen", "what is on my screen", "read my screen", "read this error", "screen pe kya", "what's on my screen", "screen dekh", "dekh kar batao")):
        return agent.analyze_screen(clean_cmd)

    # 19. AI Brain / Orchestrator for complex reasoning
    return agent.process_command(cmd)



# ══════════════════════════════════════════════════════════
#  Worker thread
# ══════════════════════════════════════════════════════════
class NiaWorker(QThread):
    response_ready = pyqtSignal(str)
    done           = pyqtSignal()

    def __init__(self, agent, voice, cmd):
        super().__init__()
        self.agent = agent
        self.voice = voice
        self.cmd   = cmd

    def run(self):
        try:
            reply = execute_unified_command(self.agent, self.cmd)
        except Exception as e:
            reply = f"Error executing command: {str(e)}"

        self.response_ready.emit(reply)
        if self.voice:
            threading.Thread(target=self.voice.speak, args=(reply,), daemon=True).start()
        self.done.emit()



class InitWorker(QThread):
    ready = pyqtSignal(object, object)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            from voice_engine import VoiceEngine
            from agent_orchestrator import NiaAgentOrchestrator
            voice = VoiceEngine(
                tts_voice=self.config["voice_settings"]["tts_voice"],
                whisper_size=self.config["voice_settings"]["whisper_model_size"]
            )
            agent = NiaAgentOrchestrator(self.config)
            self.ready.emit(agent, voice)
        except Exception as e:
            print(f"[InitWorker Error]: {e}")
            self.ready.emit(None, None)


# ══════════════════════════════════════════════════════════
#  Circular progress ring widget
# ══════════════════════════════════════════════════════════
class RingWidget(QWidget):
    def __init__(self, label, color="#3d8ef8", parent=None):
        super().__init__(parent)
        self.label    = label
        self.color    = QColor(color)
        self._value   = 0
        self.setFixedSize(66, 66)

    def set_value(self, v):
        self._value = max(0, min(100, v))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = self.width()//2, self.height()//2, 24
        # Track
        p.setPen(QPen(QColor(255,255,255,18), 4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)
        # Arc
        span = int(-360 * self._value / 100 * 16)
        pen  = QPen(self.color, 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(cx-r, cy-r, r*2, r*2, 90*16, span)
        # Value text
        p.setPen(QPen(QColor(C_TEXT)))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRect(cx-r, cy-9, r*2, 18), Qt.AlignmentFlag.AlignCenter, f"{self._value}%")
        # Label
        p.setPen(QPen(QColor(C_SUBTEXT)))
        p.setFont(QFont("Segoe UI", 7))
        p.drawText(QRect(cx-r, cy+7, r*2, 14), Qt.AlignmentFlag.AlignCenter, self.label)


# ══════════════════════════════════════════════════════════
#  Waveform widget (animated)
# ══════════════════════════════════════════════════════════
class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setMinimumWidth(120)
        self._phase = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(50)

    def _tick(self):
        self._phase += 0.18
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h // 2
        bars = 28
        bar_w = w / bars
        for i in range(bars):
            amp  = 10 * abs(math.sin(self._phase + i * 0.45))
            amp  = max(2, amp)
            alpha = int(140 + 80 * abs(math.sin(self._phase + i * 0.3)))
            c = QColor(C_BLUE)
            c.setAlpha(alpha)
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(
                int(i * bar_w + 1), int(mid - amp),
                max(2, int(bar_w - 2)), int(amp * 2), 1, 1
            )


# ══════════════════════════════════════════════════════════
#  Glass Panel base
# ══════════════════════════════════════════════════════════
class GlassPanel(QFrame):
    def __init__(self, parent=None, radius=14, border_color="#3d8ef8"):
        super().__init__(parent)
        self._radius = radius
        self._border = QColor(border_color)
        self._border.setAlpha(60)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(),
                            self._radius, self._radius)
        # Fill
        p.fillPath(path, QColor(10, 16, 46, 200))
        # Border
        p.setPen(QPen(self._border, 1))
        p.drawPath(path)


# ══════════════════════════════════════════════════════════
#  Header bar
# ══════════════════════════════════════════════════════════
class HeaderBar(QWidget):
    close_requested    = pyqtSignal()
    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    notifications_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #08091a, stop:0.5 #0c1230, stop:1 #08091a);
            border-bottom: 1px solid rgba(61,142,248,0.2);
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 16, 0)

        # Logo
        logo = QLabel("NIA")
        logo.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {C_BLUE}; letter-spacing: 4px;")

        taglines = QVBoxLayout()
        taglines.setSpacing(0)
        t1 = QLabel("Your AI Companion")
        t1.setFont(QFont("Segoe UI", 9))
        t1.setStyleSheet(f"color: {C_TEXT};")
        t2 = QLabel("Always With You")
        t2.setFont(QFont("Segoe UI", 8))
        t2.setStyleSheet(f"color: {C_SUBTEXT};")
        taglines.addWidget(t1)
        taglines.addWidget(t2)

        lay.addWidget(logo)
        lay.addSpacing(12)
        lay.addLayout(taglines)
        lay.addStretch()

        # Right icons
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(36, 36)
        notif_btn.setToolTip("Notifications")
        notif_btn.setStyleSheet(self._icon_style())
        notif_btn.clicked.connect(self.notifications_requested.emit)
        lay.addWidget(notif_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip("Settings")
        settings_btn.setStyleSheet(self._icon_style())
        settings_btn.clicked.connect(self.settings_requested.emit)
        lay.addWidget(settings_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet("color: rgba(61,142,248,0.25);")
        lay.addWidget(sep)
        lay.addSpacing(4)

        for icon, tip, signal in [
            ("─", "Minimize", self.minimize_requested),
            ("□", "Maximize", self.maximize_requested),
            ("✕", "Close",    self.close_requested),
        ]:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setToolTip(tip)
            btn.setStyleSheet(self._icon_style(
                hover="#c0392b" if icon == "✕" else "#1a3a6e"
            ))
            if signal:
                btn.clicked.connect(signal.emit)
            lay.addWidget(btn)

        self._drag_pos = None

    def _icon_style(self, hover="#1a2a5a"):
        return f"""
            QPushButton {{
                background: transparent; color: {C_TEXT};
                font-size: 14px; border: none; border-radius: 8px;
            }}
            QPushButton:hover {{ background: {hover}; color: white; }}
        """

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ══════════════════════════════════════════════════════════
#  Left sidebar
# ══════════════════════════════════════════════════════════
NAV_ITEMS = [
    ("⌂", "Home"),
    ("💬", "Chat"),
    ("⊞", "Apps & Control"),
    ("🌐", "Web & Search"),
    ("◈", "Social Media"),
    ("📄", "Files & Documents"),
    ("♫", "Media"),
    ("⚡", "Automation"),
    ("🧠", "Learning & Memory"),
    ("⚙", "Settings"),
    ("💡", "Smart Home"),
]

class Sidebar(QWidget):
    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(175)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #080918, stop:1 #0c1030);
            border-right: 1px solid rgba(61,142,248,0.15);
        """)
        self._selected = "Home"
        self._buttons  = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 18, 10, 18)
        outer.setSpacing(4)

        for icon, name in NAV_ITEMS:
            btn = self._make_nav_btn(icon, name)
            self._buttons[name] = btn
            outer.addWidget(btn)

        outer.addStretch()

        # Bottom tagline
        tag = QLabel('"More than an assistant\nA companion for a better you"')
        tag.setFont(QFont("Segoe UI", 8))
        tag.setStyleSheet(f"color: {C_SUBTEXT}; padding: 8px 4px;")
        tag.setWordWrap(True)
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(tag)

        self._update_styles()

    def _make_nav_btn(self, icon, name):
        btn = QPushButton(f"  {icon}  {name}")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _, n=name: self._select(n))
        return btn

    def _select(self, name):
        self._selected = name
        self._update_styles()
        self.nav_changed.emit(name)

    def _update_styles(self):
        for name, btn in self._buttons.items():
            if name == self._selected:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 {C_SELECTED}, stop:1 #1230a0);
                        color: white;
                        border: 1px solid rgba(61,142,248,0.5);
                        border-radius: 10px;
                        text-align: left; padding-left: 8px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {C_SUBTEXT};
                        border: none; border-radius: 10px;
                        text-align: left; padding-left: 8px;
                    }}
                    QPushButton:hover {{
                        background: rgba(61,142,248,0.12);
                        color: {C_TEXT};
                    }}
                """)


# ══════════════════════════════════════════════════════════
#  Right info panel
# ══════════════════════════════════════════════════════════
class RightPanel(GlassPanel):
    app_clicked = pyqtSignal(str)
    activity_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, radius=0)
        self.setFixedWidth(260)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:1,y1:0,x2:0,y2:0,
                stop:0 #080918, stop:1 #0c1030);
            border-left: 1px solid rgba(61,142,248,0.15);
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(61, 142, 248, 0.35);
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 212, 255, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(10)

        # ─ Time & Greeting ───────────────────
        time_panel = GlassPanel(radius=12)
        tp = QVBoxLayout(time_panel)
        tp.setContentsMargins(12, 10, 12, 10)
        tp.setSpacing(2)

        self.date_lbl = QLabel()
        self.date_lbl.setFont(QFont("Segoe UI", 9))
        self.date_lbl.setStyleSheet(f"color: {C_SUBTEXT};")

        self.time_lbl = QLabel()
        self.time_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet(f"color: {C_TEXT};")

        self.greet_lbl = QLabel()
        self.greet_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.greet_lbl.setStyleSheet(f"color: {C_TEXT};")

        sub = QLabel("Let's make today productive.")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet(f"color: {C_SUBTEXT};")

        tp.addWidget(self.date_lbl)
        tp.addWidget(self.time_lbl)
        tp.addWidget(self.greet_lbl)
        tp.addWidget(sub)
        lay.addWidget(time_panel)

        # ─ System Status ─────────────────────
        sys_panel = GlassPanel(radius=12)
        sp = QVBoxLayout(sys_panel)
        sp.setContentsMargins(10, 10, 10, 10)
        sp.setSpacing(8)

        sh = QHBoxLayout()
        stitle = QLabel("System Status")
        stitle.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        stitle.setStyleSheet(f"color: {C_TEXT};")
        sready = QLabel("🟢 Ready")
        sready.setFont(QFont("Segoe UI", 8))
        sready.setStyleSheet(f"color: {C_GREEN};")
        sh.addWidget(stitle)
        sh.addStretch()
        sh.addWidget(sready)
        sp.addLayout(sh)

        rings_row = QHBoxLayout()
        rings_row.setSpacing(6)
        rings_row.setContentsMargins(0, 0, 0, 0)
        self.cpu_ring = RingWidget("CPU",     C_BLUE)
        self.ram_ring = RingWidget("RAM",     C_CYAN)
        self.sto_ring = RingWidget("Storage", C_PURPLE)
        rings_row.addWidget(self.cpu_ring)
        rings_row.addWidget(self.ram_ring)
        rings_row.addWidget(self.sto_ring)
        sp.addLayout(rings_row)
        lay.addWidget(sys_panel)

        # ─ Quick Launch ──────────────────────
        ql_panel = GlassPanel(radius=12)
        ql = QVBoxLayout(ql_panel)
        ql.setContentsMargins(10, 10, 10, 10)
        ql.setSpacing(8)

        qlh = QHBoxLayout()
        qlt = QLabel("Quick Launch")
        qlt.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        qlt.setStyleSheet(f"color: {C_TEXT};")
        qle = QPushButton("Edit")
        qle.setCursor(Qt.CursorShape.PointingHandCursor)
        qle.setStyleSheet(f"background:transparent; color:{C_BLUE}; border:none; font-size:10px;")
        qle.clicked.connect(lambda: self.app_clicked.emit("Apps & Control"))
        qlh.addWidget(qlt)
        qlh.addStretch()
        qlh.addWidget(qle)
        ql.addLayout(qlh)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(0, 2, 0, 0)
        apps = [
            ("🌐","Chrome"),("📝","Notepad"),("💬","WhatsApp"),("▶","YouTube"),
            ("🎵","Spotify"),("⌨","VS Code"),("✈","Telegram"),("➕","Add"),
        ]
        for i, (icon, name) in enumerate(apps):
            btn = self._app_btn(icon, name)
            grid.addWidget(btn, i//4, i%4)
        ql.addLayout(grid)
        lay.addWidget(ql_panel)

        # ─ Recent Activity ───────────────────
        ra_panel = GlassPanel(radius=12)
        ra = QVBoxLayout(ra_panel)
        ra.setContentsMargins(10, 10, 10, 10)
        ra.setSpacing(6)

        rah = QHBoxLayout()
        rat = QLabel("Recent Activity")
        rat.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        rat.setStyleSheet(f"color: {C_TEXT};")
        clr = QPushButton("Clear")
        clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet(f"background:transparent; color:{C_BLUE}; border:none; font-size:10px;")
        clr.clicked.connect(self._clear_activity)
        rah.addWidget(rat)
        rah.addStretch()
        rah.addWidget(clr)
        ra.addLayout(rah)

        self.activity_lay = QVBoxLayout()
        self.activity_lay.setSpacing(6)
        activities = [
            ("🌐", "Opened Chrome",           "05:40 PM"),
            ("🎵", "Played Arijit Singh Radio","05:32 PM"),
            ("💬", "Checked WhatsApp",         "05:20 PM"),
            ("🔍", "Searched: latest AI news", "05:15 PM"),
            ("📝", "Opened Notepad",           "05:10 PM"),
        ]
        for icon, text, time in activities:
            self.activity_lay.addWidget(self._activity_row(icon, text, time))
        ra.addLayout(self.activity_lay)
        lay.addWidget(ra_panel)

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Live clock + stats timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._refresh)
        self._clock_timer.start(2000)
        self._refresh()

    def _clear_activity(self):
        while self.activity_lay.count():
            item = self.activity_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh(self):
        now = datetime.now()
        self.date_lbl.setText(now.strftime("%A, %d %b %Y"))
        self.time_lbl.setText(now.strftime("%I:%M %p"))
        hour = now.hour
        if hour < 12:
            greet = "Good Morning!"
        elif hour < 17:
            greet = "Good Afternoon!"
        else:
            greet = "Good Evening!"
        self.greet_lbl.setText(greet)

        self.cpu_ring.set_value(int(psutil.cpu_percent()))
        self.ram_ring.set_value(int(psutil.virtual_memory().percent))
        disk = psutil.disk_usage('/')
        self.sto_ring.set_value(int(disk.percent))

    def _app_btn(self, icon, name):
        btn = QPushButton(f"{icon}\n{name}")
        btn.setFixedSize(48, 48)
        btn.setFont(QFont("Segoe UI", 7))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(61,142,248,0.08);
                color: {C_TEXT};
                border: 1px solid rgba(61,142,248,0.18);
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: rgba(61,142,248,0.22);
                border-color: rgba(61,142,248,0.5);
                color: white;
            }}
        """)
        btn.clicked.connect(lambda _, n=name: self.app_clicked.emit(n))
        return btn

    def _activity_row(self, icon, text, time_str):
        row = QPushButton()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet("""
            QPushButton { background: transparent; border: none; text-align: left; }
            QPushButton:hover { background: rgba(61,142,248,0.12); border-radius: 6px; }
        """)
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)
        ic = QLabel(icon)
        ic.setFixedWidth(16)
        tx = QLabel(text)
        tx.setFont(QFont("Segoe UI", 8))
        tx.setStyleSheet(f"color: {C_TEXT};")
        tm = QLabel(time_str)
        tm.setFont(QFont("Segoe UI", 7))
        tm.setStyleSheet(f"color: {C_SUBTEXT};")
        h.addWidget(ic)
        h.addWidget(tx)
        h.addStretch()
        h.addWidget(tm)
        row.clicked.connect(lambda _, t=text: self.activity_clicked.emit(t))
        return row

    def add_activity(self, icon, text):
        now = datetime.now().strftime("%I:%M %p")
        row = self._activity_row(icon, text, now)
        self.activity_lay.insertWidget(0, row)


# ══════════════════════════════════════════════════════════
#  3D Holographic Avatar Widget — Procedural Face (no images)
# ══════════════════════════════════════════════════════════
class HoloAvatarWidget(QWidget):
    MOUTH_CLOSED = 0
    MOUTH_SLIGHT = 1
    MOUTH_OPEN   = 2
    MOUTH_WIDE   = 3

    def __init__(self, avatar_path, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 310)
        self.state = "idle"
        self._voice_engine = None

        self._angle1 = 0.0
        self._angle2 = 1.57
        self._scan_y = 10.0
        self._scan_dir = 1.0
        self._pulse = 0.0
        self._pulse_dir = 1.0

        self._bob_phase  = 0.0
        self._bob_offset = 0.0

        self._blink_phase    = 0.0
        self._blink_dir      = 0.0
        self._blink_timer    = 0
        self._blink_interval = 130

        self._current_mouth = 0
        self._target_mouth  = 0
        self._amp_smooth    = 0.0

        self._sway_phase = 0.0
        self._tick_count = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_voice_engine(self, voice_engine):
        self._voice_engine = voice_engine

    def set_state(self, state):
        self.state = state
        self.update()

    def _tick(self):
        self._tick_count += 1
        speed = 2.8 if self.state == "working" else (1.8 if self.state == "speaking" else 1.0)
        self._angle1 = (self._angle1 + 0.035 * speed) % (math.pi * 2)
        self._angle2 = (self._angle2 - 0.025 * speed) % (math.pi * 2)
        self._sway_phase = (self._sway_phase + 0.018) % (math.pi * 2)

        scan_speed = 4.0 if self.state == "working" else 1.8
        self._scan_y += scan_speed * self._scan_dir
        if self._scan_y > 220: self._scan_dir = -1.0
        elif self._scan_y < 12: self._scan_dir = 1.0

        pulse_speed = 0.06 if self.state == "working" else 0.025
        self._pulse += pulse_speed * self._pulse_dir
        if self._pulse > 1.0:
            self._pulse = 1.0; self._pulse_dir = -1.0
        elif self._pulse < 0.0:
            self._pulse = 0.0; self._pulse_dir = 1.0

        # Natural blink
        if self._blink_dir == 0.0:
            self._blink_timer += 1
            if self._blink_timer >= self._blink_interval:
                self._blink_timer = 0
                self._blink_interval = 100 + int(80 * abs(math.sin(self._tick_count * 0.07)))
                self._blink_dir = 1.0
        else:
            self._blink_phase += self._blink_dir * 0.25
            if self._blink_phase >= 1.0:
                self._blink_phase = 1.0
                self._blink_dir = -1.0
            elif self._blink_phase <= 0.0:
                self._blink_phase = 0.0
                self._blink_dir = 0.0

        if self.state == "speaking" and self._voice_engine:
            raw_amp = self._voice_engine.get_speaking_amplitude()
            alpha = 0.35
            self._amp_smooth = alpha * raw_amp + (1 - alpha) * self._amp_smooth
            amp = self._amp_smooth
            if amp < 0.18:
                self._target_mouth = self.MOUTH_CLOSED
            elif amp < 0.40:
                self._target_mouth = self.MOUTH_SLIGHT
            elif amp < 0.70:
                self._target_mouth = self.MOUTH_OPEN
            else:
                self._target_mouth = self.MOUTH_WIDE
            self._current_mouth = self._target_mouth
            self._bob_phase = (self._bob_phase + 0.12) % (math.pi * 2)
            self._bob_offset = 3.0 * math.sin(self._bob_phase)
        else:
            self._amp_smooth = max(0.0, self._amp_smooth - 0.05)
            if self._amp_smooth < 0.05:
                self._current_mouth = self.MOUTH_CLOSED
                self._amp_smooth = 0.0
            self._bob_offset *= 0.85

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # --- Layout ---
        bob_y  = int(self._bob_offset)
        sway_x = int(math.sin(self._sway_phase) * 2.5)
        W, H   = 220, 275
        cx     = W // 2 + sway_x
        face_top = 12 + bob_y
        face_w   = 152
        face_h   = 195
        face_x   = cx - face_w // 2
        face_cy  = face_top + face_h // 2

        # --- State colours ---
        if self.state == "working":
            aura_c1  = QColor(0,  212, 255, int(90 + 50 * self._pulse))
            aura_c2  = QColor(0,  30,  60,  0)
            glow_pen = QColor(0,  212, 255, int(150 + 80 * self._pulse))
            eye_glow = QColor(0,  240, 255, 230)
            scan_c   = QColor(0,  212, 255, 55)
        elif self.state == "speaking":
            pa       = self._amp_smooth
            aura_c1  = QColor(175, 70, 255, int(80 + 70 * self._pulse + 30 * pa))
            aura_c2  = QColor(20,  0,  50,  0)
            glow_pen = QColor(200, 100, 255, int(150 + 80 * self._pulse + 40 * pa))
            eye_glow = QColor(200, 120, 255, 230)
            scan_c   = QColor(180, 80,  255, 50)
        else:
            aura_c1  = QColor(61,  142, 248, int(45 + 30 * self._pulse))
            aura_c2  = QColor(12,  20,  60,  0)
            glow_pen = QColor(61,  142, 248, int(80 + 40 * self._pulse))
            eye_glow = QColor(0,   212, 255, 200)
            scan_c   = QColor(61,  142, 248, 38)

        # --- L1: Outer ambient aura ---
        rad = QRadialGradient(cx, face_cy, 145)
        rad.setColorAt(0,   aura_c1)
        rad.setColorAt(0.5, QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), aura_c1.alpha() // 3))
        rad.setColorAt(1,   aura_c2)
        p.setBrush(QBrush(rad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRect(2, face_top - 8, 216, face_h + 24), 22, 22)

        # --- L2: Face shape ---
        fw2   = face_w // 2
        dome_h = int(face_h * 0.55)
        chin_y = face_top + face_h
        face_path = QPainterPath()
        face_path.moveTo(cx, face_top)
        face_path.cubicTo(cx + fw2 * 0.90, face_top,
                          cx + fw2,         face_top + dome_h * 0.35,
                          cx + fw2,         face_top + dome_h)
        face_path.cubicTo(cx + fw2,             face_top + dome_h + int(face_h * 0.28),
                          cx + int(fw2 * 0.42), chin_y,
                          cx,                    chin_y)
        face_path.cubicTo(cx - int(fw2 * 0.42), chin_y,
                          cx - fw2,              face_top + dome_h + int(face_h * 0.28),
                          cx - fw2,              face_top + dome_h)
        face_path.cubicTo(cx - fw2,         face_top + dome_h * 0.35,
                          cx - fw2 * 0.90,  face_top,
                          cx,               face_top)
        face_path.closeSubpath()

        skin_grad = QLinearGradient(cx, face_top, cx, chin_y)
        skin_grad.setColorAt(0.0,  QColor(28, 38, 72,  255))
        skin_grad.setColorAt(0.18, QColor(22, 32, 58,  255))
        skin_grad.setColorAt(0.45, QColor(18, 26, 50,  255))
        skin_grad.setColorAt(0.80, QColor(14, 20, 42,  255))
        skin_grad.setColorAt(1.0,  QColor(10, 14, 32,  255))
        p.setBrush(QBrush(skin_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(face_path)

        p.save()
        p.setClipPath(face_path)

        # Forehead sheen
        sheen_g = QRadialGradient(cx, face_top + int(face_h * 0.14), int(face_w * 0.55))
        sheen_g.setColorAt(0, QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), 55))
        sheen_g.setColorAt(0.6, QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), 18))
        sheen_g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(sheen_g)); p.drawPath(face_path)

        # Cheekbone highlights
        for side in [-1, 1]:
            ck_x = cx + side * int(fw2 * 0.62)
            ck_y = face_top + int(face_h * 0.48)
            ck_g = QRadialGradient(ck_x, ck_y, 28)
            ck_g.setColorAt(0, QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), 32))
            ck_g.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(ck_g)); p.drawEllipse(ck_x - 28, ck_y - 16, 56, 32)

        # --- L3: Eyes ---
        eye_y      = face_top + int(face_h * 0.33)
        eye_rx     = int(fw2 * 0.44)
        eye_w      = 30
        eye_h_max  = 17
        blink_scale = 1.0 - self._blink_phase

        for side in [-1, 1]:
            ex = cx + side * eye_rx
            ey = eye_y
            eh = max(1, int(eye_h_max * blink_scale))
            ew = eye_w

            # Sclera
            sc_g = QRadialGradient(ex, ey, ew // 2)
            sc_g.setColorAt(0,   QColor(210, 225, 245, 240))
            sc_g.setColorAt(0.7, QColor(175, 195, 220, 230))
            sc_g.setColorAt(1,   QColor(130, 160, 200, 210))
            p.setBrush(QBrush(sc_g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(ex - ew // 2, ey - eh // 2, ew, eh)

            if blink_scale > 0.15:
                iris_r = max(2, int(ew * 0.41 * blink_scale))
                ir_g = QRadialGradient(ex - 2, ey - 2, iris_r)
                ir_g.setColorAt(0,    QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), 255))
                ir_g.setColorAt(0.35, QColor(int(aura_c1.red()*0.6), int(aura_c1.green()*0.6), int(aura_c1.blue()*0.6), 255))
                ir_g.setColorAt(0.75, QColor(10, 20, 55, 255))
                ir_g.setColorAt(1,    QColor(5,  10, 30, 255))
                p.setBrush(QBrush(ir_g))
                p.drawEllipse(ex - iris_r, ey - iris_r, iris_r * 2, iris_r * 2)

                pup_r = max(1, int(iris_r * 0.42))
                p.setBrush(QBrush(QColor(4, 6, 18, 255)))
                p.drawEllipse(ex - pup_r, ey - pup_r, pup_r * 2, pup_r * 2)

                spec_r = max(1, int(pup_r * 0.55))
                p.setBrush(QBrush(QColor(240, 250, 255, 220)))
                p.drawEllipse(ex - iris_r // 2, ey - iris_r // 2, spec_r * 2, spec_r * 2)

                glow_r = iris_r + 3
                p.setPen(QPen(QColor(eye_glow.red(), eye_glow.green(), eye_glow.blue(), 130), 1.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(ex - glow_r, ey - glow_r, glow_r * 2, glow_r * 2)

            # Eyelid shadow
            if blink_scale > 0.0:
                lid_g = QLinearGradient(ex, ey - eh // 2, ex, ey + eh // 2)
                lid_g.setColorAt(0, QColor(8, 12, 30, 140)); lid_g.setColorAt(0.3, QColor(0, 0, 0, 0))
                p.setBrush(QBrush(lid_g)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(ex - ew // 2, ey - eh // 2, ew, eh)

            p.setPen(QPen(QColor(eye_glow.red(), eye_glow.green(), eye_glow.blue(), 120), 0.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(ex - ew // 2, ey - eh // 2, ew, eh)

        # --- L4: Nose ---
        nose_cx  = cx
        nose_top = face_top + int(face_h * 0.47)
        nose_bot = face_top + int(face_h * 0.63)
        p.setBrush(QBrush(QColor(6, 10, 28, 90))); p.setPen(Qt.PenStyle.NoPen)
        for side in [-1, 1]:
            p.drawEllipse(nose_cx + side * 7 - 5, nose_bot - 5, 10, 8)
        br_g = QLinearGradient(nose_cx - 3, nose_top, nose_cx + 3, nose_top)
        br_g.setColorAt(0, QColor(0, 0, 0, 0))
        br_g.setColorAt(0.5, QColor(aura_c1.red(), aura_c1.green(), aura_c1.blue(), 22))
        br_g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(br_g)); p.drawRect(nose_cx - 3, nose_top, 6, nose_bot - nose_top)

        # --- L5: Mouth ---
        mouth_open_map = {self.MOUTH_CLOSED: 0.0, self.MOUTH_SLIGHT: 0.22,
                          self.MOUTH_OPEN: 0.52, self.MOUTH_WIDE: 0.88}
        open_frac = mouth_open_map.get(self._current_mouth, 0.0)
        mouth_cx = cx
        mouth_cy = face_top + int(face_h * 0.765)
        mouth_w  = int(face_w * 0.36)
        half_mw  = mouth_w // 2
        drop     = int(mouth_w * 0.32 * open_frac)

        upper_lip = QPainterPath()
        upper_lip.moveTo(mouth_cx - half_mw, mouth_cy)
        upper_lip.cubicTo(mouth_cx - half_mw + 6, mouth_cy - 4, mouth_cx - 7, mouth_cy - 5, mouth_cx, mouth_cy - 3)
        upper_lip.cubicTo(mouth_cx + 7, mouth_cy - 5, mouth_cx + half_mw - 6, mouth_cy - 4, mouth_cx + half_mw, mouth_cy)

        lower_lip = QPainterPath()
        lower_lip.moveTo(mouth_cx - half_mw, mouth_cy)
        lower_lip.cubicTo(mouth_cx - half_mw + 4, mouth_cy + 5 + drop, mouth_cx, mouth_cy + 8 + drop, mouth_cx, mouth_cy + 8 + drop)
        lower_lip.cubicTo(mouth_cx, mouth_cy + 8 + drop, mouth_cx + half_mw - 4, mouth_cy + 5 + drop, mouth_cx + half_mw, mouth_cy)

        lip_c = QPen(QColor(eye_glow.red(), eye_glow.green(), eye_glow.blue(), 160), 1.2)
        p.setPen(lip_c); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(upper_lip); p.drawPath(lower_lip)

        if open_frac > 0.05:
            gap = QPainterPath()
            gap.moveTo(mouth_cx - half_mw, mouth_cy)
            gap.cubicTo(mouth_cx - half_mw + 6, mouth_cy - 4, mouth_cx - 7, mouth_cy - 5, mouth_cx, mouth_cy - 3)
            gap.cubicTo(mouth_cx + 7, mouth_cy - 5, mouth_cx + half_mw - 6, mouth_cy - 4, mouth_cx + half_mw, mouth_cy)
            gap.cubicTo(mouth_cx + half_mw - 4, mouth_cy + 5 + drop, mouth_cx, mouth_cy + 8 + drop, mouth_cx, mouth_cy + 8 + drop)
            gap.cubicTo(mouth_cx, mouth_cy + 8 + drop, mouth_cx - half_mw + 4, mouth_cy + 5 + drop, mouth_cx - half_mw, mouth_cy)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(4, 6, 16, int(200 * open_frac))))
            p.drawPath(gap)

        # --- L6: Scan beam (inside face) ---
        scan_y = int(face_top + self._scan_y * (face_h / 230))
        bm_g = QLinearGradient(0, scan_y - 12, 0, scan_y + 12)
        bm_g.setColorAt(0, QColor(0, 0, 0, 0)); bm_g.setColorAt(0.5, scan_c); bm_g.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(QRect(face_x, scan_y - 12, face_w, 24), QBrush(bm_g))
        la = 180 if self.state == "working" else 110
        p.setPen(QPen(QColor(eye_glow.red(), eye_glow.green(), eye_glow.blue(), la), 1.0))
        p.drawLine(face_x + 4, scan_y, face_x + face_w - 4, scan_y)

        p.restore()  # end face clip

        # --- L7: Face border glow ---
        p.setPen(QPen(glow_pen, 1.6)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(face_path)

        # --- L8: HUD corner brackets ---
        bk_pen = QPen(QColor(C_CYAN if self.state == "working" else C_BLUE), 2.2)
        bk_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(bk_pen)
        bl = 11
        x1, y1 = face_x - 4, face_top - 4
        x2, y2 = face_x + face_w + 4, face_top + face_h + 4
        p.drawLine(x1, y1, x1 + bl, y1); p.drawLine(x1, y1, x1, y1 + bl)
        p.drawLine(x2, y1, x2 - bl, y1); p.drawLine(x2, y1, x2, y1 + bl)
        p.drawLine(x1, y2, x1 + bl, y2); p.drawLine(x1, y2, x1, y2 - bl)
        p.drawLine(x2, y2, x2 - bl, y2); p.drawLine(x2, y2, x2, y2 - bl)

        # --- L9: Orbit rings ---
        orbit_cy = face_top + face_h - 10 + bob_y
        rp1 = QPen(QColor(0, 212, 255, 75 if self.state != "working" else 140), 1.2, Qt.PenStyle.DashLine)
        p.setPen(rp1); p.save()
        p.translate(cx, orbit_cy); p.rotate(22)
        p.drawEllipse(QRect(-85, -24, 170, 48))
        n1_x = 85 * math.cos(self._angle1); n1_y = 24 * math.sin(self._angle1)
        d1 = math.sin(self._angle1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 240, 255, int(170 + 85 * d1) if d1 > 0 else 70)))
        p.drawEllipse(QPoint(int(n1_x), int(n1_y)), 4 if d1 > 0 else 2, 4 if d1 > 0 else 2)
        p.restore()

        rp2 = QPen(QColor(155, 89, 182, 70 if self.state != "working" else 130), 1.2, Qt.PenStyle.DotLine)
        p.setPen(rp2); p.save()
        p.translate(cx, orbit_cy + 18); p.rotate(-26)
        p.drawEllipse(QRect(-78, -18, 156, 36))
        n2_x = 78 * math.cos(self._angle2); n2_y = 18 * math.sin(self._angle2)
        d2 = math.sin(self._angle2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(195, 110, 255, int(170 + 85 * d2) if d2 > 0 else 60)))
        p.drawEllipse(QPoint(int(n2_x), int(n2_y)), 4 if d2 > 0 else 2, 4 if d2 > 0 else 2)
        p.restore()

        # --- L10: Status badge ---
        badge_rect = QRect(12, 276, 196, 26)
        if self.state == "working":
            bg_c = QColor(0,180,255,45); bd_c = QColor(0,212,255,160); txt_c = QColor(0,240,255)
            badge_text = "\u26a1  PROCESSING TASK..."
        elif self.state == "speaking":
            bg_c = QColor(155,89,182,50); bd_c = QColor(195,110,255,170); txt_c = QColor(220,160,255)
            badge_text = "\U0001f50a  SPEAKING TO YOU"
        else:
            bg_c = QColor(61,142,248,28); bd_c = QColor(61,142,248,90); txt_c = QColor(C_TEXT)
            badge_text = "\u25cf  NEURAL CORE READY"
        p.setBrush(QBrush(bg_c)); p.setPen(QPen(bd_c, 1))
        p.drawRoundedRect(badge_rect, 13, 13)
        p.setPen(QPen(txt_c)); p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

        # --- L11: Lip-sync bars ---
        if self.state == "speaking" and self._amp_smooth > 0.05:
            bar_y = 304
            bar_colors = [QColor(195,110,255,200), QColor(200,130,255,220), QColor(210,150,255,255),
                          QColor(200,130,255,220), QColor(195,110,255,200)]
            bar_heights = [int(8 + 10 * self._amp_smooth * abs(math.sin(self._bob_phase + i * 0.7))) for i in range(5)]
            bar_w, gap = 16, 8
            start_x = (220 - (5 * bar_w + 4 * gap)) // 2
            for i, (bh, bc) in enumerate(zip(bar_heights, bar_colors)):
                bx = start_x + i * (bar_w + gap)
                p.setBrush(QBrush(bc)); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(bx, bar_y - bh, bar_w, bh, 3, 3)



# ══════════════════════════════════════════════════════════
#  Live System Widgets Panel
# ══════════════════════════════════════════════════════════
class LiveWidgetsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.clock_lbl = self._make_card("🕒", "Time", "--:--")
        self.cpu_lbl   = self._make_card("⚙", "CPU", "0%")
        self.mem_lbl   = self._make_card("🧠", "RAM", "0%")
        self.bat_lbl   = self._make_card("🔋", "Battery", "100%")

        lay.addWidget(self.clock_lbl)
        lay.addWidget(self.cpu_lbl)
        lay.addWidget(self.mem_lbl)
        lay.addWidget(self.bat_lbl)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(1000)
        self._update_stats()

    def _make_card(self, icon, title, val):
        card = GlassPanel(radius=12)
        v = QVBoxLayout(card)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(f"{icon} {title}")
        t.setFont(QFont("Segoe UI", 9))
        t.setStyleSheet(f"color: {C_SUBTEXT};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        v_lbl = QLabel(val)
        v_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color: {C_TEXT};")
        v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        v.addWidget(t)
        v.addWidget(v_lbl)
        card.val_lbl = v_lbl
        return card

    def _update_stats(self):
        from datetime import datetime
        import psutil
        
        self.clock_lbl.val_lbl.setText(datetime.now().strftime("%I:%M %p"))
        
        try:
            self.cpu_lbl.val_lbl.setText(f"{int(psutil.cpu_percent())}%")
            mem = psutil.virtual_memory()
            self.mem_lbl.val_lbl.setText(f"{int(mem.percent)}%")
            
            bat = psutil.sensors_battery()
            if bat:
                self.bat_lbl.val_lbl.setText(f"{int(bat.percent)}%")
            else:
                self.bat_lbl.val_lbl.setText("AC")
        except Exception:
            pass

# ══════════════════════════════════════════════════════════
#  Center home view
# ══════════════════════════════════════════════════════════
class HomeView(QWidget):
    command_sent = pyqtSignal(str)
    avatar_model_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(16)

        # ─ Hero section ──────────────────────
        hero = QWidget()
        hero.setStyleSheet("background: transparent;")
        hero_h = QHBoxLayout(hero)
        hero_h.setContentsMargins(0, 0, 0, 0)
        hero_h.setSpacing(24)

        # 3D Animated Bot Avatar (Three.js via QWebEngineView, falls back to procedural)
        self.avatar_widget = make_3d_bot_widget()
        avatar_col = QVBoxLayout()
        avatar_col.setSpacing(6)
        avatar_col.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        avatar_col.addWidget(self.avatar_widget)

        self.avatar_selector = QComboBox()
        self.avatar_selector.addItem("Michi Bot", "michi_bot.glb")
        self.avatar_selector.addItem("Angelica", "angelica.glb")
        self.avatar_selector.addItem("Robot", "robot.glb")
        self.avatar_selector.addItem("Model", "model.glb")
        self.avatar_selector.setCurrentIndex(0)
        self.avatar_selector.setToolTip("Choose NIA's 3D avatar")
        self.avatar_selector.setFixedWidth(180)
        self.avatar_selector.setStyleSheet(f"""
            QComboBox {{
                background: rgba(15,24,60,210); color: {C_TEXT};
                border: 1px solid rgba(61,142,248,0.4);
                border-radius: 8px; padding: 6px 10px;
            }}
            QComboBox QAbstractItemView {{
                background: #101838; color: {C_TEXT};
                selection-background-color: {C_SELECTED};
            }}
        """)
        self.avatar_selector.currentIndexChanged.connect(
            lambda _index: self.avatar_model_changed.emit(self.avatar_selector.currentData())
        )
        avatar_col.addWidget(self.avatar_selector, 0, Qt.AlignmentFlag.AlignHCenter)
        hero_h.addLayout(avatar_col)

        # Text block
        txt = QVBoxLayout()
        txt.setSpacing(6)

        hello = QLabel("Hello, I'm ")
        hello.setFont(QFont("Segoe UI", 32, QFont.Weight.Light))
        hello.setStyleSheet(f"color: {C_TEXT};")

        # NIA in blue
        nia_lbl = QLabel("NIA")
        nia_lbl.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        nia_lbl.setStyleSheet(f"""
            color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {C_BLUE}, stop:1 {C_CYAN});
            letter-spacing: 5px;
        """)

        hello_row = QHBoxLayout()
        hello_row.setSpacing(4)
        hello_row.addWidget(hello)
        hello_row.addWidget(nia_lbl)
        hello_row.addStretch()

        tagline = QLabel("Think · Ask · Command · Achieve")
        tagline.setFont(QFont("Segoe UI", 11))
        tagline.setStyleSheet(f"color: {C_BLUE}; letter-spacing: 1.5px;")

        desc1 = QLabel("Your Personal AI Agent")
        desc1.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        desc1.setStyleSheet(f"color: {C_TEXT};")

        desc2 = QLabel("Always Ready. Always With You.")
        desc2.setFont(QFont("Segoe UI", 10))
        desc2.setStyleSheet(f"color: {C_SUBTEXT};")

        txt.addLayout(hello_row)
        txt.addWidget(tagline)
        txt.addSpacing(6)
        txt.addWidget(desc1)
        txt.addWidget(desc2)
        txt.addStretch()

        hero_h.addLayout(txt)
        hero_h.addStretch()
        lay.addWidget(hero)

        # ─ Quick actions ─────────────────────
        qa_panel = GlassPanel(radius=14)
        qa = QGridLayout(qa_panel)
        qa.setContentsMargins(14, 10, 14, 10)
        qa.setSpacing(8)

        actions = [
            ("⊞", "Open App",       "open "),
            ("👁️", "Screen Vision",  "what is on my screen"),
            ("♫", "Play Music",     "play music "),
            ("⚙", "Control System", "control system"),
            ("◈", "Social Media",   "social media"),
            ("📄", "Create File",   "create file "),
        ]
        for i, (icon, label, cmd) in enumerate(actions):
            btn = self._qa_btn(icon, label, cmd)
            qa.addWidget(btn, i // 3, i % 3)
        lay.addWidget(qa_panel)

        # ─ Live Widgets ──────────────────────
        self.widgets_panel = LiveWidgetsPanel()
        lay.addWidget(self.widgets_panel)

        # ─ Command input ─────────────────────
        cmd_panel = GlassPanel(radius=14)
        cmd_lay = QVBoxLayout(cmd_panel)
        cmd_lay.setContentsMargins(16, 14, 16, 14)
        cmd_lay.setSpacing(10)

        inp_row = QHBoxLayout()
        inp_row.setSpacing(8)
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Tell me what you want to do...")
        self.cmd_input.setFont(QFont("Segoe UI", 11))
        self.cmd_input.setFixedHeight(46)
        self.cmd_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10,18,50,180);
                color: {C_TEXT};
                border: 1.5px solid rgba(61,142,248,0.5);
                border-radius: 23px;
                padding: 0 16px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {C_CYAN};
            }}
        """)
        self.cmd_input.returnPressed.connect(self._send)

        self.mic_btn = QPushButton("🎙")
        self.mic_btn.setFixedSize(46, 46)
        self.mic_btn.setStyleSheet(self._icon_btn_style())
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.sound_btn = QPushButton("🔊")
        self.sound_btn.setCheckable(True)
        self.sound_btn.setFixedSize(46, 46)
        self.sound_btn.setToolTip("Mute NIA beeps")
        self.sound_btn.setStyleSheet(self._icon_btn_style())
        self.sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(46, 46)
        send_btn.setFont(QFont("Segoe UI", 15))
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {C_BLUE}, stop:1 #1230a0);
                color: white; border: none; border-radius: 23px;
            }}
            QPushButton:hover {{ background: {C_CYAN}; }}
        """)
        send_btn.clicked.connect(self._send)

        inp_row.addWidget(self.cmd_input, 1)
        inp_row.addWidget(self.sound_btn)
        inp_row.addWidget(self.mic_btn)
        inp_row.addWidget(send_btn)
        cmd_lay.addLayout(inp_row)

        # Suggestion pills arranged in 2 neat rows
        pills_grid = QGridLayout()
        pills_grid.setSpacing(6)
        pills_grid.setContentsMargins(0, 2, 0, 0)
        suggestions = [
            "Open Chrome", "Play my favorite songs", "Check my WhatsApp", "Summarize this file",
            "Post on Twitter", "Set a reminder", "What's the latest news?", "Help me code"
        ]
        for i, s in enumerate(suggestions):
            pill = QPushButton(s)
            pill.setFont(QFont("Segoe UI", 8))
            pill.setFixedHeight(28)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(61,142,248,0.1);
                    color: {C_BLUE};
                    border: 1px solid rgba(61,142,248,0.3);
                    border-radius: 12px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{ background: rgba(61,142,248,0.25); color: white; }}
            """)
            pill.clicked.connect(lambda _, t=s: self._fill(t))
            pills_grid.addWidget(pill, i // 4, i % 4)
        cmd_lay.addLayout(pills_grid)
        lay.addWidget(cmd_panel)

        # ─ Chat output ───────────────────────
        self.chat_panel = GlassPanel(radius=14)
        self.chat_lay   = QVBoxLayout(self.chat_panel)
        self.chat_lay.setContentsMargins(16, 12, 16, 12)
        self.chat_lay.setSpacing(8)
        self.chat_lay.addStretch()
        lay.addWidget(self.chat_panel)

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _send(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            self.command_sent.emit(text)

    def _fill(self, text):
        self.cmd_input.setText(text)
        self.cmd_input.setFocus()

    def _qa_btn(self, icon, label, cmd_prefix):
        btn = QPushButton(f"{icon}   {label}")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(15,24,60,190);
                color: {C_TEXT};
                border: 1px solid rgba(61,142,248,0.22);
                border-radius: 10px;
                text-align: left;
                padding-left: 14px;
            }}
            QPushButton:hover {{
                background: rgba(61,142,248,0.25);
                border-color: {C_BLUE};
                color: white;
            }}
        """)
        btn.clicked.connect(lambda: self._fill(cmd_prefix))
        return btn

    def _icon_btn_style(self):
        return f"""
            QPushButton {{
                background: rgba(61,142,248,0.12);
                color: {C_TEXT};
                border: 1px solid rgba(61,142,248,0.3);
                border-radius: 23px; font-size: 16px;
            }}
            QPushButton:hover {{ background: rgba(61,142,248,0.28); }}
        """

    def set_avatar_state(self, state):
        if hasattr(self, "avatar_widget") and self.avatar_widget:
            self.avatar_widget.set_state(state)

    def add_chat_bubble(self, text, is_user=True):
        tag = QLabel("You" if is_user else "✦ NIA")
        tag.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tag.setStyleSheet(f"color: {C_BLUE if is_user else C_CYAN}; background: transparent;")

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMaximumWidth(640)
        bubble.setStyleSheet(f"""
            background: {'rgba(30,79,216,0.18)' if is_user else 'rgba(10,60,80,0.22)'};
            color: {C_TEXT};
            border: 1px solid {'rgba(61,142,248,0.3)' if is_user else 'rgba(0,212,255,0.25)'};
            border-radius: 12px;
            padding: 10px 16px;
        """)

        vbox = QVBoxLayout()
        vbox.setSpacing(3)
        hbox = QHBoxLayout()
        if is_user:
            tag.setAlignment(Qt.AlignmentFlag.AlignRight)
            vbox.addWidget(tag)
            hbox.addStretch()
            hbox.addWidget(bubble)
        else:
            vbox.addWidget(tag)
            hbox.addWidget(bubble)
            hbox.addStretch()
        vbox.addLayout(hbox)

        self.chat_lay.insertLayout(self.chat_lay.count() - 1, vbox)


# ══════════════════════════════════════════════════════════
#  Status bar
# ══════════════════════════════════════════════════════════
class StatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            background: #060714;
            border-top: 1px solid rgba(61,142,248,0.15);
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)

        self.online_lbl = QLabel("🟡  Initializing NIA Neural Engines...")
        self.online_lbl.setFont(QFont("Segoe UI", 9))
        self.online_lbl.setStyleSheet("color: #f1c40f;")

        lay.addWidget(self.online_lbl)
        lay.addStretch()

        self.wave = WaveformWidget()
        lay.addWidget(self.wave)
        lay.addSpacing(16)

        tagline = QLabel("Smarter Tools · Happier Days")
        tagline.setFont(QFont("Segoe UI", 9))
        tagline.setStyleSheet(f"color: {C_SUBTEXT};")
        lay.addWidget(tagline)

    def set_online(self):
        self.online_lbl.setText("🟢  NIA is online")
        self.online_lbl.setStyleSheet(f"color: {C_GREEN};")

    def set_status(self, text, color=None):
        self.online_lbl.setText(f"🟢  {text}")
        if color:
            self.online_lbl.setStyleSheet(f"color: {color};")
        else:
            self.online_lbl.setStyleSheet(f"color: {C_GREEN};")


# ══════════════════════════════════════════════════════════
#  Main Window
# ══════════════════════════════════════════════════════════
class NiaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.voice  = None
        self.agent  = None
        self.worker = None
        self.voice_listener = None
        self._is_force_quitting = False
        self._mic_enabled = True
        self._sound_muted = False

        self.setWindowTitle("NIA — Your AI Companion")
        self.setMinimumSize(1366, 768)

        central = QWidget()
        central.setStyleSheet(f"background: {C_BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self.header = HeaderBar()
        self.header.close_requested.connect(self.close)
        self.header.minimize_requested.connect(self.showMinimized)
        self.header.maximize_requested.connect(
            lambda: self.showNormal() if self.isMaximized() else self.showMaximized()
        )
        root.addWidget(self.header)

        # Body row
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.nav_changed.connect(self._on_nav)
        body.addWidget(self.sidebar)

        # Stacked central views
        self.stack = QStackedWidget()

        self.home_view = HomeView()
        self.home_view.command_sent.connect(self._on_command)
        self.home_view.avatar_model_changed.connect(self._on_avatar_model_changed)
        self.home_view.sound_btn.clicked.connect(self._toggle_sound)
        self.stack.addWidget(self.home_view)

        self.chat_view = ChatView()
        self.chat_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.chat_view)

        self.apps_view = AppsView()
        self.apps_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.apps_view)

        self.web_view = WebView()
        self.web_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.web_view)

        self.social_view = SocialView()
        self.social_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.social_view)

        # Isolated WhatsApp Web Zero-Browser Engine
        session_dir = self.config.get("system_paths", {}).get("whatsapp_session_dir")
        if not session_dir:
            session_dir = os.path.join(BASE_DIR, "nia_browser_profile")
        self.wa_manager = WhatsAppManager(session_dir, headless=True)
        self.wa_manager.status_changed.connect(self._on_wa_status_changed)
        self.wa_manager.qr_updated.connect(self._on_wa_qr_updated)
        self.wa_manager.message_result.connect(self._on_wa_message_result)
        self.social_view.refresh_whatsapp.connect(self.wa_manager.refresh)
        self.social_view.check_whatsapp.connect(self.wa_manager.check_state)
        self.social_view.send_whatsapp_custom.connect(self._on_send_wa_message)
        self.wa_manager.command_received.connect(self._on_whatsapp_command)
        self.wa_manager.start()

        self.files_view = FilesView()
        self.files_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.files_view)

        self.media_view = MediaView()
        self.media_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.media_view)

        self.auto_view = AutomationView()
        self.auto_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.auto_view)

        self.memory_view = MemoryView(self.config)
        self.stack.addWidget(self.memory_view)

        self.settings_view = SettingsView(self.config)
        self.settings_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.settings_view)

        self.smart_home_view = SmartHomeView(self.config)
        self.smart_home_view.command_sent.connect(self._on_command)
        self.stack.addWidget(self.smart_home_view)

        self.view_map = {
            "Home": self.home_view,
            "Chat": self.chat_view,
            "Apps & Control": self.apps_view,
            "Web & Search": self.web_view,
            "Social Media": self.social_view,
            "Files & Documents": self.files_view,
            "Media": self.media_view,
            "Automation": self.auto_view,
            "Learning & Memory": self.memory_view,
            "Settings": self.settings_view,
            "Smart Home": self.smart_home_view,
        }

        body.addWidget(self.stack, 1)

        self.right_panel = RightPanel()
        self.right_panel.app_clicked.connect(self._on_quick_launch_app)
        self.right_panel.activity_clicked.connect(self._on_command)
        body.addWidget(self.right_panel)

        self.header.settings_requested.connect(lambda: self.sidebar._select("Settings"))
        self.header.notifications_requested.connect(self._show_notifications)

        root.addLayout(body, 1)

        # Status bar
        self.status_bar = StatusBar()
        root.addWidget(self.status_bar)

        # Initial prompt in chat
        name = self.config["user_profile"]["name"]
        init_msg = f"Namaste {name} ji! Main Nia hoon. Systems loading..."
        self.home_view.add_chat_bubble(init_msg, is_user=False)
        self.chat_view.add_chat_bubble(init_msg, is_user=False)

        # License / ₹99 Test Flight status advisory
        lic_info = self.config.get("license_info", {})
        lic_st = lic_info.get("status", "")
        if lic_st == "key_required":
            lic_msg = "⚠️ [License Required] Please enter your ₹99 Test Flight or Pro license key in Settings to activate Nia."
            self.home_view.add_chat_bubble(lic_msg, is_user=False)
            self.chat_view.add_chat_bubble(lic_msg, is_user=False)
        elif lic_st == "trial_expired":
            lic_msg = "⚠️ [Test Flight Expired] Your 7-day ₹99 Test Flight has expired. Please upgrade or enter a Pro key in Settings."
            self.home_view.add_chat_bubble(lic_msg, is_user=False)
            self.chat_view.add_chat_bubble(lic_msg, is_user=False)
        elif lic_st == "licensed" and lic_info.get("tier") == "test_flight":
            rem = lic_info.get("days_remaining", 7)
            lic_msg = f"🚀 Nia 7-Day Test Flight Active ({rem} day(s) remaining)."
            self.home_view.add_chat_bubble(lic_msg, is_user=False)
            self.chat_view.add_chat_bubble(lic_msg, is_user=False)

        # Show the window INSTANTLY
        self.showMaximized()
        self._setup_tray_icon()

        # Load heavy AI engines asynchronously in the background
        self.init_worker = InitWorker(self.config)
        self.init_worker.ready.connect(self._on_ai_ready)
        self.init_worker.start()

    def _on_ai_ready(self, agent, voice):
        self.agent = agent
        self.voice = voice
        if agent and hasattr(self, 'wa_manager') and self.wa_manager:
            self.agent.browser.wa_manager = self.wa_manager
        if not agent:
            print("[NIA] Agent failed to initialize — AI commands unavailable.")
            return
        self.status_bar.set_online()

        # ── Connect VoiceEngine to 3D Bot Avatar for speaking/idle state sync ──
        if self.voice and hasattr(self.home_view, 'avatar_widget'):
            self.home_view.avatar_widget.set_voice_engine(self.voice)

            def _on_start():
                # Called from background TTS thread — schedule GUI update on main thread
                QTimer.singleShot(0, lambda: self.home_view.set_avatar_state("speaking"))
                QTimer.singleShot(0, lambda: self.home_view.avatar_widget.set_state("speaking"))

            def _on_end():
                QTimer.singleShot(0, lambda: self.home_view.set_avatar_state("idle"))
                QTimer.singleShot(3000, lambda: self.home_view.avatar_widget.set_state("idle"))

            self.voice.on_speaking_start = _on_start
            self.voice.on_speaking_end   = _on_end

        # ── Start Reminder Manager ──
        try:
            from reminder_manager import ReminderManager
            self.agent.reminder_manager = ReminderManager(os.path.join(STATE_DIR, "reminders.json"))
            self.agent.reminder_manager.reminder_triggered.connect(self._on_reminder_triggered)
            self.agent.reminder_manager.start()
        except Exception as e:
            print(f"[Reminder Manager Error]: {e}")

        # ── Start Scheduled Workflow Manager ──
        try:
            if hasattr(self.agent, 'schedule_manager'):
                self.agent.schedule_manager.workflow_triggered.connect(self._on_scheduled_workflow_triggered)
        except Exception as e:
            print(f"[Scheduled Workflow Manager Error]: {e}")

        self.home_view.set_avatar_state("speaking")
        self._greet()
        QTimer.singleShot(4500, lambda: self.home_view.set_avatar_state("idle"))

        # Start continuous background handsfree voice listener
        if self.voice:
            try:
                self.voice_listener = VoiceListenerThread(self.voice)
                self.voice_listener.command_heard.connect(self._on_voice_command)
                self.voice_listener.listening_state.connect(self._on_listening_state)
                self.voice_listener.start()
                print("[Nia] Handsfree voice listener active in background.")
            except Exception as ex:
                print(f"[Nia Voice Listener Init Error]: {ex}")

        # Hook up the manual mic button
        if hasattr(self.home_view, "mic_btn"):
            self.home_view.mic_btn.clicked.connect(self._on_mic_clicked)
            self._set_mic_button_state(self._mic_enabled)

    def _on_mic_clicked(self):
        self._mic_enabled = not self._mic_enabled
        if self.voice_listener:
            self.voice_listener.set_enabled(self._mic_enabled)
        self._set_mic_button_state(self._mic_enabled)
        self.home_view.cmd_input.setPlaceholderText(
            "Listening for NIA..." if self._mic_enabled else "Microphone is off"
        )

    def _set_mic_button_state(self, enabled: bool):
        color = C_GREEN if enabled else "#ff4d5f"
        label = "🎙" if enabled else "🚫"
        status = "Microphone on" if enabled else "Microphone off"
        self.home_view.mic_btn.setText(label)
        self.home_view.mic_btn.setToolTip(status)
        self.home_view.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({"0, 230, 118" if enabled else "255, 77, 95"}, 0.22);
                color: {color}; border: 2px solid {color};
                border-radius: 23px; font-size: 16px;
            }}
            QPushButton:hover {{ background: rgba({"0, 230, 118" if enabled else "255, 77, 95"}, 0.38); }}
        """)

    def _toggle_sound(self):
        self._sound_muted = not self._sound_muted
        try:
            from sound_effects import SoundEffects
            SoundEffects.set_muted(self._sound_muted)
        except Exception:
            pass
        self.home_view.sound_btn.setText("🔇" if self._sound_muted else "🔊")
        self.home_view.sound_btn.setToolTip("Unmute NIA beeps" if self._sound_muted else "Mute NIA beeps")

    def _on_avatar_model_changed(self, model_file: str):
        if (hasattr(self.home_view, "avatar_widget") and
                hasattr(self.home_view.avatar_widget, "set_avatar_model")):
            self.home_view.avatar_widget.set_avatar_model(model_file)

    def _on_listening_state(self, state: str):
        if not hasattr(self.home_view, "mic_btn"): return
        if not self._mic_enabled:
            self._set_mic_button_state(False)
            return
        self._set_mic_button_state(True)
        if state == "listening":
            self.home_view.cmd_input.setPlaceholderText("Listening for NIA...")
        elif state == "processing":
            self.home_view.cmd_input.setPlaceholderText("Processing your voice...")
        else:
            self.home_view.cmd_input.setPlaceholderText("Tell me what you want to do...")

    def _greet(self):
        name = self.config["user_profile"]["name"]
        msg  = f"Namaste {name} ji! Main Nia hoon. All systems ready. Aap mujhe kya karna chahenge aaj?"
        self.home_view.add_chat_bubble(msg, is_user=False)
        self.chat_view.add_chat_bubble(msg, is_user=False)
        if self.voice:
            threading.Thread(target=self.voice.speak, args=(msg,), daemon=True).start()

    def _on_nav(self, name):
        if name in self.view_map:
            self.stack.setCurrentWidget(self.view_map[name])

    def _on_quick_launch_app(self, name):
        if name == "Chrome":
            self._on_command("open chrome")
        elif name == "Notepad":
            self._on_command("open notepad")
        elif name == "WhatsApp":
            self.sidebar._select("Social Media")
        elif name == "YouTube":
            self._on_command("open url youtube.com")
        elif name == "Spotify":
            self._on_command("open spotify")
        elif name == "VS Code":
            self._on_command("open vs code")
        elif name == "Telegram":
            self._on_command("open url web.telegram.org")
        elif name in ("Add", "Apps & Control"):
            self.sidebar._select("Apps & Control")

    def _on_reminder_triggered(self, title, msg_text):
        alert_msg = f"⏰ REMINDER: {msg_text}"
        self.home_view.add_chat_bubble(alert_msg, is_user=False)
        self.chat_view.add_chat_bubble(alert_msg, is_user=False)
        self.right_panel.add_activity("⏰", f"Reminder: {msg_text[:20]}")
        
        try:
            from sound_effects import SoundEffects
            SoundEffects.startup_chime() # Use a nice chime
        except Exception:
            pass

        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, msg_text, QSystemTrayIcon.MessageIcon.Information, 5000)
            
        if self.voice:
            import threading
            threading.Thread(target=self.voice.speak, args=(f"Aapka reminder: {msg_text}",), daemon=True).start()

    def _on_scheduled_workflow_triggered(self, name, task):
        alert_msg = f"⏱️ Scheduled Workflow '{name}' triggered: {task}"
        self.home_view.add_chat_bubble(alert_msg, is_user=False)
        self.chat_view.add_chat_bubble(alert_msg, is_user=False)
        self.right_panel.add_activity("⏱️", f"Workflow: {name}")
        
        # Dispatch the task as a command
        self._on_command(f"[Scheduled Workflow '{name}'] {task}")

    def _show_notifications(self):
        msg = "🔔 All Nia background subsystems are operational. No alerts pending."
        self.home_view.add_chat_bubble(msg, is_user=False)
        self.chat_view.add_chat_bubble(msg, is_user=False)

    def _on_wa_status_changed(self, status, details):
        try:
            self.social_view.set_whatsapp_status(status, details)
            if status == "CONNECTED":
                if hasattr(self, "status_bar"):
                    self.status_bar.set_status("ONLINE (WhatsApp Sync Active)")
                if not getattr(self, "_wa_connected_notified", False):
                    self._wa_connected_notified = True
                    connected_msg = "✅ WhatsApp Web connected successfully! Sessions will stay active in the background."
                    self.home_view.add_chat_bubble(connected_msg, is_user=False)
                    self.chat_view.add_chat_bubble(connected_msg, is_user=False)
        except Exception as e:
            print(f"[WA Status Error]: {e}")

    def _on_wa_qr_updated(self, qr_path):
        try:
            self.social_view.set_qr_image(qr_path)
            alert = "📲 WhatsApp Login Required: Open the 'Social Media' tab to scan the QR code directly inside NIA."
            self.home_view.add_chat_bubble(alert, is_user=False)
            self.chat_view.add_chat_bubble(alert, is_user=False)
        except Exception as e:
            print(f"[WA QR Error]: {e}")

    def _on_send_wa_message(self, phone, msg):
        try:
            self.home_view.add_chat_bubble(f"Sending WhatsApp message to {phone}: '{msg}'", is_user=True)
            self.chat_view.add_chat_bubble(f"Sending WhatsApp message to {phone}: '{msg}'", is_user=True)
            self.wa_manager.send_message(phone, msg)
        except Exception as e:
            print(f"[WA Send Error]: {e}")

    def _on_wa_message_result(self, success, feedback):
        try:
            self.home_view.add_chat_bubble(feedback, is_user=False)
            self.chat_view.add_chat_bubble(feedback, is_user=False)
        except Exception as e:
            print(f"[WA Msg Result Error]: {e}")

    def _on_voice_command(self, text):
        print(f"[Handsfree Voice Command Received]: '{text}'")
        self._on_command(text)

    def _on_whatsapp_command(self, text):
        try:
            print(f"[WhatsApp Remote Command Received]: '{text}'")
            bubble = f"📲 WhatsApp: {text}"
            self.home_view.add_chat_bubble(bubble, is_user=True)
            self.chat_view.add_chat_bubble(bubble, is_user=True)
            self.right_panel.add_activity("💬", f"WA: {text[:28]}")

            if not self.agent:
                return

            # Execute command through Unified Execution Router (instant local execution + AI fallback)
            reply = execute_unified_command(self.agent, text)

            self.home_view.add_chat_bubble(f"Nia → WhatsApp: {reply}", is_user=False)
            self.chat_view.add_chat_bubble(f"Nia → WhatsApp: {reply}", is_user=False)

            # Send reply back to WhatsApp
            self.wa_manager.send_chat_reply(reply)

            # Speak reply if voice is enabled
            if self.voice:
                threading.Thread(target=self.voice.speak, args=(reply,), daemon=True).start()
        except Exception as e:
            print(f"[WhatsApp Command Execution Error]: {e}")

    def _setup_tray_icon(self):
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return
            self.tray_icon = QSystemTrayIcon(self)
            if os.path.exists(AVATAR_PATH):
                self.tray_icon.setIcon(QIcon(AVATAR_PATH))
            else:
                self.tray_icon.setIcon(self.windowIcon())

            tray_menu = QMenu()
            show_act = tray_menu.addAction("🖥️  Open NIA Command Center")
            show_act.triggered.connect(self._restore_from_tray)

            self.mic_tray_act = tray_menu.addAction("🎙️  Handsfree Voice: ON")
            self.mic_tray_act.triggered.connect(self._toggle_handsfree_voice)

            tray_menu.addSeparator()
            quit_act = tray_menu.addAction("❌  Exit Completely")
            quit_act.triggered.connect(self._force_quit)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"[Tray Setup Error]: {e}")

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def _toggle_handsfree_voice(self):
        if hasattr(self, 'voice_listener') and self.voice_listener:
            self._mic_enabled = not self.voice_listener._enabled
            self.voice_listener.set_enabled(self._mic_enabled)
            self._set_mic_button_state(self._mic_enabled)
            if self._mic_enabled:
                self.mic_tray_act.setText("🎙️  Handsfree Voice: ON")
                self.status_bar.set_status("Handsfree Voice Active")
            else:
                self.mic_tray_act.setText("🎙️  Handsfree Voice: OFF (Muted)")
                self.status_bar.set_status("Voice Muted")

    def _force_quit(self):
        self._is_force_quitting = True
        try:
            if hasattr(self, 'voice_listener') and self.voice_listener:
                self.voice_listener.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'wa_manager') and self.wa_manager:
                self.wa_manager.stop()
        except Exception:
            pass
        QApplication.quit()

    def closeEvent(self, event):
        if getattr(self, '_is_force_quitting', False):
            event.accept()
            return

        # Keep running in background when closed!
        event.ignore()
        self.hide()
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "NIA Running in Background",
                "Handsfree Voice and WhatsApp commands remain active. Double-click tray icon to open.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def _on_command(self, text):
        if not self.agent:
            wait_msg = "Nia is warming up its neural engine. Please give me 2 seconds..."
            self.home_view.add_chat_bubble(wait_msg, is_user=False)
            self.chat_view.add_chat_bubble(wait_msg, is_user=False)
            return

        if self.worker:
            return

        # Trigger 3D working / holographic calculation state
        self.home_view.set_avatar_state("working")
        self.home_view.add_chat_bubble(text, is_user=True)
        self.chat_view.add_chat_bubble(text, is_user=True)
        self.right_panel.add_activity("⌨", text[:32])

        self.worker = NiaWorker(self.agent, self.voice, text)
        self.worker.response_ready.connect(self._on_ai_response)
        self.worker.done.connect(self._on_done)
        self.worker.start()

    def _on_ai_response(self, reply):
        self.home_view.add_chat_bubble(reply, is_user=False)
        self.chat_view.add_chat_bubble(reply, is_user=False)
        self.home_view.set_avatar_state("speaking")

    def _on_done(self):
        self.worker = None
        # Return to calm breathing idle state
        QTimer.singleShot(3000, lambda: self.home_view.set_avatar_state("idle"))
        try:
            from sound_effects import SoundEffects
            SoundEffects.action_done()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    from PyQt6.QtCore import QSharedMemory
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Prevent multiple conflicting instances from corrupting browser profiles or audio
    shared_mem = QSharedMemory("NIA_AI_ASSISTANT_SINGLETON_LOCK")
    if not shared_mem.create(1):
        print("[NIA] Another instance of NIA is already running in the background or system tray.")
        sys.exit(0)

    win = NiaMainWindow()
    win.show()
    sys.exit(app.exec())
