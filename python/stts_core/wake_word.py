"""Wake word detection for STTS daemon mode."""
import re
from typing import List, Optional, Tuple


# Wake-word patterns (hejken/heyken + common STT phonetic variants).
# NOTE: Match only at the beginning of the transcript.
WAKE_WORD_PATTERNS = [
    # he(j|y)[, ]? (k)en/kan
    r"^(?:hej|hey)\W*(?:ken|kan)\b",
    r"^(?:hej|hey)\W+\w*\W*(?:ken|kan)\b",
    # joined forms
    r"^(?:hejken|heyken)\b",
    # STT sometimes spells it as letters: "a i kan" / "ai kan"
    r"^a\s*i\s*(?:ken|kan)\b",
    r"^ai\s*(?:ken|kan)\b",
    # common mishearing: "hi, kan"
    r"^hi\W*(?:ken|kan)\b",
    # Vosk often truncates to just "ken" at the start
    r"^ken\b",
    r"^kan\b",
]


def check_wake_word(text: str, patterns: Optional[List[str]] = None) -> Tuple[bool, str]:
    """Check if text starts with wake word. Returns (matched, remaining_text)."""
    if not text:
        return False, ""
    src = str(text)
    pats = list(patterns or WAKE_WORD_PATTERNS)
    for pattern in pats:
        pat = str(pattern or "")
        if pat.startswith("^"):
            pat = pat[1:]

        full = r"^\s*[\W_]*" + pat
        if re.match(full, src, re.IGNORECASE):
            remaining = re.sub(full, "", src, count=1, flags=re.IGNORECASE)
            remaining = remaining.strip(" \t\r\n,:;.!?\"'""''—-")
            return True, remaining.strip()
    return False, src


def phrase_to_pattern(phrase: str) -> Optional[str]:
    """Convert literal phrase into regex that tolerates punctuation/extra spaces between words."""
    p = str(phrase or "").strip()
    if not p:
        return None
    parts = [re.escape(x) for x in re.split(r"\s+", p) if x]
    if not parts:
        return None
    if len(parts) == 1:
        return r"^" + parts[0] + r"\b"
    return r"^" + r"\W*".join(parts) + r"\b"


def generate_variants(phrase: str, max_variants: int = 24) -> List[str]:
    """Generate phonetic variants of wake word phrase for STT matching."""
    p0 = str(phrase or "").strip()
    if not p0:
        return []

    p = re.sub(r"\s+", " ", p0)
    low = p.lower()

    out: List[str] = []
    seen = set()

    def _add(x: str):
        s = str(x or "").strip()
        if not s:
            return
        if len(out) >= int(max_variants or 0):
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(s)

    _add(low)
    _add(p)
    if " " in low:
        _add(low.replace(" ", ""))

    trans_table = str.maketrans({
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "u",
        "ś": "s",
        "ź": "z",
        "ż": "z",
    })
    _add(low.translate(trans_table))

    rules = [
        ("hej", ["hey", "ej"]),
        ("hey", ["hej", "ej"]),
        ("ken", ["kan"]),
        ("kan", ["ken"]),
        ("ch", ["h"]),
        ("rz", ["z"]),
        ("sz", ["s"]),
        ("cz", ["c"]),
    ]

    base_variants = list(out)
    for src, reps in rules:
        for v in base_variants:
            if src not in v.lower():
                continue
            for r in reps:
                _add(v.lower().replace(src, r))

    for v in list(out):
        v2 = v.lower()
        if v2.startswith("h") and len(v2) > 2:
            _add(v2[1:])
        if v2.startswith("he") and len(v2) > 3:
            _add(v2[2:])

    return out


def normalize_daemon_command(text: str) -> str:
    """Heuristic normalization of command after wake-word (for STT)."""
    s = (text or "").strip()
    if not s:
        return ""

    lower = s.lower().strip()
    # Common STT distortion for "lista": "js ta" / "jesta" etc.
    lower = re.sub(r"\b(j|i)s\s*ta\b", "lista", lower)
    lower = re.sub(r"\b(j|i)est\s*a\b", "lista", lower)
    lower = re.sub(r"\ba\s+lista\b", "lista", lower)
    # Remove leading filler tokens
    lower = re.sub(r"^(a|i|y)\s+", "", lower)

    return lower.strip()
