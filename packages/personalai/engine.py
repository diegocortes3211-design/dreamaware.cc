from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from services.llm.factory import generate_json
from services.security.prompt_guard import assert_clean
from services.security.audit import log_event

# Resolve repo root and prompt paths
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
SYSTEM_PROMPT_PATH = _REPO_ROOT / "packages" / "personalai" / "prompts" / "systemprompt.md"
USER_TEMPLATE_PATH = _REPO_ROOT / "packages" / "personalai" / "prompts" / "userprompt_template.md"

# Output JSON schema
DOC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["title", "abstract", "introduction", "questions", "discussion", "conclusion", "references"],
    "properties": {
        "title": {"type": "string"},
        "abstract": {"type": "string"},
        "introduction": {"type": "string"},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "question"],
                "properties": {"id": {"type": "integer"}, "question": {"type": "string"}},
            },
        },
        "discussion": {"type": "object"},
        "conclusion": {"type": "string"},
        "figures": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "caption"],
                "properties": {"id": {"type": "integer"}, "caption": {"type": "string"}},
            },
        },
        "references": {"type": "array", "items": {"type": "string"}},
    },
}


def generate_socratic_doc(
    source: str,
    date: str,
    text: str,
    images: List[Dict[str, str]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Produce a Socratic arXiv-style JSON doc using the LLM router.
    """
    sys_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    user_tmpl = USER_TEMPLATE_PATH.read_text(encoding="utf-8")

    imgs_block = "\n".join(f"<Image id={img['id']} alt=\"{img['alt']}\">" for img in images)
    user_prompt = user_tmpl.format(source=source, date=date, text=text, images=imgs_block)

    full_prompt = (
        f"{sys_prompt}\n\n"
        f"{user_prompt}\n\n"
        "Generate the response as a single JSON object that matches the required schema. "
        "Do not include any text outside the JSON."
    )

    # Prompt guard and audited generation
    assert_clean(full_prompt)
    doc = generate_json(task="long_doc", prompt=full_prompt, schema=DOC_SCHEMA, provider=provider, model=model)
    log_event(actor="engine", task="long_doc", provider=(provider or "auto"), model=(model or "auto"), prompt_sample=full_prompt[:4000], success=True, extras={"source": source})
    return doc