import time
from .instrumentation import init_telemetry, flush_telemetry
from .agent_logic import process_user_query, get_runtime_config

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
            
            print(f"--- [Active Config | Model: {active_model} | Blacklist Rules: {len(blacklist)}] ---")
            user_input = input("You > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Shutting down LocalAgent1...")
                break

            # Execute query and emit OTel span to SigNoz
            response = process_user_query(user_input)
            print(f"\nAgent1 > {response}\n")

            # Force immediate flush of span to SigNoz OTLP receiver (4318)
            flush_telemetry()

    except KeyboardInterrupt:
        print("\nExiting LocalAgent1.")

if __name__ == "__main__":
    main()