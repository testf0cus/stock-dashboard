import yfinance as yf
import pandas as pd
import requests
import streamlit as st
import pandas_datareader.data as web
import datetime

def fetch_yield_curve():
    """
    Fetches Custom US Treasury Yields (4M, 8M, 1Y, 3Y, 5Y) using FRED data.
    4M and 8M are interpolated.
    Returns: DataFrame sorted by maturity.
    """
    try:
        # FRED Series IDs
        series_ids = ['DGS3MO', 'DGS6MO', 'DGS1', 'DGS3', 'DGS5']
        
        start = datetime.datetime.now() - datetime.timedelta(days=45) # Get enough history for 1M ago
        end = datetime.datetime.now()
        
        df = web.DataReader(series_ids, 'fred', start, end)
        
        if df.empty:
            return pd.DataFrame()
            
        latest = df.iloc[-1]
        
        # Calculate 1 Month Ago (approx 22 trading days)
        if len(df) > 22:
            prev = df.iloc[-22]
        else:
            prev = df.iloc[0]
            
        data = []
        
        # Helper for interpolation
        def interpolate(val1, val2, weight1=0.5):
            return val1 * weight1 + val2 * (1 - weight1)
            
        # --- CALCULATE CURRENT YIELDS ---
        y3m = latest['DGS3MO']
        y6m = latest['DGS6MO']
        y1y = latest['DGS1']
        y3y = latest['DGS3']
        y5y = latest['DGS5']
        
        # Interpolations
        # 4 Month: roughly 1/3 way from 3M to 6M? Or simple average?
        # 3M (90d) -> 4M (120d) -> 6M (180d). 4M is 30d from 3M, 60d from 6M.
        # It's closer to 3M. Weight 3M: 2/3, 6M: 1/3?
        # Linear: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        # x1=3, x2=6, x=4. (4-3)/(6-3) = 1/3. So 1/3 of the way from 3M to 6M.
        y4m = y3m + (1/3) * (y6m - y3m)
        
        # 8 Month: between 6M and 1Y (12M).
        # x1=6, x2=12, x=8. (8-6)/(12-6) = 2/6 = 1/3.
        y8m = y6m + (1/3) * (y1y - y6m)
        
        # --- CALCULATE PREVIOUS YIELDS ---
        p3m = prev['DGS3MO']
        p6m = prev['DGS6MO']
        p1y = prev['DGS1']
        p3y = prev['DGS3']
        p5y = prev['DGS5']
        
        p4m = p3m + (1/3) * (p6m - p3m)
        p8m = p6m + (1/3) * (p1y - p6m)
        
        # Store in list
        obs = [
            ("4 Month", y4m, p4m, 4/12),
            ("8 Month", y8m, p8m, 8/12),
            ("1 Year", y1y, p1y, 1),
            ("3 Year", y3y, p3y, 3),
            ("5 Year", y5y, p5y, 5)
        ]
        
        for name, val, prev_val, sort_key in obs:
            data.append({
                "Maturity": name,
                "Yield": float(val),
                "Yield 1M Ago": float(prev_val),
                "Delta (bps)": (val - prev_val) * 100,
                "SortKey": sort_key
            })
            
        return pd.DataFrame(data).sort_values("SortKey")

    except Exception as e:
        print(f"Error fetching yields (FRED): {e}")
        return pd.DataFrame()

def fetch_high_yield_spread():
    """
    Fetches ICE BofA US High Yield Index Option-Adjusted Spread (BAMLH0A1HYBB).
    Returns dict with value and delta.
    """
    try:
        start = datetime.datetime.now() - datetime.timedelta(days=10)
        end = datetime.datetime.now()
        series = web.DataReader('BAMLH0A1HYBB', 'fred', start, end)
        
        if not series.empty:
            hy_series = series['BAMLH0A1HYBB'].dropna()
            if len(hy_series) > 0:
                val = hy_series.iloc[-1]
                prev = hy_series.iloc[-2] if len(hy_series) > 1 else val
                return {
                    "value": val,
                    "delta": val - prev,
                    "date": hy_series.index[-1].strftime('%Y-%m-%d')
                }
    except Exception as e:
        print(f"Error fetching HY Spread: {e}")
    return None

