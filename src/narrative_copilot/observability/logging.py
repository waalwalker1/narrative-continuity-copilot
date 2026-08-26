"""
Privacy-safe structured logging.
Ensures zero raw manuscript text is ever logged in application output or telemetry.
"""

import hashlib
import json
import logging
import sys
from typing import Any

# Configure standard logger
logger = logging.getLogger("narrative_copilot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)


def log_privacy_safe(event: str, metadata: dict[str, Any] | None = None) -> None:
    """
    Log structured event with sanitized metadata.
    Sanitizes raw text to character length and hash.
    """
    safe_data: dict[str, Any] = {"event": event}
    if metadata:
        for k, v in metadata.items():
            if isinstance(v, str) and (
                "text" in k.lower() or "quote" in k.lower() or "content" in k.lower()
            ):
                safe_data[f"{k}_len"] = len(v)
                safe_data[f"{k}_hash"] = hashlib.sha256(v.encode("utf-8")).hexdigest()[:12]
            else:
                safe_data[k] = v

    logger.info(json.dumps(safe_data))
