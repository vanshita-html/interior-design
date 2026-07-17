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
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system -- "drafting sheet" aesthetic
#   ink       #1C2B33  primary dark / text
#   paper     #ECE6D8  aged blueprint-paper background
#   card      #F7F3E9  lighter card surface
#   brass     #B98B4E  accent (drafting compass)
#   sage      #6E7F62  secondary accent
#   hairline  #D9D0BC  rule / border color
#   Fraunces  -> display serif headings
#   Inter     -> body / UI text
#   IBM Plex Mono -> spec labels, measurements
# ---------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">

    <style>
        :root {
            --ink: #1C2B33;
            --paper: #ECE6D8;
            --card: #F7F3E9;
            --brass: #B98B4E;
            --sage: #6E7F62;
            --hairline: #D9D0BC;
        }

        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

        .stApp { background-color: var(--paper); }

        section[data-testid="stSidebar"] {
            background-color: var(--ink);
            border-right: 1px solid var(--hairline);
        }
        section[data-testid="stSidebar"] * { color: #EDE7D8 !important; }
        section[data-testid="stSidebar"] input {
            background-color: #2A3A44 !important;
            border: 1px solid #3E5261 !important;
            color: #F7F3E9 !important;
        }
        section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
            color: #9FB0AD !important;
        }

        /* ---------- Header ---------- */
        .studio-eyebrow {
            font-family: 'IBM Plex Mono', monospace;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--brass);
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }
        .studio-title {
            font-family: 'Fraunces', serif;
            font-size: 2.6rem;
            font-weight: 600;
            color: var(--ink);
            line-height: 1.1;
            margin: 0 0 0.4rem 0;
        }
        .studio-subtitle {
            font-family: 'Inter', sans-serif;
            color: #5B5748;
            font-size: 1.02rem;
            max-width: 640px;
            margin-bottom: 1.6rem;
        }

        /* ---------- Section numbering (drafting-sheet schedule style) ---------- */
        .spec-heading {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            color: var(--sage);
            text-transform: uppercase;
            border-bottom: 1px solid var(--hairline);
            padding-bottom: 0.4rem;
            margin: 1.3rem 0 0.9rem 0;
        }

        /* ---------- Drafting-corner cards via container key classes ---------- */
        .st-key-spec_card, .st-key-result_card {
            background-color: var(--card);
            border: 1px solid var(--hairline);
            border-radius: 4px;
            padding: 1.6rem 1.7rem 1.4rem 1.7rem;
            position: relative;
            box-shadow: 0 1px 3px rgba(28,43,51,0.06);
        }
        .st-key-spec_card::before, .st-key-spec_card::after,
        .st-key-result_card::before, .st-key-result_card::after {
            content: "";
            position: absolute;
            width: 14px;
            height: 14px;
            border-color: var(--brass);
            border-style: solid;
            opacity: 0.85;
        }
        .st-key-spec_card::before, .st-key-result_card::before {
            top: -1px; left: -1px;
            border-width: 2px 0 0 2px;
        }
        .st-key-spec_card::after, .st-key-result_card::after {
            bottom: -1px; right: -1px;
            border-width: 0 2px 2px 0;
        }

        /* ---------- Widgets ---------- */
        label, .stSelectbox label, .stRadio label { 
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            color: var(--ink) !important;
            font-size: 0.88rem !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid var(--hairline) !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="select"] > div:hover { border-color: var(--brass) !important; }

        /* Room-type segmented control (st.radio, horizontal) */
        div[role="radiogroup"] {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        div[role="radiogroup"] label {
            background-color: #FFFFFF;
            border: 1px solid var(--hairline);
            border-radius: 999px;
            padding: 0.4rem 1rem !important;
            margin: 0 !important;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        div[role="radiogroup"] label:hover { border-color: var(--brass); }

        /* Buttons */
        .stButton>button {
            background-color: var(--ink);
            color: #F7F3E9;
            border-radius: 6px;
            padding: 0.7rem 1.4rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            border: 1px solid var(--ink);
            width: 100%;
            transition: all 0.15s ease;
        }
        .stButton>button:hover {
            background-color: var(--brass);
            border-color: var(--brass);
            color: var(--ink);
        }
        .stDownloadButton>button {
            background-color: transparent;
            color: var(--ink);
            border: 1.5px solid var(--ink);
            border-radius: 6px;
            font-weight: 600;
            width: 100%;
        }
        .stDownloadButton>button:hover {
            background-color: var(--ink);
            color: #F7F3E9;
        }

        /* Alerts */
        div[data-testid="stAlertContentInfo"], div[data-testid="stAlertContentError"] {
            font-family: 'Inter', sans-serif;
        }

        /* ---------- Title block (below generated image, drawing-sheet style) ---------- */
        .title-block {
            margin-top: 0.9rem;
            border-top: 2px solid var(--ink);
            padding-top: 0.6rem;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.6rem;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            color: var(--ink);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .title-block div span.label { color: var(--sage); display: block; font-size: 0.65rem; margin-bottom: 0.15rem; }
        .title-block div span.value { color: var(--ink); font-weight: 600; }

        .empty-state {
            font-family: 'Inter', sans-serif;
            color: #5B5748;
            text-align: center;
            padding: 3.5rem 1rem;
            border: 1px dashed var(--hairline);
            border-radius: 4px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="studio-eyebrow">AI Interior Studio &middot; FP1031</div>', unsafe_allow_html=True)
st.markdown('<h1 class="studio-title">Design your room, down to the door handle.</h1>', unsafe_allow_html=True)
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
        '<div style="font-family:\'Fraunces\',serif;font-size:1.3rem;font-weight:600;'
        'color:#F7F3E9;margin-bottom:0.2rem;">🔑 Studio Credentials</div>',
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
# Main layout
# ---------------------------------------------------------------------------
col_form, col_result = st.columns([1, 1.25], gap="large")

with col_form:
    with st.container(key="spec_card"):
        st.markdown('<div class="spec-heading">01 &nbsp;&mdash;&nbsp; Room</div>', unsafe_allow_html=True)
        room_type = st.radio("Room type", ROOM_TYPES, horizontal=True, label_visibility="collapsed")

        st.markdown('<div class="spec-heading">02 &nbsp;&mdash;&nbsp; Structure</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            door_material = st.selectbox("Door Material", DOOR_MATERIALS)
            wall_texture = st.selectbox("Wall Texture", WALL_TEXTURES)
            flooring = st.selectbox("Flooring", FLOORING_TYPES)
        with c2:
            door_color = st.selectbox("Door Color", DOOR_COLORS)
            wall_color = st.selectbox("Wall Color", WALL_COLORS)
            color_theme = st.selectbox("Overall Color Theme", COLOR_THEMES)

        st.markdown('<div class="spec-heading">03 &nbsp;&mdash;&nbsp; Furnishing</div>', unsafe_allow_html=True)
        furniture_style = st.selectbox("Furniture Style", FURNITURE_STYLES)
        lighting = st.selectbox("Lighting Style", LIGHTING_STYLES)

        room_specific_values = {}
        specific_fields = ROOM_SPECIFIC_FIELDS.get(room_type, {})
        if specific_fields:
            st.markdown('<div class="spec-heading">04 &nbsp;&mdash;&nbsp; Room Details</div>', unsafe_allow_html=True)
            cols = st.columns(len(specific_fields))
            for col, (field_label, options) in zip(cols, specific_fields.items()):
                with col:
                    room_specific_values[field_label] = st.selectbox(field_label, options)

        st.write("")
        generate_clicked = st.button("✨ Generate Interior", use_container_width=True)


with col_result:
    with st.container(key="result_card"):
        st.markdown('<div class="spec-heading">Result</div>', unsafe_allow_html=True)

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
                        <div class="title-block">
                            <div><span class="label">Room</span><span class="value">{room_type}</span></div>
                            <div><span class="label">Theme</span><span class="value">{color_theme}</span></div>
                            <div><span class="label">Materials</span><span class="value">{door_material} / {flooring}</span></div>
                            <div><span class="label">Rendered</span><span class="value">{datetime.date.today().isoformat()}</span></div>
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
