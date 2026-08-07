"""Report generation for the Week 9 Backtesting Engine.

The ``BacktestReport`` serializes a :class:`BacktestResult` into the formats
consumed by the Week 10 dashboard and for ad-hoc analysis:

    * CSV trade log
    * JSON summary
    * HTML report
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backtesting.models import BacktestResult


@dataclass(slots=True)
class BacktestReport:
    """Serializes a :class:`BacktestResult` to CSV / JSON / HTML.

    Attributes:
        result: The backtest result to report on.
    """

    result: BacktestResult

    # --- CSV -------------------------------------------------
    def to_csv(self, path: str | Path) -> Path:
        """Write the trade log to a CSV file.

        Args:
            path: Destination file path.

        Returns:
            The path written.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "id",
                    "symbol",
                    "direction",
                    "entry_price",
                    "exit_price",
                    "volume",
                    "entry_time",
                    "exit_time",
                    "risk_amount",
                    "profit_loss",
                    "commission",
                    "slippage_cost",
                    "exit_reason",
                    "result",
                    "r_multiple",
                    "confluence_score",
                    "reason",
                ]
            )
            for trade in self.result.trades:
                writer.writerow(
                    [
                        trade.id,
                        trade.symbol,
                        trade.direction.value,
                        trade.entry_price,
                        trade.exit_price,
                        trade.volume,
                        trade.entry_time.isoformat(),
                        trade.exit_time.isoformat(),
                        trade.risk_amount,
                        trade.profit_loss,
                        trade.commission,
                        trade.slippage_cost,
                        trade.exit_reason.value,
                        trade.result.value,
                        trade.r_multiple,
                        trade.confluence_score,
                        trade.reason,
                    ]
                )
        return path

    # --- JSON ------------------------------------------------
    def to_json(self, path: str | Path | None = None) -> dict:
        """Return (and optionally write) a JSON-serializable summary.

        Args:
            path: Optional destination file path.

        Returns:
            A dict with headline metrics and the trade log.
        """
        payload = {
            "initial_balance": self.result.initial_balance,
            "final_balance": self.result.final_balance,
            "total_return": self.result.total_return,
            "total_trades": self.result.total_trades,
            "winning_trades": self.result.winning_trades,
            "losing_trades": self.result.losing_trades,
            "win_rate": self.result.win_rate,
            "profit_factor": self.result.profit_factor,
            "max_drawdown": self.result.max_drawdown,
            "sharpe_ratio": self.result.sharpe_ratio,
            "average_rr": self.result.average_rr,
            "average_trade": self.result.average_trade,
            "expectancy": self.result.expectancy,
            "trades": [
                {
                    "id": str(t.id),
                    "symbol": t.symbol,
                    "direction": t.direction.value,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "profit_loss": t.profit_loss,
                    "r_multiple": t.r_multiple,
                    "result": t.result.value,
                    "confluence_score": t.confluence_score,
                }
                for t in self.result.trades
            ],
        }
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    # --- text summary ----------------------------------------
    def text_summary(self) -> str:
        """Return a formatted plain-text backtest report."""
        r = self.result
        lines = [
            "=" * 40,
            "BACKTEST REPORT",
            "=" * 40,
            f"Symbol: {r.config.symbol or '-'}",
            f"Timeframe: {r.config.timeframe or '-'}",
            f"Initial Balance: ${r.initial_balance:,.2f}",
            f"Final Balance: ${r.final_balance:,.2f}",
            f"Return: {r.total_return * 100:.2f}%",
            "-" * 40,
            f"Trades: {r.total_trades}",
            f"Wins: {r.winning_trades}",
            f"Losses: {r.losing_trades}",
            f"Win Rate: {r.win_rate * 100:.2f}%",
            f"Profit Factor: {r.profit_factor:.2f}",
            f"Expectancy: {r.expectancy:.2f}",
            f"Average R: {r.average_rr:.2f}R",
            "-" * 40,
            f"Max Drawdown: {r.max_drawdown * 100:.2f}%",
            f"Sharpe: {r.sharpe_ratio:.2f}",
            "=" * 40,
        ]
        return "\n".join(lines)

    # --- HTML ------------------------------------------------
    def to_html(self, path: str | Path | None = None) -> str:
        """Return (and optionally write) a standalone HTML report.

        Args:
            path: Optional destination file path.

        Returns:
            A full HTML document string.
        """
        r = self.result
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Backtest Report</title>
<style>
body{{font-family:sans-serif;margin:2rem;color:#222}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}}
.card{{border:1px solid #ddd;border-radius:8px;padding:1rem}}
.card .k{{font-size:.8rem;color:#666}}
.card .v{{font-size:1.4rem;font-weight:700}}
table{{border-collapse:collapse;width:100%;margin-top:1rem}}
th,td{{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;font-size:.85rem}}
</style></head><body>
<h1>Backtest Report</h1>
<div class="grid">
  <div class="card"><div class="k">Final Balance</div><div class="v">${r.final_balance:,.2f}</div></div>
  <div class="card"><div class="k">Return</div><div class="v">{r.total_return*100:.2f}%</div></div>
  <div class="card"><div class="k">Trades</div><div class="v">{r.total_trades}</div></div>
  <div class="card"><div class="k">Win Rate</div><div class="v">{r.win_rate*100:.2f}%</div></div>
  <div class="card"><div class="k">Profit Factor</div><div class="v">{r.profit_factor:.2f}</div></div>
  <div class="card"><div class="k">Max Drawdown</div><div class="v">{r.max_drawdown*100:.2f}%</div></div>
  <div class="card"><div class="k">Expectancy</div><div class="v">{r.expectancy:.2f}</div></div>
  <div class="card"><div class="k">Sharpe</div><div class="v">{r.sharpe_ratio:.2f}</div></div>
</div>
<h2>Trade Log</h2>
<table>
<tr><th>#</th><th>Symbol</th><th>Dir</th><th>Entry</th><th>Exit</th><th>P/L</th><th>R</th><th>Result</th><th>Confluence</th></tr>
{''.join(
    f"<tr><td>{i}</td><td>{t.symbol}</td><td>{t.direction.value}</td>"
    f"<td>{t.entry_price:.2f}</td><td>{t.exit_price:.2f}</td>"
    f"<td>{t.profit_loss:.2f}</td><td>{t.r_multiple:.2f}</td>"
    f"<td>{t.result.value}</td><td>{t.confluence_score:.0f}</td></tr>"
    for i, t in enumerate(self.result.trades, 1)
)}
</table>
</body></html>"""
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
        return html


__all__ = ["BacktestReport"]
