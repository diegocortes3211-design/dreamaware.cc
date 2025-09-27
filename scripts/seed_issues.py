#!/usr/bin/env python3
"""
Seed GitHub issues from .github/issue_seeds.yaml
Idempotent: skips if an open issue with the same title already exists.
Filters:
  ONLY_TITLES="Title1,Title2"  -> create only matching titles
  DRY_RUN="1"                  -> print plan only
"""
import os, sys, json, requests, yaml
from pathlib import Path

SEEDS = Path(".github/issue_seeds.yaml")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN")
ONLY = {t.strip() for t in os.environ.get("ONLY_TITLES", "").split(",") if t.strip()}
DRY = os.environ.get("DRY_RUN", "0") in ("1","true","True","YES","yes")

def gh(url, method="GET", **kw):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    return requests.request(method, url, headers=h, **kw)

def main():
    if not TOKEN:
        print("ERROR: GITHUB_TOKEN not set", file=sys.stderr); sys.exit(2)
    if not REPO:
        print("ERROR: GITHUB_REPOSITORY not set", file=sys.stderr); sys.exit(2)
    if not SEEDS.exists():
        print("No seeds file found, skipping."); return
    data = yaml.safe_load(SEEDS.read_text()) or {}
    seeds = data.get("issues", [])

    # fetch open issues (first 100)
    base = f"https://api.github.com/repos/{REPO}"
    cur = gh(f"{base}/issues?state=open&per_page=100").json()
    open_titles = {i["title"] for i in cur if "pull_request" not in i}

    created = []
    for it in seeds:
        title = it.get("title","").strip()
        if not title: continue
        if ONLY and title not in ONLY:
            continue
        if title in open_titles:
            print(f"skip (exists): {title}")
            continue
        body = it.get("body","")
        labels = it.get("labels",[])
        payload = {"title": title, "body": body, "labels": labels}
        if DRY:
            print(f"DRY: would create issue: {title} labels={labels}")
            continue
        r = gh(f"{base}/issues", method="POST", json=payload)
