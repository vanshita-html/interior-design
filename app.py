"""
app.py
------
AI Interior Design Generator - Streamlit front end.

Flow:
  1. User picks room type + customization options (dropdowns).
  2. Groq turns those choices into a rich image-generation prompt.
  3. Hugging Face Inference API renders the room image from that prompt.
  4. Result + prompt + download button are shown to the user.

Run locally:
    streamlit run app.py

API keys are read from environment variables / .env (local) or
st.secrets (Streamlit Community Cloud) -- NEVER hardcoded here.
"""

import os
import io
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
# Page setup + styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Interior Designer",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.3rem;
            font-weight: 800;
            margin-bottom: 0;
            color: #1f2937;
        }
        .subtitle {
            color: #6b7280;
            font-size: 1.05rem;
            margin-top: 0.2rem;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            background-color: #111827;
            color: white;
            border-radius: 8px;
            padding: 0.6rem 1.4rem;
            font-weight: 600;
            border: none;
        }
        .stButton>button:hover {
            background-color: #374151;
            color: white;
        }
        section[data-testid="stSidebar"] {
            background-color: #f9fafb;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🏠 AI Interior Design Generator</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Pick a room, choose your materials, colors and style '
    '- get a photorealistic AI-generated interior in seconds.</p>',
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
    st.header("🔑 API Keys")
    st.caption("Stored only for this session. Prefer setting these in a `.env` file or Streamlit secrets.")

    groq_key = get_key("GROQ_API_KEY") or st.text_input("Groq API Key", type="password")
    hf_key = get_key("HF_API_KEY") or st.text_input("Hugging Face API Key", type="password")

    st.divider()
    st.caption(
        "Groq writes the design prompt.\n\n"
        "Hugging Face (FLUX.1-schnell) renders the image.\n\n"
        "Get free keys at console.groq.com and huggingface.co/settings/tokens."
    )


# ---------------------------------------------------------------------------
# Main form
# ---------------------------------------------------------------------------
col_form, col_result = st.columns([1, 1.3], gap="large")

with col_form:
    st.subheader("1. Room & Customization")

    room_type = st.selectbox("Room Type", ROOM_TYPES)

    c1, c2 = st.columns(2)
    with c1:
        door_material = st.selectbox("Door Material", DOOR_MATERIALS)
        wall_texture = st.selectbox("Wall Texture", WALL_TEXTURES)
        flooring = st.selectbox("Flooring", FLOORING_TYPES)
        color_theme = st.selectbox("Overall Color Theme", COLOR_THEMES)
    with c2:
        door_color = st.selectbox("Door Color", DOOR_COLORS)
        wall_color = st.selectbox("Wall Color", WALL_COLORS)
        furniture_style = st.selectbox("Furniture Style", FURNITURE_STYLES)
        lighting = st.selectbox("Lighting Style", LIGHTING_STYLES)

    # Room-specific extra fields, rendered dynamically
    st.markdown("**Room-specific details**")
    room_specific_values = {}
    specific_fields = ROOM_SPECIFIC_FIELDS.get(room_type, {})
    if specific_fields:
        cols = st.columns(len(specific_fields))
        for col, (field_label, options) in zip(cols, specific_fields.items()):
            with col:
                room_specific_values[field_label] = st.selectbox(field_label, options)
    else:
        st.caption("No extra fields for this room type.")

    generate_clicked = st.button("✨ Generate Interior", use_container_width=True)


# ---------------------------------------------------------------------------
# Generation + result display
# ---------------------------------------------------------------------------
with col_result:
    st.subheader("2. Result")

    if generate_clicked:
        if not groq_key or not hf_key:
            st.error("Please enter both your Groq API Key and Hugging Face API Key in the sidebar.")
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
                with st.spinner("Writing your design prompt..."):
                    image_prompt = build_image_prompt(groq_key, room_type, selections)

                with st.expander("📝 Generated design prompt (editable)", expanded=False):
                    image_prompt = st.text_area("Prompt", value=image_prompt, height=120)

                with st.spinner("Rendering your room (first run can take ~20-30s while the model warms up)..."):
                    image_bytes = generate_image(hf_key, image_prompt)

                st.image(image_bytes, caption=f"{room_type} - {color_theme} theme", use_container_width=True)

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
        st.info("Fill in your preferences on the left and click **Generate Interior**.")
