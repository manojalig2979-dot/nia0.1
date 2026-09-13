"""
gui_views.py — Dedicated interactive view panels for NIA's sidebar tabs:
Chat, Apps & Control, Web & Search, Social Media, Files & Documents,
Media, Automation, Learning & Memory, Settings.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QGridLayout, QTextEdit,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath, QPixmap

# Reuse global colors from GUI
C_BG       = "#08091a"
C_BLUE     = "#3d8ef8"
C_CYAN     = "#00d4ff"
C_PURPLE   = "#9b59b6"
C_TEXT     = "#c8d8f8"
C_SUBTEXT  = "#5a6a9a"
C_GREEN    = "#00e676"


class BaseCard(QFrame):
    """Semi-transparent glass panel with glowing border."""
    def __init__(self, parent=None, radius=14, border_color="#3d8ef8"):
        super().__init__(parent)
        self._radius = radius
        self._border = QColor(border_color)
        self._border.setAlpha(65)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius, self._radius)
        p.fillPath(path, QColor(10, 16, 46, 200))
        p.setPen(QPen(self._border, 1.2))
        p.drawPath(path)


def make_header(title: str, subtitle: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 10)
    lay.setSpacing(4)
    t = QLabel(title)
    t.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
    t.setStyleSheet(f"color: {C_BLUE}; letter-spacing: 2px;")
    s = QLabel(subtitle)
    s.setFont(QFont("Segoe UI", 10))
    s.setStyleSheet(f"color: {C_SUBTEXT};")
    lay.addWidget(t)
    lay.addWidget(s)
    return w


class ActionButton(QPushButton):
    def __init__(self, icon: str, title: str, desc: str, cmd: str, signal, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.signal = signal
        self.setFixedHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(14, 22, 58, 200);
                border: 1px solid rgba(61, 142, 248, 0.25);
                border-radius: 12px;
                text-align: left;
                padding: 8px 14px;
            }}
            QPushButton:hover {{
                background: rgba(61, 142, 248, 0.22);
                border-color: {C_BLUE};
            }}
            QPushButton:pressed {{
                background: rgba(0, 212, 255, 0.28);
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(12)

        ic = QLabel(icon)
        ic.setFont(QFont("Segoe UI", 20))
        ic.setFixedWidth(36)
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        txt_v = QVBoxLayout()
        txt_v.setSpacing(2)
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {C_TEXT};")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        d = QLabel(desc)
        d.setFont(QFont("Segoe UI", 8))
        d.setStyleSheet(f"color: {C_SUBTEXT};")
        d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        txt_v.addWidget(t)
        txt_v.addWidget(d)

        lay.addWidget(ic)
        lay.addLayout(txt_v)
        lay.addStretch()

        self.clicked.connect(self._on_click)

    def _on_click(self):
        if self.signal:
            self.signal.emit(self.cmd)


def make_action_btn(icon: str, title: str, desc: str, cmd: str, signal) -> QPushButton:
    return ActionButton(icon, title, desc, cmd, signal)



# ══════════════════════════════════════════════════════════
#  1. Chat View
# ══════════════════════════════════════════════════════════
class ChatView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)

        lay.addWidget(make_header("💬  Conversation with NIA", "Full-screen intelligent assistant chat stream"))

        # Scroll area for conversation
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_lay = QVBoxLayout(self.chat_container)
        self.chat_lay.setContentsMargins(12, 10, 12, 10)
        self.chat_lay.setSpacing(10)
        self.chat_lay.addStretch()

        self.scroll.setWidget(self.chat_container)
        lay.addWidget(self.scroll, 1)

        # Input Card
        inp_card = BaseCard(radius=14)
        inp_lay = QHBoxLayout(inp_card)
        inp_lay.setContentsMargins(14, 10, 14, 10)
        inp_lay.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or question for Nia...")
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setFixedHeight(44)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 22px;
                padding: 0 16px;
            }}
            QLineEdit:focus {{ border-color: {C_CYAN}; }}
        """)
        self.input_field.returnPressed.connect(self._send)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(44, 44)
        send_btn.setFont(QFont("Segoe UI", 14))
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0);
                color: white; border: none; border-radius: 22px;
            }}
            QPushButton:hover {{ background: {C_CYAN}; }}
        """)
        send_btn.clicked.connect(self._send)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(44)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_SUBTEXT}; border: 1px solid rgba(61, 142, 248, 0.25);
                border-radius: 22px; padding: 0 14px;
            }}
            QPushButton:hover {{ color: {C_BLUE}; border-color: {C_BLUE}; }}
        """)
        clear_btn.clicked.connect(self._clear_chat)

        inp_lay.addWidget(self.input_field, 1)
        inp_lay.addWidget(send_btn)
        inp_lay.addWidget(clear_btn)
        lay.addWidget(inp_card)

    def _send(self):
        txt = self.input_field.text().strip()
        if txt:
            self.input_field.clear()
            self.command_sent.emit(txt)

    def _clear_chat(self):
        while self.chat_lay.count() > 1:
            item = self.chat_lay.takeAt(0)
            if item.layout():
                while item.layout().count():
                    c = item.layout().takeAt(0)
                    if c.widget(): c.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

    def add_chat_bubble(self, text: str, is_user: bool = True):
        tag = QLabel("You" if is_user else "✦ NIA")
        tag.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tag.setStyleSheet(f"color: {C_BLUE if is_user else C_CYAN};")

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 10))
        bubble.setMaximumWidth(700)
        bubble.setStyleSheet(f"""
            background: {'rgba(30,79,216,0.18)' if is_user else 'rgba(10,60,80,0.24)'};
            color: {C_TEXT};
            border: 1px solid {'rgba(61,142,248,0.35)' if is_user else 'rgba(0,212,255,0.3)'};
            border-radius: 12px;
            padding: 8px 14px;
        """)

        v = QVBoxLayout()
        v.setSpacing(2)
        h = QHBoxLayout()
        if is_user:
            tag.setAlignment(Qt.AlignmentFlag.AlignRight)
            v.addWidget(tag)
            h.addStretch()
            h.addWidget(bubble)
        else:
            tag.setAlignment(Qt.AlignmentFlag.AlignLeft)
            v.addWidget(tag)
            h.addWidget(bubble)
            h.addStretch()
        v.addLayout(h)
        self.chat_lay.insertLayout(self.chat_lay.count() - 1, v)
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))


