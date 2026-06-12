"""
AI Trait Asset Generator — generates individual trait PNGs via free AI APIs.

Backends:
  - puter:       Puter.js (30+ models, free, no key needed)
  - nanobanana:  Google Gemini API (using AI Studio key)
  - pollinations: Pollinations.AI (free pk_ key)
  - cloudflare:  Cloudflare Workers AI (FLUX Schnell)

Usage:
    python scripts/generate_traits.py --backend puter --model flux-schnell
    python scripts/generate_traits.py --backend nanobanana
    python scripts/generate_traits.py --backend pollinations --api-key <pk_key>
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


# ── Nano Banana (Google Gemini API) ──────────────────────────────────

class NanoBananaBackend:
    """Google Gemini API image generation."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    MODELS = {
        "flash": "gemini-3.1-flash-image",
        "flash-2.5": "gemini-2.5-flash-image",
        "pro": "gemini-3-pro-image",
    }

    def __init__(self, api_key: str, model: str = "flash"):
        self.api_key = api_key
        self.model_name = self.MODELS.get(model, model)
        self.url = f"{self.BASE_URL}/{self.model_name}:generateContent"

    def generate(self, prompt: str, output_path: str) -> bool:
        """Generate an image and save to output_path."""
        from google import genai
        import PIL.Image

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_modalities": ["image", "text"]},
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    return True
            return False
        except Exception as e:
            print(f"  ✗ Nano Banana error: {e}")
            return False


# ── Pollinations.AI ─────────────────────────────────────────────────

class PollinationsBackend:
    """Pollinations.AI keyless image generation."""

    BASE_URL = "https://gen.pollinations.ai/image"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("POLLINATIONS_KEY", "")

    def generate(self, prompt: str, output_path: str,
                 model: str = "flux", width: int = 1024, height: int = 1024) -> bool:
        """Generate an image via Pollinations."""
        import urllib.parse
        params = {
            "model": model,
            "width": width,
            "height": height,
        }
        if self.api_key:
            params["key"] = self.api_key

        url = f"{self.BASE_URL}/{urllib.parse.quote(prompt)}?{urllib.parse.urlencode(params)}"

        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                return True
            else:
                print(f"  ✗ Pollinations HTTP {r.status_code}: {r.text[:200]}")
                return False
        except Exception as e:
            print(f"  ✗ Pollinations error: {e}")
            return False


# ── Cloudflare Workers AI ────────────────────────────────────────────

