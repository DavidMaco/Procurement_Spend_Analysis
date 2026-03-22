"""Immutable recommendation event log for audit trail.

Every recommendation produced by the system is recorded with its full context:
input snapshot reference, model version, payload, approval status, and timestamps.
Designed for append-only storage with a tamper-evident hash chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ActionTaken(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RecommendationEvent(BaseModel):
    """Single immutable audit record for a recommendation."""

    event_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    model_id: str
    model_version: str
    input_snapshot_ref: str
    recommendation_type: str
    recommendation_payload: dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    related_event_id: Optional[str] = None
    approver_id: Optional[str] = None
    action_taken: ActionTaken = ActionTaken.PENDING
    action_timestamp: Optional[str] = None
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None

    model_config = {"frozen": True}


class EventLog:
    """Append-only in-memory event store.

    In production this would be backed by an immutable ledger (e.g. append-only
    table, event stream, or object-store journal). The in-memory implementation
    fulfils the M2 contract and is fully testable.
    """

    def __init__(
        self,
        file_path: str | Path | None = None,
        archive_path: str | Path | None = None,
    ) -> None:
        self._genesis_hash = "0" * 64
        self._file_path = Path(file_path) if file_path else None
        self._archive_path = Path(archive_path) if archive_path else None
        self._events: list[RecommendationEvent] = []
        self._resolved_events: dict[str, str] = {}
        self._sync_from_disk()

    # ------------------------------------------------------------------
    # Write path (append-only)
    # ------------------------------------------------------------------

    def record(self, event: RecommendationEvent) -> str:
        """Append an event and return its event_id."""
        self._sync_from_disk()
        sealed = self._seal_event(event, self._last_hash())
        self._events.append(sealed)
        self._resolved_events = self._build_resolved_index(self._events)
        self._append_to_disk(sealed)
        return sealed.event_id

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get(self, event_id: str) -> Optional[RecommendationEvent]:
        """Retrieve a single event by ID, or ``None``."""
        self._sync_from_disk()
        for ev in self._events:
            if ev.event_id == event_id:
                return ev
        return None

    def query(
        self,
        *,
        recommendation_type: Optional[str] = None,
        action_taken: Optional[ActionTaken] = None,
        model_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[RecommendationEvent]:
        """Filter events by optional criteria. Most recent first."""
        self._sync_from_disk()
        results = reversed(self._events)
        filtered: list[RecommendationEvent] = []
        for ev in results:
            if recommendation_type and ev.recommendation_type != recommendation_type:
                continue
            if action_taken and ev.action_taken != action_taken:
                continue
            if model_id and ev.model_id != model_id:
                continue
            filtered.append(ev)
            if len(filtered) >= limit:
                break
        return filtered

    def count(self) -> int:
        self._sync_from_disk()
        return len(self._events)

    def all_events(self) -> list[RecommendationEvent]:
        """Return all events in insertion order (oldest first)."""
        self._sync_from_disk()
        return list(self._events)

    def stats(self) -> dict[str, Any]:
        """Return operational statistics for the recommendation ledger."""
        self._sync_from_disk()
        counts = {action.value: 0 for action in ActionTaken}
        recommendation_types: dict[str, int] = {}
        model_ids: dict[str, int] = {}

        for event in self._events:
            counts[event.action_taken.value] += 1
            recommendation_types[event.recommendation_type] = (
                recommendation_types.get(event.recommendation_type, 0) + 1
            )
            model_ids[event.model_id] = model_ids.get(event.model_id, 0) + 1

        timestamps = [event.timestamp for event in self._events]
        return {
            "total_events": len(self._events),
            "root_recommendations": sum(
                1 for event in self._events if event.related_event_id is None
            ),
            "decision_events": sum(
                1 for event in self._events if event.related_event_id is not None
            ),
            "action_counts": counts,
            "recommendation_types": recommendation_types,
            "model_ids": model_ids,
            "integrity_verified": self.verify_integrity(),
            "chain_head": self._last_hash(),
            "file_path": str(self._file_path) if self._file_path else None,
            "archive_path": str(self._archive_path) if self._archive_path else None,
            "first_event_at": min(timestamps) if timestamps else None,
            "last_event_at": max(timestamps) if timestamps else None,
        }

    def verify_integrity(self) -> bool:
        """Return whether the current event chain is intact."""
        self._sync_from_disk()
        chain = self._genesis_hash
        for event in self._events:
            expected_prev = chain
            expected_hash = self._compute_entry_hash(event, expected_prev)
            if event.prev_hash != expected_prev or event.entry_hash != expected_hash:
                return False
            chain = expected_hash
        return True

    def to_jsonl(self) -> str:
        """Return the current ledger contents as JSONL text."""
        self._sync_from_disk()
        return "\n".join(
            json.dumps(event.model_dump(mode="json")) for event in self._events
        ) + ("\n" if self._events else "")

    def compact(self) -> int:
        """Rewrite the on-disk ledger from the current in-memory event set."""
        self._sync_from_disk()
        return self._rewrite_active_file()

    def _rewrite_active_file(self) -> int:
        """Persist the current in-memory active ledger without reloading from disk."""
        if self._file_path is None:
            return len(self._events)

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._file_path.with_suffix(self._file_path.suffix + ".tmp")
        payload = "\n".join(
            json.dumps(event.model_dump(mode="json")) for event in self._events
        ) + ("\n" if self._events else "")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self._file_path)
        return len(self._events)

    def archive_before(self, before_timestamp: str) -> dict[str, int]:
        """Archive resolved recommendation threads whose latest event is before the cutoff."""
        self._sync_from_disk()
        if self._archive_path is None:
            raise ValueError("Archive path is not configured")

        cutoff = datetime.fromisoformat(before_timestamp)
        threads = self._thread_index(self._events)
        archive_roots: set[str] = set()
        archived_events: list[RecommendationEvent] = []

        for root_id, events in threads.items():
            if root_id not in self._resolved_events:
                continue
            latest_ts = max(self._event_sort_key(event) for event in events)
            if latest_ts < cutoff:
                archive_roots.add(root_id)
                archived_events.extend(events)

        if not archived_events:
            return {
                "archived_threads": 0,
                "archived_events": 0,
                "retained_events": len(self._events),
            }

        self._append_many_to_archive(archived_events)
        self._events = [
            event
            for event in self._events
            if self._root_event_id(event) not in archive_roots
        ]
        self._resolved_events = self._build_resolved_index(self._events)
        self._rewrite_active_file()
        return {
            "archived_threads": len(archive_roots),
            "archived_events": len(archived_events),
            "retained_events": len(self._events),
        }

    def archive_jsonl(self) -> str:
        """Return the archived ledger contents as JSONL text."""
        if self._archive_path is None or not self._archive_path.exists():
            return ""
        return self._archive_path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Approval workflow
    # ------------------------------------------------------------------

    def approve(self, event_id: str, approver_id: str) -> RecommendationEvent:
        """Append an approval event while preserving the original recommendation."""
        return self._transition(event_id, ActionTaken.APPROVED, approver_id)

    def reject(self, event_id: str, approver_id: str) -> RecommendationEvent:
        """Append a rejection event while preserving the original recommendation."""
        return self._transition(event_id, ActionTaken.REJECTED, approver_id)

    def history(self, event_id: str) -> list[RecommendationEvent]:
        """Return the original recommendation and any decision events tied to it."""
        self._sync_from_disk()
        return [
            ev
            for ev in self._events
            if ev.event_id == event_id or ev.related_event_id == event_id
        ]

    @staticmethod
    def _build_resolved_index(events: list[RecommendationEvent]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for event in events:
            if event.related_event_id and event.action_taken != ActionTaken.PENDING:
                resolved[event.related_event_id] = event.event_id
        return resolved

    @staticmethod
    def _root_event_id(event: RecommendationEvent) -> str:
        return event.related_event_id or event.event_id

    @staticmethod
    def _event_sort_key(event: RecommendationEvent) -> datetime:
        stamp = event.action_timestamp or event.timestamp
        return datetime.fromisoformat(stamp)

    @classmethod
    def _thread_index(
        cls,
        events: list[RecommendationEvent],
    ) -> dict[str, list[RecommendationEvent]]:
        threads: dict[str, list[RecommendationEvent]] = {}
        for event in events:
            threads.setdefault(cls._root_event_id(event), []).append(event)
        return threads

    def _sync_from_disk(self) -> None:
        if self._file_path is None or not self._file_path.exists():
            return

        loaded: list[RecommendationEvent] = []
        migrated = False
        for line in self._file_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            loaded.append(RecommendationEvent.model_validate_json(line))

        normalized: list[RecommendationEvent] = []
        chain = self._genesis_hash
        for event in loaded:
            expected_hash = self._compute_entry_hash(event, chain)
            if event.prev_hash is None or event.entry_hash is None:
                event = event.model_copy(
                    update={"prev_hash": chain, "entry_hash": expected_hash}
                )
                migrated = True
            normalized.append(event)
            chain = event.entry_hash or expected_hash

        self._events = normalized
        self._resolved_events = self._build_resolved_index(self._events)
        if migrated:
            self._rewrite_active_file()

    def _append_to_disk(self, event: RecommendationEvent) -> None:
        if self._file_path is None:
            return

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    def _append_many_to_archive(self, events: list[RecommendationEvent]) -> None:
        if self._archive_path is None:
            return

        self._archive_path.parent.mkdir(parents=True, exist_ok=True)
        with self._archive_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    def _transition(
        self,
        event_id: str,
        action: ActionTaken,
        approver_id: str,
    ) -> RecommendationEvent:
        self._sync_from_disk()
        if event_id in self._resolved_events:
            prior_action = self.get(self._resolved_events[event_id])
            resolved_as = (
                prior_action.action_taken.value if prior_action else "resolved"
            )
            raise ValueError(f"Event {event_id} already resolved as {resolved_as}")

        for ev in self._events:
            if ev.event_id == event_id:
                if ev.action_taken != ActionTaken.PENDING:
                    raise ValueError(
                        f"Event {event_id} already resolved as {ev.action_taken.value}"
                    )
                updated = RecommendationEvent(
                    model_id=ev.model_id,
                    model_version=ev.model_version,
                    input_snapshot_ref=ev.input_snapshot_ref,
                    recommendation_type=ev.recommendation_type,
                    recommendation_payload=ev.recommendation_payload,
                    confidence_score=ev.confidence_score,
                    related_event_id=ev.event_id,
                    approver_id=approver_id,
                    action_taken=action,
                    action_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self.record(updated)
                self._resolved_events[event_id] = updated.event_id
                return self.get(updated.event_id) or updated
        raise KeyError(f"Event {event_id} not found")

    def _last_hash(self) -> str:
        if not self._events:
            return self._genesis_hash
        return self._events[-1].entry_hash or self._genesis_hash

    @staticmethod
    def _payload_dict(event: RecommendationEvent) -> dict[str, Any]:
        payload = event.model_dump(mode="json")
        payload.pop("prev_hash", None)
        payload.pop("entry_hash", None)
        return payload

    @classmethod
    def _compute_entry_hash(cls, event: RecommendationEvent, prev_hash: str) -> str:
        payload = json.dumps(
            cls._payload_dict(event), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(f"{prev_hash}:{payload}".encode("utf-8")).hexdigest()

    @classmethod
    def _seal_event(
        cls, event: RecommendationEvent, prev_hash: str
    ) -> RecommendationEvent:
        entry_hash = cls._compute_entry_hash(event, prev_hash)
        return event.model_copy(
            update={"prev_hash": prev_hash, "entry_hash": entry_hash}
        )
