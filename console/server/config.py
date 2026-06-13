"""Console configuration — single source of truth for paths and ports."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = PROJECT_ROOT / "base"
CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
SKILL_DIR = BASE_DIR / "skills" / "dnd"

HOST = "127.0.0.1"
PORT = 8765
