from services.providers.grok_client import chat

async def answer_with_long_context(query: str, big_doc_text: str, chunk_hint: int = 120_000):
    """
    Streams a large doc directly when Grok is selected.
    chunk_hint is a soft cap; adjust via probe below.
    """
    messages = [
        {"role":"system","content":"You summarize with citations and numbered bullets."},
        {"role":"user","content": f"QUESTION:\n{query}\n\nDOCUMENT:\n{big_doc_text[:chunk_hint]}"},
    ]
    resp = await chat(messages, tools=None, temperature=0.2)
    return resp["choices"][0]["message"]["content"]