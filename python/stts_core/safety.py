"""Command safety checking for STTS."""
import re
import shutil
import sys
from typing import Tuple


# Dangerous command patterns (denylist)
DANGEROUS_PATTERNS = [
    r"^\s*rm\s+(-[rfRvfi\s]+)*\s*/\s*$",  # rm -rf /
    r"^\s*rm\s+(-[rfRvfi\s]+)*\s*/[a-z]+",  # rm -rf /usr, /etc, etc.
    r"^\s*dd\s+.*of=/dev/[sh]d",  # dd to disk
    r"^\s*mkfs",  # format filesystem
    r"^\s*:()\s*{\s*:\|\:&\s*}\s*;",  # fork bomb
    r"^\s*chmod\s+(-[Rrf\s]+)*\s*777\s+/",  # chmod 777 /
    r"^\s*chown\s+(-[Rrf\s]+)*\s*.*\s+/\s*$",  # chown /
    r"^\s*shutdown",
    r"^\s*reboot",
    r"^\s*init\s+0",
    r"^\s*halt",
    r">\s*/dev/[sh]d",  # write to disk device
    r"^\s*curl.*\|\s*(ba)?sh",  # curl | sh
    r"^\s*wget.*\|\s*(ba)?sh",  # wget | sh
]


# Interactive commands that can block a voice-driven daemon.
INTERACTIVE_PATTERNS = [
    r"^\s*(?:ba)?sh\s*$",  # bash/sh
    r"^\s*zsh\s*$",
    r"^\s*fish\s*$",
    r"^\s*ssh(\s|$)",
    r"^\s*top\s*$",
    r"^\s*htop\s*$",
]


# SQL patterns (not valid shell commands)
SQL_PATTERNS = [
    r"^\s*SELECT\s+",
    r"^\s*INSERT\s+INTO\s+",
    r"^\s*UPDATE\s+\w+\s+SET\s+",
    r"^\s*DELETE\s+FROM\s+",
    r"^\s*DROP\s+(TABLE|DATABASE)\s+",
    r"^\s*CREATE\s+(TABLE|DATABASE)\s+",
    r"^\s*ALTER\s+TABLE\s+",
]


def is_dangerous_command(cmd: str) -> Tuple[bool, str]:
    """Check if command matches dangerous patterns. Returns (is_dangerous, reason)."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, f"Matches dangerous pattern: {pattern[:30]}..."
    return False, ""


def is_sql_command(cmd: str) -> bool:
    """Check if command looks like SQL (not shell)."""
    for pattern in SQL_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False


def check_command_safety(
    cmd: str,
    config: dict,
    dry_run: bool,
    cprint=None,
    Colors=None,
) -> Tuple[bool, str]:
    """Check if command is safe to execute.

    Args:
        cmd: Command to check
        config: STTS configuration
        dry_run: If True, returns False with "dry-run" reason
        cprint: Optional colored print function
        Colors: Optional Colors class for output styling

    Returns:
        Tuple of (is_safe, reason)
    """
    if dry_run:
        return False, "dry-run"

    _print = cprint if cprint else lambda c, m: print(m)

    # In daemon mode, block commands that are very likely to hang waiting for user input.
    if config.get("_daemon", False):
        for pattern in INTERACTIVE_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                if config.get("safe_mode", False):
                    if not sys.stdin.isatty():
                        _print(Colors.YELLOW if Colors else None, "🔒 SAFE MODE (stdin nie jest TTY)")
                        return False, "safe-mode"
                    _print(Colors.YELLOW if Colors else None, "⚠️  Interactive command in daemon mode")
                    ans = input(f"Uruchomić interaktywnie? ({cmd}) (y/n): ").strip().lower()
                    if ans == "y":
                        break
                    return False, "interactive"
                _print(Colors.RED if Colors else None, "🚫 ZABLOKOWANO: interactive command in daemon mode")
                return False, "interactive"

    is_dangerous, reason = is_dangerous_command(cmd)
    if is_dangerous:
        _print(Colors.RED if Colors else None, f"🚫 ZABLOKOWANO: {reason}")
        return False, "dangerous"

    if config.get("safe_mode", False):
        if not sys.stdin.isatty():
            _print(Colors.YELLOW if Colors else None, "🔒 SAFE MODE (stdin nie jest TTY)")
            return False, "safe-mode"
        _print(Colors.YELLOW if Colors else None, "🔒 SAFE MODE")
        ans = input("Uruchomić? (y/n): ").strip().lower()
        if ans != "y":
            return False, "safe-mode"

    return True, ""


def is_sql_query(text: str) -> bool:
    """Check if text looks like a SQL query."""
    return is_sql_command(text)


def looks_like_natural_language(s: str) -> bool:
    """Check if text looks like natural language rather than a shell command."""
    try:
        import shlex
        toks = [t for t in shlex.split(s) if t]
    except Exception:
        toks = [t for t in (s or "").strip().split() if t]

    if len(toks) < 2:
        return False
    head = (toks[0] or "").strip()
    if not head:
        return False
    if head.startswith("/") or head.startswith("."):
        return False
    if "=" in head:
        return False
    if head in ("cd", "export", "set", "unset", "alias", "source", "."):
        return False
    if shutil.which(head):
        return False
    return True
