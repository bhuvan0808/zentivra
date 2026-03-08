"""
RunLogger - Per-trigger, per-agent NDJSON execution logger.

Directory layout:
    data/logs/<trigger_id>/<agent_name>/logs.ndjson

Each pipeline step (discover, fetch, extract, preprocess, summarize, …)
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
    Writes structured NDJSON log entries for a single pipeline trigger.

    Use ``for_agent(agent_name)`` to get a sub-logger that writes to
    ``<trigger_id>/<agent_name>/logs.ndjson``.
    """

    def __init__(self, trigger_id: str, log_dir: Path | str):
        self.trigger_id = trigger_id
        self.log_dir = Path(log_dir) / trigger_id
        self._agents: dict[str, "_AgentLogger"] = {}

        # Orchestrator-level logger
        self._orchestrator = self._make_agent_logger("orchestrator")

    def _make_agent_logger(self, agent_name: str) -> "_AgentLogger":
        """Create a new _AgentLogger for the given agent, ensuring its directory exists."""
        agent_dir = self.log_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        file_path = agent_dir / "logs.ndjson"
        return _AgentLogger(
            trigger_id=self.trigger_id,
            agent_name=agent_name,
            file_path=file_path,
        )

    def for_agent(self, agent_name: str) -> "_AgentLogger":
        """Return (or create) the sub-logger for the given agent. Caches per agent."""
        if agent_name not in self._agents:
            self._agents[agent_name] = self._make_agent_logger(agent_name)
        return self._agents[agent_name]

    # ── Convenience: orchestrator-level logging ──

    def info(self, event: str, **kw: Any):
        self._orchestrator.info(event, **kw)

    def warning(self, event: str, **kw: Any):
        self._orchestrator.warning(event, **kw)

    def error(self, event: str, **kw: Any):
        self._orchestrator.error(event, **kw)

    def log(self, level: str, event: str, **kw: Any):
        self._orchestrator.log(level, event, **kw)

    def close(self):
        """Close orchestrator and all agent loggers, flushing and releasing file handles."""
        self._orchestrator.close()
        for al in self._agents.values():
            al.close()


class _AgentLogger:
    """
    Writes NDJSON for one agent within a trigger execution.

    Each entry is a JSON line with ts, trigger_id, level, agent, step, event, plus
    arbitrary extra fields. Entries are also mirrored to the terminal via the
    standard logger.
    """

    def __init__(self, trigger_id: str, agent_name: str, file_path: Path):
        self.trigger_id = trigger_id
        self.agent_name = agent_name
        self.file_path = file_path
        self._file = open(file_path, "a", encoding="utf-8")

    def log(
        self,
        level: str,
        event: str,
        *,
        step: Optional[str] = None,
        **data: Any,
    ):
        """Append a JSON log entry to the NDJSON file and mirror to terminal."""
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trigger_id": self.trigger_id,
            "level": level,
            "agent": self.agent_name,
            "step": step or "pipeline",
            "event": event,
        }
        entry.update(data)

        self._file.write(json.dumps(entry, default=str) + "\n")
        self._file.flush()

        # Mirror to terminal
        log_level = getattr(logging, level.upper(), logging.INFO)
        parts = [f"[trigger:{self.trigger_id[:8]}]"]
        if self.agent_name:
            parts.append(f"[{self.agent_name}]")
        if step:
            parts.append(f"[{step}]")
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
