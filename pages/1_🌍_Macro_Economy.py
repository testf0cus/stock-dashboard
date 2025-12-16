import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from macro_data import fetch_yield_curve, fetch_crypto_fear_greed, fetch_market_fear_vix, fetch_economic_data, fetch_basic_market_data, fetch_sector_performance, fetch_high_yield_spread
from auth import check_password

if not check_password():
    st.stop()

st.set_page_config(
    page_title="Macro Economy",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Macro Economic Dashboard")
st.markdown("---")

# --- ROW 1: KEY METRICS ---
col1, col2, col3 = st.columns(3)

# 1. Market Fear (VIX)
with col1:
    st.subheader("📉 Market Fear (VIX)")
    vix_data = fetch_market_fear_vix()
    if vix_data:
        val = vix_data['value']
        prev = vix_data['previous']
        delta = val - prev
        st.metric("VIX Index", f"{val:.2f}", f"{delta:.2f}", delta_color="inverse")
        
        if val < 15:
            st.success("Market Complacent / Greed")
        elif val > 30:
            st.error("Market Fear / High Volatility")
        else:
            st.info("Normal Volatility")
    else:
        st.warning("VIX data unavailable")

# 2. Crypto Sentiment
with col2:
    st.subheader("₿ Crypto Sentiment")
    fg_data = fetch_crypto_fear_greed()
    if fg_data:
        val = fg_data['value']
        label = fg_data['classification']
        
        # Color logic
        color = "red" if val < 25 else "green" if val > 75 else "orange"
        
        st.metric("Fear & Greed Index", f"{val}/100", label)
        st.progress(val / 100)
    else:
        st.warning("API unavailable")

# 3. Reference Rates (Placeholder/Simple)
with col3:
    st.subheader("🏛️ Reference Rates")
    # Hardcoded or fetchable if possible.
    # Showing static info for now as placeholder for FRED integration
    st.markdown("""
    **Fed Funds Rate**: ~4.25% - 4.50%
    **ECB Deposit Rate**: ~3.25%
    **BoJ Policy Rate**: ~0.25%
    """)
    st.caption("*Rates are approximate/latest known.*")

    st.caption("*Rates are approximate/latest known.*")

st.markdown("---")

# --- ROW 2: ECONOMIC HEALTH (v0.2) ---
st.subheader("🇺🇸 US Economic Health")
eco_col1, eco_col2, eco_col3 = st.columns(3)

eco_data = fetch_economic_data()

with eco_col1:
    st.metric("Inflation Rate (CPI YoY)", f"{eco_data['cpi_yoy']}%")
with eco_col2:
    st.metric("Unemployment Rate", f"{eco_data['unemployment']}%")
with eco_col3:
    st.metric("GDP Growth (Ann.)", f"{eco_data['gdp_growth']}%")

st.caption(f"Source: {eco_data['source']}")

st.markdown("---")


st.subheader("📈 US Treasury Yields (Custom: 4M, 8M, 1Y, 3Y, 5Y)")

yield_df = fetch_yield_curve()

if not yield_df.empty:
    # --- High Yield Spread (Replacement for Inversion Check) ---
    hy_data = fetch_high_yield_spread()
    
    col_spread1, col_spread2 = st.columns([1, 2])
    with col_spread1:
        if hy_data:
            st.metric(
                "High Yield Spread (BofA)", 
                f"{hy_data['value']:.2f}%", 
                f"{hy_data['delta']:.2f}%", 
                delta_color="inverse" # Rising spread is bad (red)
            )
        else:
            st.warning("Spread data unavailable")
    
    with col_spread2:
        st.caption("**ICE BofA US High Yield Index Option-Adjusted Spread**")
        st.caption("A proxy for credit risk. Rising spread = Stress/Fear. Falling spread = Confident market.")

    # Plot
    fig = go.Figure()
    
    # Trace 1: Current
    fig.add_trace(go.Scatter(
        x=yield_df['Maturity'], 
        y=yield_df['Yield'], 
        name='Current',
        line=dict(color='#00FF00', width=3),
        mode='lines+markers'
    ))
    
    # Trace 2: 1 Month Ago
    fig.add_trace(go.Scatter(
        x=yield_df['Maturity'], 
        y=yield_df['Yield 1M Ago'], 
        name='1 Month Ago',
        line=dict(color='gray', width=2, dash='dot'),
        mode='lines+markers'
    ))
    
    fig.update_layout(
        title="Yield Curve: Current vs 1 Month Ago",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title="Yield (%)", showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        xaxis=dict(showgrid=False),
        dragmode='pan',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
else:
    st.error("Could not load Yield Curve data.")

st.markdown("---")

# --- ROW 4: GLOBAL MARKETS & SECTORS ---
st.subheader("🌐 Global Markets & Sectors")
gm_col1, gm_col2 = st.columns([1, 2])

with gm_col1:
    st.markdown("#### Key Assets")
    market_data = fetch_basic_market_data()
    
    if "DXY" in market_data:
        d = market_data["DXY"]
        st.metric("🇺🇸 Dollar Index (DXY)", f"{d['price']:.2f}", f"{d['pct']:.2f}%")
        
    if "Gold" in market_data:
        g = market_data["Gold"]
        st.metric("🥇 Gold (Futures)", f"${g['price']:.2f}", f"{g['pct']:.2f}%")
    
    st.info("Performance vs previous close.")

with gm_col2:
    st.markdown("#### 🏗️ Sector Performance (1D)")
    sector_df = fetch_sector_performance()
    
    if not sector_df.empty:
        # Bar Chart
        # Color based on value
        sector_df['Color'] = sector_df['Change (%)'].apply(lambda x: '#00FF00' if x >= 0 else '#FF0000')
        
        fig_sec = px.bar(
            sector_df, 
            x='Change (%)', 
            y='Sector', 
            orientation='h', 
            text_auto='.2f',
            title="S&P 500 Sectors",
        )
        fig_sec.update_traces(marker_color=sector_df['Color'])
        fig_sec.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange="reversed"), # Top performer at top
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            height=400
        )
        st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.warning("Sector data unavailable.")

# End of Dashboard
