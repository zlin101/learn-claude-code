from dotenv import load_dotenv

from tools import TOOL_HANDLERS, CHILD_TOOLS, PARENT_TOOLS, TOOL_HANDLERS
from skills import SKILL_LOADER
from config import MODEL, client, THRESHOLD, WORKDIR
from layout_message import LOGGER, log_message, start_logging, save_conversation
from context import micro_compact, estimate_tokens, auto_compact
from manager import BG

load_dotenv(override=True)

SYSTEM = f"You are a coding agent at {WORKDIR}. Use task tools to plan and track work.Skills available:{SKILL_LOADER.get_descriptions()}."

SUBAGENT_SYSTEM = f"You are a coding subagent at {WORKDIR}. Complete the given task, then summarize your findings."

# -- The core pattern: a while loop that calls tools until the model stops --
def agent_loop(messages: list):
    while True:
        # Drain background notifications and inject as system message before LLM call
        notifs = BG.drain_notifications()
        if notifs and messages:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs
            )
            messages.append({"role": "user", "content": f"<background-results>\n{notif_text}\n</background-results>"})
            messages.append({"role": "assistant", "content": "Noted background results."})

        # Layer 1: micro_compact before each LLM call;
        micro_compact(messages)
        # Layer 2: auto_compact if token estimate exceeds threshold
        if estimate_tokens(messages) > THRESHOLD:
            print("[auto_compact triggered]")
            messages[:] = auto_compact(messages)
        
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=PARENT_TOOLS, max_tokens=8000,
        )

        messages.append({"role": "assistant", "content": response.content})
        log_message("assistant", response.content, "model_response")

        if response.stop_reason != "tool_use":
            save_conversation(messages)
            return

        results = []
        manual_compact = False
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "compact":
                    manual_compact = True
                    output = "Compressing ... "
                else:
                    handler = TOOL_HANDLERS.get(block.name)
                    try:
                        output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                    except Exception as e:
                        output = f"Error: {e}"
                print(f"> {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})

        messages.append({"role": "user", "content": results})
        log_message("user", results, "tool_results")
         # Layer 3: manual compact triggered by the compact tool
        if manual_compact:
            print("[manual compacted]")
            messages[:] = auto_compact(messages)

if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms07 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break

        # 开始新的日志会话
        task_name = query[:30].replace(" ", "_").replace("/", "_")
        start_logging(task_name)

        history.append({"role": "user", "content": query})

        # 记录用户输入
        log_message("user", query, "user_input")

        agent_loop(history)

        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()

        # 输出日志保存位置
        log_path = LOGGER.get_session_path()
        print(f"\033[90m[日志保存到: {log_path}]\033[0m")
