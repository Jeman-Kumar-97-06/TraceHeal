# import time
# import json
# import chromadb
# from openai import OpenAI
# from opentelemetry import trace
# from .instrumentation import flush_telemetry

# tracer = trace.get_tracer("LocalAgent1")

# ALLOWED_TOOLS = ["read_file", "execute_command"]

# # Initialize ChromaDB Vector Store
# chroma_client = chromadb.Client()
# collection = chroma_client.get_or_create_collection("agent_kb")

# # Seed sample context if collection is empty
# if collection.count() == 0:
#     collection.add(
#         documents=[
#             "The system administration password policy requires 16 characters.",
#             "LocalAgent1 runs on a local Ollama instance using gemma2/llama3.2:3b.",
#             "Database maintenance is scheduled every Sunday at 02:00 UTC."
#         ],
#         ids=["doc1", "doc2", "doc3"]
#     )

# # OpenAI Client pointing to local Ollama instnce
# ollama_client = OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key="ollama"
# )

# # def check_prompt_security(user_input: str) -> tuple[bool, str]:
# #     """Scans for prompt injection signatures."""
# #     attack_keywords = [
# #         "ignore previous instructions", 
# #         "system prompt", 
# #         "override safety",
# #         "dan mode"
# #     ]
# #     for pattern in attack_keywords:
# #         if pattern in user_input.lower():
# #             return True, pattern
# #     return False, ""
# def get_runtime_config():
#     """Reads dynamic runtime patches written by LocalAgent2."""
#     try:
#         with open("data/memory.json", "r") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {
#             "blacklist": [],
#             "max_rag_chunks": 2,
#             "active_model": "llama3.2:3b",
#             "strict_grounding": False
#         }

# def check_prompt_security(user_input: str) -> tuple[bool, str]:
#     config = get_runtime_config()
    
#     # Baseline patterns + dynamic keywords appended by Agent 2 LLM
#     baseline_keywords = [
#         "ignore previous instructions", 
#         "system prompt", 
#         "override safety", 
#         "dan mode"
#     ]
#     all_keywords = list(set(baseline_keywords + config.get("blacklist", [])))
    
#     for pattern in all_keywords:
#         if pattern in user_input.lower():
#             return True, pattern
#     return False, ""

# def execute_tool(tool_name: str, args: dict) -> str:
#     """Executes agent tools wrapped in OpenTelemetry spans."""
#     config = get_runtime_config()
#     disabled_tools = config.get("disabled_tools", [])

#     with tracer.start_as_current_span("Agent Tool Execution") as tool_span:
#         tool_span.set_attribute("tool.name", tool_name)
#         tool_span.set_attribute("tool.args", str(args))

#         # Check if Sentinel disabled this tool
#         if tool_name in disabled_tools:
#             tool_span.set_attribute("tool.blocked", True)
#             tool_span.set_status(trace.StatusCode.ERROR, f"Tool '{tool_name}' disabled by Sentinel.")
#             return f"⚠️ Security Block: Tool '{tool_name}' has been disabled by Agent 2 Sentinel."

#         # Detect unsafe parameters (e.g., destructive shell commands)
#         if tool_name == "execute_command":
#             cmd = args.get("command", "")
#             unsafe_patterns = ["rm -rf", "sudo", "chmod", "drop table", "config/"]
#             if any(pattern in cmd.lower() for pattern in unsafe_patterns):
#                 tool_span.set_attribute("tool.violation", True)
#                 tool_span.set_attribute("tool.unsafe_command", cmd)
#                 tool_span.set_status(trace.StatusCode.ERROR, f"Unsafe command detected: {cmd}")
#                 return f"⚠️ Execution Blocked: Destructive or restricted command detected."

#         # Execute safe tool logic here...
#         tool_span.set_status(trace.StatusCode.OK)
#         return f"Successfully executed tool '{tool_name}' with args {args}"

# # def process_user_query(user_input: str) -> str:
# #     """Executes the full RAG pipeline with OTel instrumentation and Agent2 dynamic memory integration."""
    
# #     # 0. Load dynamic config patched by Agent 2
# #     config = get_runtime_config()
# #     active_model = config.get("active_model", "llama3.2")
# #     max_chunks = config.get("max_rag_chunks", 2)
# #     strict_mode = config.get("strict_grounding", False)

# #     with tracer.start_as_current_span("Agent Conversation Turn") as turn_span:
# #         turn_span.set_attribute("agent.user_input", user_input)
# #         turn_span.set_attribute("agent.active_model", active_model)

