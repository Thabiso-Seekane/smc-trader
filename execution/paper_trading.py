"""Run the Week 11 paper trading engine from the command line."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import sleep

from data import mt5_client
from execution.market_data import MT5MarketData, ClosedCandleDetector
from execution.paper_broker import PaperBroker
from execution.paper_executor import PaperExecutor, PaperExecutionConfig
from execution.persistence import PaperStore
from risk.account import Account
from risk.analyzer import RiskAnalyzer
from strategy.analyzer import StrategyAnalyzer
from strategy.filters import StrategyFilters
from structure.analyzer import MarketStructureAnalyzer
from liquidity.analyzer import LiquidityAnalyzer
from smart_money.analyzer import SmartMoneyAnalyzer
from smart_money.order_block_engine import OrderBlockEngine
from smart_money.imbalance import ImbalanceEngine
from config.settings import settings


@dataclass(slots=True)
class AnalysisBundle:
    df: object
    structure: object
    liquidity: object
    events: object
    order_blocks: object
    imbalances: object
    strategy: object
    plan: object
    account: object
    symbol: str
    timeframe: str
    current_price: float


class PaperTradingApp:
    def __init__(self) -> None:
        self.store = PaperStore(settings.paper_database)
        self.broker = PaperBroker(self.store, initial_balance=settings.paper_initial_balance)
        self.executor = PaperExecutor(self.broker, PaperExecutionConfig.from_settings(settings))
        self.market_data = MT5MarketData()
        self.detector = ClosedCandleDetector()
        self.health = {
            "mt5": False,
            "market_data": False,
            "strategy": False,
            "paper_broker": True,
            "database": True,
            "last_candle": None,
            "last_signal": None,
            "last_execution": None,
        }

    def run(self) -> None:
        self._connect_mt5()
        symbol = mt5_client.resolve_symbol(settings.default_symbol) or settings.default_symbol
        timeframe = settings.default_timeframe
        print("SMC Trader")
        print("====================================")
        print("MODE: PAPER TRADING")
        print("MT5 REAL ORDER: NONE")
        print()
        print(f"MT5 connection: {'CONNECTED' if self.health['mt5'] else 'DISCONNECTED'}")
        print(f"Symbol: {symbol}")
        print(f"Timeframe: {timeframe}")
        print()
        print("Paper account:")
        self._print_account()
        print()
        print("Waiting for new candle...")

        try:
            while True:
                candles = self.market_data.candles(symbol, timeframe, 500)
                tick = self.market_data.tick(symbol)
                if tick is None or candles is None or candles.empty:
                    sleep(1)
                    continue

                self.broker.set_symbol(self.market_data.symbol(symbol) or self.broker.get_symbol(symbol))
                self.broker.set_tick(tick)
                closed = self.detector.new_closed_candle(candles)
                if closed is None:
                    sleep(1)
                    continue

                self.health["last_candle"] = self.detector.last_closed_at
                print(f"New candle detected: {self.detector.last_closed_at}")
                print("Running market structure, liquidity, CHoCH/BOS, OB/FVG, confluence, strategy and risk checks...")
                analysis = self._run_analysis(candles.iloc[:-1], symbol, timeframe)
                self.health["strategy"] = True
                if analysis.plan is None:
                    self._report_status()
                    sleep(1)
                    continue

                signal_id = f"{symbol}:{timeframe}:{self.detector.last_closed_at.isoformat()}:{analysis.plan.direction}:{getattr(getattr(analysis.strategy, 'best', None), 'id', 'setup')}"
                self.health["last_signal"] = signal_id
                result = self.executor.execute(analysis.plan, signal_id)
                self.health["last_execution"] = datetime.now(timezone.utc)
                if result.position is not None:
                    print("PAPER ORDER CREATED")
                    print(f"Order ID: {result.order.trade_id}")
                    print("PAPER POSITION OPENED")
                else:
                    print(f"TRADE REJECTED: {result.order.rejection_reason}")

                self._print_account()
                self._report_status()
                sleep(1)
        except KeyboardInterrupt:
            print("Paper trading stopped.")
        finally:
            mt5_client.disconnect()
            self.store.close()

    def _connect_mt5(self) -> None:
        try:
            mt5_client.connect()
            self.health["mt5"] = True
            self.health["market_data"] = True
        except Exception:
            self.health["mt5"] = False
            self.health["market_data"] = False

    def _run_analysis(self, candles, symbol, timeframe) -> AnalysisBundle:
        structure = MarketStructureAnalyzer(lookback=2).analyze(candles)
        liquidity = LiquidityAnalyzer(symbol=symbol, timeframe=timeframe).analyze(candles)
        events = SmartMoneyAnalyzer(timeframe=timeframe).analyze(candles=candles, structure=structure, liquidity=liquidity)
        order_blocks = OrderBlockEngine(timeframe=timeframe).analyze(df=candles, structure=structure, liquidity=liquidity, events=events)
        imbalances = ImbalanceEngine(timeframe=timeframe).analyze(df=candles, structure=structure, liquidity=liquidity, events=events, order_blocks=order_blocks)
        strategy = StrategyAnalyzer(
            timeframe=timeframe,
            filters=StrategyFilters(
                min_confluence=settings.minimum_confluence,
                min_displacement=settings.minimum_displacement,
                premium_discount_match=settings.premium_discount_match,
                min_risk_reward=settings.minimum_risk_reward,
                require_liquidity_sweep=settings.require_liquidity_sweep,
            ),
        ).analyze(df=candles, structure=structure, liquidity=liquidity, events=events, order_blocks=order_blocks, imbalances=imbalances)
        # Size new plans from current paper equity, not the original deposit.
        account = Account(balance=self.broker.get_account().equity)
        try:
            instrument = self.broker.get_symbol(symbol)
            risk = RiskAnalyzer(
                symbol=symbol,
                timeframe=timeframe,
                default_risk_percent=settings.risk_percent,
                instrument_joint=max(instrument.contract_size, 1.0),
            )
            plan = risk.plan(getattr(strategy, 'best', None), account=account)
        except Exception:
            plan = None
        current_price = float(candles['close'].iloc[-1]) if len(candles) else 0.0
        return AnalysisBundle(df=candles, structure=structure, liquidity=liquidity, events=events, order_blocks=order_blocks, imbalances=imbalances, strategy=strategy, plan=plan, account=account, symbol=symbol, timeframe=timeframe, current_price=current_price)

    def _print_account(self) -> None:
        account = self.broker.get_account()
        print(f"Balance: ${account.balance:,.2f}")
        print(f"Equity:  ${account.equity:,.2f}")

    def _report_status(self) -> None:
        print()
        print("Health")
        print(f"MT5 Connection: {'CONNECTED' if self.health['mt5'] else 'DISCONNECTED'}")
        print(f"Market Data: {'RECEIVING' if self.health['market_data'] else 'UNAVAILABLE'}")
        print(f"Strategy Engine: {'RUNNING' if self.health['strategy'] else 'NOT RUNNING'}")
        print(f"Paper Broker: {'RUNNING' if self.health['paper_broker'] else 'STOPPED'}")
        print(f"Database: {'CONNECTED' if self.health['database'] else 'DISCONNECTED'}")
        print(f"Last Candle: {self.health['last_candle']}")
        print(f"Last Signal: {self.health['last_signal']}")
        print(f"Last Execution: {self.health['last_execution']}")


def main() -> None:
    app = PaperTradingApp()
    app.run()


if __name__ == "__main__":
    main()
