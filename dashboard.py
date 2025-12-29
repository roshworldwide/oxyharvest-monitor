import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from curl_cffi import requests
from streamlit_lottie import st_lottie
import time
from datetime import datetime, timedelta

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OxyHarvest | Genpact Monitor",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# --- 2. THEME CSS (White BG + Gray Cards) ---
st.markdown("""
    <style>
        /* MAIN BACKGROUND: Pure White */
        .stApp {
            background-color: #FFFFFF;
            color: #333333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* HIDE UI ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #F8F9FA;
            border-right: 1px solid #E0E0E0;
        }

        /* CARDS: Light Gray to contrast with White BG */
        div.css-1r6slb0, div.stMetric {
            background: #F4F6F9; /* Light Gray */
            border: 1px solid #E0E0E0;
            box-shadow: none; /* Flat corporate look */
            padding: 20px;
            border-radius: 8px;
            color: #333;
        }
        
        /* METRIC VALUES */
        div[data-testid="stMetricValue"] {
            font-family: 'Arial', sans-serif;
            font-size: 48px !important;
            font-weight: 700 !important;
            color: #0F2A4A !important; /* Corporate Navy */
        }
        div[data-testid="stMetricLabel"] {
            color: #666666 !important;
            font-size: 14px !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* INFO BOX */
        .info-box {
            background: #F4F6F9; /* Match cards */
            border-left: 5px solid #007BFF;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Segoe UI', sans-serif;
        }
        .info-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }
        .info-value { font-size: 16px; color: #333; font-weight: 600; margin-bottom: 5px; }

        /* TABLE */
        .packet-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .packet-table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .packet-key { color: #666; font-weight: 600; }
        .packet-val { color: #333; text-align: right; }
        
        /* TICKER */
        .ticker-wrap { position: fixed; bottom: 0; left: 0; width: 100%; height: 35px; line-height: 35px; z-index: 100; transition: background 0.5s ease; }
        .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 40s linear infinite; }
        .ticker-item { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #FFFFFF; padding: 0 50px; text-transform: uppercase; letter-spacing: 1px; }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    </style>
""", unsafe_allow_html=True)

# --- 3. ASSETS & UTILS ---
LOGO_URL = "my_logo.png"

def get_ist_time(dt_obj=None):
    """Converts UTC/Server time to IST (UTC+5:30)"""
    if dt_obj is None:
        dt_obj = datetime.utcnow()
    return dt_obj + timedelta(hours=5, minutes=30)

