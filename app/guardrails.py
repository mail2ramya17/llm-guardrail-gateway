import re

INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"(reveal|print|show).{0,20}(system prompt|instructions)",
    r"you are now (dan|in developer mode)",
    r"disregard .{0,20}(rules|policy)",
]

PII_PATTERNS = {
    "EMAIL": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "CARD": r"\b(?:\d[ -]?){13,16}\b",
    "PHONE": r"\b\+?1?[ -.]?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}\b",
}


def detect_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


def redact_pii(text: str) -> tuple[str, list[str]]:
    found = []
    for label, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            found.append(label)
            text = re.sub(pattern, f"<{label}>", text)
    return text, found
