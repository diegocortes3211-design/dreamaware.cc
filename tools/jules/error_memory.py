from __future__ import annotations
import json, re, time
from pathlib import Path
from typing import Dict, List, Any

def ensure_memory_store(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({}, indent=2))
    return p

def load_memory(path: str | Path) -> Dict[str, List[Dict[str, Any]]]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text() or "{}")
    except Exception:
        return {}

def save_memory(path: str | Path, data: Dict[str, List[Dict[str, Any]]]) -> None:
    Path(path).write_text(json.dumps(data, indent=2))

def _first_line(s: str, limit: int = 200) -> str:
    return (s.strip().splitlines() or [""])[0][:limit]

def _heuristic(stderr: str, rc: int) -> str:
    # Python specific
    if "ModuleNotFoundError" in stderr:
        m = re.search(r"No module named ['\"]([^'\"]+)['\"]", stderr)
        return f"Try: pip install {m.group(1)}" if m else "Try: pip install <missing_module>"
    if "ImportError" in stderr and "cannot import name" in stderr:
        return "Check module version/relative import; ensure the symbol exists in the installed package."
    if "NameError" in stderr:
        m = re.search(r"name ['\"]([^'\"]+)['\"] is not defined", stderr)
        return f"Define or import `{m.group(1)}`." if m else "Define or import the missing symbol."
    if "SyntaxError" in stderr:
        return "Fix syntax; run a linter (flake8/ruff) before re-running."
    if "pytest" in stderr and "AssertionError" in stderr:
        return "Open the failing test, read the assertion diff, and update code or test accordingly."

    # Linters and type checkers
    if "mypy" in stderr.lower() and "found" in stderr.lower() and "error" in stderr.lower():
        return "Mypy found type errors. Run mypy with --show-error-codes to debug."
    if re.search(r"\b[A-Z]{1,3}\d{3,4}\b", stderr): # Common linter code format (e.g., F841, E501)
        return "Linter error detected. Run the linter with --show-source to see the offending line."

    # Hardware/Resource issues
    if "CUDA out of memory" in stderr:
        return "Lower batch size or switch to CPU."
    if "torch_geometric" in stderr and ("ImportError" in stderr or "ModuleNotFoundError" in stderr):
        return "Install PyG extras (torch-scatter/torch-sparse) matching your Torch CUDA version."

    # Filesystem and permissions
    if "FileNotFoundError" in stderr or "No such file or directory" in stderr:
        m = re.search(r"No such file or directory: ['\"]([^'\"]+)['\"]", stderr)
        return f"Create/mount path `{m.group(1)}` or fix the path." if m else "Create the missing file or fix the path."
    if "Permission denied" in stderr:
        return "Add execute permissions (e.g., chmod +x) or run with proper privileges."

    # Networking and services
    if "address already in use" in stderr.lower():
        return "Free the port or change to an unused port."

    # Node.js/NPM
    if "npm ERR! code ERESOLVE" in stderr:
        return "NPM dependency conflict. Try running `npm install --legacy-peer-deps` or `npm install --force`."
    if "npm ERR! 404 Not Found" in stderr:
        return "NPM package not found. Check the package name in package.json and ensure the registry is accessible."
    if "npm ERR!" in stderr:
        return "NPM error detected. Check the full log for details (often found in a log file mentioned in the error)."

    # General command errors
    if rc == 127 or "command not found" in stderr:
        return "Install the missing command or fix PATH."

    return "Review the log in .jules/logs and re-run; consider enabling debug prints."

def analyze_and_learn(memory_path: str | Path, task_id: str, stderr: str, rc: int) -> str:
    memory_path = ensure_memory_store(memory_path)
    mem = load_memory(memory_path)
    patterns = mem.get(task_id, [])
    now = int(time.time())
    for rule in patterns:
        try:
            if re.search(rule["pattern"], stderr, re.MULTILINE):
                rule["count"] = int(rule.get("count", 0)) + 1
                rule["last_seen"] = now
                save_memory(memory_path, mem)
                return rule.get("advice", "")
        except re.error:
            continue
    advice = _heuristic(stderr, rc)
    first = _first_line(stderr)
    safe_pattern = re.escape(first) if first else r".+"
    patterns.append({
        "pattern": safe_pattern,
        "advice": advice,
        "count": 1,
        "last_seen": now
    })
    mem[task_id] = patterns
    save_memory(memory_path, mem)
    return advice

def suggest_followups(memory_path: str | Path, task_id: str, top_n: int = 5) -> List[str]:
    mem = load_memory(memory_path)
    rules = sorted(mem.get(task_id, []), key=lambda r: (-int(r.get("count", 0)), -int(r.get("last_seen", 0))))
    adv = [r.get("advice", "") for r in rules if r.get("advice")]
    seen, out = set(), []
    for a in adv:
        if a not in seen:
            seen.add(a)
            out.append(a)
        if len(out) >= top_n:
            break
    return out