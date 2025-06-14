import numpy as np
import pandas as pd

# --- STRATEGIES ---
def adx_strategy(df, period=14):
    df['tr'] = df['high'] - df['low']
    df['dm_plus'] = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']), 
                             df['high'] - df['high'].shift(1), 0)
    df['dm_minus'] = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)), 
                              df['low'].shift(1) - df['low'], 0)
    df['tr_sum'] = df['tr'].rolling(period).sum()
    df['dm_plus_sum'] = df['dm_plus'].rolling(period).sum()
    df['dm_minus_sum'] = df['dm_minus'].rolling(period).sum()
    df['di_plus'] = 100 * df['dm_plus_sum'] / df['tr_sum']
    df['di_minus'] = 100 * df['dm_minus_sum'] / df['tr_sum']
    df['adx'] = 100 * abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus'])
    df['signal'] = np.where(df['adx'] > 25, 1, 0)
    return df

def atr_strategy(df, period=14):
    df['tr'] = df['high'] - df['low']
    df['atr'] = df['tr'].rolling(period).mean()
    df['signal'] = np.where(df['close'] > df['close'].shift(1) + df['atr'], 1, 0)
    return df

def bollinger_bands(df, period=20, std=2):
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + (std * df['std'])
    df['lower'] = df['ma'] - (std * df['std'])
    df['signal'] = np.where(df['close'] < df['lower'], 1, np.where(df['close'] > df['upper'], -1, 0))
    return df

def breakout_high(df, window=20):
    df['high_rolling'] = df['high'].rolling(window).max()
    df['signal'] = np.where(df['close'] > df['high_rolling'].shift(1), 1, 0)
    return df

def cci_strategy(df, period=20, constant=0.015):
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['ma_tp'] = df['tp'].rolling(period).mean()
    df['mad'] = df['tp'].rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['cci'] = (df['tp'] - df['ma_tp']) / (constant * df['mad'])
    df['signal'] = np.where(df['cci'] < -100, 1, np.where(df['cci'] > 100, -1, 0))
    return df

def ichimoku_cloud(df, tenkan=9, kijun=26, senkou=52):
    df['tenkan'] = (df['high'].rolling(tenkan).max() + df['low'].rolling(tenkan).min()) / 2
    df['kijun'] = (df['high'].rolling(kijun).max() + df['low'].rolling(kijun).min()) / 2
    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(kijun)
    df['senkou_b'] = ((df['high'].rolling(senkou).max() + df['low'].rolling(senkou).min()) / 2).shift(kijun)
    df['signal'] = np.where(df['close'] > df['senkou_a'], 1, np.where(df['close'] < df['senkou_b'], -1, 0))
    return df

def ma_crossover(df, short=10, long=30):
    df['ma_short'] = df['close'].rolling(short).mean()
    df['ma_long'] = df['close'].rolling(long).mean()
    df['signal'] = np.where(df['ma_short'] > df['ma_long'], 1, np.where(df['ma_short'] < df['ma_long'], -1, 0))
    return df

def macd_strategy(df, fast=12, slow=26, signal=9):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal_line'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['signal'] = np.where(df['macd'] > df['signal_line'], 1, np.where(df['macd'] < df['signal_line'], -1, 0))
    return df

def momentum(df, period=14):
    df['momentum'] = df['close'].pct_change(periods=period) * 100
    df['signal'] = np.where(df['momentum'] > 0, 1, np.where(df['momentum'] < 0, -1, 0))
    return df

def obv_strategy(df):
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['signal'] = np.where(df['obv'] > df['obv'].shift(1), 1, 0)
    return df

