import streamlit as st
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Dynamic Lab Clock", layout="wide")

# Hide extra Streamlit padding to make the clock as big as possible
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 0rem; }
        header { visibility: hidden; }
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
    
    # Create a form to hold the 5 modes
    with st.form("settings_form"):
        # Header Row
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
            
        submitted = st.form_submit_button("💾 Save Settings")
        if submitted:
            save_settings(new_settings)
            st.success("Settings saved! Go to the 'Clock Display' tab to see changes.")


# --- 2. DISPLAY TAB ---
with tab_display:
    # We pass the JSON settings directly into the Javascript inside the HTML
    settings_json = json.dumps(load_settings())
    
    # We use CSS `min(vw, vh)` to dynamically scale fonts perfectly to screen size.
    # We use vanilla Javascript to run the clock quickly in the browser.
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
            #content {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }}
            /* Dynamic sizing utilizing viewport width/height */
            #date-label {{ font-size: min(3.5vw, 6vh); margin-bottom: 0.5vh; opacity: 0.9; }}
            #clock-label {{ font-size: min(15vw, 22vh); font-weight: bold; line-height: 1; margin-bottom: 1vh; }}
            #msg-label {{ font-size: min(6vw, 10vh); font-weight: 600; }}
            
            #controls {{
                padding: 2vh 0;
                display: flex;
                justify-content: center;
                gap: 1vw;
                background: rgba(0,0,0,0.2);
            }}
            button {{
                padding: 1.5vh 2vw;
                font-size: min(2vw, 3vh);
                cursor: pointer;
                border: none; border-radius: 8px;
                background-color: #ffffff; color: #000000;
                font-weight: bold;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                transition: transform 0.1s;
            }}
            button:active {{ transform: scale(0.95); }}
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

            // Generate buttons based on Streamlit settings
            const controls = document.getElementById('controls');
            modes.forEach((mode, index) => {{
                const btn = document.createElement('button');
                btn.innerText = mode.name || `Mode ${{index + 1}}`;
                btn.onclick = () => setMode(index);
                controls.appendChild(btn);
            }});

            function updateClock() {{
                const now = new Date();
                
                // Formulate Clock HH:MM:SS
                const hh = String(now.getHours()).padStart(2, '0');
                const mm = String(now.getMinutes()).padStart(2, '0');
                const ss = String(now.getSeconds()).padStart(2, '0');
                document.getElementById('clock-label').innerText = `${{hh}}:${{mm}}:${{ss}}`;

                // Formulate Date 'dd mmm yyyy (weekday)'
                const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
                const dd = String(now.getDate()).padStart(2, '0');
                const mmm = months[now.getMonth()];
                const yyyy = now.getFullYear();
                const weekday = days[now.getDay()];
                document.getElementById('date-label').innerText = `${{dd}} ${{mmm}} ${{yyyy}} (${{weekday}})`;

                // Auto-Switch Logic
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

            setMode(0); // Start on first mode
            setInterval(updateClock, 200); // Check multiple times a second for exact tick
        </script>
    </body>
    </html>
    """
    
    # Inject the HTML/JS into Streamlit
    st.components.v1.html(html_code, height=750)
