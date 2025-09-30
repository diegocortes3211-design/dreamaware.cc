import asyncio
import json
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

from .router import resolve, REGISTRY
from .schemas import ChatRequest, ErrorResponse, ErrorDetail
from .security import check_egress, estimate_and_reserve_budget, audit_event
from services.auth.spire_validator import verify_spiffe_identity


app = FastAPI(title="UCAPI")

@app.get("/v1/models")
async def models(_: dict = Depends(verify_spiffe_identity)):
    """Lists the available models in the registry."""
    return {"data": [{"id": k, **v} for k, v in REGISTRY.items()]}

@app.post("/v1/chat", response_model_exclude_none=True)
async def chat(
    body: ChatRequest,
    ident: dict = Depends(verify_spiffe_identity),
    req: Request = None
):
    """Handles non-streaming chat requests."""
    job_id = (body.metadata or {}).get("job_id", "unknown")

    try:
        adapter, provider_model = resolve(body.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- Zero-Trust Gates ---
    await check_egress(service_spiffe=ident["sub"], host=f"api.{adapter.name}.com")
    await estimate_and_reserve_budget(job_id, body.model, body.model_dump())
    # ------------------------

    try:
        params = {
            "temperature": body.temperature,
            "max_tokens": body.max_tokens,
        }
        resp = await adapter.chat(
            provider_model,
            [msg.model_dump() for msg in body.messages],
            [tool.model_dump() for tool in body.tools] if body.tools else None,
            body.tool_choice,
            params,
            stream=False,
        )
        await audit_event("ucapi_chat", ident["sub"], {"job_id": job_id, "model": body.model, "usage": resp.get("usage")})
        return JSONResponse(resp)
    except Exception as e:
        error = ErrorResponse(error=ErrorDetail(type="PROVIDER_ERROR", message=str(e)))
        return JSONResponse(status_code=502, content=error.model_dump())


@app.post("/v1/chat/stream")
async def chat_stream(body: ChatRequest, ident: dict = Depends(verify_spiffe_identity)):
    """Handles streaming chat requests using Server-Sent Events."""
    job_id = (body.metadata or {}).get("job_id", "unknown")

    try:
        adapter, provider_model = resolve(body.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def event_generator():
        q = asyncio.Queue()

        def push_to_queue(event: dict):
            q.put_nowait(event)

        # --- Zero-Trust Gates ---
        await check_egress(service_spiffe=ident["sub"], host=f"api.{adapter.name}.com")
        await estimate_and_reserve_budget(job_id, body.model, body.model_dump())
        # ------------------------

        async def stream_adapter():
            try:
                params = {
                    "temperature": body.temperature,
                    "max_tokens": body.max_tokens,
                }
                # The adapter's chat method returns an async generator for streaming
                streamer = await adapter.chat(
                    provider_model,
                    [msg.model_dump() for msg in body.messages],
                    [tool.model_dump() for tool in body.tools] if body.tools else None,
                    body.tool_choice,
                    params,
                    stream=True,
                    stream_cb=push_to_queue,
                )
                # We need to iterate over the generator to drive it
                async for _ in streamer:
                    pass
            except Exception as e:
                error_event = {"event": "error", "data": {"type": "PROVIDER_ERROR", "message": str(e)}}
                push_to_queue(error_event)

        # Run the adapter streaming in a background task
        task = asyncio.create_task(stream_adapter())

        try:
            while True:
                event = await q.get()
                if event.get("event") == "error":
                    yield f"event: error\n"
                    yield f"data: {json.dumps(event.get('data'))}\n\n"
                    break
                if event.get("event") == "message.done":
                    yield f"event: message.done\n"
                    yield f"data: {json.dumps(event)}\n\n"
                    break

                yield f"event: {event.get('event', 'message')}\n"
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            task.cancel()
            await audit_event("ucapi_stream_done", ident["sub"], {"job_id": job_id, "model": body.model})

    return StreamingResponse(event_generator(), media_type="text/event-stream")