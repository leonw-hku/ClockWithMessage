import streamlit as st
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Dynamic Lab Clock", layout="wide")

# STREAMLIT FULLSCREEN HACK
st.markdown("""
    <style>
        .block-container { 
            padding: 0rem !important; 
            max-width: 100% !important; 
        }
        header { visibility: hidden; }
        footer { visibility: hidden; }
        
        /* Forces the tab content area to stretch */
        .stTabs [data-baseweb="tab-panel"] {
            padding: 0 !important;
        }

        /* Forces the HTML iframe to perfectly fit the screen height minus the tab bar */
        iframe[title="streamlit_app.components_v1.html"] {
            height: calc(100vh - 60px) !important;
            width: 100vw !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

SETTINGS_FILE = 'settings.json'

DEFAULT_MODES = [
    {"name": "Open", "bg": "#00d100", "fg": "#ffffff", "msg": "Lab Open", "time": ""},
    {"name": "Closed", "bg": "#8b0000", "fg": "#ffffff", "msg": "Lab Close", "time": "17:30"},
    {"name": "Break", "bg": "#ffa500", "fg": "#000000", "msg": "On Break", "time": "12:00"},
    {"name": "Meeting", "bg": "#0000ff", "fg": "#ffffff", "msg": "In Meeting", "time": "14:00"},
    {"name": "Maintenance", "bg": "#333333", "fg": "#ffffff", "msg": "Maintenance", "time": ""}
]

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_MODES, f, indent=4)
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- APP LAYOUT ---
tab_display, tab_settings = st.tabs(["⏱️ Clock Display", "⚙️ Settings"])

# --- 1. SETTINGS TAB ---
with tab_settings:
    st.header("Configure Clock Modes")
    st.write("Leave the 'Auto Start' field blank if you do not want the clock to trigger automatically.")
    
    current_settings = load_settings()
    new_settings = []
    
    with st.form("settings_form"):
        cols = st.columns([1, 2, 1, 1, 3, 2])
        cols[0].markdown("**Mode #**")
        cols[1].markdown("**Mode Name**")
        cols[2].markdown("**Background**")
        cols[3].markdown("**Text Color**")
        cols[4].markdown("**Message**")
        cols[5].markdown("**Auto Start (HH:MM)**")
        
        for i in range(5):
            mode = current_settings[i] if i < len(current_settings) else DEFAULT_MODES[i]
            cols = st.columns([1, 2, 1, 1, 3, 2])
            
            cols[0].markdown(f"### {i+1}")
            name = cols[1].text_input("Name", value=mode.get("name", ""), key=f"name_{i}", label_visibility="collapsed")
            bg = cols[2].color_picker("BG", value=mode.get("bg", "#000000"), key=f"bg_{i}", label_visibility="collapsed")
            fg = cols[3].color_picker("FG", value=mode.get("fg", "#ffffff"), key=f"fg_{i}", label_visibility="collapsed")
            msg = cols[4].text_input("Msg", value=mode.get("msg", ""), key=f"msg_{i}", label_visibility="collapsed")
            time_val = cols[5].text_input("Time", value=mode.get("time", ""), key=f"time_{i}", placeholder="e.g. 14:30", label_visibility="collapsed")
            
            new_settings.append({
                "name": name, "bg": bg, "fg": fg, "msg": msg, "time": time_val.strip()
            })
            
        if st.form_submit_button("💾 Save Settings"):
            save_settings(new_settings)
            st.success("Settings saved! Go to the 'Clock Display' tab to see changes.")

# --- 2. DISPLAY TAB ---
with tab_display:
    settings_json = json.dumps(load_settings())
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            :root {{
                --bg-color: #000000;
                --font-color: #ffffff;
            }}
            body, html {{
                margin: 0; padding: 0;
                width: 100%; height: 100%;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg-color);
                color: var(--font-color);
                transition: background-color 0.5s ease, color 0.5s ease;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            
            /* Center Content stretches to fill space automatically */
            #content {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 2vw;
            }}
            
            /* MASSIVE, Dynamic Sizing */
            #date-label {{ 
                font-size: min(5vw, 8vh); 
                margin-bottom: 2vh; 
                opacity: 0.9; 
                font-weight: 500;
            }}
            #clock-label {{ 
                font-size: min(20vw, 32vh); 
                font-weight: 800; 
                line-height: 0.85; 
                margin-bottom: 2vh; 
                letter-spacing: -0.2vw;
            }}
            #msg-label {{ 
                font-size: min(8vw, 15vh); 
                font-weight: 700; 
            }}
            
            /* SMALLER, Fluid, Non-Fixed Buttons */
            #controls {{
                display: flex;
                flex-wrap: wrap;       
                justify-content: center;
                align-items: center;
                gap: 1vw;              /* Tighter gap */
                padding: 1.5vh 2vw;    /* Reduced padding footprint */
                background: rgba(0,0,0,0.15);
                width: 100%;
                box-sizing: border-box;
            }}
            
            button {{
                padding: 1vh 1.5vw;
                font-size: min(1.8vw, 2.5vh); /* Smaller text on buttons */
                cursor: pointer;
                border: none; 
                border-radius: 8px; /* Standard pill shape */
                background-color: rgba(255, 255, 255, 0.9); 
                color: #000000;
                font-weight: 700;
                box-shadow: 0 3px 6px rgba(0,0,0,0.3);
                transition: transform 0.1s ease-in-out, background-color 0.2s;
                flex-grow: 1; 
                max-width: 160px; /* Forces them to stay small rather than stretch wildly */
            }}
            button:active {{ 
                transform: scale(0.92); 
            }}
            button:hover {{
                background-color: #ffffff;
            }}
        </style>
    </head>
    <body>
        <div id="content">
            <div id="date-label"></div>
            <div id="clock-label">00:00:00</div>
            <div id="msg-label"></div>
        </div>
        <div id="controls"></div>

        <script>
            const modes = {settings_json};
            let lastCheckedMinute = null;

            function setMode(index) {{
                const mode = modes[index];
                document.documentElement.style.setProperty('--bg-color', mode.bg);
                document.documentElement.style.setProperty('--font-color', mode.fg);
                document.getElementById('msg-label').innerText = mode.msg;
            }}

            const controls = document.getElementById('controls');
            modes.forEach((mode, index) => {{
                const btn = document.createElement('button');
                btn.innerText = mode.name || `Mode ${{index + 1}}`;
                btn.onclick = () => setMode(index);
                controls.appendChild(btn);
            }});

            function updateClock() {{
                const now = new Date();
                
                const hh = String(now.getHours()).padStart(2, '0');
                const mm = String(now.getMinutes()).padStart(2, '0');
                const ss = String(now.getSeconds()).padStart(2, '0');
                document.getElementById('clock-label').innerText = `${{hh}}:${{mm}}:${{ss}}`;

                const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
                const dd = String(now.getDate()).padStart(2, '0');
                const mmm = months[now.getMonth()];
                const yyyy = now.getFullYear();
                const weekday = days[now.getDay()];
                document.getElementById('date-label').innerText = `${{dd}} ${{mmm}} ${{yyyy}} (${{weekday}})`;

                const currentHM = `${{hh}}:${{mm}}`;
                if (currentHM !== lastCheckedMinute) {{
                    lastCheckedMinute = currentHM;
                    modes.forEach((mode, index) => {{
                        if (mode.time === currentHM) {{
                            setMode(index);
                        }}
                    }});
                }}
            }}

            setMode(0);
            setInterval(updateClock, 200); 
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(html_code, height=800)
