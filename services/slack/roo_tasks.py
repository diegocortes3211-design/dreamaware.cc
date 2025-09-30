from __future__ import annotations
import os, re, time, json, base64, hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException
import httpx

router = APIRouter()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO  = os.getenv("GITHUB_REPO", "diegocortes3211-design/dreamaware.cc")
GITHUB_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")

def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "task"

async def _github_put_file(path: str, content_bytes: bytes, message: str):
    api = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    async with httpx.AsyncClient(timeout=30.0) as c:
        # get sha if file exists (to update)
        sha = None
        r = await c.get(api, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
        if r.status_code == 200:
            sha = r.json().get("sha")
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode(),
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha
        r = await c.put(api, headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                                      "Accept": "application/vnd.github+json"}, json=payload)
        if r.status_code not in (200,201):
            raise HTTPException(status_code=500, detail=f"GitHub error: {r.text}")
        return r.json()

@router.post("/slack/roo")
async def slack_roo(request: Request):
    form = await request.form()
    text = (form.get("text") or "").strip()
    user_name = form.get("user_name") or "unknown"
    channel_id = form.get("channel_id") or ""

    if not text:
        return {"response_type":"ephemeral",
                "text":"Usage: `/roo <title> — <optional description>`"}

    # Parse "title — description"
    if "—" in text:
        title, desc = [x.strip() for x in text.split("—", 1)]
    elif "--" in text:
        title, desc = [x.strip() for x in text.split("--", 1)]
    else:
        title, desc = text, ""

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H-%MZ")
    task_id = f"roo-{ts}-{_slug(title)}"
    rel_path = f".roo/tasks/{ts}-{_slug(title)}.md"

    body = f"""---
id: {task_id}
title: "{title}"
priority: normal
labels: [roo]
assignee: {user_name}
status: todo
---

{desc or "**No description provided.**"}

**Created from Slack** (channel: {channel_id}, user: {user_name}, at {ts})
"""
    await _github_put_file(rel_path, body.encode(), f"chore(roo): add task {task_id}")

    return {
        "response_type": "in_channel",
        "text": f"🦘 Roo task created: `{title}` → `{rel_path}`"
    }