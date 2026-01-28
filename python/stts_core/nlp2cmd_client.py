from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


def nlp2cmd_service_query_ex(
    query: str,
    url: str = "http://localhost:8000",
    execute: bool = True,
    timeout: float = 30.0,
) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
    try:
        import urllib.request

        endpoint = f"{url.rstrip('/')}/query"
        payload = (
            json.dumps(
                {
                    "query": query,
                    "dsl": "shell",
                    "execute": execute,
                }
            )
        ).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data, None
    except Exception as e:
        return None, e


def nlp2cmd_service_query(
    query: str,
    url: str = "http://localhost:8000",
    execute: bool = True,
    timeout: float = 30.0,
) -> Optional[Dict[str, Any]]:
    data, _ = nlp2cmd_service_query_ex(
        query=query,
        url=url,
        execute=execute,
        timeout=timeout,
    )
    return data


def nlp2cmd_service_health_ex(url: str, timeout: float = 2.5) -> Tuple[bool, Optional[Exception]]:
    try:
        import urllib.request

        endpoint = f"{url.rstrip('/')}/health"
        with urllib.request.urlopen(endpoint, timeout=timeout) as resp:
            if getattr(resp, "status", 0) != 200:
                return False, None
            data = json.loads(resp.read().decode("utf-8"))
            return (data or {}).get("status") == "healthy", None
    except Exception as e:
        return False, e


def nlp2cmd_service_health(url: str, timeout: float = 2.5) -> bool:
    ok, _ = nlp2cmd_service_health_ex(url=url, timeout=timeout)
    return ok