# ══════════════════════════════════════════════════════════
#  2. Apps & Control View
# ══════════════════════════════════════════════════════════
class AppsView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("⊞  Apps & System Control", "Launch desktop programs and manage computer power"))

        # App Launchers
        apps_card = BaseCard(radius=14)
        ac_lay = QVBoxLayout(apps_card)
        ac_lay.setContentsMargins(18, 14, 18, 14)
        ac_lay.setSpacing(12)

        lbl = QLabel("Desktop Applications")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C_TEXT};")
        ac_lay.addWidget(lbl)

        grid = QGridLayout()
        grid.setSpacing(10)
        app_list = [
            ("📝", "Notepad", "Fast text editor", "open notepad"),
            ("🌐", "Google Chrome", "Web browser", "open chrome"),
            ("🧮", "Calculator", "Math calculations", "open calculator"),
            ("⌨", "Visual Studio Code", "Code editor", "open vs code"),
            ("📊", "Task Manager", "Monitor system performance", "open taskmgr"),
            ("📁", "File Explorer", "Browse PC storage", "open explorer"),
            ("⚙", "Command Prompt", "Windows terminal", "open cmd"),
            ("🎨", "MS Paint", "Quick sketching & image tool", "open mspaint"),
        ]
        for i, (ic, title, desc, cmd) in enumerate(app_list):
            btn = make_action_btn(ic, title, desc, cmd, self.command_sent)
            grid.addWidget(btn, i // 2, i % 2)
        ac_lay.addLayout(grid)
        lay.addWidget(apps_card)

        # Power Controls
        pwr_card = BaseCard(radius=14)
        pc_lay = QVBoxLayout(pwr_card)
        pc_lay.setContentsMargins(18, 14, 18, 14)
        pc_lay.setSpacing(10)

        plbl = QLabel("System Power Management")
        plbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        plbl.setStyleSheet(f"color: {C_TEXT};")
        pc_lay.addWidget(plbl)

        pwr_grid = QHBoxLayout()
        pwr_grid.setSpacing(10)
        pwr_actions = [
            ("🛑", "Shutdown PC", "Shutdown with 10s countdown", "shutdown in 10 seconds"),
            ("🔄", "Restart PC", "Reboot system cleanly", "restart system"),
            ("❌", "Cancel Shutdown", "Abort any scheduled power action", "cancel shutdown"),
        ]
        for ic, title, desc, cmd in pwr_actions:
            btn = make_action_btn(ic, title, desc, cmd, self.command_sent)
            pwr_grid.addWidget(btn)
        pc_lay.addLayout(pwr_grid)
        lay.addWidget(pwr_card)
        lay.addStretch()


# ══════════════════════════════════════════════════════════
#  3. Web & Search View
# ══════════════════════════════════════════════════════════
class WebView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("🌐  Web & Online Search", "Search Google and launch instant web portals"))

        # Search Card
        search_card = BaseCard(radius=14)
        sc_lay = QVBoxLayout(search_card)
        sc_lay.setContentsMargins(18, 14, 18, 14)
        sc_lay.setSpacing(10)

        slbl = QLabel("Search the Web with Google")
        slbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        slbl.setStyleSheet(f"color: {C_TEXT};")
        sc_lay.addWidget(slbl)

        srow = QHBoxLayout()
        srow.setSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter search topic or query...")
        self.search_box.setFont(QFont("Segoe UI", 11))
        self.search_box.setFixedHeight(44)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 22px;
                padding: 0 16px;
            }}
            QLineEdit:focus {{ border-color: {C_CYAN}; }}
        """)
        self.search_box.returnPressed.connect(self._do_search)

        sbtn = QPushButton("🔍  Search Google")
        sbtn.setFixedHeight(44)
        sbtn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        sbtn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0);
                color: white; border: none; border-radius: 22px; padding: 0 18px;
            }}
            QPushButton:hover {{ background: {C_CYAN}; }}
        """)
        sbtn.clicked.connect(self._do_search)

        srow.addWidget(self.search_box, 1)
        srow.addWidget(sbtn)
        sc_lay.addLayout(srow)
        lay.addWidget(search_card)

        # Portals Card
        portals_card = BaseCard(radius=14)
        pc_lay = QVBoxLayout(portals_card)
        pc_lay.setContentsMargins(18, 14, 18, 14)
        pc_lay.setSpacing(10)

        plbl = QLabel("Instant Web Portals")
        plbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        plbl.setStyleSheet(f"color: {C_TEXT};")
        pc_lay.addWidget(plbl)

        grid = QGridLayout()
        grid.setSpacing(10)
        portals = [
            ("▶", "YouTube", "Video & music streaming", "open url youtube.com"),
            ("🐙", "GitHub", "Code repositories & projects", "open url github.com"),
            ("📚", "Stack Overflow", "Developer community & QA", "open url stackoverflow.com"),
            ("✨", "Google Gemini", "Gemini AI Workspace", "open url gemini.google.com"),
            ("📖", "Wikipedia", "Free online encyclopedia", "open url wikipedia.org"),
            ("👾", "Reddit", "Discussions & news communities", "open url reddit.com"),
        ]
        for i, (ic, title, desc, cmd) in enumerate(portals):
            btn = make_action_btn(ic, title, desc, cmd, self.command_sent)
            grid.addWidget(btn, i // 2, i % 2)
        pc_lay.addLayout(grid)
        lay.addWidget(portals_card)
        lay.addStretch()

    def _do_search(self):
        q = self.search_box.text().strip()
        if q:
            self.command_sent.emit(f"search {q}")


# ══════════════════════════════════════════════════════════
#  4. Social Media View
# ══════════════════════════════════════════════════════════
class SocialView(QWidget):
    command_sent = pyqtSignal(str)
    refresh_whatsapp = pyqtSignal()
    send_whatsapp_custom = pyqtSignal(str, str)
    check_whatsapp = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(14)

        lay.addWidget(make_header("◈  Social & Messaging Hub", "WhatsApp Web zero-browser synchronization & social accounts"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(0, 0, 8, 0)
        c_lay.setSpacing(14)

        # ── 1. WhatsApp Web Connection & QR Center ───────────
        wa_card = BaseCard(radius=14)
        wc_lay = QVBoxLayout(wa_card)
        wc_lay.setContentsMargins(18, 14, 18, 14)
        wc_lay.setSpacing(10)

        top_h = QHBoxLayout()
        wlbl = QLabel("💬  WhatsApp Web — Zero-Browser Background Sync")
        wlbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        wlbl.setStyleSheet(f"color: {C_TEXT};")
        top_h.addWidget(wlbl, 1)

        self.wa_badge = QLabel("🟢  CONNECTED")
        self.wa_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.wa_badge.setStyleSheet("color: #00e676; background: rgba(0, 230, 118, 0.15); border: 1px solid rgba(0, 230, 118, 0.4); border-radius: 12px; padding: 3px 10px;")
        top_h.addWidget(self.wa_badge)
        wc_lay.addLayout(top_h)

        self.wa_desc = QLabel("Operates in NIA's dedicated background profile. Synchronizes, receives commands, and stays connected even when Chrome, Edge, and external browsers are closed.")
        self.wa_desc.setFont(QFont("Segoe UI", 9))
        self.wa_desc.setStyleSheet(f"color: {C_SUBTEXT};")
        self.wa_desc.setWordWrap(True)
        wc_lay.addWidget(self.wa_desc)

        # QR Code Display Frame (Visible when QR is required, hidden when connected)
        self.qr_frame = QFrame()
        self.qr_frame.setStyleSheet("background: rgba(10, 18, 50, 200); border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 12px; padding: 12px;")
        qf_lay = QVBoxLayout(self.qr_frame)
        qf_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qf_lay.setSpacing(8)

        self.qr_instr = QLabel("📲 Scan this QR Code with your phone's WhatsApp (Linked Devices):")
        self.qr_instr.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.qr_instr.setStyleSheet(f"color: {C_CYAN};")
        self.qr_instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qf_lay.addWidget(self.qr_instr)

        self.qr_img_label = QLabel("No QR code needed. Active session detected.")
        self.qr_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_img_label.setStyleSheet(f"color: {C_TEXT}; font-size: 11px;")
        self.qr_img_label.setFixedSize(220, 220)
        qf_lay.addWidget(self.qr_img_label, 0, Qt.AlignmentFlag.AlignCenter)

        wc_lay.addWidget(self.qr_frame)
        self.qr_frame.hide()

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        ref_btn = QPushButton("🔄  Refresh WhatsApp Session")
        ref_btn.setFixedHeight(36)
        ref_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        ref_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ref_btn.setStyleSheet(f"QPushButton {{ background: rgba(61, 142, 248, 0.2); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.4); border-radius: 8px; padding: 0 12px; }} QPushButton:hover {{ background: rgba(61, 142, 248, 0.35); }}")
        ref_btn.clicked.connect(self._on_refresh)
        btn_row.addWidget(ref_btn)

        chk_btn = QPushButton("📡  Check Connection")
        chk_btn.setFixedHeight(36)
        chk_btn.setFont(QFont("Segoe UI", 9))
        chk_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chk_btn.setStyleSheet(f"QPushButton {{ background: rgba(61, 142, 248, 0.12); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.25); border-radius: 8px; padding: 0 12px; }} QPushButton:hover {{ background: rgba(61, 142, 248, 0.25); }}")
        chk_btn.clicked.connect(self._on_check)
        btn_row.addWidget(chk_btn)

        ext_btn = QPushButton("🌐  Open Full Web in Browser")
        ext_btn.setFixedHeight(36)
        ext_btn.setFont(QFont("Segoe UI", 9))
        ext_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ext_btn.setStyleSheet(f"QPushButton {{ background: rgba(61, 142, 248, 0.12); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.25); border-radius: 8px; padding: 0 12px; }} QPushButton:hover {{ background: rgba(61, 142, 248, 0.25); }}")
        ext_btn.clicked.connect(lambda: self.command_sent.emit("open url web.whatsapp.com"))
        btn_row.addWidget(ext_btn)

        btn_row.addStretch()
        wc_lay.addLayout(btn_row)

        # Quick Message Subcard
        qmsg_box = QFrame()
        qmsg_box.setStyleSheet("background: rgba(10, 18, 50, 120); border-radius: 10px; padding: 8px;")
        qmlay = QHBoxLayout(qmsg_box)
        qmlay.setContentsMargins(8, 4, 8, 4)
        qmlay.setSpacing(8)

        self.wa_target_phone = QLineEdit("+918979640795")
        self.wa_target_phone.setFixedWidth(140)
        self.wa_target_phone.setFixedHeight(36)
        self.wa_target_phone.setPlaceholderText("Phone / Number")
        self.wa_target_phone.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 8px; }}")

        self.wa_msg_input = QLineEdit()
        self.wa_msg_input.setFixedHeight(36)
        self.wa_msg_input.setPlaceholderText("Type a quick WhatsApp message to send...")
        self.wa_msg_input.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 12px; }}")
        self.wa_msg_input.returnPressed.connect(self._on_send_msg)

        send_wa_btn = QPushButton("📤  Send Message")
        send_wa_btn.setFixedHeight(36)
        send_wa_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        send_wa_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_wa_btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #25D366, stop:1 #128C7E); color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #2bee72; }")
        send_wa_btn.clicked.connect(self._on_send_msg)

        qmlay.addWidget(self.wa_target_phone)
        qmlay.addWidget(self.wa_msg_input, 1)
        qmlay.addWidget(send_wa_btn)
        wc_lay.addWidget(qmsg_box)

        c_lay.addWidget(wa_card)

        # ── 2. Tweet / X Composer ───────────────────────────
        x_card = BaseCard(radius=14)
        xc_lay = QVBoxLayout(x_card)
        xc_lay.setContentsMargins(18, 14, 18, 14)
        xc_lay.setSpacing(10)

        xlbl = QLabel("Compose Update for Twitter / X")
        xlbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        xlbl.setStyleSheet(f"color: {C_TEXT};")
        xc_lay.addWidget(xlbl)

        self.tweet_text = QTextEdit()
        self.tweet_text.setPlaceholderText("What is happening in your world? Write a post...")
        self.tweet_text.setFixedHeight(80)
        self.tweet_text.setStyleSheet(f"QTextEdit {{ background: rgba(10, 18, 50, 180); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.4); border-radius: 10px; padding: 8px; }}")
        xc_lay.addWidget(self.tweet_text)

        post_btn = QPushButton("Post to Twitter / X")
        post_btn.setFixedHeight(38)
        post_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        post_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        post_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0); color: white; border: none; border-radius: 10px; }} QPushButton:hover {{ background: {C_CYAN}; }}")
        post_btn.clicked.connect(self._post_tweet)
        xc_lay.addWidget(post_btn)
        c_lay.addWidget(x_card)

        # ── 3. Quick Channels ───────────────────────────────
        ch_card = BaseCard(radius=14)
        cc_lay = QVBoxLayout(ch_card)
        cc_lay.setContentsMargins(18, 14, 18, 14)
        cc_lay.setSpacing(10)

        clbl = QLabel("Connected Channels")
        clbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        clbl.setStyleSheet(f"color: {C_TEXT};")
        cc_lay.addWidget(clbl)

        grid = QGridLayout()
        grid.setSpacing(10)
        channels = [
            ("💬", "WhatsApp Web", "Open active WhatsApp chats", "open url web.whatsapp.com"),
            ("💼", "LinkedIn Feed", "Professional network feed", "open url linkedin.com/feed"),
            ("✈", "Telegram Web", "Telegram messaging client", "open url web.telegram.org"),
            ("📸", "Instagram", "Photos, reels & messaging", "open url instagram.com"),
        ]
        for i, (ic, title, desc, cmd) in enumerate(channels):
            btn = make_action_btn(ic, title, desc, cmd, self.command_sent)
            grid.addWidget(btn, i // 2, i % 2)
        cc_lay.addLayout(grid)
        c_lay.addWidget(ch_card)

        scroll.setWidget(container)
        lay.addWidget(scroll, 1)

    def set_whatsapp_status(self, status: str, details: str):
        try:
            if status == "CONNECTED":
                self.wa_badge.setText("🟢  CONNECTED")
                self.wa_badge.setStyleSheet("color: #00e676; background: rgba(0, 230, 118, 0.15); border: 1px solid rgba(0, 230, 118, 0.4); border-radius: 12px; padding: 3px 10px;")
                self.wa_desc.setText(f"Status: {details}")
                self.qr_frame.hide()
            elif status == "QR_REQUIRED":
                self.wa_badge.setText("🟡  SCAN QR CODE")
                self.wa_badge.setStyleSheet("color: #ffd600; background: rgba(255, 214, 0, 0.15); border: 1px solid rgba(255, 214, 0, 0.4); border-radius: 12px; padding: 3px 10px;")
                self.wa_desc.setText(details)
                self.qr_frame.show()
            elif status == "CONNECTING":
                self.wa_badge.setText("🔵  CONNECTING...")
                self.wa_badge.setStyleSheet("color: #00d4ff; background: rgba(0, 212, 255, 0.15); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 12px; padding: 3px 10px;")
                self.wa_desc.setText(details)
            else:
                self.wa_badge.setText("⚪  OFFLINE")
                self.wa_badge.setStyleSheet("color: #8892b0; background: rgba(136, 146, 176, 0.15); border: 1px solid rgba(136, 146, 176, 0.4); border-radius: 12px; padding: 3px 10px;")
                self.wa_desc.setText(details)
        except Exception as e:
            print(f"[set_whatsapp_status Error]: {e}")

    def set_qr_image(self, qr_path: str):
        try:
            if os.path.exists(qr_path):
                pix = QPixmap(qr_path)
                if not pix.isNull():
                    self.qr_img_label.setPixmap(pix.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.qr_frame.show()
        except Exception as e:
            print(f"[set_qr_image Error]: {e}")

    def _on_refresh(self):
        self.set_whatsapp_status("CONNECTING", "Refreshing session in background...")
        self.refresh_whatsapp.emit()

    def _on_check(self):
        self.check_whatsapp.emit()

    def _on_send_msg(self):
        phone = self.wa_target_phone.text().strip()
        msg = self.wa_msg_input.text().strip()
        if phone and msg:
            self.send_whatsapp_custom.emit(phone, msg)
            self.wa_msg_input.clear()

    def _post_tweet(self):
        txt = self.tweet_text.toPlainText().strip()
        if txt:
            self.command_sent.emit(f"post on twitter: {txt}")


# ══════════════════════════════════════════════════════════
#  5. Files & Documents View
# ══════════════════════════════════════════════════════════
class FilesView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("📄  Files & Document Drafting", "Draft Word (.docx) documents and capture screenshots"))

        # Doc Drafter Card
        doc_card = BaseCard(radius=14)
        dc_lay = QVBoxLayout(doc_card)
        dc_lay.setContentsMargins(18, 14, 18, 14)
        dc_lay.setSpacing(10)

        dlbl = QLabel("Autonomous Word Document Drafter (.docx)")
        dlbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        dlbl.setStyleSheet(f"color: {C_TEXT};")
        dc_lay.addWidget(dlbl)

        h_row = QHBoxLayout()
        self.doc_title = QLineEdit()
        self.doc_title.setPlaceholderText("Document Title (e.g. Sick Leave Application, Meeting Notes)...")
        self.doc_title.setFont(QFont("Segoe UI", 10))
        self.doc_title.setFixedHeight(38)
        self.doc_title.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 8px;
                padding: 0 12px;
            }}
        """)
        h_row.addWidget(self.doc_title, 1)

        self.doc_type = QLineEdit()
        self.doc_type.setPlaceholderText("Type (Letter/Report/Notes)...")
        self.doc_type.setText("Letter")
        self.doc_type.setFont(QFont("Segoe UI", 10))
        self.doc_type.setFixedHeight(38)
        self.doc_type.setFixedWidth(160)
        self.doc_type.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 8px;
                padding: 0 12px;
            }}
        """)
        h_row.addWidget(self.doc_type)
        dc_lay.addLayout(h_row)

        self.doc_content = QTextEdit()
        self.doc_content.setPlaceholderText("Enter the key points or details of the document here...")
        self.doc_content.setFixedHeight(90)
        self.doc_content.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        dc_lay.addWidget(self.doc_content)

        draft_btn = QPushButton("📝  Generate & Save Word Document (.docx)")
        draft_btn.setFixedHeight(40)
        draft_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        draft_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        draft_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0);
                color: white; border: none; border-radius: 10px;
            }}
            QPushButton:hover {{ background: {C_CYAN}; }}
        """)
        draft_btn.clicked.connect(self._draft)
        dc_lay.addWidget(draft_btn)
        lay.addWidget(doc_card)

        # Screenshots Card
        ss_card = BaseCard(radius=14)
        sc_lay = QVBoxLayout(ss_card)
        sc_lay.setContentsMargins(18, 14, 18, 14)
        sc_lay.setSpacing(10)

        slbl = QLabel("Screen Capture Tools")
        slbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        slbl.setStyleSheet(f"color: {C_TEXT};")
        sc_lay.addWidget(slbl)

        srow = QHBoxLayout()
        srow.setSpacing(10)
        ss_btn1 = make_action_btn("📸", "Take Screenshot", "Save current screen to Pictures", "take a screenshot", self.command_sent)
        ss_btn2 = make_action_btn("📲", "Screenshot to WhatsApp", "Capture and send to phone", "take a screenshot and send to my WhatsApp", self.command_sent)
        srow.addWidget(ss_btn1)
        srow.addWidget(ss_btn2)
        sc_lay.addLayout(srow)
        lay.addWidget(ss_card)
        lay.addStretch()

    def _draft(self):
        title = self.doc_title.text().strip() or "Drafted Document"
        dtype = self.doc_type.text().strip() or "Letter"
        content = self.doc_content.toPlainText().strip() or "General template document drafted by NIA."
        self.command_sent.emit(f"draft a {dtype} titled '{title}' with content: {content}")


# ══════════════════════════════════════════════════════════
#  6. Media View
# ══════════════════════════════════════════════════════════
class MediaView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("♫  Music & Media Center", "Search and play YouTube songs with hands-free control"))

        # Search Music Card
        music_card = BaseCard(radius=14)
        mc_lay = QVBoxLayout(music_card)
        mc_lay.setContentsMargins(18, 14, 18, 14)
        mc_lay.setSpacing(10)

        mlbl = QLabel("Music & Audio Player (Windows Media Player Default)")
        mlbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        mlbl.setStyleSheet(f"color: {C_TEXT};")
        mc_lay.addWidget(mlbl)

        sub_lbl = QLabel("Songs play in Windows Media Player by default. YouTube will auto-play the 1st song when selected.")
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setStyleSheet(f"color: {C_SUBTEXT};")
        mc_lay.addWidget(sub_lbl)

        srow = QHBoxLayout()
        srow.setSpacing(8)
        self.song_box = QLineEdit()
        self.song_box.setPlaceholderText("Enter song name or singer (e.g. Arijit Singh, Kesariya)...")
        self.song_box.setFont(QFont("Segoe UI", 11))
        self.song_box.setFixedHeight(44)
        self.song_box.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 18, 50, 180);
                color: {C_TEXT};
                border: 1px solid rgba(61, 142, 248, 0.4);
                border-radius: 22px;
                padding: 0 16px;
            }}
            QLineEdit:focus {{ border-color: {C_CYAN}; }}
        """)
        self.song_box.returnPressed.connect(self._play_wmp)

        wmp_btn = QPushButton("▶  Play (WMP)")
        wmp_btn.setFixedHeight(44)
        wmp_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        wmp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wmp_btn.setToolTip("Plays in Windows Media Player (Default)")
        wmp_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0);
                color: white; border: none; border-radius: 22px; padding: 0 16px;
            }}
            QPushButton:hover {{ background: {C_CYAN}; }}
        """)
        wmp_btn.clicked.connect(self._play_wmp)

        yt_btn = QPushButton("▶  YouTube (Auto-Play)")
        yt_btn.setFixedHeight(44)
        yt_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        yt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yt_btn.setToolTip("Plays the 1st song directly on YouTube")
        yt_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #cc181e, stop:1 #800000);
                color: white; border: none; border-radius: 22px; padding: 0 16px;
            }}
            QPushButton:hover {{ background: #ff3333; }}
        """)
        yt_btn.clicked.connect(self._play_yt)

        srow.addWidget(self.song_box, 1)
        srow.addWidget(wmp_btn)
        srow.addWidget(yt_btn)
        mc_lay.addLayout(srow)
        lay.addWidget(music_card)

        # Preset Stations Card
        st_card = BaseCard(radius=14)
        sc_lay = QVBoxLayout(st_card)
        sc_lay.setContentsMargins(18, 14, 18, 14)
        sc_lay.setSpacing(10)

        slbl = QLabel("One-Click Music Stations & Controls")
        slbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        slbl.setStyleSheet(f"color: {C_TEXT};")
        sc_lay.addWidget(slbl)

        grid = QGridLayout()
        grid.setSpacing(10)
        stations = [
            ("🎵", "Arijit Singh (WMP)", "Windows Media Player local music", "play Arijit Singh"),
            ("▶️", "Arijit Hits (YouTube)", "Plays 1st song directly on YouTube", "play Arijit Singh hits on youtube"),
            ("🎧", "Lo-Fi Beats (WMP)", "Windows Media Player chill music", "play lofi chill beats"),
            ("▶️", "Lo-Fi Live (YouTube)", "Directly streams 1st Lo-Fi stream", "play lofi hip hop radio on youtube"),
            ("📻", "Retro Hindi (WMP)", "Golden vintage Hindi melodies", "play classic hindi songs"),
            ("💽", "Open Media Player", "Launch Windows Media Player app", "open windows media player"),
        ]
        for i, (ic, title, desc, cmd) in enumerate(stations):
            btn = make_action_btn(ic, title, desc, cmd, self.command_sent)
            grid.addWidget(btn, i // 2, i % 2)
        sc_lay.addLayout(grid)
        lay.addWidget(st_card)
        lay.addStretch()

    def _play_wmp(self):
        s = self.song_box.text().strip()
        if s:
            self.command_sent.emit(f"play {s}")
        else:
            self.command_sent.emit("open windows media player")

    def _play_yt(self):
        s = self.song_box.text().strip()
        if s:
            self.command_sent.emit(f"play {s} on youtube")
        else:
            self.command_sent.emit("play trending hindi songs on youtube")


# ══════════════════════════════════════════════════════════
#  7. Automation View
# ══════════════════════════════════════════════════════════
class AutomationView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        import os
        from workflow_manager import WorkflowManager
        self.wm = WorkflowManager(os.path.join(os.path.dirname(__file__), "workflows.json"))
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("⚡  Automation Workflows", "Create multi-step routines triggered by a single voice command"))

        # My Custom Workflows
        self.wf_card = BaseCard(radius=14)
        wc_lay = QVBoxLayout(self.wf_card)
        wc_lay.setContentsMargins(18, 14, 18, 14)
        wc_lay.setSpacing(12)

        lbl = QLabel("My Active Workflows")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C_TEXT};")
        wc_lay.addWidget(lbl)

        self.wf_text = QTextEdit()
        self.wf_text.setReadOnly(True)
        self.wf_text.setStyleSheet(f"QTextEdit {{ background: rgba(10, 18, 50, 180); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.4); border-radius: 8px; padding: 10px; font-size: 14px; }}")
        self.wf_text.setFixedHeight(120)
        wc_lay.addWidget(self.wf_text)

        self._refresh_wfs()

        # Build Form
        lbl_new = QLabel("Create New Routine")
        lbl_new.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_new.setStyleSheet(f"color: {C_TEXT}; margin-top: 10px;")
        wc_lay.addWidget(lbl_new)

        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Routine Name (e.g. Morning Startup)")
        self.name_in.setFixedHeight(36)
        self.name_in.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 10px; }}")

        self.trig_in = QLineEdit()
        self.trig_in.setPlaceholderText("Voice Trigger (e.g. 'start my morning')")
        self.trig_in.setFixedHeight(36)
        self.trig_in.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 10px; }}")

        self.act_in = QLineEdit()
        self.act_in.setPlaceholderText("Actions separated by commas (e.g. 'open vscode, open chrome, play lofi')")
        self.act_in.setFixedHeight(36)
        self.act_in.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 10px; }}")

        form_grid = QGridLayout()
        form_grid.setSpacing(10)
        form_grid.addWidget(self.name_in, 0, 0)
        form_grid.addWidget(self.trig_in, 0, 1)
        form_grid.addWidget(self.act_in, 1, 0, 1, 2)
        wc_lay.addLayout(form_grid)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("💾 Save Routine")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0); color: white; border: none; border-radius: 8px; padding: 0 16px; font-weight: bold; }} QPushButton:hover {{ background: {C_CYAN}; }}")
        add_btn.clicked.connect(self._add_wf)
        
        del_btn = QPushButton("🗑️ Clear All Routines")
        del_btn.setFixedHeight(36)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"QPushButton {{ background: rgba(220, 53, 69, 0.2); color: #ff6b6b; border: 1px solid rgba(220, 53, 69, 0.5); border-radius: 8px; padding: 0 16px; }} QPushButton:hover {{ background: rgba(220, 53, 69, 0.4); color: white; }}")
        del_btn.clicked.connect(self._clear_wfs)
        
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        wc_lay.addLayout(btn_row)

        lay.addWidget(self.wf_card)
        lay.addStretch()

    def _refresh_wfs(self):
        self.wm.load()
        if not self.wm.workflows:
            self.wf_text.setPlainText("No custom routines built yet.")
            return
        
        lines = []
        for trig, d in self.wm.workflows.items():
            acts = ", ".join(d["actions"])
            lines.append(f"• {d['name']} \n  Trigger: '{trig}' \n  Actions: {acts}\n")
        self.wf_text.setPlainText("\n".join(lines))

    def _add_wf(self):
        n = self.name_in.text().strip()
        t = self.trig_in.text().strip()
        a = self.act_in.text().strip()
        if n and t and a:
            acts = [x.strip() for x in a.split(",")]
            self.wm.add_workflow(n, t, acts)
            self.name_in.clear()
            self.trig_in.clear()
            self.act_in.clear()
            self._refresh_wfs()

    def _clear_wfs(self):
        self.wm.workflows.clear()
        self.wm.save()
        self._refresh_wfs()


