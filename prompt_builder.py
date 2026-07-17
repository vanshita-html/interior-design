"""
prompt_builder.py
------------------
Uses Groq (fast Llama inference) to turn the user's structured form
selections into a single, richly detailed prompt suitable for a
text-to-image model (FLUX / Stable Diffusion style).

Groq itself does NOT generate images -- it only writes the prompt.
Image rendering happens separately in image_generator.py.
"""

from groq import Groq
from config import GROQ_MODEL


SYSTEM_PROMPT = """You are an expert interior designer and prompt engineer for \
text-to-image AI models (FLUX / Stable Diffusion style).

Given a structured set of room customization choices, write ONE single \
paragraph (max ~120 words) that describes a photorealistic interior photo \
of that room, incorporating every provided detail (materials, colors, \
textures, furniture style, lighting, and any room-specific items).

Rules:
- Output ONLY the image prompt text. No preamble, no markdown, no quotes.
- Be concrete and visual: mention materials, colors, finishes, light quality, camera angle.
- End with quality boosters like: "interior design photography, realistic lighting, \
high detail, 8k, architectural digest style".
- Do not invent details the user did not specify beyond reasonable, tasteful defaults.
"""


def build_image_prompt(groq_api_key: str, room_type: str, selections: dict) -> str:
    """
    Call Groq to convert form selections into a text-to-image prompt.

    Args:
        groq_api_key: Groq API key (loaded from env/secrets, never hardcoded).
        room_type: e.g. "Bedroom", "Kitchen".
        selections: dict of {field_label: chosen_value} from the Streamlit form.

    Returns:
        A single-paragraph prompt string ready to send to the image model.
    """
    client = Groq(api_key=groq_api_key)

    details_lines = "\n".join(f"- {label}: {value}" for label, value in selections.items())
    user_prompt = (
        f"Room type: {room_type}\n\n"
        f"Customization choices:\n{details_lines}\n\n"
        "Write the image generation prompt now."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
