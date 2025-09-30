import os, json, asyncio, httpx
from hypothesis import given, settings, strategies as st
from services.failurelog.logger import failure_event

UCAPI_URL = os.getenv("UCAPI_URL", "http://localhost:8080")
UCAPI_KEY = os.getenv("UCAPI_SERVICE_KEY", "dev-key") # dev only

async def _post(payload):
    headers = {"Authorization": f"Bearer {UCAPI_KEY}"}
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{UCAPI_URL}/v1/chat/completions", json=payload, headers=headers)
    return r

@given(
    model=st.text(min_size=1, max_size=32),
    content=st.text(min_size=1, max_size=512),
    temperature=st.floats(min_value=0, max_value=1)
)
@settings(max_examples=25, deadline=None)
def test_ucapi_never_500(model, content, temperature):
    payload = {"model": model, "messages": [{"role":"user","content":content}], "temperature": float(temperature)}
    try:
        r = asyncio.get_event_loop().run_until_complete(_post(payload))
        # Property: server never 500s; if it does, log with repro
        assert r.status_code < 500, f"Server 5xx: {r.status_code}"
    except Exception as e:
        failure_event("ucapi_fuzz_exception", {"payload": payload}, err=e)
        raise