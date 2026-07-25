### Prerequisites
* Docker installed and running
* Python 3.10+
* Ollama running locally (`ollama run llama3.2`)
* ollama pull llama3.2
* ollama pull qwen2.5:0.5b

### 1. Spin up SigNoz Telemetry Stack
Run the setup script to install `foundryctl` and deploy SigNoz via Foundry:

# Autonomous LLM Sentinel & Self-Healing Telemetry Stack

> **A dual-agent observability and active defense architecture powered by OpenTelemetry, SigNoz, and local SLMs.**

---

## Overview

Large Language Model (LLM) agents operating in production face unique operational challenges: **prompt injections, uncontrolled context/token bloat, latency degradation, and hallucination loops**. Traditional static guardrails inside the target application can easily be bypassed or corrupted if the target agent's context is compromised.

This project introduces a **Self-Healing Observability Loop** using two decoupled local agents:

* **`LocalAgent1` (The Monitored Worker):** Interfaces with users, processes vector context via ChromaDB, and executes user prompts using `llama3.2`. It emits real-time OpenTelemetry (OTel) spans for every decision turn.
* **`LocalAgent2` (The Autonomous Sentinel):** Runs out-of-band, continuously querying the local **SigNoz** trace store. When anomaly or attack telemetry is detected, `LocalAgent2` uses an ultra-fast local reasoning engine (`qwen2.5:0.5b`) to synthesize an immediate security patch and dynamically reconfigures `LocalAgent1`'s runtime state (`data/memory.json`).

---

## System Architecture

```text
                           ┌───────────────────────────────────────────────┐
                           │               USER INTERFACE                  │
                           └───────────────────────┬───────────────────────┘
                                                   │
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             LOCALAGENT1                                                │
│                                                                                                        │
│   ┌────────────────────────┐       ┌───────────────────────┐       ┌───────────────────────────────┐   │
│   │  Runtime Config Hook   │ ◄───  │ Prompt Security Check │  ───► │ ChromaDB Vector Retrieval     │   │
│   │   (data/memory.json)   │       │ (Static + Dynamic)    │       │ (Dynamic Context Limit)       │   │
│   └────────────────────────┘       └───────────────────────┘       └───────────────┬───────────────┘   │
│                                                                                    │                   │
│                                                                                    ▼                   │
│                                                                    ┌───────────────────────────────┐   │
│                                                                    │ Ollama Generation (llama3.2)  │   │
│                                                                    └───────────────┬───────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                                     │
                                           Emits OpenTelemetry Traces                │ OTLP HTTP (Port 4318)
                                                                                     ▼
                                                            ┌────────────────────────────────────────────┐
                                                            │           SIGNOZ TELEMETRY STACK           │
                                                            │   (ClickHouse / OTLP Collector / UI)     │
                                                            └───────────────┬────────────────────────────┘
                                                                                     │
                                           Queries Span Telemetry                    │ Query API (Port 8080)
                                                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             LOCALAGENT2                                                │
│                                                                                                        │
│   ┌────────────────────────┐       ┌───────────────────────┐       ┌───────────────────────────────┐   │
│   │ Telemetry Span Parser  │  ───► │  Sentinel Reasoning   │  ───► │  Dynamic Memory Patching      │   │
│   │ (Latency/Security/RAG) │       │     (qwen2.5:0.5b)    │       │ (Writes to data/memory.json) │   │
│   └────────────────────────┘       └───────────────────────┘       └───────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘

## File Structure:
signoz-agent-monitor/
├── casting.yaml                    # SigNoz deployment spec (foundryctl)
├── setup.sh                        # Automated setup script
├── data/
│   └── memory.json                 # Shared runtime dynamic state
├── local_agent_1/                  # Target Agent
│   └── src/
│       ├── agent_logic.py          # RAG pipeline + OTel instrumentation
│       ├── instrumentation.py      # OpenTelemetry provider initialization
│       └── main.py                 # Interactive shell interface
├── local_agent_2/                  # Sentinel Watchdog Agent
│   └── src/
│       ├── signoz_client.py        # SigNoz Query API integration
│       ├── detectors/              # Metric analysis modules
│       └── main.py                 # Sentinel loop & LLM reasoner
├── test_run.py                     # E2E demonstration script
└── requirements.txt                # Python dependencies

## Setup

```bash
chmod +x setup.sh && ./setup.sh

## Demo : 
python3 test_run.py