# #         # 1. Security Guardrail Check (Static + Dynamic Blacklist)
# #         with tracer.start_as_current_span("Prompt Security Check") as sec_span:
# #             is_attack, pattern = check_prompt_security(user_input)
# #             if is_attack:
# #                 sec_span.set_attribute("security.prompt_injection_detected", True)
# #                 sec_span.set_attribute("security.attack_pattern", pattern)
# #                 sec_span.set_status(trace.StatusCode.ERROR, f"Attack Detected: {pattern}")
                
# #                 turn_span.set_attribute("security.alert", True)
# #                 print(f"⚠️ [SECURITY ALERT]: Prompt Injection detected! Pattern: '{pattern}'")
# #                 return f"⚠️ Access Denied: Query contains blocked pattern '{pattern}'."

# #         # 2. ChromaDB RAG Vector Retrieval (Distance Filtered)
# #         with tracer.start_as_current_span("ChromaDB Vector Retrieval") as rag_span:
# #             start_time = time.time()
            
# #             # ADD include=["documents", "distances"] HERE:
# #             results = collection.query(
# #                 query_texts=[user_input], 
# #                 n_results=max_chunks,
# #                 include=["documents", "distances"]
# #             )
# #             retrieval_ms = (time.time() - start_time) * 1000
            
# #             raw_docs = results['documents'][0] if results.get('documents') else []
# #             distances = results['distances'][0] if results.get('distances') else []

# #             # Filter out irrelevant chunks (distances >= 1.0 mean poor match in Chroma)
# #             retrieved_docs = []
# #             if distances:
# #                 for doc, dist in zip(raw_docs, distances):
# #                     if dist < 1.0:  # Default L2 distance threshold for ChromaDB
# #                         retrieved_docs.append(doc)

# #             retrieved_count = len(retrieved_docs)
# #             rag_span.set_attribute("rag.retrieved_chunks", retrieved_count)
# #             rag_span.set_attribute("rag.retrieval_duration_ms", retrieval_ms)
# #             # 3. Strict Grounding Enforcement (Hard Short-Circuit)
# #         if strict_mode and retrieved_count == 0:
# #             turn_span.set_attribute("rag.grounding_blocked", True)
# #             return "⚠️ [Strict Grounding Active]: I cannot answer this query because no verified context was found in my reference library."

# #         # 4. Model Generation
# #         context_str = "\n".join(retrieved_docs) if retrieved_docs else "No relevant context found."
        
# #         system_prompt = "You are a helpful AI assistant."
# #         if strict_mode:
# #             system_prompt = "You are a strict QA bot. Answer strictly using ONLY the provided context. If context is missing, reply with 'Data unavailable'."

# #         prompt_payload = f"Context:\n{context_str}\n\nUser Question: {user_input}"
# #         turn_span.set_attribute("gen_ai.prompt_tokens_est", len(prompt_payload.split()))

# #         try:
# #             response = ollama_client.chat.completions.create(
# #                 model=active_model,
# #                 messages=[
# #                     {"role": "system", "content": system_prompt},
# #                     {"role": "user", "content": prompt_payload}
# #                 ]
# #             )
# #             reply = response.choices[0].message.content
# #             turn_span.set_attribute("gen_ai.completion_tokens_est", len(reply.split()))
# #             turn_span.set_status(trace.StatusCode.OK)
# #             return reply

# #         except Exception as e:
# #             turn_span.record_exception(e)
# #             turn_span.set_status(trace.StatusCode.ERROR, str(e))
# #             return f"Error executing query: {e}"

# #         finally:
# #             flush_telemetry()

# def process_user_query(user_input: str) -> str:
#     """Executes the full RAG pipeline with OTel instrumentation and Agent2 dynamic memory integration."""
    
#     # 0. Load dynamic config patched by Agent 2
#     config = get_runtime_config()
#     active_model = config.get("active_model", "llama3.2")
#     max_chunks = config.get("max_rag_chunks", 2)
#     strict_mode = config.get("strict_grounding", False)

#     with tracer.start_as_current_span("Agent Conversation Turn") as turn_span:
#         turn_span.set_attribute("agent.user_input", user_input)
#         turn_span.set_attribute("agent.active_model", active_model)

#         # 1. Security Guardrail Check (Static + Dynamic Blacklist)
#         with tracer.start_as_current_span("Prompt Security Check") as sec_span:
#             is_attack, pattern = check_prompt_security(user_input)
#             if is_attack:
#                 sec_span.set_attribute("security.prompt_injection_detected", True)
#                 sec_span.set_attribute("security.attack_pattern", pattern)
#                 sec_span.set_status(trace.StatusCode.ERROR, f"Attack Detected: {pattern}")
                
