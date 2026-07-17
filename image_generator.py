"""
image_generator.py
-------------------
Generates the room image via Hugging Face's Inference Providers ecosystem.

Why huggingface_hub instead of raw requests:
  Hugging Face retired its old single-backend "api-inference" endpoint.
  Image models like FLUX are now served by third-party providers (fal-ai,
  replicate, together, etc.) that HF routes to for you. Hardcoding a REST
  URL to one specific provider breaks whenever that provider stops hosting
  a model. The official `huggingface_hub` client with provider="auto"
  handles that routing/fallback automatically, which is the supported way
  to call Inference Providers going forward.
"""

import io
import time

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

from config import HF_IMAGE_MODEL, HF_PROVIDER


class ImageGenerationError(Exception):
    """Raised when Inference Providers fails to return an image after retries."""


def generate_image(hf_api_key: str, prompt: str, max_retries: int = 3) -> bytes:
    """
    Generate an image from a text prompt using Hugging Face Inference Providers.

    Args:
        hf_api_key: Hugging Face access token (needs "Make calls to Inference
                     Providers" permission -- set on a fine-grained token).
        prompt: The image description to render.
        max_retries: Retries for transient provider errors (e.g. cold start).

    Returns:
        Raw PNG image bytes ready to display or save.

    Raises:
        ImageGenerationError: if generation fails after all retries.
    """
    client = InferenceClient(api_key=hf_api_key, provider=HF_PROVIDER)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            image = client.text_to_image(prompt, model=HF_IMAGE_MODEL)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        except HfHubHTTPError as e:
            status = getattr(e.response, "status_code", None)

            if status == 403:
                raise ImageGenerationError(
                    "Permission denied (403). Your Hugging Face token needs the "
                    "'Make calls to Inference Providers' permission -- create a "
                    "fine-grained token at huggingface.co/settings/tokens with "
                    "that box checked, and make sure billing/provider access is "
                    "set up if the provider requires it."
                )

            if status == 404:
                raise ImageGenerationError(
                    f"Model '{HF_IMAGE_MODEL}' isn't currently served by any "
                    "provider. Check huggingface.co/models?pipeline_tag=text-to-image "
                    "for a model that's actively hosted, and update HF_IMAGE_MODEL "
                    "in config.py."
                )

            if status in (410, 424) or "deprecated" in str(e).lower():
                raise ImageGenerationError(
                    f"Model '{HF_IMAGE_MODEL}' is deprecated on its serving "
                    "provider. Pick a currently-active model from "
                    "huggingface.co/models?pipeline_tag=text-to-image and update "
                    "HF_IMAGE_MODEL in config.py."
                )

            if status == 503:
                last_error = f"Provider warming up (attempt {attempt}/{max_retries})"
                time.sleep(10)
                continue

            last_error = str(e)
            break

        except Exception as e:
            last_error = str(e)
            break

    raise ImageGenerationError(f"Image generation failed: {last_error}")
