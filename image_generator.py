"""
image_generator.py
-------------------
Sends the final text prompt to the Hugging Face Inference API and
returns the generated image bytes.
"""

import time
import requests
from config import HF_API_URL


class ImageGenerationError(Exception):
    """Raised when the HF Inference API fails or returns an error payload."""


def generate_image(hf_api_key: str, prompt: str, max_retries: int = 3) -> bytes:
    """
    Generate an image from a text prompt using the Hugging Face Inference API.

    Args:
        hf_api_key: Hugging Face access token (loaded from env/secrets).
        prompt: The image description to render.
        max_retries: Number of retries if the model is still "warming up"
                     (HF free-tier models unload when idle, first call can 503).

    Returns:
        Raw image bytes (PNG/JPEG) ready to display or save.

    Raises:
        ImageGenerationError: if the API returns a non-image / error response
                               after all retries are exhausted.
    """
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": prompt}

    last_error = None
    for attempt in range(1, max_retries + 1):
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)

        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and content_type.startswith("image/"):
            return response.content

        # Model is loading -- HF returns JSON with an "estimated_time"
        if response.status_code == 503:
            try:
                wait_time = response.json().get("estimated_time", 15)
            except ValueError:
                wait_time = 15
            last_error = f"Model is warming up, waited {wait_time:.0f}s (attempt {attempt}/{max_retries})"
            time.sleep(min(wait_time, 30))
            continue

        # 404 usually means this specific model isn't served by the
        # "hf-inference" provider under the new router -- not a typo/DNS issue.
        if response.status_code == 404:
            raise ImageGenerationError(
                "Model not found on the hf-inference provider (HTTP 404). "
                f"'{HF_API_URL}' may not host this model under the new router. "
                "Check the model page on huggingface.co for which Inference "
                "Providers list it, or try a different provider suffix "
                "(e.g. 'black-forest-labs/FLUX.1-schnell:together')."
            )

        # Any other error -- capture and stop
        try:
            last_error = response.json()
        except ValueError:
            last_error = response.text
        break

    raise ImageGenerationError(f"Image generation failed: {last_error}")
