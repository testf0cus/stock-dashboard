import pandas as pd
import numpy as np

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def add_indicators(df):
    """
    Adds technical indicators to the DataFrame in-place.
    """
    close = df['Close']
    
    # Simple Moving Averages
    df['SMA_50'] = close.rolling(window=50).mean()
    df['SMA_200'] = close.rolling(window=200).mean()
    
    # RSI
    df['RSI'] = calculate_rsi(close)
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def analyze_technical(df):
    """
    Performs technical analysis on a DataFrame with OHLCV data.
    """
    if len(df) < 50:
        return {"valid": False, "message": "Insufficient data (need >50 periods)"}

    # Work on a copy with indicators
    df = df.copy()
    add_indicators(df)
    
    close = df['Close']
    # Rest of the analysis uses the calculated columns...

    # 2. Price Action / Trend
    current_price = close.iloc[-1]
    sma_50_val = df['SMA_50'].iloc[-1]
    sma_200_val = df['SMA_200'].iloc[-1]
    
    trend = "Neutral"
    if current_price > sma_50_val:
        trend = "Bullish (Short Term)"
        if not np.isnan(sma_200_val) and current_price > sma_200_val:
             trend = "Strong Bullish"
    elif current_price < sma_50_val:
        trend = "Bearish (Short Term)"
        if not np.isnan(sma_200_val) and current_price < sma_200_val:
             trend = "Strong Bearish"

    # 3. Support & Resistance (Simplified: Recent major High/Low)
    # Look at last 6 months (approx 126 trading days) or full data
    lookback = min(len(df), 126) 
    recent_data = df.tail(lookback)
    resistance = recent_data['High'].max()
    support = recent_data['Low'].min()

    # 4. Candlestick Patterns (Last Candle)
    last_candle = df.iloc[-1]
    body_size = abs(last_candle['Close'] - last_candle['Open'])
    full_range = last_candle['High'] - last_candle['Low']
    
    pattern = "Normal"
    # Doji: Body is very small relative to range
    if full_range > 0 and (body_size / full_range) < 0.1:
        pattern = "Doji (Indecision)"
    # Hammer: Small body, long lower wick, small upper wick ( Bullish Reversal?)
    # ... simplified logic for now

    # 5. Volume
    avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
    current_vol = last_candle['Volume']
    vol_status = "Normal"
    if current_vol > avg_vol * 1.5:
        vol_status = "High (Strong Conviction)"
    elif current_vol < avg_vol * 0.5:
        vol_status = "Low (Weak Conviction)"

    return {
        "valid": True,
        "current_price": current_price,
        "trend": trend,
        "rsi": df['RSI'].iloc[-1],
        "macd": df['MACD'].iloc[-1],
        "macd_signal": df['Signal_Line'].iloc[-1],
        "support": support,
        "resistance": resistance,
        "pattern": pattern,
        "volume_status": vol_status,
        "sma_50": sma_50_val,
        "sma_200": sma_200_val
    }
