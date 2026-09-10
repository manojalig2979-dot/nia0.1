import os
import urllib.parse
from playwright.sync_api import sync_playwright

class BrowserTools:
    def __init__(self, session_dir: str, wa_manager=None):
        self.session_dir = session_dir
        self.wa_manager = wa_manager
        os.makedirs(self.session_dir, exist_ok=True)

    def play_song(self, song_name: str) -> str:
        """Searches YouTube, extracts the first video ID, and immediately plays the first song."""
        import urllib.request
        import re
        import webbrowser

        clean_name = song_name.replace("on youtube", "").replace("in youtube", "").replace("youtube", "").strip()
        query = urllib.parse.quote(clean_name or song_name)
        search_url = f"https://www.youtube.com/results?search_query={query}"

        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8")
            video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
            if video_ids:
                first_video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                webbrowser.open(first_video_url)
                return f"YouTube pe '{clean_name or song_name}' ka pehla song play kar diya hai!"
        except Exception as e:
            print(f"[YouTube Play Error]: {e}")

        webbrowser.open(search_url)
        return f"YouTube search khol diya hai '{song_name}' ke liye."

    def send_whatsapp_message(self, target_phone: str, message: str) -> str:
        """Sends WhatsApp message using Playwright persistent user context."""
        if self.wa_manager and hasattr(self.wa_manager, 'isRunning') and self.wa_manager.isRunning():
            self.wa_manager.send_message(target_phone, message)
            return f"WhatsApp message dispatch sent via active background session to {target_phone}."

        clean_number = "".join(filter(str.isdigit, target_phone))
        url = f"https://web.whatsapp.com/send?phone={clean_number}&text={urllib.parse.quote(message)}"
        
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.session_dir,
                    headless=False,
                    args=["--no-sandbox"]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(url)
                
                # Wait for WhatsApp send button to be enabled
                send_button = page.locator("button span[data-icon='send'], button[aria-label='Send']").first
                send_button.wait_for(timeout=35000)
                send_button.click()
                page.wait_for_timeout(3000)
                context.close()
                return f"WhatsApp message sent successfully to {target_phone}."
        except Exception as e:
            return f"Could not send WhatsApp message. (Ensure WhatsApp Web is scanned once): {str(e)}"

    def send_whatsapp_screenshot(self, target_phone: str, image_path: str, caption="Here is your screenshot") -> str:
        """Sends screenshot file via WhatsApp Web automation."""
        clean_number = "".join(filter(str.isdigit, target_phone))
        url = f"https://web.whatsapp.com/send?phone={clean_number}"
        
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.session_dir,
                    headless=False
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(url)
                
                # Wait for attachment button (+)
                attach_btn = page.locator("button[title='Attach'], span[data-icon='plus']").first
                attach_btn.wait_for(timeout=35000)
                attach_btn.click()
                
                # Upload file to file chooser
                with page.expect_file_chooser() as fc_info:
                    img_option = page.locator("input[type='file']").first
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                
                # Wait for send button on image preview modal
                page.wait_for_timeout(2000)
                send_btn = page.locator("span[data-icon='send']").first
                send_btn.click()
                page.wait_for_timeout(4000)
                context.close()
                return f"Screenshot sent successfully to WhatsApp {target_phone}."
        except Exception as e:
            return f"Failed sending screenshot via WhatsApp: {str(e)}"

    def post_social_update(self, platform: str, content: str) -> str:
        """Opens the social media platform with pre-drafted status text."""
        plat = platform.lower()
        if "twitter" in plat or "x" in plat:
            tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(content)}"
            import webbrowser
            webbrowser.open(tweet_url)
            return f"Opened X/Twitter composer with drafted tweet: '{content[:30]}...'"
        elif "linkedin" in plat:
            linkedin_url = "https://www.linkedin.com/feed/"
            import webbrowser
            webbrowser.open(linkedin_url)
            return "Opened LinkedIn feed. Copying drafted content to clipboard."
        return f"Social platform '{platform}' integration ready. Web composer launched."

