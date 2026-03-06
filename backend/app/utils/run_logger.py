"""
RunLogger - Per-run NDJSON execution logger.

Each pipeline run gets its own .ndjson file where every step
(discover, fetch, extract, change_detect, summarize, finding, error)
is recorded as a JSON line. The same content is also forwarded to
the terminal via the standard logger.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.utils.logger import logger


class RunLogger:
    """
    Writes structured NDJSON log entries for a single pipeline run
    and mirrors them to the terminal logger.
    """

    def __init__(self, run_id: str, log_dir: Path):
        self.run_id = run_id
        self.file_path = log_dir / f"{run_id}.ndjson"
        self._file = open(self.file_path, "a", encoding="utf-8")

    def log(
        self,
        level: str,
        event: str,
        *,
        agent: Optional[str] = None,
        phase: Optional[str] = None,
        **data: Any,
    ):
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "level": level,
            "agent": agent,
            "phase": phase,
            "event": event,
        }
        entry.update(data)

        self._file.write(json.dumps(entry, default=str) + "\n")
        self._file.flush()

        log_level = getattr(logging, level.upper(), logging.INFO)
        parts = [f"[run:{self.run_id[:8]}]"]
        if agent:
            parts.append(f"[{agent}]")
        if phase:
            parts.append(f"[{phase}]")
        parts.append(event)
        extra_str = " ".join(f"{k}={v}" for k, v in data.items())
        if extra_str:
            parts.append(extra_str)
        logger.log(log_level, " ".join(parts))

    def info(self, event: str, **kw: Any):
        self.log("INFO", event, **kw)

    def warning(self, event: str, **kw: Any):
        self.log("WARNING", event, **kw)

    def error(self, event: str, **kw: Any):
        self.log("ERROR", event, **kw)

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()