def parabolic_sar(df, start=0.02, increment=0.02, maximum=0.2):
    df['sar'] = df['close'].shift(1)
    trend = 0
    af = start
    for i in range(1, len(df)):
        if trend == 0:
            if df['high'].iloc[i] > df['sar'].iloc[i-1]:
                trend = 1
                ep = df['high'].iloc[i]
            else:
                df['sar'].iloc[i] = df['low'].iloc[i-1]
        elif trend == 1:
            if df['low'].iloc[i] < df['sar'].iloc[i-1]:
                trend = -1
                df['sar'].iloc[i] = ep
                af = start
            else:
                ep = max(ep, df['high'].iloc[i])
                af = min(af + increment, maximum)
                df['sar'].iloc[i] = df['sar'].iloc[i-1] + af * (ep - df['sar'].iloc[i-1])
        else:
            if df['high'].iloc[i] > df['sar'].iloc[i-1]:
                trend = 1
                df['sar'].iloc[i] = ep
                af = start
            else:
                ep = min(ep, df['low'].iloc[i])
                af = min(af + increment, maximum)
                df['sar'].iloc[i] = df['sar'].iloc[i-1] + af * (ep - df['sar'].iloc[i-1])
    df['signal'] = np.where(df['close'] > df['sar'], 1, np.where(df['close'] < df['sar'], -1, 0))
    return df

def pivot_points(df):
    df['pivot'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
    df['s1'] = (2 * df['pivot']) - df['high'].shift(1)
    df['r1'] = (2 * df['pivot']) - df['low'].shift(1)
    df['signal'] = np.where(df['close'] > df['r1'], 1, np.where(df['close'] < df['s1'], -1, 0))
    return df

def roc_strategy(df, period=14):
    df['roc'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
    df['signal'] = np.where(df['roc'] > 0, 1, np.where(df['roc'] < 0, -1, 0))
    return df

def rsi_strategy(df, period=14, overbought=70, oversold=30):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['signal'] = np.where(df['rsi'] < oversold, 1, np.where(df['rsi'] > overbought, -1, 0))
    return df

def stochastic_oscillator(df, k_period=14, d_period=3):
    low_min = df['low'].rolling(k_period).min()
    high_max = df['high'].rolling(k_period).max()
    df['k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['d'] = df['k'].rolling(d_period).mean()
    df['signal'] = np.where(df['k'] < 20, 1, np.where(df['k'] > 80, -1, 0))
    return df

def stochastic_rsi(df, period=14, k_period=3, d_period=3):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    low_min = df['rsi'].rolling(k_period).min()
    high_max = df['rsi'].rolling(k_period).max()
    df['stoch_rsi'] = 100 * (df['rsi'] - low_min) / (high_max - low_min)
    df['signal'] = np.where(df['stoch_rsi'] < 20, 1, np.where(df['stoch_rsi'] > 80, -1, 0))
    return df

def volume_breakout(df, window=20):
    df['vol_rolling'] = df['volume'].rolling(window).mean()
    df['signal'] = np.where(df['volume'] > df['vol_rolling'].shift(1) * 1.5, 1, 0)
    return df

def williams_r(df, period=14):
    high_max = df['high'].rolling(period).max()
    low_min = df['low'].rolling(period).min()
    df['wr'] = -100 * (high_max - df['close']) / (high_max - low_min)
    df['signal'] = np.where(df['wr'] < -80, 1, np.where(df['wr'] > -20, -1, 0))
    return df

# --- STRATEGY MAP ---
strategy_map = {
    "adx_strategy": adx_strategy,
    "atr_strategy": atr_strategy,
    "bollinger_bands": bollinger_bands,
    "breakout_high": breakout_high,
    "cci_strategy": cci_strategy,
    "ichimoku_cloud": ichimoku_cloud,
    "ma_crossover": ma_crossover,
    "macd_strategy": macd_strategy,
    "momentum": momentum,
    "obv_strategy": obv_strategy,
    "parabolic_sar": parabolic_sar,
    "pivot_points": pivot_points,
    "roc_strategy": roc_strategy,
    "rsi_strategy": rsi_strategy,
    "stochastic_oscillator": stochastic_oscillator,
    "stochastic_rsi": stochastic_rsi,
    "volume_breakout": volume_breakout,
    "williams_r": williams_r
}
