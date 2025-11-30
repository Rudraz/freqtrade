from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta

class MeanReversionMomentum(IStrategy):
    timeframe = '5m'
    startup_candle_count = 50

    # Basic ROI / stoploss
    minimal_roi = {"0": 0.02}
    stoploss = -0.03

    # Only trade 1 pair at a time
    max_open_trades = 1

    # Core indicators
    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df['rsi'] = ta.RSI(df, timeperiod=14)
        df['ema_fast'] = ta.EMA(df, timeperiod=12)
        df['ema_slow'] = ta.EMA(df, timeperiod=26)
        df['ema_trend'] = ta.EMA(df, timeperiod=50)

        # Volatility filter
        df['atr'] = ta.ATR(df, timeperiod=14)

        return df

    # BUY
    def populate_buy_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df['rsi'] < 32) &
                (df['ema_fast'] > df['ema_slow']) &       # Momentum turning up
                (df['close'] < df['ema_trend']) &         # Mean reversion zone
                (df['atr'] > df['atr'].rolling(20).mean() * 0.8)  # Enough volatility
            ),
            'buy'
        ] = 1
        return df

    # SELL
    def populate_sell_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df['rsi'] > 55) &
                (df['close'] > df['ema_trend'])           # Price mean-reverts upward
            ),
            'sell'
        ] = 1
        return df
