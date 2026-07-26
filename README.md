#  Autonomous LLM Sentinel & Self-Healing Telemetry Stack

> **A dual-agent observability and active defense architecture powered by OpenTelemetry, SigNoz, and local SLMs.**

---

##  Overview

Large Language Model (LLM) agents operating in production face unique operational challenges: **prompt injections, uncontrolled context/token bloat, latency degradation, tool execution violations, and hallucination loops**. Traditional static guardrails inside the target application can easily be bypassed or corrupted if the target agent's context is compromised.

This project introduces a **Self-Healing Observability Loop** using two decoupled local agents:

* **`LocalAgent1` (The Monitored Worker):** Interfaces with users, processes vector context via ChromaDB, and executes user prompts using `llama3.2:3b`. It emits real-time OpenTelemetry (OTel) spans for every decision turn.
* **`LocalAgent2` (The Autonomous Sentinel):** Runs out-of-band, continuously querying the local **SigNoz** trace store. When anomaly or attack telemetry is detected, `LocalAgent2` uses an ultra-fast local reasoning engine (`qwen2.5:0.5b`) to synthesize an immediate security patch and dynamically reconfigures `LocalAgent1`'s runtime state (`data/memory.json`).

---
### Self Healing Actions : 
```text
-------------------------------------------------------------------------------------------
| Anomaly Category | Signoz Telemetry Condition | Sentinel Action   | Applied Memory Patch |
--------------------------------------------------------------------------------------------
| Prompt Injection | security.prompt_injection_ | Extract Attack    | data/memory.json     |
|                  | detected == True           | phrase & update   | -> blacklist         |
|                  |                            | dynamic blacklist |                      |
|-------------------------------------------------------------------------------------------
| Tool Execution   | tool.violation == True     | Block dangerous   | data/memory.json     |
| Violation        |                            | bash/sys call exec| -> disabled_tools    |
|-------------------------------------------------------------------------------------------
| Context Bloat    | gen_ai.prompt_tokens_est   |Truncate max vector| data/memory.json     |
|                  | > 300                      | retrival count    | -> max_rag_chunks:1  |
|-------------------------------------------------------------------------------------------
| High Latency     | duration_ms > 3000         | Downshift model to| data/momory/json     |
|                  |                            | to faster/smaller | -> active_model      |
|                  |                            | archietecture     |                      |
|-------------------------------------------------------------------------------------------
|Anti-Hallucination| rag.retrieved_chunks ==0   | Force strict      | data/memory.json     |
|                  |                            | context grounding | -> strict_grounding: |
|                  |                            | to prevent false  | True                 |
|                  |                            | facts             |                      |
--------------------------------------------------------------------------------------------
```
---
### Prerequisites
* Docker installed and running
* Python 3.10+
* Ollama running locally (`ollama run llama3.2`)
* `ollama pull llama3.2`
* `ollama pull qwen2.5:0.5b`


### 1. Spin up SigNoz Telemetry Stack
Run the setup script to install `foundryctl` and deploy SigNoz via Foundry:

## System Architecture

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              LOCALAGENT1                               │
 │                                                                        │
 │  ┌───────────────────────┐   ┌───────────────────┐  ┌───────────────┐ │
 │  │ Prompt Security Check │   │ RAG Retrieval     │  │ Tool Executor │ │
 │  │ (Static + Dynamic)    │   │ (ChromaDB)        │  │ (MCP Guards)  │ │
 │  └───────────────────────┘   └───────────────────┘  └───────────────┘ │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                             Emits OTel Spans (Port 4318)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                             SIGNOZ STACK                               │
 │                                                                        │
 │  ┌───────────────────────┐   ┌───────────────────┐  ┌───────────────┐ │
 │  │ Custom AI Dashboard   │   │ OTLP Trace Store  │  │ Alert Webhook │ │
 │  │ (Latency / Attacks)   │   │ (ClickHouse)      │  │ (Port 9090)   │ │
 │  └───────────────────────┘   └───────────────────┘  └───────┬───────┘ │
 └─────────────────────────────────────────────────────────────┼──────────┘
                                                               │ Triggers
                                                               ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                        LOCALAGENT2 (SENTINEL)                          │
 │                                                                        │
 │   Receives Webhook / Polls Telemetry  ──►  qwen2.5:0.5b Reasoning    │
 │   ──►  Disables Tools / Blacklists Phrases in data/memory.json         │
 └────────────────────────────────────────────────────────────────────────┘

```

## File Structure:
```text
signoz-agent-monitor/
├── casting.yaml                    # SigNoz deployment spec (foundryctl)
├── setup.sh                        # Automated setup script
├── signoz/
│   └── dashboard.json              # Importable SigNoz Custom AI Dashboard
├── data/
│   └── memory.json                 # Shared dynamic runtime state
├── local_agent_1/                  # Target Worker Agent
│   └── src/
│       ├── agent_logic.py          # RAG pipeline + tool execution + OTel
│       ├── instrumentation.py      # OpenTelemetry exporter setup
│       └── main.py                 # Interactive terminal shell
├── local_agent_2/                  # Sentinel Watchdog Agent
│   └── src/
│       ├── signoz_client.py        # SigNoz Trace Query API integration
│       ├── webhook_server.py       # FastAPI webhook receiver for automated alerts
│       ├── detectors/              # Metric analysis modules
│       └── main.py                 # Sentinel loop & LLM reasoner
├── test_run.py                     # E2E test suite
└── requirements.txt                # Python dependencies
```

## Setup

```bash

chmod +x setup.sh \&\& ./setup.sh


```
## Running the Project : 
```bash
cd TraceHeal/
```
Terminal 1 : 
```bash
python -m local_agent_1.src.main
```
Terminal 2 : 
```bash
python -m local_agent_2.src.main
```
Optional Test Script:
```bash
python3 test\_run.py
```
```


