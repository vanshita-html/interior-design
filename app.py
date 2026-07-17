"""
app.py
------
AI Interior Design Generator - Streamlit front end.

Flow:
  1. User picks room type + customization options.
  2. Groq turns those choices into a rich image-generation prompt.
  3. Hugging Face Inference Providers renders the room image from that prompt.
  4. Result + prompt + download button are shown to the user.

Run locally:
    streamlit run app.py

API keys are read from environment variables / .env (local) or
st.secrets (Streamlit Community Cloud) -- NEVER hardcoded here.
"""

import os
import datetime
import streamlit as st
from dotenv import load_dotenv

from config import (
    ROOM_TYPES, DOOR_MATERIALS, DOOR_COLORS, WALL_TEXTURES, WALL_COLORS,
    FLOORING_TYPES, FURNITURE_STYLES, LIGHTING_STYLES, COLOR_THEMES,
    ROOM_SPECIFIC_FIELDS,
)
from prompt_builder import build_image_prompt
from image_generator import generate_image, ImageGenerationError

load_dotenv()  # loads .env when running locally


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Interior Studio",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system -- clean, calm, single-column form (no cramped columns
# that truncate long option text). One accent color, generous spacing.
#   bg          #F6F7F4  page background, soft neutral
#   card        #FFFFFF  card surface
#   ink         #22262B  primary text
#   muted       #6B7280  secondary text
#   accent      #3F6C51  deep sage (buttons, focus states)
#   accent-soft #E8EFEA  hover / highlight tint
#   border      #E6E4DD  hairline borders
#   Manrope     -> headings
#   Inter       -> everything else
# ---------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg: #F6F7F4;
            --card: #FFFFFF;
            --ink: #22262B;
            --muted: #6B7280;
            --accent: #3F6C51;
            --accent-soft: #E8EFEA;
            --border: #E6E4DD;
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: var(--bg); }
        .block-container { padding-top: 2.2rem; max-width: 1100px; }

        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] input {
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
        }

        /* ---------- Header ---------- */
        .studio-title {
            font-family: 'Manrope', sans-serif;
            font-size: 2.15rem;
            font-weight: 800;
            color: var(--ink);
            line-height: 1.15;
            margin: 0 0 0.35rem 0;
        }
        .studio-subtitle {
            color: var(--muted);
            font-size: 1rem;
            max-width: 620px;
            margin-bottom: 1.8rem;
        }

        /* ---------- Section labels ---------- */
        .section-label {
            font-family: 'Manrope', sans-serif;
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ink);
            margin: 1.4rem 0 0.9rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .section-label .dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: var(--accent);
            display: inline-block;
        }
        .section-label:first-of-type { margin-top: 0; }

        /* ---------- Cards ---------- */
        .st-key-spec_card, .st-key-result_card {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.8rem 1.9rem;
            box-shadow: 0 1px 2px rgba(20,20,20,0.03), 0 8px 24px rgba(20,20,20,0.04);
        }

        /* ---------- Form widgets: full width, roomy, no truncation ---------- */
        label { font-weight: 500 !important; color: var(--ink) !important; font-size: 0.9rem !important; }

        div[data-baseweb="select"] > div {
            background-color: #FBFBF9 !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            min-height: 3rem !important;
        }
        div[data-baseweb="select"] span { white-space: normal !important; }
        div[data-baseweb="select"] > div:hover { border-color: var(--accent) !important; }
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px var(--accent-soft) !important;
        }
        /* Dropdown option list -- match trigger width, don't clip text */
        ul[data-testid="stSelectboxVirtualDropdown"] li { white-space: normal !important; }

        /* Room-type segmented control */
        div[role="radiogroup"] { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        div[role="radiogroup"] label {
            background-color: #FBFBF9;
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 0.5rem 1.1rem !important;
            margin: 0 !important;
            transition: all 0.15s ease;
        }
        div[role="radiogroup"] label:hover { border-color: var(--accent); background-color: var(--accent-soft); }

        /* Buttons */
        .stButton>button {
            background-color: var(--accent);
            color: #FFFFFF;
            border-radius: 10px;
            padding: 0.75rem 1.4rem;
            font-weight: 600;
            border: none;
            width: 100%;
            transition: all 0.15s ease;
        }
        .stButton>button:hover { background-color: #345940; }

        .stDownloadButton>button {
            background-color: transparent;
            color: var(--accent);
            border: 1.5px solid var(--accent);
            border-radius: 10px;
            font-weight: 600;
            width: 100%;
        }
        .stDownloadButton>button:hover { background-color: var(--accent-soft); }

        hr { border-color: var(--border); }

        /* ---------- Result meta strip ---------- */
        .result-meta {
            margin-top: 1rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }
        .result-meta .chip {
            background-color: var(--accent-soft);
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
        }

        .empty-state {
            color: var(--muted);
            text-align: center;
            padding: 4rem 1rem;
            border: 1.5px dashed var(--border);
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<h1 class="studio-title">🏠 AI Interior Studio</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="studio-subtitle">Choose your materials, colors and furnishing style below. '
    'Groq drafts the design brief, Hugging Face renders it as a photorealistic scene.</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# API key handling (env var first, then st.secrets, else prompt in sidebar)
# ---------------------------------------------------------------------------
def get_key(name: str) -> str:
    if os.getenv(name):
        return os.getenv(name)
    if name in st.secrets:
        return st.secrets[name]
    return ""


with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Manrope\',sans-serif;font-size:1.15rem;font-weight:700;'
        'color:#22262B;margin-bottom:0.2rem;">🔑 API Keys</div>',
        unsafe_allow_html=True,
    )
    st.caption("Stored only for this session. Prefer a `.env` file or Streamlit secrets.")

    groq_key = get_key("GROQ_API_KEY") or st.text_input("Groq API Key", type="password")
    hf_key = get_key("HF_API_KEY") or st.text_input("Hugging Face API Key", type="password")

    st.divider()
    st.caption(
        "Groq writes the design brief.\n\n"
        "Hugging Face (Inference Providers) renders the image.\n\n"
        "Free keys: console.groq.com & huggingface.co/settings/tokens"
    )


# ---------------------------------------------------------------------------
# Main layout -- single-column form fields throughout, so long option
# text never gets clipped, regardless of window width.
# ---------------------------------------------------------------------------
col_form, col_result = st.columns([1, 1.15], gap="large")

with col_form:
    with st.container(key="spec_card"):
        st.markdown('<div class="section-label"><span class="dot"></span>Room</div>', unsafe_allow_html=True)
        room_type = st.radio("Room type", ROOM_TYPES, horizontal=True, label_visibility="collapsed")

        st.markdown('<div class="section-label"><span class="dot"></span>Structure</div>', unsafe_allow_html=True)
        door_material = st.selectbox("Door Material", DOOR_MATERIALS)
        door_color = st.selectbox("Door Color", DOOR_COLORS)
        wall_texture = st.selectbox("Wall Texture", WALL_TEXTURES)
        wall_color = st.selectbox("Wall Color", WALL_COLORS)
        flooring = st.selectbox("Flooring", FLOORING_TYPES)
        color_theme = st.selectbox("Overall Color Theme", COLOR_THEMES)

        st.markdown('<div class="section-label"><span class="dot"></span>Furnishing</div>', unsafe_allow_html=True)
        furniture_style = st.selectbox("Furniture Style", FURNITURE_STYLES)
        lighting = st.selectbox("Lighting Style", LIGHTING_STYLES)

        room_specific_values = {}
        specific_fields = ROOM_SPECIFIC_FIELDS.get(room_type, {})
        if specific_fields:
            st.markdown('<div class="section-label"><span class="dot"></span>Room Details</div>', unsafe_allow_html=True)
            for field_label, options in specific_fields.items():
                room_specific_values[field_label] = st.selectbox(field_label, options)

        st.write("")
        generate_clicked = st.button("✨ Generate Interior", use_container_width=True)


with col_result:
    with st.container(key="result_card"):
        st.markdown('<div class="section-label"><span class="dot"></span>Result</div>', unsafe_allow_html=True)

        if generate_clicked:
            if not groq_key or not hf_key:
                st.error("Add both your Groq API Key and Hugging Face API Key in the sidebar first.")
            else:
                selections = {
                    "Door Material": door_material,
                    "Door Color": door_color,
                    "Wall Texture": wall_texture,
                    "Wall Color": wall_color,
                    "Flooring": flooring,
                    "Furniture Style": furniture_style,
                    "Lighting Style": lighting,
                    "Color Theme": color_theme,
                    **room_specific_values,
                }

                try:
                    with st.spinner("Drafting your design brief..."):
                        image_prompt = build_image_prompt(groq_key, room_type, selections)

                    with st.expander("📝 Design brief (editable)", expanded=False):
                        image_prompt = st.text_area("Prompt", value=image_prompt, height=120, label_visibility="collapsed")

                    with st.spinner("Rendering your room (first run can take ~20-30s)..."):
                        image_bytes = generate_image(hf_key, image_prompt)

                    st.image(image_bytes, use_container_width=True)

                    st.markdown(
                        f"""
                        <div class="result-meta">
                            <span class="chip">{room_type}</span>
                            <span class="chip">{color_theme}</span>
                            <span class="chip">{door_material} door</span>
                            <span class="chip">{flooring}</span>
                            <span class="chip">{datetime.date.today().isoformat()}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.write("")
                    st.download_button(
                        label="⬇️ Download Image",
                        data=image_bytes,
                        file_name=f"{room_type.replace(' ', '_').lower()}_design.png",
                        mime="image/png",
                        use_container_width=True,
                    )

                except ImageGenerationError as e:
                    st.error(f"Image generation failed: {e}")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
        else:
            st.markdown(
                '<div class="empty-state">Fill in your specification and click '
                '<strong>Generate Interior</strong> to see the render here.</div>',
                unsafe_allow_html=True,
            )
