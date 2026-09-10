"""
whatsapp_manager.py
──────────────────────────────────────────────────────────
Autonomous background WhatsApp Web manager for NIA.
- Runs isolated in NIA's dedicated Chromium profile (nia_browser_profile).
- Works even when external system browsers (Chrome, Edge, etc.) are closed.
- Emits real-time connection status and captures live QR code directly for NIA UI.
- Maintains and refreshes session automatically in the background.
- Listens 24/7 for incoming WhatsApp commands and replies automatically.
"""

import os
import time
import queue
import urllib.parse
from PyQt6.QtCore import QThread, pyqtSignal

class WhatsAppManager(QThread):
    status_changed   = pyqtSignal(str, str)    # (status: CONNECTED|QR_REQUIRED|CONNECTING|OFFLINE, details)
    qr_updated       = pyqtSignal(str)         # path to captured QR code image
    message_result   = pyqtSignal(bool, str)   # (success, feedback)
    command_received = pyqtSignal(str)         # incoming command text from WhatsApp chat!

    def __init__(self, session_dir: str, target_chat="Nia Commands", headless: bool = True, parent=None):
        super().__init__(parent)
        self.session_dir = session_dir
        self.target_chat = target_chat
        self.headless = headless
        self._running = True
        self._command_queue = queue.Queue()
        self.qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_qr.png")
        self.status = "OFFLINE"
        self.status_detail = "Initializing..."
        self._sent_replies = set()
        self._seen_message_ids = set()
        self._last_msgs = []
        self._chat_opened = False

    def run(self):
        from playwright.sync_api import sync_playwright

        self.status = "CONNECTING"
        self.status_detail = "Starting background WhatsApp engine..."
        self.status_changed.emit(self.status, self.status_detail)

        # Clean stale SingletonLock if left behind by previous unexpected crashes
        if os.path.exists(self.session_dir):
            for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
                lock_file = os.path.join(self.session_dir, lock_name)
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                    except Exception:
                        pass

        try:
            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=self.session_dir,
                    headless=self.headless,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://web.whatsapp.com", timeout=60000)

                # Initial status check
                self._inspect_and_update_state(page)
                last_poll = time.time()
                last_msg_check = time.time()

                # Worker loop
                while self._running:
                    try:
                        cmd, args = self._command_queue.get(timeout=2)
                        if cmd == "stop":
                            break
                        elif cmd == "refresh":
                            self.status = "CONNECTING"
                            self.status_detail = "Refreshing WhatsApp session..."
                            self.status_changed.emit(self.status, self.status_detail)
                            try:
                                page.reload(timeout=30000)
                                self._inspect_and_update_state(page)
                            except Exception as ex:
                                self.status_detail = f"Refresh note: {ex}"
                        elif cmd == "send_message":
                            phone, text = args
                            success, feedback = self._do_send_message(page, phone, text)
                            self.message_result.emit(success, feedback)
                        elif cmd == "chat_reply":
                            reply_text = args
                            self._sent_replies.add(reply_text)
                            self._do_send_chat_reply(page, reply_text)
                        elif cmd == "check_state":
                            self._inspect_and_update_state(page)
                    except queue.Empty:
                        now = time.time()

                        # Connection state heartbeat
                        interval = 120 if self.status == "CONNECTED" else 4
                        if now - last_poll >= interval:
                            last_poll = now
                            self._inspect_and_update_state(page)

                        # Incoming message listener loop (every 2.5 seconds when connected)
                        if self.status == "CONNECTED" and now - last_msg_check >= 2.5:
                            last_msg_check = now
                            self._check_incoming_messages(page)

                context.close()
        except Exception as e:
            self.status = "OFFLINE"
            self.status_detail = f"Connection error: {str(e)}"
            self.status_changed.emit(self.status, self.status_detail)

    def _inspect_and_update_state(self, page):
        """Checks whether WhatsApp Web is logged in or requires QR scan."""
        try:
            if page.is_closed():
                return

            # Check for chat pane or search box indicating active logged-in session
            logged_in = page.locator("div[data-tab='3'], div[aria-label='Search input textbox'], header[data-testid='chatlist-header'], div#pane-side").first
            if logged_in.is_visible(timeout=3000):
                if self.status != "CONNECTED":
                    self.status = "CONNECTED"
                    self.status_detail = "WhatsApp Web is active, synced & ready."
                    self.status_changed.emit(self.status, self.status_detail)
                return

            # Check if QR code canvas is present
            canvases = page.locator("canvas").all()
            if canvases and canvases[0].is_visible():
                try:
                    canvases[0].screenshot(path=self.qr_path)
                    if self.status != "QR_REQUIRED":
                        self.status = "QR_REQUIRED"
                        self.status_detail = "Scan the QR code with your WhatsApp app on your phone."
                        self.status_changed.emit(self.status, self.status_detail)
                    self.qr_updated.emit(self.qr_path)
                    return
                except Exception:
                    pass

            # Still loading or sync in progress
            if self.status != "CONNECTING":
                self.status = "CONNECTING"
                self.status_detail = "Syncing WhatsApp Web with server..."
                self.status_changed.emit(self.status, self.status_detail)
        except Exception as e:
            if "Target closed" in str(e) or "browser has been closed" in str(e).lower():
                self.status = "OFFLINE"
                self.status_detail = "Browser session closed."
                self.status_changed.emit(self.status, self.status_detail)

    def _init_seen_messages(self, page):
        """Initializes seen message IDs so pre-existing messages are not re-executed."""
        try:
            rows = page.locator("div[data-id]").all()
            for r in rows:
                did = r.get_attribute("data-id")
                if did:
                    self._seen_message_ids.add(did)
            print(f"[WhatsAppManager] Initialized with {len(self._seen_message_ids)} existing messages in chat.")
        except Exception as e:
            print(f"[WhatsAppManager Init Messages Note]: {e}")

    def _ensure_command_chat_open(self, page) -> bool:
        """Opens self-chat (You) or user's active command chat."""
        if self._chat_opened:
            return True
        try:
            # Check if chat is already open (input box visible)
            box = page.locator("div[contenteditable='true'][data-tab='10'], footer div[contenteditable='true']").first
            if box.is_visible(timeout=800):
                self._chat_opened = True
                self._init_seen_messages(page)
                return True

            # 1. Look for self-chat: (You) in chat list
            self_chat = page.locator("div#pane-side span:has-text('(You)'), div#pane-side span[title*='You'], div#pane-side span[title*='93542']").first
            if self_chat.is_visible(timeout=2000):
                print("[WhatsAppManager] Found (You) self-chat. Clicking to open...")
                self_chat.click()
                time.sleep(1.0)
                self._chat_opened = True
                self._init_seen_messages(page)
                return True

            # 2. Look for target chat if specified and not 'Nia Commands'
            if self.target_chat and self.target_chat != "Nia Commands":
                target = page.locator(f"div#pane-side span[title='{self.target_chat}']").first
                if target.is_visible(timeout=1000):
                    target.click()
                    time.sleep(1.0)
                    self._chat_opened = True
                    self._init_seen_messages(page)
                    return True

            # 3. Fallback: Click the very first row in chat list
            first_row = page.locator("div#pane-side div[role='row']").first
            if first_row.is_visible(timeout=2000):
                print("[WhatsAppManager] Opening top chat in list...")
                first_row.click()
                time.sleep(1.0)
                self._chat_opened = True
                self._init_seen_messages(page)
                return True
        except Exception as e:
            print(f"[WhatsAppManager Open Chat Exception]: {e}")
        return False

    def _check_incoming_messages(self, page):
        """Polls for new incoming command messages from WhatsApp."""
        try:
            if not self._chat_opened:
                if not self._ensure_command_chat_open(page):
                    return

            rows = page.locator("div[data-id]").all()
            for row in rows:
                try:
                    did = row.get_attribute("data-id")
                    if not did or did in self._seen_message_ids:
                        continue

                    # Mark as seen immediately
                    self._seen_message_ids.add(did)

                    # Extract text
                    txt_el = row.locator("span.selectable-text").first
                    if not txt_el.is_visible(timeout=200):
                        continue

                    text = txt_el.inner_text().strip()
                    if not text:
                        continue

                    # Skip Nia's own sent replies
                    if text in self._sent_replies:
                        continue

                    print(f"[WhatsApp Remote Command Received]: '{text}'")
                    try:
                        from sound_effects import SoundEffects
                        SoundEffects.whatsapp_received()
                    except Exception:
                        pass
                    
                    self.command_received.emit(text)
                except Exception:
                    continue
        except Exception as e:
            pass

    def _do_send_chat_reply(self, page, text: str):
        """Types and sends reply directly in the currently active chat."""
        try:
            box = page.locator("div[contenteditable='true'][data-tab='10'], footer div[contenteditable='true']").first
            if box.is_visible(timeout=3000):
                box.click()
                box.fill(text)
                time.sleep(0.2)
                page.keyboard.press("Enter")
                time.sleep(0.5)
                print(f"[WhatsAppManager] Sent reply: '{text[:40]}...'")
        except Exception as e:
            print(f"[WhatsApp Send Reply Error]: {e}")

    def _do_send_message(self, page, phone: str, message: str) -> tuple[bool, str]:
        clean_number = "".join(filter(str.isdigit, phone))
        url = f"https://web.whatsapp.com/send?phone={clean_number}&text={urllib.parse.quote(message)}"
        try:
            page.goto(url, timeout=30000)
            time.sleep(2.5)
            send_btn = page.locator("button[aria-label='Send'], span[data-icon='send'], div[contenteditable='true'][data-tab='10']").first
            send_btn.wait_for(timeout=15000)
            
            box = page.locator("div[contenteditable='true'][data-tab='10']").first
            if box.is_visible():
                box.click()
                page.keyboard.press("Enter")
                time.sleep(1)
                return True, f"Message sent successfully to {phone}!"
            else:
                send_btn.click()
                time.sleep(1)
                return True, f"Message sent successfully to {phone}!"
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"

    # Public thread-safe API
    def send_chat_reply(self, reply_text: str):
        self._command_queue.put(("chat_reply", reply_text))

    def refresh(self):
        self._command_queue.put(("refresh", None))

    def check_state(self):
        self._command_queue.put(("check_state", None))

    def send_message(self, phone: str, text: str):
        self._command_queue.put(("send_message", (phone, text)))

    def stop(self):
        self._running = False
        self._command_queue.put(("stop", None))
        self.wait(3000)