#                 turn_span.set_attribute("security.alert", True)
#                 print(f"⚠️ [SECURITY ALERT]: Prompt Injection detected! Pattern: '{pattern}'")
#                 return f"⚠️ Access Denied: Query contains blocked pattern '{pattern}'."

#         # 2. ChromaDB RAG Vector Retrieval (Distance Filtered)
#         with tracer.start_as_current_span("ChromaDB Vector Retrieval") as rag_span:
#             start_time = time.time()
#             results = collection.query(query_texts=[user_input], n_results=max_chunks)
#             retrieval_ms = (time.time() - start_time) * 1000
            
#             raw_docs = results['documents'][0] if results.get('documents') else []
#             distances = results['distances'][0] if results.get('distances') else []

#             # Filter out irrelevant chunks (distances >= 1.2 mean poor match)
#             retrieved_docs = []
#             if distances:
#                 for doc, dist in zip(raw_docs, distances):
#                     if dist < 1.2:
#                         retrieved_docs.append(doc)
#             else:
#                 retrieved_docs = raw_docs

#             retrieved_count = len(retrieved_docs)
#             rag_span.set_attribute("rag.retrieved_chunks", retrieved_count)
#             rag_span.set_attribute("rag.retrieval_duration_ms", retrieval_ms)

#         # 3. Strict Grounding Enforcement (Hard Short-Circuit)
#         if strict_mode and retrieved_count == 0:
#             turn_span.set_attribute("rag.grounding_blocked", True)
#             return "⚠️ [Strict Grounding Active]: I cannot answer this query because no verified context was found in my reference library."

#         # 4. Model Generation
#         context_str = "\n".join(retrieved_docs) if retrieved_docs else "No relevant context found."
        
#         system_prompt = "You are a helpful AI assistant."
#         if strict_mode:
#             system_prompt = "You are a strict QA bot. Answer strictly using ONLY the provided context. If context is missing, reply with 'Data unavailable'."

#         prompt_payload = f"Context:\n{context_str}\n\nUser Question: {user_input}"
#         turn_span.set_attribute("gen_ai.prompt_tokens_est", len(prompt_payload.split()))

#         try:
#             response = ollama_client.chat.completions.create(
#                 model=active_model,
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": prompt_payload}
#                 ]
#             )
#             reply = response.choices[0].message.content
#             turn_span.set_attribute("gen_ai.completion_tokens_est", len(reply.split()))
#             turn_span.set_status(trace.StatusCode.OK)
#             return reply

#         except Exception as e:
#             turn_span.record_exception(e)
#             turn_span.set_status(trace.StatusCode.ERROR, str(e))
#             return f"Error executing query: {e}"

#         finally:
#             flush_telemetry()

import time
import json
import chromadb
from openai import OpenAI
from opentelemetry import trace
from .instrumentation import flush_telemetry

tracer = trace.get_tracer("LocalAgent1")

ALLOWED_TOOLS = ["read_file", "execute_command"]

# Initialize ChromaDB Vector Store
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("agent_kb")

# Seed sample context if collection is empty
if collection.count() == 0:
    collection.add(
        documents=[
            "The system administration password policy requires 16 characters.",
            "LocalAgent1 runs on a local Ollama instance using gemma2/llama3.2:3b.",
            "Database maintenance is scheduled every Sunday at 02:00 UTC."
        ],
        ids=["doc1", "doc2", "doc3"]
    )

# OpenAI Client pointing to local Ollama instance
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def get_runtime_config():
    """Reads dynamic runtime patches written by LocalAgent2."""
    try:
        with open("data/memory.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "blacklist": [],
            "max_rag_chunks": 2,
            "active_model": "llama3.2:3b",
            "strict_grounding": False
        }

def check_prompt_security(user_input: str) -> tuple[bool, str]:
    config = get_runtime_config()
    
    # Baseline patterns + dynamic keywords appended by Agent 2 LLM
    baseline_keywords = [
        "ignore previous instructions", 
        "system prompt", 
        "override safety", 
        "dan mode"
    ]
    all_keywords = list(set(baseline_keywords + config.get("blacklist", [])))
    
    for pattern in all_keywords:
        if pattern in user_input.lower():
            return True, pattern
    return False, ""

