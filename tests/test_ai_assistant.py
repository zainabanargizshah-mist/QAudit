"""Regression tests for safe AI configuration diagnostics."""

from pathlib import Path

import qshield.ai_assistant as ai_module
from qshield.ai_assistant import AIAssistant


def test_missing_env_file_has_actionable_configuration_message(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(ai_module, "ENV_FILE", tmp_path / ".env")

    assistant = AIAssistant()

    assert assistant.is_available() is False
    assert "Copy .env.example to .env" in assistant.configuration_message()
