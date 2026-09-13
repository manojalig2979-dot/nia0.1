import json
import os
import sys
import getpass

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    """Loads config if present, else prompts user interactively to setup."""
    if not os.path.exists(CONFIG_PATH):
        return run_first_time_setup()
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            api_keys = config.setdefault("api_keys", {})
            # Prefer key saved in config.json; fall back to ENV if empty
            if not api_keys.get("gemini_api_key"):
                api_keys["gemini_api_key"] = os.getenv("NIA_GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
            if not api_keys.get("openai_api_key"):
                api_keys["openai_api_key"] = os.getenv("NIA_OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
            # Keep os.environ in sync with the active key
            if api_keys.get("gemini_api_key"):
                os.environ["GEMINI_API_KEY"] = api_keys["gemini_api_key"]
                os.environ["NIA_GEMINI_API_KEY"] = api_keys["gemini_api_key"]

            # Hardware-locked license check
            try:
                from license_guard import check_license_status, get_machine_fingerprint
                lic_key = config.get("license_key") or os.getenv("NIA_LICENSE_KEY", "")
                config["license_info"] = check_license_status(license_key=lic_key)
            except Exception as e:
                lic_key = config.get("license_key") or os.getenv("NIA_LICENSE_KEY", "")
                if lic_key:
                    config["license_info"] = {"status": "licensed", "days_remaining": 7, "message": str(e)}
                else:
                    config["license_info"] = {"status": "key_required", "days_remaining": 0, "message": "License key required."}

            return config
        except Exception:
            print("[Nia Config] Corrupted config.json found. Rerunning setup.")
            return run_first_time_setup()

def run_first_time_setup():
    """First-time dynamic configuration setup wizard."""
    print("=" * 65)
    print("        WELCOME TO NIA (NEURAL INTELLIGENT AGENT) SETUP")
    print("=" * 65)
    print("Please provide the required settings to personalize Nia for you.\n")
    
    user_name = input("Enter your full name (e.g., Manoj): ").strip() or "User"
    license_key = input("Enter your Nia License Key (₹99 Test Flight / Pro / Lifetime): ").strip()
    whatsapp_number = input("Enter your registered WhatsApp number with country code (e.g., +919876543210): ").strip()
    openai_key = input("Enter your OpenAI/LiteLLM API Key (or press enter if using ENV): ").strip()
    projects_dir = input("Enter default Projects Directory (e.g., C:/Projects or D:/WebDev): ").strip()
    
    config = {
        "license_key": license_key,
        "user_profile": {
            "name": user_name,
            "whatsapp_number": whatsapp_number,
            "language_mode": "hinglish",
            "wake_word": "nia"
        },
        "system_paths": {
            "projects_dir": projects_dir if projects_dir else os.path.expanduser("~/Documents/Projects"),
            "whatsapp_session_dir": os.path.join(os.path.dirname(__file__), "nia_browser_profile")
        },
        "api_keys": {
            "openai_api_key": openai_key
        },
        "voice_settings": {
            "tts_voice": "hi-IN-SwaraNeural",
            "whisper_model_size": "base"
        }
    }
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        
    print(f"\n[+] Configuration saved successfully to: {CONFIG_PATH}\n")
    return config

def update_config_field(section, field, value):
    config = load_config()
    if section in config:
        config[section][field] = value
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

