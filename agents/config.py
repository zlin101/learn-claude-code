import os
import subprocess
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):
        return False

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency
    Anthropic = None

load_dotenv(override=True)


class _MissingMessagesClient:
    def create(self, *args, **kwargs):
        raise RuntimeError(
            "anthropic package is not installed. Install it before running the agent."
        )


class MissingAnthropicClient:
    messages = _MissingMessagesClient()

BASE_DIR = Path(__file__).resolve().parent.parent


def detect_repo_root(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        root = Path(result.stdout.strip())
        return root if root.exists() else None
    except Exception:
        return None


def _resolve_from_base(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (BASE_DIR / path).resolve()


WORKDIR = _resolve_from_base(os.getenv("WORKDIR", "."))
REPO_ROOT = detect_repo_root(WORKDIR) or WORKDIR
SKILLDIR = _resolve_from_base(os.getenv("SKILLDIR", "."))
MODEL = os.getenv("MODEL", "glm-5-turbo")

TEAM_DIR = REPO_ROOT / ".team"
INBOX_DIR = TEAM_DIR / "inbox"
TASKS_DIR = REPO_ROOT / ".tasks"
TRANSCRIPT_DIR = REPO_ROOT / ".transcript"

THRESHOLD = 50000
KEEP_RECENT = 3
POLL_INTERVAL = 5
IDLE_TIMEOUT = 60

client = (
    Anthropic(
        api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )
    if Anthropic is not None
    else MissingAnthropicClient()
)

VALID_MSG_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval_response",
}
