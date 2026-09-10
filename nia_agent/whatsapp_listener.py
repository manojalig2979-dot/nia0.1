"""
whatsapp_listener.py
──────────────────────────────────────────────────────────
Nia WhatsApp Web Listener — no Twilio, no ngrok needed!

HOW IT WORKS:
1. Opens WhatsApp Web in a Chromium browser window.
2. First run: shows QR code → scan it with your phone once.
   Session is saved so you never scan again.
3. Opens a chat named "Nia Commands" (you must create this
   saved contact / note-to-self chat on your phone first).
4. Polls every 3 seconds for new incoming messages.
5. Sends each new message to Nia's agent brain.
6. Types and sends the reply back in the same WhatsApp chat.
"""

import time
import os
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
from config_manager import load_config
from voice_engine import VoiceEngine
from agent_orchestrator import NiaAgentOrchestrator

# ── Configuration ───────────────────────────────────────
POLL_INTERVAL_SEC = 3
CHAT_NAME         = "Nia Commands"
# ────────────────────────────────────────────────────────


def speak_async(voice, text):
    """Speak in a background thread to avoid asyncio event loop conflict."""
    threading.Thread(target=voice.speak, args=(text,), daemon=True).start()


def _get_all_message_texts(page) -> list[str]:
    """
    Returns text of ALL visible message bubbles (incoming + outgoing).
    Works for self-chats (Note to Self) where all msgs are 'message-out'.
    """
    results = []
    try:
        rows = page.locator("div[data-id]").all()
        for row in rows:
            try:
                text_el = row.locator(
                    "span.selectable-text span, span[class*='selectable-text']"
                ).first
                text = text_el.inner_text(timeout=500).strip()
                if text:
                    results.append(text)
            except Exception:
                continue
    except Exception as e:
        print(f"[Debug] Error reading messages: {e}")
    return results


def _send_reply(page, text: str):
    """Types a reply into the WhatsApp message box and sends it."""
    try:
        box = page.locator("div[contenteditable='true'][data-tab='10']").first
        box.click()
        box.fill("")
        box.type(text, delay=20)
        page.keyboard.press("Enter")
        time.sleep(1)
    except Exception as e:
        print(f"[WhatsApp] Could not send reply: {e}")


def run_listener():
    config     = load_config()
    voice      = VoiceEngine(
        tts_voice    = config["voice_settings"]["tts_voice"],
        whisper_size = config["voice_settings"]["whisper_model_size"]
    )
    agent      = NiaAgentOrchestrator(config)
    session_dir = config["system_paths"]["whatsapp_session_dir"]
    user_name   = config["user_profile"]["name"]

    print("=" * 60)
    print("   NIA — WhatsApp Web Listener")
    print("=" * 60)
    print(f"[*] Session directory: {session_dir}")
    print(f"[*] Monitoring chat:   '{CHAT_NAME}'")
    print("[*] Starting browser… (QR scan needed only on first run)\n")

    with sync_playwright() as pw:
        # Persistent context keeps you logged in after first QR scan
        context = pw.chromium.launch_persistent_context(
            user_data_dir = session_dir,
            headless      = False,
            args          = ["--no-sandbox", "--start-maximized"],
            viewport      = None
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.whatsapp.com", timeout=60000)

        # ── Wait for WhatsApp to fully load ────────────────
        print("[*] Waiting for WhatsApp Web to load…")
        print("    👉 If this is your first time, scan the QR code with your phone!")
        try:
            # Wait until the search box is visible (means logged in)
            page.wait_for_selector(
                "div[data-tab='3'], div[aria-label='Search input textbox']",
                timeout=120000
            )
            print("[✓] WhatsApp Web loaded and logged in!\n")
        except PwTimeout:
            print("[!] Timed out waiting for WhatsApp. Please try again.")
            context.close()
            return

        # ── Open the target chat ───────────────────────────
        try:
            search = page.locator(
                "div[data-tab='3'], div[aria-label='Search input textbox']"
            ).first
            search.click()
            time.sleep(0.5)
            search.type(CHAT_NAME, delay=60)
            time.sleep(1.5)

            # Click the first result
            first_result = page.locator(
                f"span[title='{CHAT_NAME}'], span[dir='auto']"
            ).first
            first_result.wait_for(timeout=8000)
            first_result.click()
            time.sleep(1)
            print(f"[✓] Opened chat: '{CHAT_NAME}'")
        except PwTimeout:
            print(f"\n[!] Could not find chat '{CHAT_NAME}'.")
            print("    Please create a WhatsApp contact named exactly:")
            print(f"    ➜  {CHAT_NAME}")
            print("    You can use 'Note to Self' or any saved contact/group.")
            context.close()
            return

        # ── Greeting ───────────────────────────────────────
        greeting = f"Namaste {user_name} ji! Nia yahan hai. Apna command likhiye!"
        _send_reply(page, greeting)
        speak_async(voice, greeting)
        print(f"[Nia] {greeting}\n")

        # ── Polling loop ───────────────────────────────────
        # Seed the last known messages so we don't re-process old ones
        last_msgs = _get_all_message_texts(page)
        nia_replies = set()  # track what Nia sent so we skip it
        nia_replies.add(greeting)

        print(f"[*] Listening for messages every {POLL_INTERVAL_SEC}s. Press Ctrl+C to stop.")
        print(f"[*] Seeded with {len(last_msgs)} existing messages. Waiting for new ones...\n")

        try:
            while True:
                time.sleep(POLL_INTERVAL_SEC)
                current_msgs = _get_all_message_texts(page)

                if len(current_msgs) > len(last_msgs):
                    # New message(s) arrived
                    new_msgs = current_msgs[len(last_msgs):]
                    last_msgs = current_msgs

                    for new_text in new_msgs:
                        # Skip Nia's own replies to avoid echo loop
                        if new_text in nia_replies:
                            print(f"[Skip] Nia's own reply: '{new_text[:40]}'")
                            continue

                        print(f"\n[You → Nia]: {new_text}")
                        reply = agent.process_command(new_text)
                        print(f"[Nia → You]: {reply}")

                        nia_replies.add(reply)
                        _send_reply(page, reply)
                        speak_async(voice, reply)
                else:
                    print(f"[Waiting] {len(current_msgs)} msgs total, no new ones.")

        except KeyboardInterrupt:
            print("\n[*] Nia WhatsApp listener stopped.")
            bye = "Alvida! Nia band ho rahi hai. Phir milenge!"
            _send_reply(page, bye)
            context.close()


if __name__ == "__main__":
    run_listener()