def fetch_crypto_fear_greed():
    """
    Fetches Crypto Fear & Greed Index from alternative.me API.
    """
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url)
        data = response.json()
        if data['metadata']['error'] is None:
            item = data['data'][0]
            return {
                "value": int(item['value']),
                "classification": item['value_classification'],
                "timestamp": item['timestamp']
            }
    except Exception as e:
        print(f"Error fetching Crypto F&G: {e}")
    return None

def fetch_market_fear_vix():
    """
    Fetches VIX (CBOE Volatility Index) via yfinance.
    """
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return {
                "value": hist['Close'].iloc[-1],
                "previous": hist['Open'].iloc[-1] 
            }
    except Exception as e:
        print(f"Error fetching VIX: {e}")
    return None

def fetch_economic_data():
    """
    Fetches CPI, Unemployment, and GDP using pandas_datareader (FRED).
    Fallbacks to recent known values.
    """
    fallback_data = {
        "cpi_yoy": 2.6, 
        "unemployment": 4.2, 
        "gdp_growth": 2.8,
        "source": "Estimate (FRED API Unavailable)"
    }
    
    start = datetime.datetime.now() - datetime.timedelta(days=365*2)
    end = datetime.datetime.now()

    try:
        cpi = web.DataReader('CPIAUCSL', 'fred', start, end)
        unrate = web.DataReader('UNRATE', 'fred', start, end)
        gdp = web.DataReader('GDP', 'fred', start, end)
        
        latest_cpi = cpi['CPIAUCSL'].iloc[-1]
        year_ago_cpi = cpi['CPIAUCSL'].iloc[-13] 
        cpi_yoy = ((latest_cpi - year_ago_cpi) / year_ago_cpi) * 100
        
        latest_unrate = unrate['UNRATE'].iloc[-1]
        
        latest_gdp = gdp['GDP'].iloc[-1]
        prev_gdp = gdp['GDP'].iloc[-2]
        gdp_growth = ((latest_gdp / prev_gdp) ** 4 - 1) * 100
        
        return {
            "cpi_yoy": round(cpi_yoy, 2),
            "unemployment": round(latest_unrate, 2),
            "gdp_growth": round(gdp_growth, 2),
            "source": "FRED (Live)"
        }
        
    except Exception as e:
        print(f"FRED Fetch failed: {e}. Using fallback.")
        return fallback_data

def fetch_basic_market_data():
    """
    Fetches DXY (Dollar Index) and Gold Futures.
    """
    tickers = {
        "DX-Y.NYB": "DXY", # Dollar Index
        "GC=F": "Gold"     # Gold Futures
    }
    results = {}
    try:
        ticker_str = " ".join(tickers.keys())
        # Multi-ticker download returns MultiIndex cols if >1 ticker
        df = yf.download(ticker_str, period="2d", progress=False)['Close']
        
        # Check if df has columns for each
        # If single result, df is Series? No, 'Close' of multiple is DF.
        # But if only 1 valid, might be different.
        
        if not df.empty:
            for symbol, name in tickers.items():
                if symbol in df.columns:
                    series = df[symbol].dropna()
                    if len(series) >= 1:
                        val = series.iloc[-1]
                        prev = series.iloc[-2] if len(series) > 1 else val
                        delta = val - prev
                        pct = (delta / prev) * 100
                        results[name] = {"price": val, "delta": delta, "pct": pct}
    except Exception as e:
        print(f"Error fetching market data: {e}")
        
    return results

def fetch_sector_performance():
    """
    Fetches major US Sector ETFs and calculates 1D % Change.
    """
    sectors = {
        "XLE": "Energy",
        "XLF": "Financials",
        "XLK": "Technology",
        "XLV": "Health Care",
        "XLP": "Cons. Staples",
        "XLY": "Cons. Discret.",
        "XLI": "Industrials",
        "XLC": "Comm. Svcs",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLU": "Utilities"
    }
    
    data = []
    try:
        ticker_str = " ".join(sectors.keys())
        df = yf.download(ticker_str, period="2d", progress=False)['Close']
        
        if not df.empty:
             for symbol, name in sectors.items():
                if symbol in df.columns:
                    series = df[symbol].dropna()
                    if len(series) > 0:
                        val = series.iloc[-1]
                        prev = series.iloc[-2] if len(series) > 1 else val
                        pct_change = ((val - prev) / prev) * 100
                        
                        data.append({
                            "Sector": name,
                            "Change (%)": pct_change
                        })
    except Exception as e:
        print(f"Error fetching sectors: {e}")
        
    return pd.DataFrame(data).sort_values("Change (%)", ascending=False)
