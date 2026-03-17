import subprocess
from openai import OpenAI

client = OpenAI(
    api_key="",
    base_url=""
)

def run_bash(command: str) -> str:
    """Execute bash command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)


class AgentLoop:
    """Agent loop with tool calling capability."""

    def __init__(self, query: str, model: str, system: str, tools: list):
        self.model = model
        self.system = system
        self.tools = tools
        self.messages = [{"role": "user", "content": query}]

    def loop(self):
        """Main agent loop that handles tool calls."""
        while True:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                max_tokens=8000,
            )
            self.messages.append({"role": "assistant", "content": response.choices[0].message.content})

            # Check if model wants to use tools
            message = response.choices[0].message
            if not message.tool_calls:
                return message.content

            # Execute tool calls
            results = []
            for tool_call in message.tool_calls:
                if tool_call.function.name == "run_bash":
                    import json
                    args = json.loads(tool_call.function.arguments)
                    output = run_bash(args.get("command", ""))
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "run_bash",
                        "content": output,
                    })
            self.messages.extend(results)

if __name__ == "__main__":
    query = "List all Python files in this directory"

    system_prompt = "You are a helpful assistant that can execute bash commands."

    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_bash",
                "description": "Execute a bash command in the terminal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            }
        }
    ]

    agent = AgentLoop(
        query=query,
        model="glm-4.7",
        system=system_prompt,
        tools=tools
    )

    result = agent.loop()
    print("最终回答:")
    print(result)
