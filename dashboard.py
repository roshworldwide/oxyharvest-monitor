import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from curl_cffi import requests
from streamlit_lottie import st_lottie
import time
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OxyHarvest | Enterprise",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# --- 2. CORPORATE THEME CSS ---
st.markdown("""
    <style>
        .stApp {
            background-color: #F4F6F9;
            color: #333333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E0E0E0;
        }
        div.css-1r6slb0, div.stMetric {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            padding: 20px;
            border-radius: 8px;
            color: #333;
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Arial', sans-serif;
            font-size: 48px !important;
            font-weight: 700 !important;
            color: #0F2A4A !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #666666 !important;
            font-size: 14px !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .info-box {
            background: #FFFFFF;
            border-left: 5px solid #007BFF;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-family: 'Segoe UI', sans-serif;
        }
        .info-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }
        .info-value { font-size: 16px; color: #333; font-weight: 600; margin-bottom: 5px; }
        .packet-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        .packet-table td { padding: 8px; border-bottom: 1px solid #eee; }
        .packet-key { color: #666; font-weight: 600; }
        .packet-val { color: #333; text-align: right; }
        
        /* TICKER STYLE */
        .ticker-wrap { position: fixed; bottom: 0; left: 0; width: 100%; height: 35px; line-height: 35px; z-index: 100; transition: background 0.5s ease; }
        .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 40s linear infinite; }
        .ticker-item { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #FFFFFF; padding: 0 50px; text-transform: uppercase; letter-spacing: 1px; }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    </style>
""", unsafe_allow_html=True)

# --- 3. ASSETS & API ---
LOGO_URL = "my_logo.png" 

