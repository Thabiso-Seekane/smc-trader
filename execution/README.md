# Week 11 Paper Execution

This package is a paper-only execution boundary. It consumes the existing
Week 8 `TradePlan`; it does not calculate strategy or risk decisions and it
does not call `mt5.order_send`.

`PaperBroker` persists virtual orders, positions, account state, and executed
signal IDs in SQLite. `PaperExecutor` validates duplicate signals, session,
spread, maximum open positions, and daily loss before creating a virtual
position. Every failure rejects the order and fails closed.

`MT5MarketData` and `MT5Broker` are read-only adapters. They supply ticks,
symbol metadata, and candles for the `RealTimePaperEngine`, which evaluates
only when a candle has closed.
