from __future__ import annotations

class TopicSanitizer:
    def sanitize(self, topic: str) -> tuple[str, list[str]]:
        threats = []
        cleaned = topic
        if "<|im_end|>" in topic or "<|im_start|>" in topic or "Ignore previous instructions" in topic:
            raise ValueError("Injection pattern detected")
        if "\u200B" in topic:
            threats.append("INVISIBLE_UNICODE")
            cleaned = cleaned.replace("\u200B", "")
        if len(topic) > 500: # Simplified length check
            raise ValueError("Length limit exceeded")
        return cleaned, threats