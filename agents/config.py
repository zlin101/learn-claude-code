import os
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

def _resolve_from_base(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (BASE_DIR / path).resolve()


WORKDIR = _resolve_from_base(os.getenv("WORKDIR", "."))
SKILLDIR = _resolve_from_base(os.getenv("SKILLDIR", "."))
MODEL = os.getenv("MODEL", "glm-4.7")

TEAM_DIR = WORKDIR / ".team"
INBOX_DIR = TEAM_DIR / "inbox"
TASKSDIR = WORKDIR / ".tasks"
TRANSCRIPT_DIR = WORKDIR / ".transcript"

THRESHOLD = 50000
KEEP_RECENT = 3

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BASE_URL")
)

VALID_MSG_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval_response",
}