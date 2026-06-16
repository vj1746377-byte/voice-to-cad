# =============================================================================
# Voice-to-CAD Prompt Assistant
# A Streamlit web app that converts natural language design requests
# into Python/FreeCAD scripts using Google's Gemini AI.
# =============================================================================

# --- IMPORTS ---
# We import all the libraries we need at the top of the file.
import streamlit as st   # The web framework that builds our UI
import google.generativeai as genai  # Google's Gemini AI library
import re                # For cleaning up AI output (removing unwanted text)

# =============================================================================
# PAGE CONFIGURATION
# This MUST be the first Streamlit command in the file.
# It sets the browser tab title, icon, and overall page layout.
# =============================================================================
st.set_page_config(
    page_title="Voice-to-CAD Assistant",
    page_icon="🔩",
    layout="wide",          # Use the full width of the browser window
    initial_sidebar_state="expanded"  # Show the sidebar open by default
)

# =============================================================================
# CUSTOM CSS STYLING
# We inject custom CSS to make the app look polished and professional.
# Streamlit's default look is functional but plain — this makes it distinctive.
# =============================================================================
st.markdown("""
<style>
    /* Import a clean engineering-style font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* --- Global styles --- */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* --- Main app background --- */
    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 50%, #0f1117 100%);
    }

    /* --- Sidebar styling --- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e2235 0%, #161929 100%);
        border-right: 1px solid #2d3252;
    }

    /* --- Hero header section --- */
    .hero-header {
        background: linear-gradient(135deg, #1e2235 0%, #252a42 100%);
        border: 1px solid #3d4575;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        color: #8892b0;
        font-size: 1.05rem;
        margin-top: 0.6rem;
        font-weight: 400;
    }

    /* --- Input card --- */
    .input-card {
        background: #1e2235;
        border: 1px solid #2d3252;
        border-radius: 12px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
    }
    .card-label {
        color: #a0aec0;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* --- Generate button --- */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2.5rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s ease;
        letter-spacing: 0.02em;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5b52f0 0%, #8b47ff 100%);
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
    }

    /* --- Output section --- */
    .output-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #34d399;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .output-meta {
        background: #1e2235;
        border: 1px solid #2d3252;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 1rem;
        color: #8892b0;
        font-size: 0.88rem;
    }

    /* --- Download button --- */
    [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.35) !important;
    }

    /* --- Warning/error messages --- */
    .warning-box {
        background: #2d1f1f;
        border: 1px solid #7f1d1d;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        color: #fca5a5;
        font-size: 0.9rem;
        margin-top: 1rem;
    }

    /* --- Sidebar labels --- */
    .sidebar-section-title {
        color: #a0aec0;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
        margin-top: 1rem;
    }

    /* Make code blocks use JetBrains Mono for that IDE feel */
    code, pre, [data-testid="stCode"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Remove default Streamlit footer */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# THE SYSTEM PROMPT FOR GEMINI
# This is the most important part of the AI logic.
# A "system prompt" tells the AI exactly HOW to behave and what format to use.
# We're being very strict here so Gemini only outputs clean, usable CAD code.
# =============================================================================
SYSTEM_PROMPT = """You are an expert CAD automation engineer specializing in FreeCAD Python scripting.
Your ONLY job is to convert natural language design requests into clean, executable FreeCAD Python scripts.

STRICT OUTPUT RULES — follow every rule without exception:
1. Output ONLY valid Python code. No markdown fences (no ```python), no introductory sentences, no explanations outside of code comments.
2. Start the script immediately with a module docstring (triple-quoted string) describing the part.
3. Every logical section must have a clear comment explaining what it does (for beginner readers).
4. Always import FreeCAD modules at the top: `import FreeCAD, Part, FreeCADGui`.
5. Always create a new FreeCAD document and assign it to a variable called `doc`.
6. Always call `doc.recompute()` and `FreeCADGui.ActiveDocument.ActiveView.fitAll()` at the end.
7. Use SI units: millimeters for dimensions, degrees for angles. Convert if the user provides other units.
8. Add a final comment block listing the key parameters so they're easy to find and modify.
9. If a shape is impossible or the request is ambiguous, write a Python script that raises a descriptive ValueError explaining what's missing.
10. Keep the code clean and production-quality — no TODO comments, no placeholder values.

OUTPUT FORMAT (follow exactly):
\"\"\"
<One-line description of the part>

Parameters:
  - <param_name>: <value> <unit>  # one line per key dimension
\"\"\"

import FreeCAD
import Part
import FreeCADGui

# --- Script generated by Voice-to-CAD Assistant ---

# [rest of the script...]
"""

# =============================================================================
# SIDEBAR
# Everything inside `with st.sidebar:` appears in the left panel.
# =============================================================================
with st.sidebar:
    # App logo / title
    st.markdown("## 🔩 Voice-to-CAD")
    st.markdown(
        "<p style='color:#8892b0; font-size:0.88rem; line-height:1.6;'>"
        "Type a plain-English design request and get a ready-to-run "
        "<strong style='color:#a78bfa;'>FreeCAD Python script</strong> in seconds."
        "</p>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- How it works section ---
    st.markdown("**How it works**")
    st.markdown(
        "<ol style='color:#8892b0; font-size:0.85rem; padding-left:1.2rem; line-height:1.9;'>"
        "<li>Paste your Gemini API key below</li>"
        "<li>Describe your part in plain English</li>"
        "<li>Click <em>Generate CAD Script</em></li>"
        "<li>Download and run in FreeCAD</li>"
        "</ol>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- API Key input ---
    # `type="password"` hides the key so it can't be seen over someone's shoulder.
    st.markdown(
        "<p class='sidebar-section-title'>🔑 Gemini API Key</p>",
        unsafe_allow_html=True
    )
    api_key = st.text_input(
        label="Gemini API Key",       # Required label (hidden visually)
        type="password",              # Masks the characters
        placeholder="AIza...",
        label_visibility="collapsed"  # We use our own label above
    )

    # Give the user a link to get their API key
    st.markdown(
        "<p style='color:#6b7280; font-size:0.78rem; margin-top:0.4rem;'>"
        "Get a free key at "
        "<a href='https://aistudio.google.com/app/apikey' target='_blank' "
        "style='color:#60a5fa;'>Google AI Studio ↗</a>"
        "</p>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- CAD software note ---
    st.markdown(
        "<p style='color:#6b7280; font-size:0.8rem; line-height:1.6;'>"
        "⚙️ Scripts are written for <strong style='color:#a0aec0;'>FreeCAD 0.21+</strong>. "
        "Open FreeCAD → Macro Editor → paste and run."
        "</p>",
        unsafe_allow_html=True
    )

# =============================================================================
# MAIN PAGE
# Everything below appears in the main body of the app.
# =============================================================================

# --- Hero Header ---
st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">Voice-to-CAD Prompt Assistant</h1>
    <p class="hero-subtitle">
        Describe any mechanical part in plain English → get a runnable FreeCAD script instantly
    </p>
</div>
""", unsafe_allow_html=True)

# --- Instructions row ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        "<div class='input-card' style='text-align:center;'>"
        "<div style='font-size:1.8rem;'>✍️</div>"
        "<div style='color:#e2e8f0; font-weight:600; margin:0.4rem 0 0.2rem;'>Describe</div>"
        "<div style='color:#6b7280; font-size:0.85rem;'>Type your part's shape and dimensions in plain words</div>"
        "</div>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        "<div class='input-card' style='text-align:center;'>"
        "<div style='font-size:1.8rem;'>🤖</div>"
        "<div style='color:#e2e8f0; font-weight:600; margin:0.4rem 0 0.2rem;'>Generate</div>"
        "<div style='color:#6b7280; font-size:0.85rem;'>Gemini AI translates your request into FreeCAD Python</div>"
        "</div>",
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        "<div class='input-card' style='text-align:center;'>"
        "<div style='font-size:1.8rem;'>⬇️</div>"
        "<div style='color:#e2e8f0; font-weight:600; margin:0.4rem 0 0.2rem;'>Download & Run</div>"
        "<div style='color:#6b7280; font-size:0.85rem;'>Save the script and run it directly inside FreeCAD</div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# USER INPUT SECTION
# This is where the user types their design command.
# =============================================================================
st.markdown(
    "<p class='card-label'>🗣️ Your design command</p>",
    unsafe_allow_html=True
)

# The large text area where the user types their design request.
# The `value` sets a pre-filled default example so users know what to type.
user_prompt = st.text_area(
    label="Design command",            # Required but hidden
    label_visibility="collapsed",
    value="Design a hollow cylinder with an outer diameter of 50mm, inner diameter of 40mm, and height of 120mm.",
    height=120,
    placeholder="e.g. Create an L-shaped bracket with a length of 30 cm, width of 5 cm, and a thickness of 5 mm"
)

# A few quick-example buttons so beginners can see what's possible
st.markdown(
    "<p style='color:#6b7280; font-size:0.8rem; margin-top:0.6rem; margin-bottom:0.4rem;'>"
    "💡 Quick examples — click to load:</p>",
    unsafe_allow_html=True
)

# We lay out three example buttons side by side
ex1, ex2, ex3 = st.columns(3)
# Each button, when clicked, uses st.session_state to pre-fill the text area.
# `st.session_state` is Streamlit's way of remembering values between interactions.
with ex1:
    if st.button("🔩 L-bracket", use_container_width=True):
        st.session_state["example"] = (
            "Create an L-shaped bracket with a horizontal leg length of 80mm, "
            "vertical leg height of 60mm, width of 40mm, and uniform thickness of 6mm. "
            "Add a 6mm diameter bolt hole at each end of both legs."
        )
with ex2:
    if st.button("⚙️ Gear blank", use_container_width=True):
        st.session_state["example"] = (
            "Create a spur gear blank: outer diameter 100mm, "
            "hub diameter 30mm, hub height 25mm, overall thickness 20mm, "
            "with a 10mm diameter central shaft hole."
        )
with ex3:
    if st.button("📦 Mounting plate", use_container_width=True):
        st.session_state["example"] = (
            "Create a rectangular mounting plate 150mm x 100mm x 5mm thick "
            "with four 5mm diameter corner holes placed 10mm from each edge."
        )

# If the user clicked an example button, update the text area with that example.
# We re-assign `user_prompt` so the Generate button sees the updated text.
if "example" in st.session_state:
    user_prompt = st.session_state["example"]
    # Clear it after use so it doesn't re-trigger on the next run
    del st.session_state["example"]
    st.rerun()  # Immediately refresh the page to show the updated text area

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# GENERATE BUTTON
# When clicked, this triggers the entire AI pipeline.
# =============================================================================
generate_clicked = st.button("⚡ Generate CAD Script", use_container_width=True)

# =============================================================================
# AI GENERATION LOGIC
# This block only runs when the user clicks "Generate CAD Script".
# =============================================================================
if generate_clicked:

    # --- Input validation ---
    # Check that the user has provided an API key before we do anything.
    if not api_key:
        st.markdown(
            "<div class='warning-box'>"
            "🔑 <strong>API key required.</strong> Please paste your Google Gemini API key "
            "in the sidebar on the left."
            "</div>",
            unsafe_allow_html=True
        )

    # Check that the user has actually typed something in the design box.
    elif not user_prompt.strip():
        st.markdown(
            "<div class='warning-box'>"
            "✍️ <strong>Empty request.</strong> Please describe the part you want to create."
            "</div>",
            unsafe_allow_html=True
        )

    else:
        # --- Everything looks good — call the Gemini API ---
        # We use a loading spinner so the user knows the app is working.
        with st.spinner("🤖 Generating your FreeCAD script..."):
            try:
                # Step 1: Configure the Gemini library with the user's API key.
                # This authenticates our request so Google knows who's calling.
                genai.configure(api_key=api_key)

                # Step 2: Choose the AI model.
                # `gemini-1.5-flash` is fast and good for code generation.
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=SYSTEM_PROMPT   # Pass our strict instructions
                )

                # Step 3: Build the full prompt.
                # We combine our system rules with the user's specific request.
                full_prompt = (
                    f"Generate a complete FreeCAD Python script for the following design request:\n\n"
                    f"REQUEST: {user_prompt.strip()}\n\n"
                    f"Remember: output ONLY the Python code, no markdown fences, no prose."
                )

                # Step 4: Send the request to Gemini and get the response.
                response = model.generate_content(full_prompt)

                # Step 5: Extract the text from the response object.
                raw_output = response.text

                # Step 6: Clean up the output.
                # Sometimes the AI wraps code in ```python ... ``` even when told not to.
                # This regex strips those markdown fences if they appear.
                cleaned_script = re.sub(
                    r"^```(?:python)?\s*\n?", "", raw_output, flags=re.IGNORECASE
                ).rstrip("`").strip()

                # =================================================================
                # OUTPUT DISPLAY
                # Show the generated script beautifully in the app.
                # =================================================================
                st.markdown("---")

                # Success header
                st.markdown(
                    "<div class='output-header'>"
                    "✅ Script generated successfully"
                    "</div>",
                    unsafe_allow_html=True
                )

                # Quick stats about the generated script
                line_count = len(cleaned_script.splitlines())
                char_count = len(cleaned_script)
                st.markdown(
                    f"<div class='output-meta'>"
                    f"📄 <strong style='color:#e2e8f0;'>{line_count}</strong> lines &nbsp;|&nbsp; "
                    f"🔡 <strong style='color:#e2e8f0;'>{char_count}</strong> characters &nbsp;|&nbsp; "
                    f"🖥️ Target: <strong style='color:#a78bfa;'>FreeCAD 0.21+ (Python 3)</strong>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Display the code with syntax highlighting.
                # `st.code()` automatically colors Python keywords, strings, etc.
                st.code(cleaned_script, language="python")

                # =================================================================
                # DOWNLOAD BUTTON
                # Let the user save the script as a .py file.
                # =================================================================
                st.download_button(
                    label="⬇️ Download  FreeCAD Script (.py)",
                    data=cleaned_script,              # The actual file content
                    file_name="freecad_script.py",    # Default filename when saved
                    mime="text/x-python",             # Tells the browser it's a Python file
                    use_container_width=True
                )

                # Usage tip
                st.markdown(
                    "<p style='color:#6b7280; font-size:0.82rem; text-align:center; margin-top:0.8rem;'>"
                    "💡 In FreeCAD: <em>Macro → Macros → Create → paste code → Execute</em>"
                    "</p>",
                    unsafe_allow_html=True
                )

            # --- Error Handling ---
            # If the API call fails, we catch the error and show a friendly message
            # instead of a scary Python traceback.
            except Exception as e:
                error_message = str(e)

                # Friendly messages for the most common errors
                if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
                    friendly_msg = (
                        "🔑 <strong>Invalid API key.</strong> "
                        "Please double-check the key you pasted in the sidebar. "
                        "Keys start with <code>AIza</code> and are about 39 characters long."
                    )
                elif "quota" in error_message.lower() or "429" in error_message:
                    friendly_msg = (
                        "⏱️ <strong>Rate limit reached.</strong> "
                        "You've hit Google's free-tier limit. Wait a minute and try again, "
                        "or check your quota at "
                        "<a href='https://aistudio.google.com' target='_blank' style='color:#60a5fa;'>"
                        "Google AI Studio ↗</a>."
                    )
                elif "network" in error_message.lower() or "connection" in error_message.lower():
                    friendly_msg = (
                        "🌐 <strong>Network error.</strong> "
                        "Please check your internet connection and try again."
                    )
                else:
                    # For any other error, show the raw message so it can be debugged.
                    friendly_msg = (
                        f"❌ <strong>Something went wrong.</strong> "
                        f"Error details: <code>{error_message}</code>"
                    )

                st.markdown(
                    f"<div class='warning-box'>{friendly_msg}</div>",
                    unsafe_allow_html=True
                )

# =============================================================================
# IDLE STATE — shown before the user clicks Generate
# =============================================================================
else:
    # Show a placeholder panel when no script has been generated yet
    st.markdown(
        "<div style='"
        "background:#1e2235; border:1px dashed #2d3252; border-radius:12px; "
        "padding:3rem; text-align:center; color:#4a5568; margin-top:1rem;'>"
        "<div style='font-size:3rem;'>📐</div>"
        "<div style='font-size:1rem; color:#6b7280; margin-top:0.8rem;'>"
        "Your generated FreeCAD script will appear here"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )
