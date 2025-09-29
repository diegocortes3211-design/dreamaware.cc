from __future__ import annotations
import argparse, asyncio, os, shlex, sys, time, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set
import yaml
from .error_memory import analyze_and_learn, ensure_memory_store, suggest_followups

LOG_DIR = Path(".jules/logs")
MEM_PATH = Path(".jules/memory.json")

@dataclass
class Task:
    id: str
    cmd: str
    depends: List[str] = field(default_factory=list)
    retries: int = 0

def _load_tasks(path: str | Path) -> Dict[str, Task]:
    doc = yaml.safe_load(Path(path).read_text())
    tasks: Dict[str, Task] = {}
    for t in doc.get("tasks", []):
        tasks[t["id"]] = Task(
            id=t["id"],
            cmd=t["cmd"],
            depends=t.get("depends", []),
            retries=int(doc.get("retries", 0) or t.get("retries", 0))
        )
    return tasks

def _toposort(tasks: Dict[str, Task]) -> List[str]:
    deps: Dict[str, Set[str]] = {tid: set(t.depends) for tid, t in tasks.items()}
    ready = [tid for tid, d in deps.items() if not d]
    order: List[str] = []
    while ready:
        tid = ready.pop()
        order.append(tid)
        for k in list(deps.keys()):
            if tid in deps[k]:
                deps[k].remove(tid)
                if not deps[k]:
                    ready.append(k)
    remaining = [k for k, d in deps.items() if d]
    if remaining:
        raise ValueError(f"Cyclic or missing deps among: {remaining}")
    return order

async def _run_shell(cmd: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy()
    )
    out_b, err_b = await proc.communicate()
    return proc.returncode, out_b.decode(errors="replace"), err_b.decode(errors="replace")

async def _run_task(t: Task, sem: asyncio.Semaphore) -> tuple[str, bool]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ensure_memory_store(MEM_PATH)
    attempt = 0
    while True:
        attempt += 1
        async with sem:
            ts = int(time.time())
            log_base = LOG_DIR / f"{t.id}-{ts}"
            rc, out, err = await _run_shell(t.cmd)
            (log_base.with_suffix(".out")).write_text(out)
            (log_base.with_suffix(".err")).write_text(err)
            if rc == 0:
                return t.id, True
            advice = analyze_and_learn(MEM_PATH, t.id, err or out, rc)
            (log_base.with_suffix(".advice")).write_text(advice or "no-advice")
            if attempt > t.retries:
                return t.id, False
            await asyncio.sleep(min(3 * attempt, 10))

async def run(tasks_file: str, concurrency: int, default_retries: int):
    tasks = _load_tasks(tasks_file)
    for t in tasks.values():
        if t.retries == 0 and default_retries > 0:
            t.retries = default_retries
    order = _toposort(tasks)
    completed: Set[str] = set()
    in_progress: Dict[str, asyncio.Task] = {}
    sem = asyncio.Semaphore(concurrency)

    async def schedule_ready():
        made = False
        for tid in order:
            if tid in completed or tid in in_progress:
                continue
            if all(dep in completed for dep in tasks[tid].depends):
                in_progress[tid] = asyncio.create_task(_run_task(tasks[tid], sem))
                made = True
        return made

    await schedule_ready()

    while in_progress:
        done, _ = await asyncio.wait(in_progress.values(), return_when=asyncio.FIRST_COMPLETED)
        for d in done:
            tid, ok = await d
            in_progress.pop(tid, None)
            completed.add(tid)
            status = "OK" if ok else "FAIL"
            print(f"[{status}] {tid}")
            if not ok:
                hints = suggest_followups(MEM_PATH, tid)
                if hints:
                    print(f" ↳ advice: {hints[0]}")
        await schedule_ready()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", required=True, help="Path to tasks.yaml")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--retries", type=int, default=1)
    args = p.parse_args()
    asyncio.run(run(args.tasks, args.concurrency, args.retries))

if __name__ == "__main__":
    main()