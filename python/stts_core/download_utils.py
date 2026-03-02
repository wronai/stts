"""Download utilities for STTS."""

from __future__ import annotations


def _download_progress(count, block_size, total_size):
    """Print download progress."""
    percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
    print(f"\r  Progress: {percent}%", end="", flush=True)
