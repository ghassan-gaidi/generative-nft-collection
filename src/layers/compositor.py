"""
Layer compositing engine — combines trait PNGs into final NFT artwork.
Uses Pillow for image processing.
"""
from PIL import Image
from pathlib import Path
from typing import Optional


class LayerCompositor:
    """
    Composites multiple transparent trait layers into one final image.

    Layer order matters: background first, then body, then
    clothes/armor, then accessories on top.
    """

    def __init__(self, canvas_size: tuple[int, int] = (1024, 1024)):
        self.canvas_size = canvas_size
        self.layer_dirs: dict[str, Path] = {}

    def register_trait_dir(self, layer_name: str, directory: Path):
        """Register where trait PNGs for a given layer live."""
        self.layer_dirs[layer_name] = directory

    def composite(self, dna: dict, output_path: Path,
                  player_type: str | None = None) -> Image.Image:
        """
        Build a final image from a DNA sequence.

        Args:
            dna: { layer_name: { "value": trait_name, ... }, ... }
            output_path: Where to save the final PNG
            player_type: Optional player subfolder in trait dirs

        Returns:
            The composited PIL Image
        """
        canvas = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))

        for layer_name, trait_info in dna.items():
            trait_value = trait_info["value"]
            if trait_value.lower() == "none":
                continue  # Skip "none" traits

            trait_path = self._find_trait(layer_name, trait_value, player_type)
            if trait_path and trait_path.exists():
                layer_img = Image.open(trait_path).convert("RGBA")
                layer_img = layer_img.resize(self.canvas_size, Image.LANCZOS)
                canvas = Image.alpha_composite(canvas, layer_img)

        # Save
        canvas.save(output_path, "PNG")
        return canvas

    def _find_trait(self, layer_name: str, trait_value: str,
                    player_type: str | None) -> Optional[Path]:
        """Find a trait PNG in registered directories."""
        search_paths = []

        if player_type:
            search_paths.append(
                Path(f"assets/traits/{player_type}/{layer_name}/{trait_value}.png")
            )

        search_paths.append(
            Path(f"assets/traits/{layer_name}/{trait_value}.png")
        )

        if layer_name in self.layer_dirs:
            search_paths.append(
                self.layer_dirs[layer_name] / f"{trait_value}.png"
            )

        for path in search_paths:
            if path.exists():
                return path

        return None

    def generate_preview(self, dna: dict, player_type: str | None = None) -> Image.Image:
        """Generate a preview image in memory (no save)."""
        canvas = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        for layer_name, trait_info in dna.items():
            trait_value = trait_info["value"]
            if trait_value.lower() == "none":
                continue
            trait_path = self._find_trait(layer_name, trait_value, player_type)
            if trait_path and trait_path.exists():
                layer_img = Image.open(trait_path).convert("RGBA")
                layer_img = layer_img.resize(self.canvas_size, Image.LANCZOS)
                canvas = Image.alpha_composite(canvas, layer_img)
        return canvas
