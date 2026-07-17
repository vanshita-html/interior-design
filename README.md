# interior-design
# AI Interior Design Generator

Streamlit app that generates photorealistic AI room images based on
user-selected customization (door material/color, wall texture/color,
flooring, furniture style, lighting, color theme, plus room-specific
fields for bedrooms, kitchens, halls, toilets, and store rooms).

## How it works

1. **Groq** (`llama-3.3-70b-versatile`) turns your dropdown selections into a
   detailed, professional image-generation prompt. Groq is a text model only
   — it does not generate images itself.
2. **Hugging Face Inference API** (`FLUX.1-schnell`) renders that prompt into
   an actual image.

## Setup

```bash
cd interior-design-app
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your own keys:

```bash
cp .env.example .env
```

```
GROQ_API_KEY=your_groq_api_key_here
HF_API_KEY=your_huggingface_api_key_here
```

- Get a free Groq key: https://console.groq.com/keys
- Get a free Hugging Face token: https://huggingface.co/settings/tokens
  (needs "Inference" permission enabled)

**IMPORTANT:** You pasted a Groq key earlier in our chat. Rotate/regenerate
it in the Groq console before deploying anywhere — treat any key that has
been shared in a chat as compromised.

## Run locally

```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repo (make sure `.env` is in `.gitignore`
   and never committed).
2. On https://share.streamlit.io, create a new app pointing at `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   HF_API_KEY = "your_huggingface_api_key_here"
   ```
4. Deploy. `app.py` automatically checks `st.secrets` when env vars aren't set.

## Project structure

```
interior-design-app/
├── app.py              # Streamlit UI + main flow
├── config.py            # All dropdown options (materials, colors, styles)
├── prompt_builder.py     # Groq: selections -> image prompt
├── image_generator.py    # Hugging Face: prompt -> image bytes
├── requirements.txt
├── .env.example
└── README.md
```

## Extending it

- **Add a new material/color/style:** just add it to the relevant list in
  `config.py` — no other code changes needed.
- **Add a new room type:** add it to `ROOM_TYPES` and give it an entry in
  `ROOM_SPECIFIC_FIELDS` in `config.py`.
- **Swap the image model:** change `HF_IMAGE_MODEL` in `config.py` to any
  text-to-image model on the HF Hub (e.g. `stabilityai/stable-diffusion-xl-base-1.0`).
- **Render onto the actual floor plan** (later upgrade): use an
  image-to-image / inpainting model instead of text-to-image, feeding in
  your FP1031 floor plan crop as the base image with a mask over the room.

## Notes / limitations

- Hugging Face's free Inference API can return a `503` while the model
  "warms up" on first use — `image_generator.py` already retries with backoff.
- Free tier has rate limits; for production use consider a paid HF
  Inference Endpoint or Replicate for guaranteed uptime.
