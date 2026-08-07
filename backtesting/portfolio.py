"""Portfolio tracking for the Week 9 Backtesting Engine.

The ``Portfolio`` tracks balance, equity, open/closed positions, and
exposure. Conceptually:

    Balance + Unrealized P/L = Equity

It is the single source of truth for how much money the simulated account
has at any point in time.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Portfolio:
    """Tracks balance, equity, and positions.

    Attributes:
        initial_balance: Starting cash balance.
        balance: Realized cash balance.
        open_positions: Currently held positions.
        closed_positions: Positions that have been closed.
    """

    initial_balance: float = 10_000.0
    balance: float = 10_000.0
    open_positions: list = field(default_factory=list)
    closed_positions: list = field(default_factory=list)

    def reset(self, initial_balance: float | None = None) -> None:
        """Reset the portfolio to a clean state.

        Args:
            initial_balance: Optional new starting balance (defaults to the
                current initial balance).
        """
        if initial_balance is not None:
            self.initial_balance = initial_balance
        self.balance = self.initial_balance
        self.open_positions = []
        self.closed_positions = []

    def open_position(self, position) -> None:
        """Register an open position.

        Args:
            position: The :class:`Position` to register.
        """
        self.open_positions.append(position)

    def close_position(self, position) -> None:
        """Move a position from open to closed and update balance.

        Args:
            position: The closed :class:`Position`.
        """
        if position in self.open_positions:
            self.open_positions.remove(position)
        self.closed_positions.append(position)
        self.balance += position.profit_loss

    def unrealized_pnl(self, price: float) -> float:
        """Return the total unrealized P&L across open positions at a price.

        Args:
            price: The current market price.

        Returns:
            The sum of unrealized P&L for all open positions.
        """
        return sum(p.unrealized_pnl(price) for p in self.open_positions)

    def equity(self, price: float) -> float:
        """Return the total equity (balance + unrealized P&L) at a price.

        Args:
            price: The current market price.

        Returns:
            Balance plus unrealized P&L.
        """
        return self.balance + self.unrealized_pnl(price)

    @property
    def exposure(self) -> float:
        """Return the total notional exposure of open positions.

        Computed as the sum of ``volume * entry_price`` per open position.
        """
        return sum(p.volume * p.entry_price for p in self.open_positions)

    @property
    def open_count(self) -> int:
        """Return the number of open positions."""
        return len(self.open_positions)

    @property
    def closed_count(self) -> int:
        """Return the number of closed positions."""
        return len(self.closed_positions)

    @property
    def total_positions(self) -> int:
        """Return the total number of positions seen so far."""
        return self.open_count + self.closed_count


__all__ = ["Portfolio"]
