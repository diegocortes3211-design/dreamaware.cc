import asyncio
from services.providers.grok_client import chat

async def main():
    test = "Reply with the single word: READY."
    try:
        r = await chat([{"role":"user","content":test}], tools=None, temperature=0)
        print("ok:", r["choices"][0]["message"]["content"])
    except Exception as e:
        print("fail:", e)

if __name__ == "__main__":
    asyncio.run(main())