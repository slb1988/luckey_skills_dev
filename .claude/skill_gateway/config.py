"""Configuration management for skill gateway."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Centralized configuration for skill gateway."""

    # Backend API Configuration
    USE_BACKEND_API: bool = True  # 使用后端API而不是直接调用大模型
    BACKEND_DEV_URL: str = "http://127.0.0.1:5000"  # 开发环境后端URL
    BACKEND_PROD_URL: str = "http://127.0.0.1:5000"  # 生产环境后端URL (占位)
    BACKEND_ENVIRONMENT: str = "dev"  # dev | prod

    # Legacy MiniMax API Configuration (废弃，保留向后兼容)
    ANTHROPIC_API_KEY: str = ""  # 不再需要，后端处理
    ANTHROPIC_BASE_URL: str = "https://api.minimaxi.com/anthropic"
    CLAUDE_MODEL: str = "MiniMax-M2.1"
    TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 1024

    # Policy Configuration
    CONFIDENCE_THRESHOLD: float = 0.75

    # Directory Configuration
    PROJECT_DIR: Path = Path(__file__).parent.parent.parent
    SKILL_GATEWAY_DIR: Path = Path(__file__).parent
    SKILLS_DIR: Path = PROJECT_DIR / ".claude" / "skills"
    REGISTRY_DIR: Path = SKILL_GATEWAY_DIR / "registry"
    AUDIT_DIR: Path = SKILL_GATEWAY_DIR / ".audit"

    @classmethod
    def get_backend_url(cls) -> str:
        """Get backend URL based on environment."""
        if cls.BACKEND_ENVIRONMENT == "prod":
            return cls.BACKEND_PROD_URL
        return cls.BACKEND_DEV_URL

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if cls.USE_BACKEND_API:
            backend_url = cls.get_backend_url()
            if not backend_url:
                errors.append("Backend URL not configured")
        else:
            # 只有在不使用后端API时才检查API Key
            if not cls.ANTHROPIC_API_KEY:
                errors.append("ANTHROPIC_API_KEY not configured")

        if not cls.SKILLS_DIR.exists():
            errors.append(f"Skills directory not found: {cls.SKILLS_DIR}")

        return errors

    @classmethod
    def get_skills_dir(cls) -> Path:
        """Return absolute path to skills directory."""
        return cls.SKILLS_DIR.resolve()

    @classmethod
    def get_registry_path(cls, filename: str) -> Path:
        """Return path to registry file."""
        return cls.REGISTRY_DIR / filename

    @classmethod
    def get_audit_dir(cls) -> Path:
        """Return audit directory path, create if not exists."""
        cls.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.AUDIT_DIR

    @classmethod
    def load_config(cls) -> dict:
        """Load configuration as dictionary."""
        return {
            "anthropic_api_key": cls.ANTHROPIC_API_KEY[:20] + "..." if cls.ANTHROPIC_API_KEY else None,
            "anthropic_base_url": cls.ANTHROPIC_BASE_URL,
            "claude_model": cls.CLAUDE_MODEL,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "confidence_threshold": cls.CONFIDENCE_THRESHOLD,
            "project_dir": str(cls.PROJECT_DIR),
            "skills_dir": str(cls.SKILLS_DIR),
            "registry_dir": str(cls.REGISTRY_DIR),
            "audit_dir": str(cls.AUDIT_DIR),
        }
