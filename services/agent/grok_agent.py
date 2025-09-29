from services.providers.grok_client import chat
from services.agent.grok_tools import tool_schemas, dispatch

SYSTEM = {"role":"system","content": "You are Dreamaware.ai’s agent. Use tools when helpful. Keep answers concise."}

async def run_agent(user_input: str, history=None):
    msgs = [SYSTEM] + (history or []) + [{"role":"user","content":user_input}]
    while True:
        resp = await chat(msgs, tools=tool_schemas())
        msg = resp["choices"][0]["message"]
        if "function_call" in msg:
            tool_res = await dispatch(msg)
            msgs += [msg, {"role":"function", "name": tool_res["name"], "content": tool_res["content"]}]
            continue
        return msg["content"]