@st.cache_data(ttl=1) 
def fetch_latest_reading():
    try:
        url = "https://xuva-ncmn-ay0r.m2.xano.io/api:j58-rI7r/Device_Data_By_Device_Id?device_id=100000007aa77c62"
        r = requests.get(url, impersonate="chrome110")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict): df = pd.DataFrame([data])
            else: df = pd.DataFrame(data)
            
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'], unit='ms', errors='coerce')
                if df['created_at'].isnull().all():
                     df['created_at'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                df['created_at'] = datetime.now()
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 4. NAVIGATION & SIDEBAR ---
st.sidebar.title("Control Panel")
auto_refresh = st.sidebar.checkbox("🔴 Live Updates", value=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate:", ["📊 Dashboard", "⚙️ Admin Settings"])

# --- 5. INITIALIZATION ---
if 'static_co2' not in st.session_state: st.session_state['static_co2'] = "*"
if 'static_trees' not in st.session_state: st.session_state['static_trees'] = "*"
if 'client_name' not in st.session_state: st.session_state['client_name'] = "ACME Industries Ltd."
if 'client_loc' not in st.session_state: st.session_state['client_loc'] = "New York, HQ"
if 'history_data' not in st.session_state: st.session_state['history_data'] = pd.DataFrame(columns=['created_at', 'co2'])
if 'packet_buffer' not in st.session_state: st.session_state['packet_buffer'] = []
# New: Force Offline Mode for Demo
if 'force_offline' not in st.session_state: st.session_state['force_offline'] = False

# --- 6. ADMIN SETTINGS ---
if page == "⚙️ Admin Settings":
    st.title("⚙️ System Configuration")
    st.markdown("---")
    
    with st.form("admin_form"):
        st.subheader("Client Details")
        c1, c2 = st.columns(2)
        with c1: new_client = st.text_input("Client Name", value=st.session_state['client_name'])
        with c2: new_loc = st.text_input("Location", value=st.session_state['client_loc'])
            
        st.subheader("Impact Data")
        c3, c4 = st.columns(2)
        with c3: new_co2 = st.text_input("Cumulative CO2", value=st.session_state['static_co2'])
        with c4: new_trees = st.text_input("Tree Equivalence", value=st.session_state['static_trees'])
        
        st.markdown("---")
        # DEMO TOOL: Simulate Offline
        sim_offline = st.checkbox("⚠️ Simulate Device Offline Mode", value=st.session_state['force_offline'])
        
        if st.form_submit_button("Update Dashboard"):
            st.session_state['client_name'] = new_client
            st.session_state['client_loc'] = new_loc
            st.session_state['static_co2'] = new_co2
            st.session_state['static_trees'] = new_trees
            st.session_state['force_offline'] = sim_offline
            st.success("Configuration saved.")

# --- 7. DASHBOARD ---
elif page == "📊 Dashboard":
    
    new_df = fetch_latest_reading()
    
    # OFFLINE LOGIC
    is_offline = False
    status_text = "ONLINE"
    status_label = "Active"
    
    if not new_df.empty:
        curr = new_df.iloc[-1]
        
        # Buffer Logic
        current_ts = str(curr['created_at'])
        st.session_state['packet_buffer'].append(current_ts)
        if len(st.session_state['packet_buffer']) > 3: st.session_state['packet_buffer'].pop(0)
            
        # Check Condition: 3 identical packets OR Force Switch is ON
        if (len(st.session_state['packet_buffer']) == 3 and len(set(st.session_state['packet_buffer'])) == 1) or st.session_state['force_offline']:
            is_offline = True
            status_text = "OFFLINE - CHECK CONNECTION"
            status_label = "Offline"

        # Update History
        last_saved_time = None
        if not st.session_state['history_data'].empty:
            last_saved_time = st.session_state['history_data'].iloc[-1]['created_at']
        if curr['created_at'] != last_saved_time:
             st.session_state['history_data'] = pd.concat([st.session_state['history_data'], new_df[['created_at', 'co2']]]).tail(100)

        # TICKER (FIXED SPACING)
        spacer = "&nbsp;" * 20
        # Added spacer at the END of the string to prevent looping text collision
        if is_offline:
             t_text = (f"⚠️ WARNING: DEVICE OFFLINE {spacer} LAST SEEN: {current_ts} {spacer} CONTACT SUPPORT {spacer}") * 5
        else:
             t_text = (f"SYSTEM STATUS: {status_text} {spacer} DEVICE: 100...7C62 {spacer} AQI: {curr.get('AQI',0)} {spacer} CO2: {curr.get('co2',0)} PPM {spacer} UPDATED: {datetime.now().strftime('%H:%M:%S')} {spacer}") * 5
        
        # Ticker Background: Red if offline, Navy if online
        ticker_bg = "#D32F2F" if is_offline else "#0F2A4A"
        st.markdown(f'<div class="ticker-wrap" style="background: {ticker_bg};"><div class="ticker-move"><span class="ticker-item">{t_text}</span></div></div>', unsafe_allow_html=True)

    # HEADER
    st.markdown("<br>", unsafe_allow_html=True)
    c_logo, c_title, c_info = st.columns([2, 3, 3])
    
    with c_logo:
        try: st.image(LOGO_URL, width=220)
        except: st.warning("Logo missing")
    
    with c_title:
        st.markdown("""
            <div style="font-size: 40px; font-weight: 800; color: #0F2A4A; line-height: 1.2;">
                OXYHARVEST<br>
                <span style="font-size: 18px; font-weight: 400; color: #666;">Enterprise Monitor</span>
            </div>
        """, unsafe_allow_html=True)
        
    with c_info:
        st.markdown(f"""
        <div class="info-box">
            <div style="display: flex; justify-content: space-between;">
                <div><div class="info-label">Client Name</div><div class="info-value">{st.session_state['client_name']}</div></div>
                <div><div class="info-label">Location</div><div class="info-value">{st.session_state['client_loc']}</div></div>
                <div><div class="info-label">Device ID</div><div class="info-value" style="font-family: monospace;">100...7C62</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # METRICS
    if not new_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("AQI Index", f"{curr.get('AQI',0)}", f"Status: {status_label}")
        with c2: st.metric("PM 2.5", f"{curr.get('pm2_5',0)}")
        with c3: st.metric("PM 10", f"{curr.get('pm10',0)}")
        with c4: st.metric("CO2 Levels", f"{curr.get('co2',0)} PPM")
    else:
        st.warning("Connecting...")

    # PLACEHOLDERS
    st.markdown("<br>", unsafe_allow_html=True)
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f"""<div class="css-1r6slb0" style="border-left: 5px solid #28a745;"><div style="font-size: 12px; color: #888; font-weight: bold;">CUMULATIVE CO2 ABSORBED</div><div style="font-size: 36px; font-weight: 800; color: #28a745;">{st.session_state['static_co2']}</div></div>""", unsafe_allow_html=True)
    with i2:
        st.markdown(f"""<div class="css-1r6slb0" style="border-left: 5px solid #28a745;"><div style="font-size: 12px; color: #888; font-weight: bold;">TREE EQUIVALENCE</div><div style="font-size: 36px; font-weight: 800; color: #28a745;">{st.session_state['static_trees']}</div></div>""", unsafe_allow_html=True)

    # CHARTS
    st.markdown("<br>", unsafe_allow_html=True)
    col_chart, col_data = st.columns([2, 1])

    with col_chart:
        st.markdown("**24-Hour CO2 Trend**")
        plot_df = st.session_state['history_data']
        if not plot_df.empty:
            fig = go.Figure()
            # Gray line if offline
            line_color = '#999999' if is_offline else '#0F2A4A'
            fig.add_trace(go.Scatter(x=plot_df['created_at'], y=plot_df['co2'], mode='lines', line=dict(width=3, color=line_color), fill='tozeroy', fillcolor='rgba(15, 42, 74, 0.1)'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=10), height=300, xaxis=dict(showgrid=True, gridcolor='#eee'), yaxis=dict(showgrid=True, gridcolor='#eee'))
            st.plotly_chart(fig, use_container_width=True)

    with col_data:
        st.markdown("**Device Telemetry Packet**")
        if not new_df.empty:
            aqi_c = curr.get('AQI_Color', '#333')
            signal_text = '<span style="color:red;">NO SIGNAL</span>' if is_offline else '<span style="color:green;">Excellent</span>'
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
                <table class="packet-table">
                    <tr><td class="packet-key">Timestamp</td><td class="packet-val">{curr.get('created_at','--')}</td></tr>
                    <tr><td class="packet-key">Uptime</td><td class="packet-val">{curr.get('uptime',0)}s</td></tr>
                    <tr><td class="packet-key">AQI Status</td><td class="packet-val" style="color:{aqi_c}; font-weight:bold;">● {curr.get('AQI',0)}</td></tr>
                    <tr><td class="packet-key">Device Hash</td><td class="packet-val">...7AA77C62</td></tr>
                    <tr><td class="packet-key">Signal</td><td class="packet-val">{signal_text}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    if auto_refresh:
        time.sleep(30)
        st.rerun()