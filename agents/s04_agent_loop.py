import os
from anthropic import Anthropic
from dotenv import load_dotenv

from tools import TOOL_HANDLERS, CHILD_TOOLS, PARENT_TOOLS, WORKDIR, TOOL_HANDLERS
from skills import SKILL_LOADER

load_dotenv(override=True)

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BASE_URL")
)

MODEL = "glm-4.7"

SYSTEM = f"""You are a coding agent at {WORKDIR}. Skills available:{SKILL_LOADER.get_descriptions()}"""

SUBAGENT_SYSTEM = f"You are a coding subagent at {WORKDIR}. Complete the given task, then summarize your findings."

# -- The core pattern: a while loop that calls tools until the model stops --
def agent_loop(messages: list):
    rounds_since_todo = 0
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=PARENT_TOOLS, max_tokens=8000,
        )
        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})
        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            return
        # Execute each tool call, collect results
        results = []
        used_todo = False
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "task":
                    desc = block.input.get("description", "subtask")
                    print(f"> task ({desc}): {block.input['prompt'][:80]}")
                    output = run_subagent(block.input["prompt"])
                else:
                    handler = TOOL_HANDLERS.get(block.name)
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                print(f"  {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})

def run_subagent(prompt: str) -> str:
    sub_message = [{"role": "user", "content": prompt}]
    for _ in range(30):
        response  = client.messages.create(
            model=MODEL, system=SUBAGENT_SYSTEM, messages=sub_message,
            tools=CHILD_TOOLS, max_tokens=8000,
        )
        sub_message.append(({"role": "assistant", "content": response.content}))

        if response.stop_reason != "tool_use":
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                hander = TOOL_HANDLERS.get(block.name)
                output = hander(**block.input)
                results.append({
                    "type": "tool_result", 
                    "tool_use_id": block.id, 
                    "content": str(output)
                    })
        sub_message.append({"role": "user", "content": results})
    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"
    
if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()