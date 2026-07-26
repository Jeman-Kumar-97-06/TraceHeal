import time
from .instrumentation import init_telemetry, flush_telemetry
from .agent_logic import process_user_query, get_runtime_config,execute_tool

def main():
    # 1. Initialize OTel exporter
    init_telemetry("LocalAgent1")
    print("\n🤖 LocalAgent1 (Target Agent) Online.")
    print("Type your queries below. Type 'exit' or 'quit' to stop.\n")

    try:
        while True:
            # Show active dynamic configuration patched by Agent 2
            config = get_runtime_config()
            active_model = config.get("active_model", "llama3.2")
            blacklist = config.get("blacklist", [])
            disabled_tools = config.get("disabled_tools", [])
            strict_grounding = config.get("strict_grounding", False)

            # Updated header showing active defenses
            print(
                f"--- [Active Config | Model: {active_model} | "
                f"Blacklist Rules: {len(blacklist)} | "
                f"Disabled Tools: {len(disabled_tools)} | "
                f"Strict Grounding: {'ON' if strict_grounding else 'OFF'}] ---"
            )
            user_input = input("You > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Shutting down LocalAgent1...")
                break

            # 2. Route tool execution vs standard chat conversation
            if user_input.startswith("execute_command:"):
                cmd = user_input.replace("execute_command:", "").strip()
                # Route to execute_tool to trigger OTel span & MCP guardrails
                response = execute_tool("execute_command", {"command": cmd})

            elif user_input.startswith("tool:"):
                # Generic tool syntax parser: tool:<tool_name>:<args>
                parts = user_input.split(":", 2)
                tool_name = parts[1].strip() if len(parts) > 1 else "unknown"
                arg_val = parts[2].strip() if len(parts) > 2 else ""
                response = execute_tool(tool_name, {"arg": arg_val})

            else:
                # Standard conversation & RAG query path
                response = process_user_query(user_input)

            print(f"\nAgent1 > {response}\n")

            # Force immediate flush of span to SigNoz OTLP receiver (4318)
            flush_telemetry()

    except KeyboardInterrupt:
        print("\nExiting LocalAgent1.")

if __name__ == "__main__":
    main()