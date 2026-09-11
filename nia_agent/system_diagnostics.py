import json
import os
from pathlib import Path


class SystemDiagnostics:
    """Collects a small, redacted diagnostics report for the NIA runtime."""

    def __init__(self, config: dict | None = None, log_dir: str | None = None):
        self.config = config or {}
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), "logs")

    @staticmethod
    def _normalize_model(model_name: str | None) -> str:
        if not model_name:
            return "gemini/gemini-3.6-flash"
        model_name = str(model_name).strip()
        return model_name or "gemini/gemini-3.6-flash"

    @staticmethod
    def _detect_provider(model_name: str) -> str:
        name = (model_name or "").lower()
        if "gemini" in name:
            return "gemini"
        if "openai" in name or "gpt" in name:
            return "openai"
        if "ollama" in name or "llama" in name or "mistral" in name:
            return "ollama"
        return "unknown"

    @staticmethod
    def _redact_value(value):
        if value is None:
            return "[missing]"
        text = str(value).strip()
        if not text:
            return "[missing]"
        if len(text) <= 6:
            return "[redacted]"
        return "[redacted]"

    def _get_model(self) -> str:
        return self._normalize_model(
            self.config.get("llm_settings", {}).get("model")
        )

    def _get_api_key_state(self, provider: str) -> tuple[bool, str | None]:
        api_keys = self.config.get("api_keys", {}) or {}
        if provider == "gemini":
            key = api_keys.get("gemini_api_key")
            return bool(key and str(key).strip()), key
        if provider == "openai":
            key = api_keys.get("openai_api_key")
            return bool(key and str(key).strip()), key
        if provider == "ollama":
            return True, None
        return False, None

    def _microphone_status(self) -> bool:
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            if not devices:
                return False
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        model_name = self._get_model()
        provider = self._detect_provider(model_name)
        api_key_present, api_key_value = self._get_api_key_state(provider)
        microphone_available = self._microphone_status()

        warning = ""
        if provider in {"gemini", "openai"} and not api_key_present:
            warning = (
                f"{provider.title()} API key is missing. Add it in Settings before using the AI provider."
            )

        return {
            "ai_provider": provider,
            "ai_model": model_name,
            "api_key_present": api_key_present,
            "microphone_available": microphone_available,
            "warning": warning,
            "api_key_preview": self._redact_value(api_key_value),
        }

    def format_status_message(self) -> str:
        status = self.get_status()
        provider = status["ai_provider"]
        model = status["ai_model"]
        mic = "available" if status["microphone_available"] else "unavailable"
        key = "ready" if status["api_key_present"] else "missing"
        if status["warning"]:
            return (
                f"AI status: {provider} / {model} | API key: {key} | Microphone: {mic}. "
                f"Warning: {status['warning']}"
            )
        return f"AI status: {provider} / {model} | API key: {key} | Microphone: {mic}."

    def get_status_summary(self) -> str:
        return self.format_status_message()

    def write_startup_log(self) -> str:
        status = self.get_status()
        log_dir = Path(self.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "nia_startup_diagnostics.txt"

        safe_lines = [
            "NIA startup diagnostics",
            "======================",
            f"AI provider: {status['ai_provider']}",
            f"AI model: {status['ai_model']}",
            f"API key present: {'yes' if status['api_key_present'] else 'no'}",
            f"Microphone available: {'yes' if status['microphone_available'] else 'no'}",
            f"Warning: {status['warning'] or 'none'}",
            "",
            "Secret scan:",
            "- API keys are redacted before writing to this log.",
            "- System configuration values are sanitized to avoid leaking credentials.",
        ]
        log_path.write_text("\n".join(safe_lines) + "\n", encoding="utf-8")
        return str(log_path)

    def __str__(self) -> str:
        return json.dumps(self.get_status(), indent=2, sort_keys=True)
