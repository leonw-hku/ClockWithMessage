import streamlit as st
import json
import os
import csv
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Multi-Channel Lab Clock", layout="wide")

# CSS HACK: Stretches the app, hides padding, styles Streamlit native buttons
st.markdown("""
    <style>
        .block-container { 
            padding: 0rem !important; 
            max-width: 100% !important; 
            overflow: hidden !important;
        }
        header { visibility: hidden !important; height: 0px !important; }
        footer { visibility: hidden !important; height: 0px !important; }
        
        .stTabs [data-baseweb="tab-panel"] {
            padding: 0 !important;
            height: calc(100vh - 55px) !important; 
            overflow: hidden !important;
        }

        /* Forces iframe to fit top area, leaving room for Streamlit buttons */
        iframe {
            height: calc(100vh - 120px) !important; 
            width: 100vw !important;
            border: none !important;
            overflow: hidden !important;
        }

        /* Style the Streamlit Native Buttons to look like the previous JS buttons */
        div[data-testid="stButton"] button {
            width: 100%;
            height: 6vh;
            min-height: 50px;
            font-size: min(2vw, 2.5vh) !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #000000 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
            border: none !important;
            transition: transform 0.1s ease-in-out !important;
        }
        div[data-testid="stButton"] button:active {
            transform: scale(0.92) !important;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

SETTINGS_FILE = 'settings.json'
STATES_FILE = 'states.csv'

# --- DEFAULTS ---
DEFAULT_MODES = [
    {"name": "Open", "bg": "#198754", "fg": "#ffffff", "msg": "Lab Open", "time": ""},
    {"name": "Closed", "bg": "#8b0000", "fg": "#ffffff", "msg": "Lab Closed", "time": "17:50"},
    {"name": "Break", "bg": "#ffc107", "fg": "#000000", "msg": "On Break", "time": "13:00"},
    {"name": "Busy Lv1", "bg": "#fd7e14", "fg": "#ffffff", "msg": "Extremely Busy", "time": ""},
    {"name": "Busy Lv100", "bg": "#dc3545", "fg": "#ffffff", "msg": "Extremely Busy Pro Max", "time": ""}
]

DEFAULT_FONTS = {
    "date": "min(15vw, 15vh)",
    "time": "min(45vw, 45vh)",
    "msg": "min(15vw, 15vh)"
}

# --- FILE HANDLERS ---
def init_files():
    # Generate Settings
    if not os.path.exists(SETTINGS_FILE):
        default_data = {
            "fonts": DEFAULT_FONTS,
            "channels": {str(i): list(DEFAULT_MODES) for i in range(1, 6)}
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)
            
    # Generate CSV States (Channel, ModeIndex)
    if not os.path.exists(STATES_FILE):
        with open(STATES_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Channel", "ModeIndex"])
            for i in range(1, 6):
                writer.writerow([str(i), 0])

def load_settings():
    init_files()
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_states():
    init_files()
    states = {}
    with open(STATES_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            states[row["Channel"]] = int(row["ModeIndex"])
    return states

def write_state(channel_str, mode_index):
    states = load_states()
    states[channel_str] = mode_index
    with open(STATES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Channel", "ModeIndex"])
        for ch, idx in states.items():
            writer.writerow([ch, idx])

# --- APP LAYOUT ---
init_files()
current_settings = load_settings()
current_states = load_states()
fonts = current_settings.get("fonts", DEFAULT_FONTS)

# Create Tabs
tabs = st.tabs(["📺 Ch 1", "📺 Ch 2", "📺 Ch 3", "📺 Ch 4", "📺 Ch 5", "⚙️ Settings"])

# --- RENDER 5 DISPLAY CHANNELS ---
for i in range(5):
    with tabs[i]:
        ch_num = str(i + 1)
        ch_modes = current_settings["channels"].get(ch_num, DEFAULT_MODES)
        active_idx = current_states.get(ch_num, 0)
        
        active_mode_json = json.dumps(ch_modes[active_idx])
        all_modes_json = json.dumps(ch_modes)
        
        # 1. HTML Clock Display
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body, html {{
                    margin: 0; padding: 0;
                    width: 100%; height: 100%;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: {ch_modes[active_idx]['bg']};
                    color: {ch_modes[active_idx]['fg']};
                    transition: background-color 0.5s ease, color 0.5s ease;
                    display: flex; flex-direction: column; overflow: hidden; 
                }}
                #content {{
                    flex: 1; display: flex; flex-direction: column;
                    justify-content: center; align-items: center; text-align: center;
                }}
                #date-label {{ font-size: {fonts['date']}; font-weight: 800; line-height: 0.85; margin-bottom: 2vh; opacity: 0.95; letter-spacing: -0.1vw; }}
                #clock-label {{ font-size: {fonts['time']}; font-weight: 800; line-height: 0.85; margin-bottom: 3vh; letter-spacing: -0.2vw; }}
                #msg-label {{ font-size: {fonts['msg']}; font-weight: 700; }}
            </style>
        </head>
        <body>
            <div id="content">
                <div id="date-label"></div>
                <div id="clock-label">00:00:00</div>
                <div id="msg-label">{ch_modes[active_idx]['msg']}</div>
            </div>

            <script>
                const allModes = {all_modes_json};
                let lastCheckedMinute = null;

                function updateClock() {{
                    const now = new Date();
                    
                    const hh = String(now.getHours()).padStart(2, '0');
                    const mm = String(now.getMinutes()).padStart(2, '0');
                    const ss = String(now.getSeconds()).padStart(2, '0');
                    document.getElementById('clock-label').innerText = `${{hh}}:${{mm}}:${{ss}}`;

                    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
                    const dd = String(now.getDate()).padStart(2, '0');
                    const mmm = months[now.getMonth()];
                    const yyyy = now.getFullYear();
                    const weekday = days[now.getDay()];
                    document.getElementById('date-label').innerText = `${{dd}} ${{mmm}} ${{yyyy}} (${{weekday}})`;

                    // Handle Auto-Start instantly on the frontend
                    const currentHM = `${{hh}}:${{mm}}`;
                    if (currentHM !== lastCheckedMinute) {{
                        lastCheckedMinute = currentHM;
                        allModes.forEach((mode, index) => {{
                            if (mode.time === currentHM) {{
                                document.body.style.backgroundColor = mode.bg;
                                document.body.style.color = mode.fg;
                                document.getElementById('msg-label').innerText = mode.msg;
                            }}
                        }});
                    }}
                }}
                setInterval(updateClock, 200); 
                updateClock();
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code)

        # 2. Native Streamlit Buttons for Control
        with st.container():
            st.markdown(f'<div style="background-color: {ch_modes[active_idx]["bg"]}20; padding: 15px; border-radius: 5px;">', unsafe_allow_html=True)
            cols = st.columns(5)
            for btn_idx in range(5):
                btn_name = ch_modes[btn_idx].get("name", f"Mode {btn_idx+1}")
                if cols[btn_idx].button(btn_name, key=f"btn_{ch_num}_{btn_idx}"):
                    write_state(ch_num, btn_idx)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# --- 6. SETTINGS TAB ---
with tabs[5]:
    st.header("⚙️ Multi-Channel Settings")
    
    # 1. Font Settings
    with st.expander("📝 Font Sizes (Applies to all channels)", expanded=False):
        font_cols = st.columns(3)
        date_font = font_cols[0].text_input("Date Font Size", value=fonts["date"])
        time_font = font_cols[1].text_input("Time Font Size", value=fonts["time"])
        msg_font = font_cols[2].text_input("Message Font Size", value=fonts["msg"])
        
        if st.button("💾 Save Fonts"):
            current_settings["fonts"] = {"date": date_font, "time": time_font, "msg": msg_font}
            save_settings(current_settings)
            st.success("Fonts saved!")
            time.sleep(0.5)
            st.rerun()

    st.divider()

    # 2. Channel Specific Modes
    sel_ch = st.selectbox("Select Channel to Edit Modes", ["1", "2", "3", "4", "5"])
    ch_modes = current_settings["channels"].get(sel_ch, DEFAULT_MODES)

    with st.form(f"settings_form_ch_{sel_ch}"):
        st.write(f"Editing Modes for **Channel {sel_ch}**")
        
        new_modes = []
        cols = st.columns([1, 2, 1, 1, 3, 2])
        cols[0].markdown("**Mode #**")
        cols[1].markdown("**Mode Name**")
        cols[2].markdown("**Background**")
        cols[3].markdown("**Text Color**")
        cols[4].markdown("**Message**")
        cols[5].markdown("**Auto Start (HH:MM)**")
        
        for i in range(5):
            mode = ch_modes[i] if i < len(ch_modes) else DEFAULT_MODES[i]
            cols = st.columns([1, 2, 1, 1, 3, 2])
            
            cols[0].markdown(f"### {i+1}")
            name = cols[1].text_input("Name", value=mode.get("name", ""), key=f"name_{sel_ch}_{i}", label_visibility="collapsed")
            bg = cols[2].color_picker("BG", value=mode.get("bg", "#000000"), key=f"bg_{sel_ch}_{i}", label_visibility="collapsed")
            fg = cols[3].color_picker("FG", value=mode.get("fg", "#ffffff"), key=f"fg_{sel_ch}_{i}", label_visibility="collapsed")
            msg = cols[4].text_input("Msg", value=mode.get("msg", ""), key=f"msg_{sel_ch}_{i}", label_visibility="collapsed")
            time_val = cols[5].text_input("Time", value=mode.get("time", ""), key=f"time_{sel_ch}_{i}", label_visibility="collapsed")
            
            new_modes.append({
                "name": name, "bg": bg, "fg": fg, "msg": msg, "time": time_val.strip()
            })
            
        if st.form_submit_button(f"💾 Save Channel {sel_ch} Modes"):
            current_settings["channels"][sel_ch] = new_modes
            save_settings(current_settings)
            st.success(f"Channel {sel_ch} settings saved!")
            time.sleep(0.5)
            st.rerun()

# --- GLOBAL AUTO-SYNC LOOP ---
# This unconditionally re-reads the CSV file and silently updates the app every 10 seconds.
time.sleep(10)
st.rerun()