# ══════════════════════════════════════════════════════════
#  8. Learning & Memory View
# ══════════════════════════════════════════════════════════
class MemoryView(QWidget):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        import os
        from memory_manager import MemoryManager
        self.mm = MemoryManager(os.path.join(os.path.dirname(__file__), "memory_bank.json"))
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("🧠  Learning & Memory Profile", "Nia's active personalization memory and user profile"))

        # Facts Card
        self.facts_card = BaseCard(radius=14)
        c_lay = QVBoxLayout(self.facts_card)
        c_lay.setContentsMargins(18, 14, 18, 14)
        c_lay.setSpacing(12)

        lbl = QLabel("Remembered Facts")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C_TEXT};")
        c_lay.addWidget(lbl)

        self.facts_text = QTextEdit()
        self.facts_text.setReadOnly(True)
        self.facts_text.setStyleSheet(f"QTextEdit {{ background: rgba(10, 18, 50, 180); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.4); border-radius: 8px; padding: 10px; font-size: 14px; }}")
        c_lay.addWidget(self.facts_text)
        
        self._refresh_facts()

        # Add Fact Row
        h_row = QHBoxLayout()
        self.topic_in = QLineEdit()
        self.topic_in.setPlaceholderText("Topic (e.g. Work, Preferences)")
        self.topic_in.setFixedHeight(36)
        self.topic_in.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 8px; }}")
        
        self.fact_in = QLineEdit()
        self.fact_in.setPlaceholderText("Fact to remember...")
        self.fact_in.setFixedHeight(36)
        self.fact_in.setStyleSheet(f"QLineEdit {{ background: rgba(15, 25, 60, 200); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.3); border-radius: 8px; padding: 0 8px; }}")
        
        add_btn = QPushButton("➕ Remember")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0); color: white; border: none; border-radius: 8px; padding: 0 16px; font-weight: bold; }} QPushButton:hover {{ background: {C_CYAN}; }}")
        add_btn.clicked.connect(self._add_fact)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setFixedHeight(36)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"QPushButton {{ background: rgba(220, 53, 69, 0.2); color: #ff6b6b; border: 1px solid rgba(220, 53, 69, 0.5); border-radius: 8px; padding: 0 16px; }} QPushButton:hover {{ background: rgba(220, 53, 69, 0.4); color: white; }}")
        clear_btn.clicked.connect(self._clear_all)

        h_row.addWidget(self.topic_in)
        h_row.addWidget(self.fact_in, 1)
        h_row.addWidget(add_btn)
        h_row.addWidget(clear_btn)
        c_lay.addLayout(h_row)

        lay.addWidget(self.facts_card)
        lay.addStretch()

    def _refresh_facts(self):
        self.mm.load()
        ctx = self.mm.get_all_context()
        self.facts_text.setPlainText(ctx)

    def _add_fact(self):
        t = self.topic_in.text().strip()
        f = self.fact_in.text().strip()
        if t and f:
            self.mm.remember(t, f)
            self.topic_in.clear()
            self.fact_in.clear()
            self._refresh_facts()

    def _clear_all(self):
        self.mm.memories.clear()
        self.mm.save()
        self._refresh_facts()



