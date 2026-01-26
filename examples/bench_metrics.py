#!/usr/bin/env python3
import math
import re
import statistics
import sys
from difflib import SequenceMatcher
from typing import Iterable, List, Tuple


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    # keep unicode letters/numbers, turn everything else into spaces
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE).strip()
    return s


def _tokens(s: str) -> List[str]:
    s = _norm(s)
    return [t for t in s.split(" ") if t]


def _edit_distance(a: List[str], b: List[str]) -> int:
    # classic DP Levenshtein on token lists
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    cur = [0] * (m + 1)
    for i in range(1, n + 1):
        cur[0] = i
        ai = a[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(
                prev[j] + 1,      # deletion
                cur[j - 1] + 1,   # insertion
                prev[j - 1] + cost,  # substitution
            )
        prev, cur = cur, prev
    return prev[m]


def wer(ref: str, hyp: str) -> float:
    r = _tokens(ref)
    h = _tokens(hyp)
    if len(r) == 0:
        return 0.0 if len(h) == 0 else 1.0
    return _edit_distance(r, h) / float(len(r))


def cer(ref: str, hyp: str) -> float:
    r = list(_norm(ref))
    h = list(_norm(hyp))
    if len(r) == 0:
        return 0.0 if len(h) == 0 else 1.0
    return _edit_distance(r, h) / float(len(r))


def ratio(ref: str, hyp: str) -> float:
    return SequenceMatcher(a=_norm(ref), b=_norm(hyp)).ratio()


def stats(values: Iterable[float]) -> Tuple[float, float, float, float, float]:
    v = list(values)
    if not v:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    v_sorted = sorted(v)
    avg = float(statistics.mean(v_sorted))
    p50 = float(statistics.median(v_sorted))
    # p95 via nearest-rank
    k = max(0, min(len(v_sorted) - 1, int(math.ceil(0.95 * len(v_sorted))) - 1))
    p95 = float(v_sorted[k])
    return avg, p50, p95, float(v_sorted[0]), float(v_sorted[-1])


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: bench_metrics.py <wer|cer|ratio|stats> ...", file=sys.stderr)
        return 2

    op = sys.argv[1].strip().lower()
    if op in ("wer", "cer", "ratio"):
        if len(sys.argv) < 4:
            print(f"usage: bench_metrics.py {op} <ref> <hyp>", file=sys.stderr)
            return 2
        ref = sys.argv[2]
        hyp = sys.argv[3]
        if op == "wer":
            print(f"{wer(ref, hyp):.4f}")
        elif op == "cer":
            print(f"{cer(ref, hyp):.4f}")
        else:
            print(f"{ratio(ref, hyp):.4f}")
        return 0

    if op == "stats":
        if len(sys.argv) < 3:
            print("usage: bench_metrics.py stats <v1> <v2> ...", file=sys.stderr)
            return 2
        vals = []
        for x in sys.argv[2:]:
            try:
                vals.append(float(x))
            except Exception:
                pass
        avg, p50, p95, vmin, vmax = stats(vals)
        print(f"{avg:.4f},{p50:.4f},{p95:.4f},{vmin:.4f},{vmax:.4f}")
        return 0

    print(f"unknown op: {op}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
