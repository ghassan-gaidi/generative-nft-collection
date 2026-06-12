"""
Puter.js AI image generation wrapper.
Requires: npm install @heyputer/puter.js

Usage:
    from src.ai_generation.puter import PuterGenerator
    gen = PuterGenerator()
    gen.generate("a dragon", "output.png", model="gemini-3.1-flash-image-preview")
"""
import json
import subprocess
import tempfile
from pathlib import Path


class PuterGenerator:
    """AI image generation via Puter.js (free, no API key)."""

    def __init__(self, model: str = "gemini-3.1-flash-image-preview"):
        self.model = model
        self._check_deps()

    def _check_deps(self):
        """Verify @heyputer/puter.js is installed."""
        result = subprocess.run(
            ["node", "-e", "require('@heyputer/puter.js')"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "@heyputer/puter.js not found. Run: npm install @heyputer/puter.js"
            )

    def generate(self, prompt: str, output_path: str | Path,
                 model: str | None = None, width: int = 1024,
                 height: int = 1024) -> bool:
        """Generate an image via Puter.js."""
        use_model = model or self.model
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        js_code = f"""
const {{ puter }} = require('@heyputer/puter.js');
const fs = require('fs');

(async () => {{
  try {{
    const image = await puter.ai.txt2img(
      {json.dumps(prompt)},
      {{ model: {json.dumps(use_model)}, width: {width}, height: {height} }}
    );
    const buffer = await image.arrayBuffer();
    fs.writeFileSync({json.dumps(str(output_path))}, Buffer.from(buffer));
    console.log('OK');
  }} catch (e) {{
    console.error('ERROR', e.message);
  }}
}})();
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            script_path = f.name

        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True, text=True, timeout=120,
            )
            return "OK" in result.stdout
        except subprocess.TimeoutExpired:
            print(f"  ✗ Puter.js timeout for: {prompt[:50]}...")
            return False
        finally:
            Path(script_path).unlink(missing_ok=True)
