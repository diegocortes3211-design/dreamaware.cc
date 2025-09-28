"""
packages.ingest.prompt_chain

Defines prompt chaining for RAG.
"""
from typing import List


class PromptChain:
    def __init__(self, prompts: List[str] | None = None):
        """
        prompts: list of prompt templates to apply in sequence.
        """
        self.prompts = prompts or []

    def run(self, query: str, context: List[str]) -> str:
        """
        Compose prompts with context and generate LLM response.
        Returns generated text.
        """
        raise NotImplementedError

    def build_rag_prompt(
        self,
        task_spec: str,
        question: str,
        contexts: List[str],
        sources: List[str],
        format_spec: str,
    ) -> str:
        """
        Construct a minimal RAG prompt template.
        Includes task, question, fenced context with sources, answer format, and question repeat.
        """
        fence_start = "<<<DOCS"
        fence_end = "DOCS>>>"

        # Pair contexts with sources (zip to shortest; ignore extras)
        docs_entries: List[str] = []
        for text, src in zip(contexts, sources):
            text = (text or "").strip()
            src = (src or "").strip()
            docs_entries.append(f"{text}\n--- SOURCE: {src}".strip())
        docs_block = "\n\n".join(docs_entries)

        return (
            "System:\n"
            'You answer using only the provided context. If context is insufficient, say "insufficient context". Zero slop. Return the requested format only.\n\n'
            "User:\n"
            f"Task: {task_spec}\n"
            f"Question: {question}\n\n"
            "Context:\n"
            f"{fence_start}\n"
            f"{docs_block}\n"
            f"{fence_end}\n\n"
            "Answer format:\n"
            f"{format_spec}\n\n"
            f"Repeat question: {question}"
        )