class CloudflareBackend:
    """Cloudflare Workers AI via API token."""

    BASE_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"

    def __init__(self, account_id: str, api_token: str):
        self.url = self.BASE_URL.format(account_id=account_id)
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def generate(self, prompt: str, output_path: str,
                 model: str = "@cf/black-forest-labs/flux-1-schnell",
                 steps: int = 4) -> bool:
        """Generate via Cloudflare Workers AI."""
        try:
            r = requests.post(
                f"{self.url}/{model}",
                headers=self.headers,
                json={"prompt": prompt, "steps": steps},
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                if "result" in data and "image" in data["result"]:
                    img_bytes = base64.b64decode(data["result"]["image"])
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    return True
            print(f"  ✗ Cloudflare HTTP {r.status_code}")
            return False
        except Exception as e:
            print(f"  ✗ Cloudflare error: {e}")
            return False


# ── Puter.js (via Node.js) ──────────────────────────────────────────

class PuterBackend:
    """Puter.js image generation via Node.js bridge."""

    def __init__(self, model: str = "gemini-3.1-flash-image-preview"):
        self.model = model

    def generate(self, prompt: str, output_path: str) -> bool:
        """Generate via Puter.js Node.js script."""
        script = f"""
const {{ puter }} = require('@heyputer/puter.js');
const fs = require('fs');

(async () => {{
  try {{
    const image = await puter.ai.txt2img({json.dumps(prompt)}, {json.dumps({"model": self.model})});
    const buffer = await image.arrayBuffer();
    fs.writeFileSync({json.dumps(output_path)}, Buffer.from(buffer));
    console.log("OK");
  }} catch (e) {{
    console.error("ERROR:", e.message);
  }}
}})();
"""
        script_path = "/tmp/_puter_gen.js"
        with open(script_path, "w") as f:
            f.write(script)

        result = subprocess.run(
            ["node", script_path],
            capture_output=True, text=True, timeout=120,
        )

        if "OK" in result.stdout:
            return True
        else:
            print(f"  ✗ Puter.js error: {result.stderr[:200]}")
            return False


# ── Trait Generation Orchestrator ────────────────────────────────────

TRAIT_PROMPTS = {
    "background": {
        "sky": "a bright blue sky with soft clouds, digital art, 1024x1024",
        "dungeon": "dark stone dungeon with torches, pixel art style, 1024x1024",
        "forest": "enchanted forest with glowing mushrooms, fantasy art, 1024x1024",
        "volcano": "erupting volcano against dark sky, dramatic lighting, 1024x1024",
        "void": "cosmic void with distant stars and nebula, space art, 1024x1024",
        "city": "neon-lit cyberpunk city at night, rain, 1024x1024",
        "lab": "futuristic laboratory with holographic displays, 1024x1024",
        "neon": "neon grid in cyberspace, Tron aesthetic, 1024x1024",
        "wasteland": "post-apocalyptic wasteland with ruins, 1024x1024",
        "digital": "abstract digital landscape made of code and data streams, 1024x1024",
        "library": "ancient magical library with floating books, 1024x1024",
        "tower": "high wizard tower above clouds, fantasy, 1024x1024",
        "astral": "astral plane with swirling cosmic energy, 1024x1024",
        "mountain": "snow-capped mountain peak at sunset, 1024x1024",
        "ocean": "deep ocean with bioluminescent creatures, 1024x1024",
        "cosmos": "galaxy spiral nebula with planets, 1024x1024",
    },
    "body": {
        "human_male": "a muscular human warrior body, fantasy character design, clean silhouette",
        "human_female": "a fit human female warrior body, fantasy character design, clean silhouette",
        "orc": "a large green orc body with muscular build, fantasy",
        "dwarf": "a stout dwarf body with beard, fantasy character",
        "undead": "a skeletal undead warrior body with dark energy, gothic",
        "elf": "a slender elegant elf body with pointed ears, fantasy",
        "ancient": "an ancient being body with runic tattoos, mythical",
        "angel": "a celestial angel body with glowing aura, divine",
        "chrome": "a sleek chrome-plated cyborg body, cyberpunk",
        "steel": "a steel-armored cyborg body with rivets, cyberpunk",
        "carbon": "a matte black carbon fiber cyborg body, futuristic",
        "prototype": "a prototype cyborg body with exposed circuits, cyberpunk",
        "quantum": "a quantum-enhanced cyborg body shimmering with energy",
        "wolf": "a massive wolf body with thick fur, mythical beast",
        "bear": "a giant bear body with powerful muscles, wild",
        "serpent": "a long serpentine dragon body with scales",
        "lion": "a majestic lion body with golden mane",
        "dragon": "a powerful dragon body with iridescent scales",
    },
}


def generate_trait_set(player_type: str, layer_name: str, trait_name: str,
                       prompt: str, backend, output_path: str):
    """
    Generate one trait image and save it.
    Prompts are optimized for the specific backend.
    """
    print(f"  → {player_type}/{layer_name}/{trait_name}...", end=" ")
    success = backend.generate(prompt, output_path)
    print("✓" if success else "✗")
    time.sleep(0.5)  # Rate limit
    return success


def main():
    parser = argparse.ArgumentParser(description="Generate NFT Trait Assets via AI")
    parser.add_argument("--backend", choices=["puter", "nanobanana", "pollinations", "cloudflare"],
                        default="puter")
    parser.add_argument("--model", default="flux-schnell",
                        help="AI model name for the backend")
    parser.add_argument("--api-key", default="",
                        help="API key (for nanobanana, pollinations, cloudflare)")
    parser.add_argument("--account-id", default="",
                        help="Cloudflare account ID")
    parser.add_argument("--output", default="assets/traits",
                        help="Output base directory")
    parser.add_argument("--players", default="configs/players.yaml",
                        help="Players config YAML")
    parser.add_argument("--traits", nargs="+", default=[],
                        help="Specific traits to generate (default: all)")

    args = parser.parse_args()

    # Set up backend
    if args.backend == "puter":
        backend = PuterBackend(model=args.model)
    elif args.backend == "nanobanana":
        key = args.api_key or os.getenv("NANO_BANANA_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            print("✗ Need --api-key or NANO_BANANA_KEY for nanobanana backend")
            sys.exit(1)
        backend = NanoBananaBackend(api_key=key, model=args.model)
    elif args.backend == "pollinations":
        backend = PollinationsBackend(api_key=args.api_key)
    elif args.backend == "cloudflare":
        key = args.api_key or os.getenv("CLOUDFLARE_API_TOKEN")
        if not key or not args.account_id:
            print("✗ Need --api-key and --account-id for cloudflare")
            sys.exit(1)
        backend = CloudflareBackend(account_id=args.account_id, api_token=key)

    # Load players config
    import yaml
    with open(args.players) as f:
        players = yaml.safe_load(f)["players"]

    output_base = Path(args.output)
    total, success = 0, 0

    for player_name, pconfig in players.items():
        for layer_name, trait_pool in pconfig["trait_pool"].items():
            for trait_name in trait_pool:
                if args.traits and trait_name not in args.traits and not any(
                    t in f"{player_name}/{layer_name}/{trait_name}" for t in args.traits
                ):
                    continue

                # Get prompt template
                prompt_template = TRAIT_PROMPTS.get(layer_name, {}).get(trait_name)
                if not prompt_template:
                    # Generate a generic prompt
                    prompt_template = f"{trait_name} {layer_name} for {player_name} character, game art, clean PNG on transparent background"

                # Add transparency instruction
                full_prompt = f"{prompt_template}, transparent background, isolated character, game asset, high quality"

                out_path = output_base / player_name / layer_name / f"{trait_name}.png"
                out_path.parent.mkdir(parents=True, exist_ok=True)

                total += 1
                if generate_trait_set(player_name, layer_name, trait_name,
                                       full_prompt, backend, str(out_path)):
                    success += 1

    print(f"\n✅ Generated {success}/{total} trait images")
    print(f"   Location: {output_base}")


if __name__ == "__main__":
    main()
