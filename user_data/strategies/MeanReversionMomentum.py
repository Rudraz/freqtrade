from freqtrade.strategy import IStrategy
import pandas as pd
import talib.abstract as ta


class MeanReversionMomentum(IStrategy):
    """
    Simple example strategy:
    - Uses RSI and two EMAs
    - Buys when RSI is oversold and fast EMA > slow EMA
    - Exits when RSI is overbought
    """

    # Use 5m candles
    timeframe = "5m"

    # Simple minimal ROI target: 2%
    minimal_roi = {
        "0": 0.02
    }

    # Stoploss at -3%
    stoploss = -0.03

    # Only long for now
    can_short = False

    # Process only new candles to reduce CPU
    process_only_new_candles = True

    # Number of candles needed before we start
    startup_candle_count = 50

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Add RSI and two EMAs.
        """
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Entry logic:
        - RSI below 30 (oversold)
        - Fast EMA above slow EMA (upward momentum)
        """
        dataframe.loc[:, "enter_long"] = 0

        buy_cond = (
            (dataframe["rsi"] < 30) &
            (dataframe["ema_fast"] > dataframe["ema_slow"])
        )

        dataframe.loc[buy_cond, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Exit logic:
        - RSI above 70 (overbought)
        """
        dataframe.loc[:, "exit_long"] = 0

        sell_cond = dataframe["rsi"] > 70
        dataframe.loc[sell_cond, "exit_long"] = 1
        return dataframe
