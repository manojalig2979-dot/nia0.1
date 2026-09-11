from pathlib import Path

from system_diagnostics import SystemDiagnostics


def test_diagnostics_reports_sensitive_status_and_sanitizes_logs(tmp_path):
    config = {
        "api_keys": {"gemini_api_key": "test-secret-key"},
        "llm_settings": {"model": "gemini/gemini-3.6-flash"},
        "voice_settings": {"tts_voice": "hi-IN-SwaraNeural"},
    }
    diagnostics = SystemDiagnostics(config, log_dir=str(tmp_path))

    status = diagnostics.get_status()
    assert status["ai_provider"] == "gemini"
    assert status["api_key_present"] is True
    assert status["ai_model"] == "gemini/gemini-3.6-flash"
    assert isinstance(status["microphone_available"], bool)

    log_path = diagnostics.write_startup_log()
    log_text = Path(log_path).read_text(encoding="utf-8")
    assert "test-secret-key" not in log_text
    assert "gemini" in log_text.lower()
    assert "ai model" in log_text.lower() or "llm" in log_text.lower()


def test_diagnostics_handles_missing_api_key_gracefully(tmp_path):
    diagnostics = SystemDiagnostics({"api_keys": {}, "llm_settings": {"model": "gemini/gemini-3.6-flash"}}, log_dir=str(tmp_path))
    status = diagnostics.get_status()

    assert status["api_key_present"] is False
    assert status["warning"]
