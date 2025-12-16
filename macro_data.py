import yfinance as yf
import pandas as pd
import requests
import streamlit as st
import pandas_datareader.data as web
import datetime

def fetch_yield_curve():
    """
    Fetches US Treasury Yields using yfinance proxies.
    Returns: DataFrame with 'Maturity', 'Yield', 'Yield 1M Ago', 'Delta'.
    """
    # Yahoo Finance Tickers for US Treasury Yields
    tickers = {
        "^IRX": "13 Week",
        "^FVX": "5 Year",
        "^TNX": "10 Year",
        "^TYX": "30 Year"
    }
    
    current_data = {}
    prev_data = {}
    
    try:
        # Fetch 1mo + extra buffer to ensure we get a point ~30 days ago
        ticker_str = " ".join(tickers.keys())
        hist = yf.download(ticker_str, period="2mo", progress=False)['Close']
        
        if not hist.empty:
            # Latest valid day
            latest = hist.iloc[-1]
            
            # ~30 days ago (simple approximation: look back ~22 trading days)
            # Or find index nearest to today - 30 days
            target_date = datetime.datetime.now() - datetime.timedelta(days=30)
            
            # Find nearest index in hist to target_date
            # abs(hist.index - target_date).argmin()
            
            try:
                # Convert index to datetime if needed (usually it is already)
                # Ensure index is timezone naive or compatible
                idx_pos = hist.index.get_indexer([target_date], method='nearest')[0]
                prev = hist.iloc[idx_pos]
            except:
                 # Fallback: Just take 22 days ago (approx 1 trading month)
                 if len(hist) > 22:
                     prev = hist.iloc[-22]
                 else:
                     prev = hist.iloc[0]

            for symbol, maturity in tickers.items():
                if symbol in latest:
                    current_data[maturity] = float(latest[symbol])
                if symbol in prev:
                    prev_data[maturity] = float(prev[symbol])
            
            # Create DataFrame
            rows = []
            for maturity in tickers.values():
                curr_val = current_data.get(maturity, 0)
                prev_val = prev_data.get(maturity, 0)
                rows.append({
                    "Maturity": maturity,
                    "Yield": curr_val,
                    "Yield 1M Ago": prev_val,
                    "Delta (bps)": (curr_val - prev_val) * 100
                })

            yield_df = pd.DataFrame(rows)
            
            # Sort
            sort_map = {"13 Week": 0.25, "5 Year": 5, "10 Year": 10, "30 Year": 30}
            yield_df['SortKeys'] = yield_df['Maturity'].map(sort_map)
            yield_df = yield_df.sort_values('SortKeys').drop('SortKeys', axis=1)
            
            return yield_df
            
    except Exception as e:
        print(f"Error fetching yields: {e}")
        return pd.DataFrame()

    return pd.DataFrame()

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
