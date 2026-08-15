"""SQLite persistence for paper orders, positions, account state, and signals."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from execution.enums import CloseReason, ExecutionStatus, OrderSide, OrderType
from execution.models import PaperAccount, PaperFill, PaperOrder, PaperPosition, PaperTrade

T = TypeVar("T")


def _encode(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _decode_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class PaperStore:
    """Small transactional repository that survives process restarts."""

    def __init__(self, database: str | Path = "data_store/paper_trading.db") -> None:
        self.path = Path(database)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(kind, key))")
        self.connection.execute("CREATE TABLE IF NOT EXISTS signals (signal_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def signal_seen(self, signal_id: str) -> bool:
        return self.connection.execute("SELECT 1 FROM signals WHERE signal_id = ?", (signal_id,)).fetchone() is not None

    def record_signal(self, signal_id: str, created_at: datetime) -> None:
        self.connection.execute("INSERT OR IGNORE INTO signals(signal_id, created_at) VALUES (?, ?)", (signal_id, created_at.isoformat()))
        self.connection.commit()

    def save_account(self, account: PaperAccount) -> None:
        self._save("account", "current", account)

    def load_account(self, default: PaperAccount) -> PaperAccount:
        payload = self._load("account", "current")
        if payload is None:
            return default
        payload["updated_at"] = _decode_time(payload["updated_at"])
        return PaperAccount(**payload)

    def save_order(self, order: PaperOrder) -> None:
        self._save("order", order.trade_id, order)

    def save_position(self, position: PaperPosition) -> None:
        self._save("position", position.trade_id, position)

    def save_fill(self, fill: PaperFill) -> None:
        self._save("fill", fill.fill_id, fill)

    def save_trade(self, trade: PaperTrade) -> None:
        self._save("trade", trade.trade_id, trade)

    def orders(self) -> list[PaperOrder]:
        return [self._to_order(payload) for payload in self._all("order")]

    def positions(self) -> list[PaperPosition]:
        return [self._to_position(payload) for payload in self._all("position")]

    def fills(self) -> list[PaperFill]:
        return [self._to_fill(payload) for payload in self._all("fill")]

    def trades(self) -> list[PaperTrade]:
        return [self._to_trade(payload) for payload in self._all("trade")]

    def _save(self, kind: str, key: str, value: T) -> None:
        payload = json.dumps(asdict(value), default=_encode)
        self.connection.execute("INSERT OR REPLACE INTO records(kind, key, payload) VALUES (?, ?, ?)", (kind, key, payload))
        self.connection.commit()

    def _load(self, kind: str, key: str) -> dict | None:
        row = self.connection.execute("SELECT payload FROM records WHERE kind = ? AND key = ?", (kind, key)).fetchone()
        return json.loads(row[0]) if row else None

    def _all(self, kind: str) -> list[dict]:
        return [json.loads(row[0]) for row in self.connection.execute("SELECT payload FROM records WHERE kind = ? ORDER BY key", (kind,))]

    @staticmethod
    def _to_order(payload: dict) -> PaperOrder:
        for key in ("created_at", "filled_at"):
            payload[key] = _decode_time(payload.get(key))
        payload["side"] = OrderSide(payload["side"])
        payload["status"] = ExecutionStatus(payload["status"])
        payload["order_type"] = OrderType(payload.get("order_type", "MARKET"))
        return PaperOrder(**payload)

    @staticmethod
    def _to_position(payload: dict) -> PaperPosition:
        for key in ("opened_at", "closed_at"):
            payload[key] = _decode_time(payload.get(key))
        payload["side"] = OrderSide(payload["side"])
        payload["status"] = ExecutionStatus(payload["status"])
        if payload.get("close_reason"):
            payload["close_reason"] = CloseReason(payload["close_reason"])
        return PaperPosition(**payload)

    @staticmethod
    def _to_fill(payload: dict) -> PaperFill:
        payload["filled_at"] = _decode_time(payload.get("filled_at"))
        payload["side"] = OrderSide(payload["side"])
        return PaperFill(**payload)

    @staticmethod
    def _to_trade(payload: dict) -> PaperTrade:
        for key in ("opened_at", "closed_at"):
            payload[key] = _decode_time(payload.get(key))
        payload["side"] = OrderSide(payload["side"])
        payload["close_reason"] = CloseReason(payload["close_reason"])
        return PaperTrade(**payload)


__all__ = ["PaperStore"]
