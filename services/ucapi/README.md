# Universal Chat API (UCAPI)

The UCAPI service provides a unified, zero-trust gateway for all Large Language Model (LLM) interactions within the Dreamaware.ai platform. It acts as a single, stable API endpoint that abstracts away the specifics of different model providers (like OpenAI, Anthropic, etc.), enforces security policies, and provides centralized auditing and cost control.

## Key Features

- **Unified Interface**: A single set of API endpoints (`/v1/chat`, `/v1/chat/stream`) for all models.
- **Normalized I/O**: Standardized request and response schemas, including for tool-calling and errors.
- **Model Routing**: A central registry (`registry.py`) maps user-friendly model aliases (e.g., `sonnet-latest`) to specific provider models.
- **Hot-Swappable Adapters**: A pluggable architecture (`adapters/`) allows for easy addition of new model providers without changing the gateway logic.
- **Zero-Trust Security**: Integrates with SPIFFE for service identity verification and includes hooks for OPA-based egress policy checks.
- **Observability & Control**: Provides hooks for centralized auditing (`audit_event`) and cost management (`estimate_and_reserve_budget`).
- **Streaming Support**: Natively supports Server-Sent Events (SSE) for real-time, token-by-token responses.

## API Endpoints

- `GET /v1/models`: Lists all available model aliases from the registry.
- `POST /v1/chat`: For synchronous, non-streaming chat completions.
- `POST /v1/chat/stream`: For streaming chat completions via Server-Sent Events.

## Running the Service

1.  **Install Dependencies**:
    ```bash
    pip install -e .[api]
    ```

2.  **Set Environment Variables**:
    Ensure the required API keys for the adapters are set in your environment. For example:
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

3.  **Start the Server**:
    ```bash
    uvicorn services.ucapi.gateway:app --host 0.0.0.0 --port 8080
    ```

## Testing

To run the unit tests for the service:
```bash
pytest services/ucapi/tests/
```