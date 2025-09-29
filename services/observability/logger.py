import logging, json
from typing import Any

class AgentLogger:
    def __init__(self, name="agent"):
        self._log = logging.getLogger(name)
        self._log.setLevel(logging.INFO)

    def info(self, msg: str, **meta: Any):
        print(json.dumps({"level":"info","msg":msg, **meta}))

    def error(self, msg: str, **meta: Any):
        print(json.dumps({"level":"error","msg":msg, **meta}))