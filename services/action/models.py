from pydantic import BaseModel, Field
from typing import Dict

class PatchReq(BaseModel):
    planId: str
    stepId: str
    repo: str
    branch: str
    diff: str = Field(..., min_length=1)
    commitMessage: str
    author: Dict[str, str]  # keys: name, email

class PatchResp(BaseModel):
    commitSha: str
    signature: str
    timestamp: str