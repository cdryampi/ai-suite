"""
Application settings and configuration.

Configuration is loaded in this order (later overrides earlier):
1. default.yaml (committed defaults)
2. local.yaml (local overrides, gitignored)
3. Environment variables
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LLMSettings:
    """LLM provider settings."""

    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout: int = 120
    max_retries: int = 3
    api_key: Optional[str] = None


@dataclass
class OutputSettings:
    """Output and artifact settings."""

    base_path: str = "./outputs"
    max_size_mb: int = 100
    cleanup_after_days: int = 30


@dataclass
class JobSettings:
    """Job runner settings."""

    max_concurrent: int = 4
    default_timeout: int = 300
    log_retention_hours: int = 24


@dataclass
class Settings:
    """Application settings container."""

    env: str = "development"
    debug: bool = True

    llm: LLMSettings = field(default_factory=LLMSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
    job: JobSettings = field(default_factory=JobSettings)

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from a YAML file."""
        if not path.exists():
            return cls()

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "Settings":
        """Create Settings from a dictionary."""
        llm_data = data.get("llm", {})
        output_data = data.get("output", {})
        job_data = data.get("job", {})

        return cls(
            env=data.get("env", "development"),
            debug=data.get("debug", True),
            llm=LLMSettings(**llm_data),
            output=OutputSettings(**output_data),
            job=JobSettings(**job_data),
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings

    if _settings is None:
        config_dir = Path(__file__).parent
        _settings = Settings.from_yaml(config_dir / "default.yaml")

        local_path = config_dir / "local.yaml"
        if local_path.exists():
            local_settings = Settings.from_yaml(local_path)
            _settings = local_settings

    return _settings
