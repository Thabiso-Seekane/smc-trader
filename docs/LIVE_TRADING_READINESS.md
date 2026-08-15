# Live Trading Readiness

Live execution is implemented but fail-closed. Do not enable it merely
because a short backtest is positive; no strategy can guarantee profit.

## Required evidence

The out-of-sample readiness report must pass all gates:

- at least 5 untouched folds and 100 closed trades;
- aggregate return and expectancy above zero;
- profit factor at least 1.20;
- maximum drawdown no greater than 10%;
- at least 60% of folds profitable.

After a passing historical report, run paper-forward trading for at least 30
calendar days and reconcile every signal, rejection, fill, stop, target, fee,
and restart. A demo account should then run the identical live adapter before
any real-money account is considered.

## Controlled enablement

Keep source defaults unchanged. Set secrets and flags only in the private
runtime environment:

```dotenv
TRADING_MODE=live
LIVE_TRADING_ENABLED=true
LIVE_RISK_ACKNOWLEDGEMENT=I_ACCEPT_LIVE_TRADING_RISK
RISK_PERCENT=0.25
LIVE_MAX_MARGIN_FRACTION=0.10
```

Enable MT5 algorithmic trading and confirm both the terminal and account
report `trade_allowed`. Start on a demo account first. The live broker still
blocks orders unless the in-memory `ReadinessReport.passed` value is true,
spread is acceptable, broker-calculated stop loss stays inside the risk
budget, required margin stays inside the cap, and MT5 `order_check` succeeds.

## Rollback

Set `LIVE_TRADING_ENABLED=false` or `TRADING_MODE=paper` and restart the
process. Either change independently blocks new live submissions. Existing
broker positions must still be managed or closed from MT5; disabling new
submissions does not close positions automatically.

## Current status

The strategy does not currently meet the evidence requirements. Keep the
runtime in paper mode until a new, untouched evaluation passes and the
paper-forward observation period is complete.
