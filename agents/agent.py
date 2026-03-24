import json

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):
        return False

try:
    from .context import auto_compact, estimate_tokens, micro_compact
    from .layout_message import LOGGER, log_message, save_conversation, start_logging
    from .message import BUS
    from .manager import BG
    from .config import MODEL, THRESHOLD, WORKDIR, client
    from .skills import SKILL_LOADER
    from .tools import CHILD_TOOLS, PARENT_TOOLS, TOOL_HANDLERS
except ImportError:  # pragma: no cover - script execution fallback
    from context import auto_compact, estimate_tokens, micro_compact
    from layout_message import LOGGER, log_message, save_conversation, start_logging
    from message import BUS
    from manager import BG
    from config import MODEL, THRESHOLD, WORKDIR, client
    from skills import SKILL_LOADER
    from tools import CHILD_TOOLS, PARENT_TOOLS, TOOL_HANDLERS

load_dotenv(override=True)

SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Use todo/task tools to plan work, worktree tools for risky or parallel changes, "
    "background jobs for long-running commands, and teammate tools for delegation. "
    "Check inbox messages when teammates report back. "
    f"Skills available:\n{SKILL_LOADER.get_descriptions()}"
)

SUBAGENT_SYSTEM = (
    f"You are a coding subagent at {WORKDIR}. "
    "Complete the assigned task using the available tools, then summarize the result clearly."
)


def _extract_text(content) -> str:
    parts = [block.text for block in content if hasattr(block, "text")]
    return "\n".join(part for part in parts if part).strip()


def _inject_inbox(messages: list) -> None:
    inbox = BUS.read_inbox("lead")
    if not inbox:
        return
    messages.append(
        {
            "role": "user",
            "content": f"<inbox>{json.dumps(inbox, indent=2)}</inbox>",
        }
    )
    messages.append({"role": "assistant", "content": "Noted inbox messages."})


def _inject_background_results(messages: list) -> None:
    notifications = BG.drain_notifications()
    if not notifications:
        return
    content = "\n".join(
        f"[bg:{item['task_id']}] {item['status']}: {item['result']}"
        for item in notifications
    )
    messages.append(
        {
            "role": "user",
            "content": f"<background-results>\n{content}\n</background-results>",
        }
    )
    messages.append({"role": "assistant", "content": "Noted background results."})


def _maybe_compact(messages: list) -> None:
    micro_compact(messages)
    if estimate_tokens(messages) > THRESHOLD:
        print("[auto_compact triggered]")
        messages[:] = auto_compact(messages)


def _execute_blocks(blocks, allow_subagent: bool) -> tuple[list, bool]:
    results = []
    manual_compact = False
    for block in blocks:
        if block.type != "tool_use":
            continue
        if block.name == "compact":
            manual_compact = True
            output = "Compressing ..."
        elif block.name == "task" and allow_subagent:
            description = block.input.get("description", "subtask")
            print(f"> task ({description}): {block.input['prompt'][:120]}")
            output = run_subagent(block.input["prompt"])
        else:
            handler = TOOL_HANDLERS.get(block.name)
            try:
                output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
            except Exception as e:
                output = f"Error: {e}"
        print(f"> {block.name}: {str(output)[:200]}")
        results.append(
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(output),
            }
        )
    return results, manual_compact


def run_subagent(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    final_response = None
    for _ in range(30):
        _maybe_compact(messages)
        response = client.messages.create(
            model=MODEL,
            system=SUBAGENT_SYSTEM,
            messages=messages,
            tools=CHILD_TOOLS,
            max_tokens=8000,
        )
        final_response = response
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results, manual_compact = _execute_blocks(response.content, allow_subagent=False)
        messages.append({"role": "user", "content": results})
        if manual_compact:
            print("[manual compacted]")
            messages[:] = auto_compact(messages)
    if final_response is None:
        return "(no summary)"
    return _extract_text(final_response.content) or "(no summary)"


def agent_loop(messages: list):
    while True:
        _inject_inbox(messages)
        _inject_background_results(messages)
        _maybe_compact(messages)

        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=PARENT_TOOLS,
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        log_message("assistant", response.content, "model_response")

        if response.stop_reason != "tool_use":
            save_conversation(messages)
            return

        results, manual_compact = _execute_blocks(response.content, allow_subagent=True)
        messages.append({"role": "user", "content": results})
        log_message("user", results, "tool_results")

        if manual_compact:
            print("[manual compacted]")
            messages[:] = auto_compact(messages)


def main():
    history = []
    while True:
        try:
            query = input("\033[36magent >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break

        if LOGGER.get_session_path() is None:
            task_name = query[:30].replace(" ", "_").replace("/", "_")
            start_logging(task_name)

        history.append({"role": "user", "content": query})
        log_message("user", query, "user_input")

        agent_loop(history)

        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()

        log_path = LOGGER.get_session_path()
        print(f"\033[90m[日志保存到: {log_path}]\033[0m")


if __name__ == "__main__":
    main()
