import json
from typing import Any, Dict, Callable, Tuple

# name -> (callable, schema)
REGISTRY: Dict[str, Tuple[Callable[[Dict[str, Any]], Any], Dict[str, Any]]] = {}

def register(name: str, fn: Callable, schema: Dict[str, Any]):
    REGISTRY[name] = (fn, schema)

def tool_schemas():
    return [{"name": n, "description": s.get("description",""), "parameters": s["parameters"]} for n, (_, s) in REGISTRY.items()]

async def dispatch(tool_call_msg) -> Dict[str, Any]:
    # OpenAI-style: message["function_call"]={ "name": ..., "arguments": "JSON" }
    name = tool_call_msg["function_call"]["name"]
    args = json.loads(tool_call_msg["function_call"]["arguments"] or "{}")
    fn, _ = REGISTRY[name]
    res = await fn(args) if callable(fn) else None
    return {"name": name, "content": json.dumps(res or {})}

# Example tools
# websearch (stub), rag_fetch (your store), run_analysis (your microbench)
register("websearch", lambda a: {"results": []}, {
    "description":"Search web for a query",
    "parameters":{"type":"object","properties":{"query":{"type":"string"}}, "required":["query"]}
})