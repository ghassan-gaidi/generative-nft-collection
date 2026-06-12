"""
Nano Banana (Google Gemini API) image generation wrapper.
"""
import os
import base64
from pathlib import Path

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class NanoBananaGenerator:
    """Image generation via Google Gemini API (Nano Banana)."""

    MODELS = {
        "flash": "gemini-3.1-flash-image",
        "flash-2.5": "gemini-2.5-flash-image",
        "pro": "gemini-3-pro-image",
    }

    def __init__(self, api_key: str | None = None, model: str = "flash"):
        if not HAS_GENAI:
            raise ImportError(
                "google-genai not installed. Run: uv pip install google-genai"
            )
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("NANO_BANANA_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key. Set GOOGLE_API_KEY or NANO_BANANA_KEY env, or pass api_key"
            )
        self.model_name = self.MODELS.get(model, model)
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, output_path: str | Path) -> bool:
        """Generate an image and save to file."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_modalities": ["image", "text"]},
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(part.inline_data.data))
                    return True
            return False
        except Exception as e:
            print(f"  ✗ Nano Banana error: {e}")
            return False
