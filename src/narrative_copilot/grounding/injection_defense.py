"""
Prompt-injection defense and untrusted text boundary management.
Ensures manuscript prose (even containing adversarial text) is safely treated as data.
"""

import re


class PromptInjectionDefense:
    """
    Guards the system boundary against adversarial prompt injections embedded in creative manuscripts.
    """

    ADVERSARIAL_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.I),
        re.compile(r"system\s*:\s*(?:reveal|disregard|override)", re.I),
        re.compile(r"assistant\s*:\s*mark\s+(?:all|everything)", re.I),
        re.compile(r"override\s+canon\s+status", re.I),
        re.compile(r"delete\s+all\s+alerts", re.I),
    ]

    def sanitize_for_prompt_payload(self, text: str) -> str:
        """
        Escapes and encapsulates text to prevent instruction escape.
        Does not mutate the raw manuscript content in storage.
        """
        # Neutralize markdown/XML delimiters that might try to close prompt fences
        escaped = text.replace("```", "'''")
        return escaped

    def detect_adversarial_patterns(self, text: str) -> list[str]:
        """
        Detects known injection patterns in manuscript text for security auditing.
        """
        flags: list[str] = []
        for pattern in self.ADVERSARIAL_PATTERNS:
            if pattern.search(text):
                flags.append(pattern.pattern)
        return flags
