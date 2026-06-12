"""
Weighted rarity system for NFT trait selection.
"""
import random
import yaml
from typing import Any


RARITY_TIERS = {
    "common":     (0.00, 0.49),  # 49%
    "uncommon":   (0.49, 0.79),  # 30%
    "rare":       (0.79, 0.94),  # 15%
    "epic":       (0.94, 0.99),  # 5%
    "legendary":  (0.99, 1.00),  # 1%
}


def select_trait(trait_pool: dict[str, dict], seed: int | None = None) -> tuple[str, str]:
    """
    Weighted random selection from a trait pool.

    Args:
        trait_pool: { trait_name: { weight: int, rarity: str } }
        seed: Optional seed for deterministic generation

    Returns:
        (trait_name, rarity_tier)
    """
    rng = random.Random(seed)

    # Build weighted list
    items = list(trait_pool.items())
    total_weight = sum(item[1]["weight"] for item in items)

    roll = rng.uniform(0, total_weight)
    cumulative = 0

    for name, config in items:
        cumulative += config["weight"]
        if roll <= cumulative:
            return name, config["rarity"]

    # Fallback to last item
    return items[-1][0], items[-1][1]["rarity"]


def generate_dna(player_type: str, layers_order: list[str],
                 trait_pool: dict, seed: int) -> dict:
    """
    Generate a full DNA sequence for one NFT.

    Returns:
        { layer: { "value": str, "rarity": str }, ... }
    """
    dna = {}
    for layer in layers_order:
        if layer in trait_pool:
            value, rarity = select_trait(trait_pool[layer], seed + sum(ord(c) for c in layer))
            dna[layer] = {"value": value, "rarity": rarity}
    return dna


def check_unique(dna: dict, existing_set: set) -> bool:
    """Check if a DNA sequence is unique among generated items."""
    dna_str = "|".join(f"{k}={v['value']}" for k, v in sorted(dna.items()))
    return dna_str not in existing_set


def calculate_rarity_score(dna: dict) -> float:
    """Calculate overall rarity score based on trait rarities."""
    scores = {
        "common": 1,
        "uncommon": 2,
        "rare": 4,
        "epic": 8,
        "legendary": 16,
    }
    total = sum(scores.get(t["rarity"], 1) for t in dna.values())
    max_possible = len(dna) * 16
    return total / max_possible if max_possible > 0 else 0