@st.cache_data(ttl=1) 
def fetch_latest_reading():
    try:
        url = "https://xuva-ncmn-ay0r.m2.xano.io/api:j58-rI7r/Device_Data_By_Device_Id?device_id=100000007aa77c62"
        r = requests.get(url, impersonate="chrome110")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict): df = pd.DataFrame([data])
            else: df = pd.DataFrame(data)
            
            # Timestamp Handling
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'], unit='ms', errors='coerce')
                # Fallback to timestamp field if created_at is empty
                if df['created_at'].isnull().all() and 'timestamp' in df.columns:
                     df['created_at'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                df['created_at'] = datetime.utcnow()
            
            # Convert the dataframe column to IST for display consistency
            # (Simplification: We add 5.30h to the UTC timestamp)
            df['created_at'] = df['created_at'] + timedelta(hours=5, minutes=30)
            
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 4. NAVIGATION ---
st.sidebar.title("Control Panel")
auto_refresh = st.sidebar.checkbox("🔴 Live Updates", value=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate:", ["📊 Dashboard", "⚙️ Admin Settings"])

# --- 5. INITIALIZATION ---
if 'static_co2' not in st.session_state: st.session_state['static_co2'] = "*"
if 'static_trees' not in st.session_state: st.session_state['static_trees'] = "*"
if 'client_name' not in st.session_state: st.session_state['client_name'] = "Genpact"
if 'client_loc' not in st.session_state: st.session_state['client_loc'] = "Phase - V, Gurgaon"
if 'history_data' not in st.session_state: st.session_state['history_data'] = pd.DataFrame(columns=['created_at', 'co2'])
if 'packet_buffer' not in st.session_state: st.session_state['packet_buffer'] = [] # Stores (id, timestamp) tuples
if 'force_offline' not in st.session_state: st.session_state['force_offline'] = False

# --- 6. ADMIN PAGE ---
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
        sim_offline = st.checkbox("⚠️ Simulate Device Offline Mode", value=st.session_state['force_offline'])
        if st.form_submit_button("Update Dashboard"):
            st.session_state['client_name'] = new_client
            st.session_state['client_loc'] = new_loc
            st.session_state['static_co2'] = new_co2
            st.session_state['static_trees'] = new_trees
            st.session_state['force_offline'] = sim_offline
            st.success("Saved!")

# --- 7. DASHBOARD ---
elif page == "📊 Dashboard":
    new_df = fetch_latest_reading()
    
    # VARS
    is_offline = False
    status_label = "Active" # Metric label
    signal_status = "Excellent" # Table status
    
    current_ist_time_str = get_ist_time().strftime('%H:%M:%S')

    if not new_df.empty:
        curr = new_df.iloc[-1]
        
        # --- OFFLINE LOGIC ---
        # We track a tuple: (Packet ID, Timestamp)
        # If we see the exact same tuple 3 times, data is stale.
        packet_signature = (curr.get('id', 0), str(curr['created_at']))
        
        st.session_state['packet_buffer'].append(packet_signature)
        if len(st.session_state['packet_buffer']) > 3: 
            st.session_state['packet_buffer'].pop(0)
            
        # Check if all 3 signatures in buffer are identical
        if (len(st.session_state['packet_buffer']) == 3 and len(set(st.session_state['packet_buffer'])) == 1) or st.session_state['force_offline']:
            is_offline = True
            status_label = "Offline"
            signal_status = "OFFLINE"

        # --- HISTORY UPDATE ---
        last_saved_time = None
        if not st.session_state['history_data'].empty:
            last_saved_time = st.session_state['history_data'].iloc[-1]['created_at']
        if curr['created_at'] != last_saved_time:
             st.session_state['history_data'] = pd.concat([st.session_state['history_data'], new_df[['created_at', 'co2']]]).tail(100)

        # --- TICKER ---
        spacer = "&nbsp;" * 20
        if is_offline:
             t_text = (f"⚠️ ALERT: DEVICE OFFLINE {spacer} LAST PACKET ID: {curr.get('id','N/A')} {spacer} CHECK POWER & NETWORK {spacer}") * 5
             ticker_bg = "#D32F2F" # Red
        else:
             t_text = (f"SYSTEM STATUS: ONLINE {spacer} LOCATION: {st.session_state['client_loc']} {spacer} AQI: {curr.get('AQI',0)} {spacer} CO2: {curr.get('co2',0)} PPM {spacer} IST TIME: {current_ist_time_str} {spacer}") * 5
             ticker_bg = "#0F2A4A" # Navy
        
        st.markdown(f'<div class="ticker-wrap" style="background: {ticker_bg};"><div class="ticker-move"><span class="ticker-item">{t_text}</span></div></div>', unsafe_allow_html=True)

    # --- HEADER ---
    st.markdown("<br>", unsafe_allow_html=True)
    c_logo, c_title, c_info = st.columns([2, 3, 3])
    
    with c_logo:
        try: 
            # INCREASED LOGO SIZE TO 280
            st.image(LOGO_URL, width=280)
        except: st.error("Logo missing")
    
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

    # --- METRICS ---
    if not new_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        # AQI Metric Label updates to "Status: Offline" if needed
        with c1: st.metric("AQI Index", f"{curr.get('AQI',0)}", f"Status: {status_label}", delta_color="off")
        with c2: st.metric("PM 2.5", f"{curr.get('pm2_5',0)}")
        with c3: st.metric("PM 10", f"{curr.get('pm10',0)}")
        with c4: st.metric("CO2 Levels", f"{curr.get('co2',0)} PPM")
    else:
        st.warning("Waiting for data stream...")

    # --- IMPACT PLACEHOLDERS ---
    st.markdown("<br>", unsafe_allow_html=True)
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f"""<div class="css-1r6slb0" style="border-left: 5px solid #28a745;"><div style="font-size: 12px; color: #888; font-weight: bold;">CUMULATIVE CO2 ABSORBED</div><div style="font-size: 36px; font-weight: 800; color: #28a745;">{st.session_state['static_co2']}</div></div>""", unsafe_allow_html=True)
    with i2:
        st.markdown(f"""<div class="css-1r6slb0" style="border-left: 5px solid #28a745;"><div style="font-size: 12px; color: #888; font-weight: bold;">TREE EQUIVALENCE</div><div style="font-size: 36px; font-weight: 800; color: #28a745;">{st.session_state['static_trees']}</div></div>""", unsafe_allow_html=True)

    # --- CHARTS & TELEMETRY ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_chart, col_data = st.columns([2, 1])

    with col_chart:
        st.markdown("**24-Hour CO2 Trend**")
        plot_df = st.session_state['history_data']
        if not plot_df.empty:
            fig = go.Figure()
            # Line is Gray if offline, Navy if online
            line_color = '#999999' if is_offline else '#0F2A4A'
            fig.add_trace(go.Scatter(
                x=plot_df['created_at'], 
                y=plot_df['co2'], 
                mode='lines', 
                name='CO2',
                line=dict(width=3, color=line_color),
                fill='tozeroy', 
                fillcolor='rgba(15, 42, 74, 0.05)' # Very light fill
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(l=0,r=0,t=10,b=10), 
                height=300, 
                xaxis=dict(showgrid=True, gridcolor='#eee'), 
                yaxis=dict(showgrid=True, gridcolor='#eee')
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_data:
        st.markdown("**Device Telemetry Packet**")
        if not new_df.empty:
            aqi_c = curr.get('AQI_Color', '#333')
            
            # Logic for signal text color
            if is_offline:
                sig_html = '<span style="color:red; font-weight:bold;">OFFLINE</span>'
            else:
                sig_html = '<span style="color:green; font-weight:bold;">Excellent</span>'
            
            # Format Timestamp for Table (IST)
            ts_display = curr['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            st.markdown(f"""
            <div style="background: #F4F6F9; border: 1px solid #E0E0E0; padding: 15px; border-radius: 8px;">
                <table class="packet-table">
                    <tr><td class="packet-key">Timestamp (IST)</td><td class="packet-val">{ts_display}</td></tr>
                    <tr><td class="packet-key">Packet ID</td><td class="packet-val">{curr.get('id','--')}</td></tr>
                    <tr><td class="packet-key">Uptime</td><td class="packet-val">{curr.get('uptime',0)}s</td></tr>
                    <tr><td class="packet-key">AQI Status</td><td class="packet-val" style="color:{aqi_c}; font-weight:bold;">● {curr.get('AQI',0)}</td></tr>
                    <tr><td class="packet-key">Signal Strength</td><td class="packet-val">{sig_html}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    if auto_refresh:
        time.sleep(30)
        st.rerun()