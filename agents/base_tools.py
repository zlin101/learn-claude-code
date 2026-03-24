import subprocess
import uuid
import json
import threading
from pathlib import Path

try:
    from .message import BUS
    from .config import WORKDIR, TASKS_DIR
except ImportError:  # pragma: no cover - script execution fallback
    from message import BUS
    from config import WORKDIR, TASKS_DIR

__all__ = [
    "check_shutdown_status",
    "claim_task",
    "handle_plan_review",
    "handle_shutdown_request",
    "make_identity_block",
    "respond_to_shutdown_request",
    "run_bash",
    "run_edit",
    "run_read",
    "run_write",
    "scan_unclaimed_tasks",
    "submit_plan_for_approval",
]

def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        cwd = safe_path(".")
        r = subprocess.run(command, shell=True, cwd=cwd,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    
def run_read(path: str, limit: int = None) -> str:
    try:
        text = safe_path(path).read_text()
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Written to {path}"
    except Exception as e:
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        path_obj = safe_path(path)
        text = path_obj.read_text()
        if old_text not in text:
            return f"Error: '{old_text}' not found in {path}"
        new_content = text.replace(old_text, new_text, 1)
        path_obj.write_text(new_content)
        return f"Replaced in {path}"
    except Exception as e:
        return f"Error: {e}"

# -- Request trackers: correlate by request_id --
shutdown_requests = {}
plan_requests = {}
_tracker_lock = threading.Lock()

# -- Request trackers --
_claim_lock = threading.Lock()

# -- Task board scanning --
def scan_unclaimed_tasks() -> list:
    TASKS_DIR.mkdir(exist_ok=True)
    unclaimed = []
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        task = json.loads(f.read_text())
        if (task.get("status") == "pending"
                and not task.get("owner")
                and not task.get("blockedBy")):
            unclaimed.append(task)
    return unclaimed
def claim_task(task_id: int, owner: str) -> str:
    with _claim_lock:
        path = TASKS_DIR / f"task_{task_id}.json"
        if not path.exists():
            return f"Error: Task {task_id} not found"
        task = json.loads(path.read_text())
        task["owner"] = owner
        task["status"] = "in_progress"
        path.write_text(json.dumps(task, indent=2))
    return f"Claimed task #{task_id} for {owner}"

# -- Identity re-injection after compression --
def make_identity_block(name: str, role: str, team_name: str) -> dict:
    return {
        "role": "user",
        "content": f"<identity>You are '{name}', role: {role}, team: {team_name}. Continue your work.</identity>",
    }

# -- Lead-specific protocol handlers --
def handle_shutdown_request(teammate: str) -> str:
    req_id = str(uuid.uuid4())[:8]
    with _tracker_lock:
        shutdown_requests[req_id] = {"target": teammate, "status": "pending"}
    BUS.send(
        "lead", teammate, "Please shut down gracefully.",
        "shutdown_request", {"request_id": req_id},
    )
    return f"Shutdown request {req_id} sent to '{teammate}' (status: pending)"

def handle_plan_review(request_id: str, approve: bool, feedback: str = "") -> str:
    with _tracker_lock:
        req = plan_requests.get(request_id)
    if not req:
        return f"Error: Unknown plan request_id '{request_id}'"
    with _tracker_lock:
        req["status"] = "approved" if approve else "rejected"
    BUS.send(
        "lead", req["from"], feedback, "plan_approval_response",
        {"request_id": request_id, "approve": approve, "feedback": feedback},
    )
    return f"Plan {req['status']} for '{req['from']}'"

def check_shutdown_status(request_id: str) -> str:
    with _tracker_lock:
        return json.dumps(shutdown_requests.get(request_id, {"error": "not found"}))


def respond_to_shutdown_request(
    sender: str,
    request_id: str,
    approve: bool,
    reason: str = "",
) -> str:
    with _tracker_lock:
        if request_id in shutdown_requests:
            shutdown_requests[request_id]["status"] = (
                "approved" if approve else "rejected"
            )
    BUS.send(
        sender,
        "lead",
        reason,
        "shutdown_response",
        {"request_id": request_id, "approve": approve},
    )
    return f"Shutdown {'approved' if approve else 'rejected'}"


def submit_plan_for_approval(sender: str, plan_text: str) -> str:
    request_id = str(uuid.uuid4())[:8]
    with _tracker_lock:
        plan_requests[request_id] = {
            "from": sender,
            "plan": plan_text,
            "status": "pending",
        }
    BUS.send(
        sender,
        "lead",
        plan_text,
        "plan_approval_response",
        {"request_id": request_id, "plan": plan_text},
    )
    return f"Plan submitted (request_id={request_id}). Waiting for approval."
