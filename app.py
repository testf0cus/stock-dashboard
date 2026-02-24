import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd
import numpy as np

import requests
from tickers_data import TICKERS

# Page config
st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- LOGIN SYSTEM ---
from auth import check_password

if not check_password():
    st.stop()

# --- WELCOME PAGE ---
if "welcome_seen" not in st.session_state:
    st.session_state["welcome_seen"] = False

if not st.session_state["welcome_seen"]:
    st.markdown(
        """
        <style>
            /* Hide sidebar and default Streamlit elements on welcome page */
            [data-testid="stSidebar"] { display: none; }
            header { display: none; }
            #MainMenu { display: none; }
            footer { display: none; }
        </style>
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
            padding: 2rem;
        ">
            <div style="
                background: #fffbeb;
                border: 2px solid #f59e0b;
                border-radius: 16px;
                padding: 3rem 2.5rem;
                max-width: 700px;
                width: 100%;
                box-shadow: 0 4px 24px rgba(245, 158, 11, 0.15);
                text-align: center;
            ">
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">⚠️</div>
                <h2 style="
                    color: #92400e;
                    font-size: 1.6rem;
                    font-weight: 700;
                    margin: 0 0 1.2rem 0;
                ">
                    Desarrollo pausado
                </h2>
                <p style="
                    color: #78350f;
                    font-size: 1.1rem;
                    font-weight: 400;
                    line-height: 1.8;
                    margin: 0;
                ">
                    He encontrado una web que hace exactamente lo que quiero replicar pero 100 veces más avanzado y te da la clave del éxito.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        if st.button("Continuar →", use_container_width=True):
            st.session_state["welcome_seen"] = True
            st.rerun()
    st.stop()


def search_yahoo(query):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        "q": query,
        "quotesCount": 10,
        "newsCount": 0,
        "enableFuzzyQuery": "false",
        "quotesQueryId": "tss_match_phrase_query"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if 'quotes' in data:
            results = {}
            for q in data['quotes']:
                symbol = q.get('symbol')
                shortname = q.get('shortname', symbol)
                exch = q.get('exchange', 'N/A')
                label = f"{shortname} ({symbol}) - {exch}"
                results[label] = symbol
            return results
    except Exception:
        pass
    return {}

# Title
st.title("📈 Stock Market Dashboard")

# Sidebar
st.sidebar.header("User Input")

# Search Logic
search_query = st.sidebar.text_input("Search Asset (e.g. XRP, Apple)", value="")

if search_query:
    # clear session state if search changes? Streamlit handles re-runs.
    search_results = search_yahoo(search_query)
    
    if search_results:
        selected_label = st.sidebar.selectbox("Search Results", list(search_results.keys()), index=0)
        ticker = search_results[selected_label]
    else:
        st.sidebar.warning("No results found.")
        ticker = "AAPL" # Fallback or keep previous?
else:
    # Default to Popular List
    ticker_options = list(TICKERS.keys())
    selected_label = st.sidebar.selectbox("Select Asset (Popular)", ticker_options, index=0)
    
    if TICKERS[selected_label] == "CUSTOM":
         ticker = st.sidebar.text_input("Enter Custom Ticker", value="AAPL")
    else:
        ticker = TICKERS[selected_label]

# Timeframe Selector
col_tf1, col_tf2 = st.sidebar.columns(2)
with col_tf1:
    timeframe = st.selectbox("Timeframe", ["1H", "4H", "1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "Max"], index=2)
with col_tf2:
    chart_type = st.selectbox("Chart Type", ["Mountain", "Candle", "Line"], index=1)

from plotly.subplots import make_subplots
from technical_analysis import analyze_technical, add_indicators
from fundamental_analysis import analyze_fundamental, format_large_number
from quantitative_analysis import analyze_quantitative
from news_service import fetch_general_news

# Map timeframe to yfinance arguments
# STRATEGY: Fetch MORE data than needed for valid indicators, then slice for view.
fetch_params = {
    "1H": {"period": "5d", "interval": "1m"},   # Need days for indicators on 1m
    "4H": {"period": "5d", "interval": "5m"},   # Need days for indicators on 5m
    "1D": {"period": "5d", "interval": "1m"},  
    "5D": {"period": "1mo", "interval": "15m"}, # 1 month history for 5D view?
    "1M": {"period": "6mo", "interval": "1h"},
    "6M": {"period": "2y", "interval": "1d"},
    "YTD": {"period": "2y", "interval": "1d"},
    "1Y": {"period": "2y", "interval": "1d"},
    "5Y": {"period": "10y", "interval": "1wk"},
    "Max": {"period": "max", "interval": "1wk"},
}

# --- SIDEBAR RESOURCES ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Official Resources")

with st.sidebar.expander("🏛️ Central Banks & Rates"):
    st.markdown("• [Federal Reserve (FED)](https://www.federalreserve.gov/)")
    st.markdown("• [FRED Data (St. Louis)](https://fred.stlouisfed.org)")
    st.markdown("• [FED Rates Monitor](https://es.investing.com/central-banks/fed-rate-monitor)")
    st.markdown("• [NY Fed Repo](https://www.newyorkfed.org/markets/desk-operations/repo)")
    st.markdown("• [NY Fed Reverse Repo](https://www.newyorkfed.org/markets/desk-operations/reverse-repo)")
    st.markdown("• [US Gov Bonds Yields](https://es.investing.com/rates-bonds/usa-government-bonds)")
    st.markdown("• [Euribor Rates](https://www.euribor-rates.eu/es/graficos-del-euribor/)")
    st.markdown("• [ECB (Europe)](https://www.ecb.europa.eu/home/html/index.en.html)")
    st.markdown("• [US Treasury](https://home.treasury.gov/)")

with st.sidebar.expander("📈 Yield Curve (FRED)"):
    st.caption("Official Data Series:")
    st.markdown("• [10Y - 3M Spread](https://fred.stlouisfed.org/series/T10Y3M)")
    st.markdown("• [10Y - 2Y Spread](https://fred.stlouisfed.org/series/T10Y2Y)")
    st.markdown("• [Effective Fed Funds](https://fred.stlouisfed.org/series/FEDFUNDS)")

with st.sidebar.expander("🧠 Sentiment & Psychology"):
    st.markdown("• [Fear & Greed (Stocks)](https://edition.cnn.com/markets/fear-and-greed)")
    st.markdown("• [Fear & Greed (Crypto)](https://alternative.me/crypto/fear-and-greed-index/)")
    st.markdown("• [Put/Call Ratio](https://en.macromicro.me/charts/449/us-cboe-options-put-call-ratio)")
    st.markdown("• [BTC Open Interest](https://es.coinalyze.net/bitcoin/open-interest)")
    st.markdown("• [The Kobeissi Letter](https://x.com/KobeissiLetter)")

with st.sidebar.expander("📰 News & Analysis"):
    st.markdown("• [Real Inv. Advice](https://realinvestmentadvice.com/resources/newsletter/)")
    st.markdown("• [Bloomberg Markets](https://www.bloomberg.com/markets)")
    st.markdown("• [Reuters Finance](https://www.reuters.com/finance)")
    st.markdown("• [Financial Times](https://www.ft.com/)")
    st.markdown("• [CNBC Investing](https://www.cnbc.com/investing/)")

with st.sidebar.expander("🛢️ Commodities & Energy"):
    st.markdown("• [Gas Storage (GIE ALSI)](https://alsi.gie.eu/)")
    st.markdown("• [Gas Inventory (GIE AGSI)](https://agsi.gie.eu/)")
    st.markdown("• [EIA Petroleum Status](https://www.eia.gov/petroleum/supply/weekly/)")
    st.markdown("• [OPEC Basket Price](https://www.opec.org/opec_web/en/data_graphs/40.htm)")

st.sidebar.markdown("---")
st.sidebar.caption("© 2025 Stock_dashboard. Todos los derechos reservados. | v0.2")

# Fetch Data
if ticker:
    try:
        params = fetch_params[timeframe]
        # Always fetch data
        full_data = yf.download(ticker, period=params["period"], interval=params["interval"], progress=False)
        
        if not full_data.empty:
            # Flatten MultiIndex columns if present
            if isinstance(full_data.columns, pd.MultiIndex):
                full_data.columns = full_data.columns.get_level_values(0)

            # --- CALCULATE INDICATORS ON FULL DATA ---
            # This ensures RSI/SMA are accurate even for the start of the view
            full_data = add_indicators(full_data)

            # --- SLICE FOR VIEW ---
            # Now we slice the dataframe to show only the requested timeframe
            if timeframe == "1H":
                data = full_data.tail(60) # Last 60 minutes
            elif timeframe == "4H":
                data = full_data.tail(48) # Last 48*5m = 4 hours
            elif timeframe == "1D":
                # Filter for today only? Or last 24h? Yahoo "1D" is usually current session.
                # Simple approach: Tail of approx 1 trading day (6.5h * 60m ~ 390)
                data = full_data.tail(390) 
            elif timeframe == "5D":
                data = full_data.tail(390 * 5 // 15) # Approx 5 days of 15m candles
            else:
                data = full_data # Use full fetch for longer periods
            
            if data.empty:
                st.warning("Not enough data for this timeframe.")
                st.stop()

            # Get Latest Price and Previous Close for Color logic
            latest_close = data['Close'].iloc[-1]
            price_val = float(latest_close)
            
            # Determine reference price
            previous_close = data['Close'].iloc[0] # Start of the View
            delta = price_val - previous_close
            pct_change = (delta / previous_close) * 100
            
            # Color Logic
            chart_color = '#00C805' if delta >= 0 else '#FF5000' # Yahoo Green / Red
            
            # Header
            col_metric, col_dummy = st.columns([1, 2])
            with col_metric:
                st.metric(
                    label=f"{ticker}", 
                    value=f"{price_val:.2f}", 
                    delta=f"{delta:.2f} ({pct_change:.2f}%)"
                )

            # --- PLOTTING WITH SUBPLOTS ---
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.03, 
                row_heights=[0.7, 0.3]
            )

            # MAIN CHART (Row 1)
            if chart_type == "Candle":
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='OHLC'
                ), row=1, col=1)
            elif chart_type == "Line":
                 fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    name='Close',
                    line=dict(color=chart_color, width=2)
                ), row=1, col=1)
            else: # Mountain
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    fill='tozeroy',
                    name='Close',
                    line=dict(color=chart_color, width=2),
                    fillcolor=f"rgba({int(chart_color[1:3], 16)}, {int(chart_color[3:5], 16)}, {int(chart_color[5:7], 16)}, 0.1)"
                ), row=1, col=1)

            # RSI CHART (Row 2)
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ), row=2, col=1)
            
            # RSI Bands
            fig.add_hline(y=70, line_dash="dash", line_color="gray", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="gray", row=2, col=1)
            
            # Layout customization
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, showline=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', side='right'), # Price Axis
                yaxis2=dict(title="RSI", range=[0, 100], showgrid=True, gridcolor='rgba(128,128,128,0.2)', side='right'), # RSI Axis
                hovermode='x unified',
                dragmode='pan',
                xaxis_rangeslider_visible=False, # Disable rangeslider
                height=600 # Taller for subplots
            )
            
            # Enable scroll zoom
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

            
            # --- ANALYSIS TABS ---
            st.markdown("### 🔍 Deep Dive Analysis")
            tab_tech, tab_fund, tab_quant = st.tabs(["📉 Technical", "🏛️ Fundamental", "🔢 Quantitative"])
            
            # 1. Technical Analysis Tab
            with tab_tech:
                # Use the FULL calculated data for analysis
                tech_report = analyze_technical(full_data) 
                
                if tech_report["valid"]:
                    col_tech1, col_tech2, col_tech3 = st.columns(3)
                    
                    with col_tech1:
                        st.markdown("#### ⚡ Trend & Momentum")
                        st.write(f"**Trend:** {tech_report['trend']}")
                        
                        rsi = tech_report['rsi']
                        rsi_color = "red" if rsi > 70 else "green" if rsi < 30 else "orange"
                        st.write(f"**RSI (14):** :{rsi_color}[{rsi:.1f}]")
                        if rsi > 70: st.caption("Warning: Overbought")
                        elif rsi < 30: st.caption("Opportunity: Oversold")
                        else: st.caption("Neutral Zone")

                    with col_tech2:
                         st.markdown("#### 🛡️ Sup/Res Keys")
                         st.write(f"**Resistance (High):** ${tech_report['resistance']:.2f}")
                         st.write(f"**Support (Low):** ${tech_report['support']:.2f}")
                         st.write(f"**SMA 50:** ${tech_report['sma_50']:.2f}" if not np.isnan(tech_report['sma_50']) else "N/A")
                    
                    with col_tech3:
                        st.markdown("#### 🕯️ Price Action")
                        st.write(f"**Volume:** {tech_report['volume_status']}")
                        st.write(f"**Latest Candle:** {tech_report['pattern']}")
                        
                        macd_val = tech_report['macd']
                        sig_val = tech_report['macd_signal']
                        macd_status = "Bullish Cross" if macd_val > sig_val else "Bearish"
                        st.write(f"**MACD:** {macd_status}")

                else:
                    st.info(f"Technical Analysis not available: {tech_report['message']}")

            # 2. Fundamental Analysis Tab
            with tab_fund:
                fund_report = analyze_fundamental(ticker)
                
                if fund_report["valid"]:
                    curr = fund_report['currency']
                    col_f1, col_f2, col_f3 = st.columns(3)
                    
                    with col_f1:
                        st.markdown("#### 💰 Valuation")
                        val = fund_report['valuation']
                        st.write(f"**Market Cap:** {format_large_number(val['Market Cap'])}")
                        st.write(f"**Trailing P/E:** {val['Trailing P/E']}")
                        st.write(f"**Forward P/E:** {val['Forward P/E']}")
                        st.write(f"**Price/Book:** {val['Price/Book']}")
                        st.write(f"**PEG Ratio:** {val['PEG Ratio']}")
                        
                    with col_f2:
                        st.markdown("#### 🏭 Profitability & Growth")
                        prof = fund_report['profitability']
                        grow = fund_report['growth']
                        st.write(f"**Profit Margin:** {prof['Profit Margin'] * 100 if isinstance(prof['Profit Margin'], float) else prof['Profit Margin']}%")
                        st.write(f"**ROE:** {prof['ROE'] * 100 if isinstance(prof['ROE'], float) else prof['ROE']}%")
                        st.write(f"**Rev Growth:** {grow['Revenue Growth'] * 100 if isinstance(grow['Revenue Growth'], float) else grow['Revenue Growth']}%")

                    with col_f3:
                        st.markdown("#### 🏥 Financial Health")
                        health = fund_report['health']
                        st.write(f"**Debt/Equity:** {health['Total Debt/Equity']}")
                        st.write(f"**Current Ratio:** {health['Current Ratio']}")
                        st.write(f"**Free Cash Flow:** {format_large_number(health['Free Cash Flow'])}")

                else:
                    st.warning(f"Fundamental data not available: {fund_report['message']}")
                    st.caption("Note: Fundamental data is usually available for stocks/equities, not crypto or indices.")

            # 3. Quantitative Analysis Tab
            with tab_quant:
                quant_report = analyze_quantitative(full_data)
                
                if quant_report["valid"]:
                    q_metrics = quant_report['metrics']
                    col_q1, col_q2 = st.columns(2)
                    
                    with col_q1:
                        st.markdown("#### 📊 Risk Metrics")
                        st.write(f"**Annualized Volatility:** {q_metrics['Annualized Volatility']}")
                        st.write(f"**Sharpe Ratio:** {q_metrics['Sharpe Ratio']}")
                        st.write(f"**VaR (95%):** {q_metrics['VaR (95%)']}")
                        
                    with col_q2:
                        st.markdown("#### 📉 Distribution & Return")
                        st.write(f"**Total Return (in view):** {q_metrics['Total Return (Period)']}")
                        st.write(f"**Skewness:** {q_metrics['Skewness']}")
                        st.write(f"**Kurtosis:** {q_metrics['Kurtosis']}")
                    
                    st.caption("*Metrics calculated based on the loaded data period.*")
                else:
                     st.info("Insufficient data for quantitative metrics.")

            st.write("---")
            
             # Raw Data Expander
            with st.expander("View Raw Data"):
                st.write(data)

            # Company Info & News
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Latest News")
                
                news_tab1, news_tab2 = st.tabs([f"📌 {ticker} News", "🌍 Global Markets"])
                
                with news_tab1:
                     try:
                        stock = yf.Ticker(ticker)
                        news = stock.news
                        # Handle new yfinance news structure
                        for item in news[:10]: # Increased to 10 items
                            title = item.get('title')
                            link = item.get('link')
                            
                            # Fallback for nested 'content' structure
                            if not title and 'content' in item:
                                content = item['content']
                                title = content.get('title')
                                link_obj = content.get('clickThroughUrl')
                                if link_obj:
                                    link = link_obj.get('url')
                            
                            if title and link:
                                # Yahoo Style News Card
                                st.markdown(f"""
                                <div style="border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px;">
                                    <a href="{link}" target="_blank" style="text-decoration: none; font-weight: bold; font-size: 16px;">{title}</a>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                provider = item.get('provider', {}).get('displayName') 
                                if not provider and 'content' in item:
                                    provider = item['content'].get('provider', {}).get('displayName')
                                
                                if provider:
                                    st.caption(f"Source: {provider}")
                     except Exception as e:
                        st.error(f"Could not fetch ticker news: {e}")

                with news_tab2:
                    with st.spinner("Fetching global headlines..."):
                        global_news = fetch_general_news()
                        if global_news:
                            for item in global_news:
                                st.markdown(f"""
                                <div style="border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px;">
                                    <span style="color: #FF4B4B; font-weight: bold; font-size: 0.8em;">{item['source']}</span><br>
                                    <a href="{item['link']}" target="_blank" style="text-decoration: none; font-weight: bold; font-size: 16px;">{item['title']}</a>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning("No global news found at the moment.")

            with col2:
                st.subheader("Company Info")
                try:
                    info = stock.info
                    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                    st.write(f"**Summary:** {info.get('longBusinessSummary', 'N/A')[:200]}...")
                except Exception as e:
                    st.error(f"Could not fetch info: {e}")

        else:
            st.error("No data found for this ticker. Please check the symbol.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
else:
    st.info("Please enter a stock ticker to begin.")