def execute_tool(tool_name: str, args: dict) -> str:
    """Executes agent tools wrapped in OpenTelemetry spans."""
    config = get_runtime_config()
    disabled_tools = config.get("disabled_tools", [])

    with tracer.start_as_current_span("Agent Tool Execution") as tool_span:
        tool_span.set_attribute("tool.name", tool_name)
        tool_span.set_attribute("tool.args", str(args))

        # Check if Sentinel disabled this tool
        if tool_name in disabled_tools:
            tool_span.set_attribute("tool.blocked", True)
            tool_span.set_status(trace.StatusCode.ERROR, f"Tool '{tool_name}' disabled by Sentinel.")
            return f"⚠️ Security Block: Tool '{tool_name}' has been disabled by Agent 2 Sentinel."

        # Detect unsafe parameters (e.g., destructive shell commands)
        if tool_name == "execute_command":
            cmd = args.get("command", "")
            unsafe_patterns = ["rm -rf", "sudo", "chmod", "drop table", "config/"]
            if any(pattern in cmd.lower() for pattern in unsafe_patterns):
                tool_span.set_attribute("tool.violation", True)
                tool_span.set_attribute("tool.unsafe_command", cmd)
                tool_span.set_status(trace.StatusCode.ERROR, f"Unsafe command detected: {cmd}")
                return f"⚠️ Execution Blocked: Destructive or restricted command detected."

        # Execute safe tool logic here...
        tool_span.set_status(trace.StatusCode.OK)
        return f"Successfully executed tool '{tool_name}' with args {args}"

def process_user_query(user_input: str) -> str:
    """Executes the full RAG pipeline with OTel instrumentation and Agent2 dynamic memory integration."""
    
    # 0. Load dynamic config patched by Agent 2
    config = get_runtime_config()
    active_model = config.get("active_model", "llama3.2")
    max_chunks = config.get("max_rag_chunks", 2)
    strict_mode = config.get("strict_grounding", False)

    with tracer.start_as_current_span("Agent Conversation Turn") as turn_span:
        turn_span.set_attribute("agent.user_input", user_input)
        turn_span.set_attribute("agent.active_model", active_model)

        # 1. Security Guardrail Check (Static + Dynamic Blacklist)
        with tracer.start_as_current_span("Prompt Security Check") as sec_span:
            is_attack, pattern = check_prompt_security(user_input)
            if is_attack:
                sec_span.set_attribute("security.prompt_injection_detected", True)
                sec_span.set_attribute("security.attack_pattern", pattern)
                sec_span.set_status(trace.StatusCode.ERROR, f"Attack Detected: {pattern}")
                
                turn_span.set_attribute("security.alert", True)
                print(f"⚠️ [SECURITY ALERT]: Prompt Injection detected! Pattern: '{pattern}'")
                return f"⚠️ Access Denied: Query contains blocked pattern '{pattern}'."

        # 2. ChromaDB RAG Vector Retrieval (Distance Filtered)
        with tracer.start_as_current_span("ChromaDB Vector Retrieval") as rag_span:
            start_time = time.time()
            
            # Explicitly request distances from ChromaDB
            results = collection.query(
                query_texts=[user_input], 
                n_results=max_chunks,
                include=["documents", "distances"]
            )
            retrieval_ms = (time.time() - start_time) * 1000
            
            raw_docs = results['documents'][0] if results.get('documents') else []
            distances = results['distances'][0] if results.get('distances') else []

            # Filter out irrelevant chunks (distances >= 1.0 mean poor match in Chroma)
            retrieved_docs = []
            if distances:
                for doc, dist in zip(raw_docs, distances):
                    if dist < 1.0:
                        retrieved_docs.append(doc)
            else:
                retrieved_docs = raw_docs

            retrieved_count = len(retrieved_docs)
            rag_span.set_attribute("rag.retrieved_chunks", retrieved_count)
            rag_span.set_attribute("rag.retrieval_duration_ms", retrieval_ms)

        # 3. Strict Grounding Enforcement (Hard Short-Circuit)
        if strict_mode and retrieved_count == 0:
            turn_span.set_attribute("rag.grounding_blocked", True)
            return "⚠️ [Strict Grounding Active]: I cannot answer this query because no verified context was found in my reference library."

        # 4. Model Generation
        context_str = "\n".join(retrieved_docs) if retrieved_docs else "No relevant context found."
        
        system_prompt = "You are a helpful AI assistant."
        if strict_mode:
            system_prompt = "You are a strict QA bot. Answer strictly using ONLY the provided context. If context is missing, reply with 'Data unavailable'."

        prompt_payload = f"Context:\n{context_str}\n\nUser Question: {user_input}"
        turn_span.set_attribute("gen_ai.prompt_tokens_est", len(prompt_payload.split()))

        try:
            response = ollama_client.chat.completions.create(
                model=active_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_payload}
                ]
            )
            reply = response.choices[0].message.content
            turn_span.set_attribute("gen_ai.completion_tokens_est", len(reply.split()))
            turn_span.set_status(trace.StatusCode.OK)
            return reply

        except Exception as e:
            turn_span.record_exception(e)
            turn_span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error executing query: {e}"

        finally:
            flush_telemetry()