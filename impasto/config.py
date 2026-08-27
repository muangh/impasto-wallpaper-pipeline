"""Credential and settings resolution.

Keys are read from the environment, falling back to a .env file in the project
root. Nothing is ever written to a tracked file — .env is gitignored.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

# Verified working image-to-image path for the Higgsfield SDK. Override with
# IMPASTO_MODEL if you have access to a different repaint model.
DEFAULT_MODEL = "bytedance/seedream/v4/image-to-image"


def load_env_file(path=ENV_FILE):
    """Read KEY=VALUE lines from .env into os.environ without overwriting."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def save_env_file(values, path=ENV_FILE):
    """Merge values into .env, preserving anything already there."""
    existing = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update({k: v for k, v in values.items() if v})
    body = "\n".join(f"{k}={v}" for k, v in sorted(existing.items()))
    path.write_text(body + "\n")
    path.chmod(0o600)


class Keys:
    """Resolved credentials. `higgsfield` is required; `anthropic` is optional."""

    def __init__(self):
        load_env_file()
        self.hf_key = os.environ.get("HF_API_KEY", "")
        self.hf_secret = os.environ.get("HF_API_SECRET", "")
        self.anthropic = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def has_higgsfield(self):
        return bool(self.hf_key and self.hf_secret)

    @property
    def has_anthropic(self):
        return bool(self.anthropic)

    def export(self):
        """Push credentials into os.environ for the SDKs to pick up."""
        if self.has_higgsfield:
            os.environ["HF_API_KEY"] = self.hf_key
            os.environ["HF_API_SECRET"] = self.hf_secret
            os.environ["HF_KEY"] = f"{self.hf_key}:{self.hf_secret}"
        if self.has_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = self.anthropic


def model_id():
    return os.environ.get("IMPASTO_MODEL", DEFAULT_MODEL)