# ══════════════════════════════════════════════════════════
#  9. Settings View
# ══════════════════════════════════════════════════════════
class SettingsView(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        lay.addWidget(make_header("⚙  System & AI Settings", "Configure your AI engines, API keys, and voice models"))

        card = BaseCard(radius=14)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(18, 14, 18, 14)
        c_lay.setSpacing(14)

        lbl = QLabel("Live Configuration Editor")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C_TEXT};")
        c_lay.addWidget(lbl)

        # Build form
        form_lay = QGridLayout()
        form_lay.setSpacing(10)
        
        # Helper to make label
        def mk_lbl(text):
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            l.setStyleSheet(f"color: {C_SUBTEXT};")
            return l

        # Helper to make edit
        def mk_edit(text, is_pw=False):
            e = QLineEdit(text)
            e.setFont(QFont("Segoe UI", 10))
            e.setFixedHeight(34)
            if is_pw: e.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
            e.setStyleSheet(f"QLineEdit {{ background: rgba(10, 18, 50, 180); color: {C_TEXT}; border: 1px solid rgba(61, 142, 248, 0.4); border-radius: 8px; padding: 0 10px; }}")
            return e

        self.edit_llm_model = mk_edit(self.config.get("llm_settings", {}).get("model", "gemini/gemini-3.6-flash"))
        self.edit_gemini_key = mk_edit(self.config.get("api_keys", {}).get("gemini_api_key", ""), True)
        self.edit_openai_key = mk_edit(self.config.get("api_keys", {}).get("openai_api_key", ""), True)
        self.edit_tts_voice = mk_edit(self.config.get("voice_settings", {}).get("tts_voice", "hi-IN-SwaraNeural"))
        self.edit_wa_num = mk_edit(self.config.get("user_profile", {}).get("whatsapp_number", ""))
        self.edit_user_name = mk_edit(self.config.get("user_profile", {}).get("name", "manoj"))
        self.edit_license_key = mk_edit(self.config.get("license_key", ""))

        form_lay.addWidget(mk_lbl("AI Model (e.g. ollama/llama3.2):"), 0, 0)
        form_lay.addWidget(self.edit_llm_model, 0, 1)

        form_lay.addWidget(mk_lbl("Gemini API Key:"), 1, 0)
        form_lay.addWidget(self.edit_gemini_key, 1, 1)

        form_lay.addWidget(mk_lbl("OpenAI API Key:"), 2, 0)
        form_lay.addWidget(self.edit_openai_key, 2, 1)

        form_lay.addWidget(mk_lbl("TTS Voice Model:"), 3, 0)
        form_lay.addWidget(self.edit_tts_voice, 3, 1)

        form_lay.addWidget(mk_lbl("WhatsApp Target Number:"), 4, 0)
        form_lay.addWidget(self.edit_wa_num, 4, 1)

        form_lay.addWidget(mk_lbl("User Name:"), 5, 0)
        form_lay.addWidget(self.edit_user_name, 5, 1)

        form_lay.addWidget(mk_lbl("License Key (₹99 Test / Pro):"), 6, 0)
        form_lay.addWidget(self.edit_license_key, 6, 1)

        c_lay.addLayout(form_lay)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C_BLUE}, stop:1 #1230a0); color: white; border: none; border-radius: 10px; padding: 0 16px; font-weight: bold; }} QPushButton:hover {{ background: {C_CYAN}; }}")
        save_btn.clicked.connect(self._save_settings)

        check_btn = QPushButton("🩺  Run Diagnostics")
        check_btn.setFixedHeight(40)
        check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        check_btn.setStyleSheet(f"QPushButton {{ background: rgba(61, 142, 248, 0.15); color: {C_BLUE}; border: 1px solid rgba(61, 142, 248, 0.35); border-radius: 10px; padding: 0 16px; }} QPushButton:hover {{ background: rgba(61, 142, 248, 0.3); color: white; }}")
        check_btn.clicked.connect(lambda: self.command_sent.emit("check system status"))

        btn_row.addWidget(save_btn)
        btn_row.addWidget(check_btn)
        btn_row.addStretch()
        c_lay.addLayout(btn_row)

        lay.addWidget(card)
        lay.addStretch()

    def _save_settings(self):
        import json, os
        # Update config dict
        if "llm_settings" not in self.config: self.config["llm_settings"] = {}
        if "api_keys" not in self.config: self.config["api_keys"] = {}
        if "voice_settings" not in self.config: self.config["voice_settings"] = {}
        if "user_profile" not in self.config: self.config["user_profile"] = {}

        self.config["llm_settings"]["model"] = self.edit_llm_model.text().strip()
        self.config["api_keys"]["gemini_api_key"] = self.edit_gemini_key.text().strip()
        self.config["api_keys"]["openai_api_key"] = self.edit_openai_key.text().strip()
        self.config["voice_settings"]["tts_voice"] = self.edit_tts_voice.text().strip()
        self.config["user_profile"]["whatsapp_number"] = self.edit_wa_num.text().strip()
        self.config["user_profile"]["name"] = self.edit_user_name.text().strip()
        self.config["license_key"] = self.edit_license_key.text().strip()

        # Re-check license
        try:
            from license_guard import check_license_status
            self.config["license_info"] = check_license_status(license_key=self.config["license_key"])
        except Exception:
            pass

        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            self.command_sent.emit("Settings saved successfully!")
            
            try:
                from sound_effects import SoundEffects
                SoundEffects.action_done()
            except Exception: pass

        except Exception as e:
            self.command_sent.emit(f"Failed to save settings: {e}")

