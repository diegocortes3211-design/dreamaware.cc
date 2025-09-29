---
id: grok-integration
title: Grok LLM Integration
---

This document details the integration of the Grok Large Language Model (LLM) into the Dreamaware.ai agentic system. This integration expands our capabilities, particularly in handling large contexts and enabling flexible agent personas.

## Architecture & Components

The Grok integration consists of several new services and configurations:

-   **Routing Configuration (`configs/llm_routing.json`)**: This file has been updated to include `xai` as a new provider. It defines specific task types that should be routed to Grok, such as `mega_context_summarize` and `agent_tooluse`.

-   **Grok API Client (`services/providers/grok_client.py`)**: A dedicated client for interacting with the Grok API. It is designed to send OpenAI-style payloads for chat completions and tool calls.

-   **Agent & Tooling (`services/agent/`)**:
    -   `grok_agent.py`: The core agent logic that orchestrates the interaction between the user, the Grok LLM, and the available tools.
    -   `grok_tools.py`: A tool-calling bridge that allows the agent to use registered functions (e.g., `websearch`). It manages tool schemas and dispatches calls based on the LLM's requests.

-   **High-Context RAG (`services/rag/mega_context.py`)**: A specialized module that leverages Grok's large context window to answer questions based on extensive documents provided in a single prompt.

-   **Persona Adapters (`services/agent/persona_adapters.py`)**: This module allows the agent's system prompt to be dynamically adjusted, enabling different interaction styles (e.g., professional, snarky).

-   **Guardrails (`configs/limits.yaml`, `services/agent/guardrails.py`)**: To ensure safe and responsible usage, a limits configuration file has been added to define rate limits and other constraints. A guardrails module provides functions for input sanitization.

## Configuration

To enable the Grok integration, the following environment variables must be set:

-   `GROK_API_KEY`: Your API key for the Grok service.
-   `GROK_MODEL_ID`: (Optional) The specific Grok model to use (e.g., `grok-4-fast-reasoning`). Defaults to `grok-4-fast-reasoning`.
-   `GROK_BASE_URL`: (Optional) The base URL for the Grok API endpoint.

## Verification

To verify that the Grok API is configured correctly, you can run the capability probe script:

```bash
python scripts/probe_grok.py
```

A successful run will print "ok: READY".

## Testing

Unit tests have been added to `tests/test_grok_routing.py` to verify that the orchestrator's routing logic correctly directs tasks to the `xai` provider based on the rules in `configs/llm_routing.json`.