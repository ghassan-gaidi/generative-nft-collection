"""
Main collection generation orchestrator.

Usage:
    python scripts/generate_collection.py \
        --config configs/collection.yaml \
        --count 100 \
        --output /tmp/nft-collection

This script:
  1. Loads player definitions from YAML
  2. Generates unique DNA sequences for each NFT
  3. Composites trait layers into final images
  4. Exports OpenSea-compatible metadata
"""
import argparse
import json
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rarity.weights import generate_dna, check_unique, calculate_rarity_score
from metadata.generator import MetadataGenerator
from layers.compositor import LayerCompositor


def load_config(config_path: str) -> dict:
    """Load YAML configuration."""
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_collection(players: dict, total_count: int,
                        output_dir: Path, canvas_size: tuple[int, int] = (1024, 1024)):
    """
    Generate the full NFT collection.

    Steps:
    1. Allocate supply per player type
    2. Generate unique DNA for each NFT
    3. Composite images
    4. Export metadata

    Returns:
        list of (token_id, dna, player_type, rarity_score)
    """
    output_dir = Path(output_dir)
    images_dir = output_dir / "images"
    metadata_dir = output_dir / "metadata"
    images_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    compositor = LayerCompositor(canvas_size=canvas_size)
    
    collection_name = "Generative NFT Collection"
    meta_gen = MetadataGenerator(
        collection_name=collection_name,
        description="AI-generated multi-player NFT collection",
        image_base_uri="",
    )

    # Allocate supply per player
    total_requested = 0
    player_allocations = {}
    for pname, pconfig in players.items():
        supply = pconfig.get("supply", total_count // len(players))
        player_allocations[pname] = supply
        total_requested += supply

    # Scale down if over total_count
    if total_requested > total_count:
        scale = total_count / total_requested
        for pname in player_allocations:
            player_allocations[pname] = max(1, int(player_allocations[pname] * scale))

    print(f"Allocations: {json.dumps(player_allocations, indent=2)}")

    collection = []
    existing_dna = set()
    token_id = 1
    seed = random.randint(0, 2**32)

    for player_type, pconfig in players.items():
        supply = player_allocations[player_type]
        layers_order = pconfig["layers"]
        trait_pool = pconfig["trait_pool"]
        generated = 0
        attempts = 0
        max_attempts = supply * 100  # Safety cap

        while generated < supply and attempts < max_attempts:
            dna = generate_dna(player_type, layers_order, trait_pool, seed + attempts)
            attempts += 1

            if check_unique(dna, existing_dna):
                existing_dna.add("|".join(
                    f"{k}={v['value']}" for k, v in sorted(dna.items())
                ))
                rarity_score = calculate_rarity_score(dna)

                # Composite image
                output_path = images_dir / f"{token_id}.png"
                try:
                    compositor.composite(dna, output_path, player_type)
                except FileNotFoundError as e:
                    print(f"  ⚠ Missing trait image for token #{token_id}: {e}")
                    print(f"     DNA: {dna}")
                    print(f"     Run generate_traits.py first or create trait PNGs")
                except Exception as e:
                    print(f"  ✗ Error compositing token #{token_id}: {e}")
                    continue

                # Generate metadata
                meta = meta_gen.generate_metadata(
                    token_id, dna, player_type, rarity_score
                )
                meta_gen.save_metadata(meta, metadata_dir, token_id)

                # Store raw data
                collection.append((token_id, dna, player_type, rarity_score))

                if token_id % 100 == 0:
                    print(f"  Generated {token_id}/{total_count}...")

                token_id += 1
                generated += 1

        print(f"  ✓ {player_type}: {generated} NFTs generated")

    # Export collection summary
    summary = {
        "total_supply": len(collection),
        "players": player_allocations,
        "unique_dna_count": len(existing_dna),
    }
    with open(output_dir / "collection_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Collection generated: {len(collection)} NFTs")
    print(f"   Images: {images_dir}")
    print(f"   Metadata: {metadata_dir}")

    return collection


def main():
    parser = argparse.ArgumentParser(description="Generate NFT Collection")
    parser.add_argument("--config", default="configs/collection.yaml",
                        help="Collection YAML config")
    parser.add_argument("--players", default="configs/players.yaml",
                        help="Players YAML config")
    parser.add_argument("--count", type=int, default=100,
                        help="Number of NFTs to generate")
    parser.add_argument("--output", default="assets/output",
                        help="Output directory")
    parser.add_argument("--size", default="1024",
                        help="Canvas size (e.g., 1024 or 1024x1024)")

    args = parser.parse_args()

    try:
        players = load_config(args.players)["players"]
    except KeyError:
        players = load_config(args.players)

    if "x" in args.size:
        w, h = args.size.split("x")
        canvas_size = (int(w), int(h))
    else:
        s = int(args.size)
        canvas_size = (s, s)

    generate_collection(players, args.count, Path(args.output), canvas_size)


if __name__ == "__main__":
    main()
