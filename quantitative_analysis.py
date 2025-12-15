import pandas as pd
import numpy as np

def analyze_quantitative(df):
    """
    Calculates quantitative metrics from historical price data.
    """
    if len(df) < 50:
        return {"valid": False, "message": "Need more data for Quant analysis"}

    df = df.copy()
    close_prices = df['Close']
    
    # Daily Returns
    returns = close_prices.pct_change().dropna()
    
    if len(returns) < 2:
        return {"valid": False, "message": "Insufficient data"}
        
    # 1. Volatility (Annualized)
    # Assuming daily data (252 trading days)
    # If data is minute/hour, we need to adjust, but yf.download usually gives us what we ask.
    # We'll assume the input 'df' passed is the High-Res one, BUT typically Quant stats 
    # are best done on Daily candles for standard interpretation.
    
    # We will compute stats on the provided data, noting the frequency is important.
    # For robust simple stats, we'll calculate basic distribution metrics.
    
    volatility = returns.std() * np.sqrt(252) # Standard annualized assumption
    
    # 2. Distribution
    skewness = returns.skew()
    kurtosis = returns.kurtosis()
    
    # 3. Performance
    total_return = (close_prices.iloc[-1] / close_prices.iloc[0]) - 1
    
    # Sharpe Ratio Proxy (Risk Free Rate = 2% approx 0.02)
    risk_free_daily = 0.02 / 252
    excess_return = returns - risk_free_daily
    sharpe_ratio = (excess_return.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
    
    # 4. VaR (Value at Risk) - 95% Confidence
    var_95 = np.percentile(returns, 5)
    
    return {
        "valid": True,
        "metrics": {
            "Annualized Volatility": f"{volatility:.2%}",
            "Skewness": f"{skewness:.2f}",
            "Kurtosis": f"{kurtosis:.2f}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "VaR (95%)": f"{var_95:.2%}",
            "Total Return (Period)": f"{total_return:.2%}"
        },
        "count": len(returns)
    }
