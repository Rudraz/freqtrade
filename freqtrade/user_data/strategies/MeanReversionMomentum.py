from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class MeanReversionMomentum(IStrategy):
    timeframe = '5m'
    startup_candle_count = 50
    can_short = False

    minimal_roi = {"0": 0.02, "30": 0.01, "60": 0.005}
    stoploss = -0.03
    trailing_stop = False
    max_open_trades = 1

    # Hyperopt search spaces
    buy_rsi = IntParameter(20, 45, default=32, space='buy', optimize=True)
    sell_rsi = IntParameter(50, 75, default=55, space='sell', optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space='buy', optimize=True)
    ema_fast_period = IntParameter(8, 20, default=12, space='buy', optimize=True)
    ema_slow_period = IntParameter(20, 35, default=26, space='buy', optimize=True)
    ema_trend_period = IntParameter(40, 70, default=50, space='buy', optimize=True)
    atr_filter = DecimalParameter(0.5, 1.2, default=0.8, space='buy', optimize=True)

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        for val in self.rsi_period.range:
            df[f'rsi_{val}'] = ta.RSI(df, timeperiod=val)
        for val in self.ema_fast_period.range:
            df[f'ema_fast_{val}'] = ta.EMA(df, timeperiod=val)
        for val in self.ema_slow_period.range:
            df[f'ema_slow_{val}'] = ta.EMA(df, timeperiod=val)
        for val in self.ema_trend_period.range:
            df[f'ema_trend_{val}'] = ta.EMA(df, timeperiod=val)
        df['atr'] = ta.ATR(df, timeperiod=14)
        df['atr_ma'] = df['atr'].rolling(20).mean()
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df[f'rsi_{self.rsi_period.value}'] < self.buy_rsi.value) &
                (df[f'ema_fast_{self.ema_fast_period.value}'] > df[f'ema_slow_{self.ema_slow_period.value}']) &
                (df['close'] < df[f'ema_trend_{self.ema_trend_period.value}']) &
                (df['atr'] > df['atr_ma'] * self.atr_filter.value) &
                (df['volume'] > 0)
            ),
            'enter_long'
        ] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df[f'rsi_{self.rsi_period.value}'] > self.sell_rsi.value) &
                (df['close'] > df[f'ema_trend_{self.ema_trend_period.value}']) &
                (df['volume'] > 0)
            ),
            'exit_long'
        ] = 1
        return df
