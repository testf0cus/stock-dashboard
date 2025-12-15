import yfinance as yf

def analyze_fundamental(ticker_symbol):
    """
    Extracts fundamental data for a given ticker.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Valuation Metrics
        valuation = {
            "Price": info.get("currentPrice", "N/A"),
            "Market Cap": info.get("marketCap", "N/A"),
            "Trailing P/E": info.get("trailingPE", "N/A"),
            "Forward P/E": info.get("forwardPE", "N/A"),
            "PEG Ratio": info.get("pegRatio", "N/A"),
            "Price/Book": info.get("priceToBook", "N/A"),
        }
        
        # Profitability
        profitability = {
            "ROE": info.get("returnOnEquity", "N/A"),
            "ROA": info.get("returnOnAssets", "N/A"),
            "Profit Margin": info.get("profitMargins", "N/A"),
            "Operating Margin": info.get("operatingMargins", "N/A"),
        }
        
        # Financial Health
        health = {
            "Total Debt/Equity": info.get("debtToEquity", "N/A"),
            "Current Ratio": info.get("currentRatio", "N/A"),
            "Quick Ratio": info.get("quickRatio", "N/A"),
            "Free Cash Flow": info.get("freeCashflow", "N/A"),
        }
        
        # Growth (some might be missing)
        growth = {
            "Revenue Growth": info.get("revenueGrowth", "N/A"),
            "Earnings Growth": info.get("earningsGrowth", "N/A"),
        }
        
        return {
            "valid": True,
            "valuation": valuation,
            "profitability": profitability,
            "health": health,
            "growth": growth,
            "currency": info.get("currency", "USD")
        }
    except Exception as e:
        return {"valid": False, "message": str(e)}

def format_large_number(num):
    if isinstance(num, (int, float)):
        if num >= 1e12:
            return f"{num/1e12:.2f}T"
        elif num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif num >= 1e6:
            return f"{num/1e6:.2f}M"
        return f"{num:,.2f}"
    return num
