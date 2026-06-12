"""
Metadata generator — creates OpenSea/ERC-721 compliant JSON metadata files.
"""
import json
from pathlib import Path
from typing import Optional


class MetadataGenerator:
    """
    Generates metadata JSON files for NFT collections.
    Compliant with OpenSea metadata standards:
    https://docs.opensea.io/docs/metadata-standards
    """

    def __init__(self, collection_name: str = "Generative NFT Collection",
                 description: str = "AI-generated NFT collection with multi-player traits",
                 image_base_uri: str = "",
                 external_url: str = ""):
        self.collection_name = collection_name
        self.description = description
        self.image_base_uri = image_base_uri.rstrip("/")
        self.external_url = external_url

    def generate_metadata(self, token_id: int, dna: dict,
                          player_type: str,
                          rarity_score: float) -> dict:
        """
        Generate a single metadata object.

        Args:
            token_id: NFT token number
            dna: { layer_name: { "value": str, "rarity": str }, ... }
            player_type: Character class/player type
            rarity_score: 0-1 float

        Returns:
            Dict ready for JSON serialization
        """
        attributes = [
            {
                "trait_type": "Player Type",
                "value": player_type.replace("_", " ").title(),
            },
            {
                "trait_type": "Rarity Score",
                "value": f"{rarity_score:.4f}",
                "display_type": "number",
            },
        ]

        for layer_name, trait_info in dna.items():
            attributes.append({
                "trait_type": layer_name.replace("_", " ").title(),
                "value": trait_info["value"].replace("_", " ").title(),
            })
            attributes.append({
                "trait_type": f"{layer_name.replace('_', ' ').title()} Rarity",
                "value": trait_info["rarity"].title(),
            })

        metadata = {
            "name": f"{self.collection_name} #{token_id}",
            "description": self.description,
            "image": f"{self.image_base_uri}/{token_id}.png" if self.image_base_uri else "",
            "external_url": f"{self.external_url}/{token_id}" if self.external_url else "",
            "attributes": attributes,
        }

        return metadata

    @staticmethod
    def save_metadata(metadata: dict, output_dir: Path, token_id: int):
        """Save metadata to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{token_id}.json"
        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)
        return filepath

    @staticmethod
    def generate_collection_metadata(
        total_supply: int,
        name: str,
        description: str,
        image_url: str,
        banner_url: str = "",
    ) -> dict:
        """Generate contract-level metadata (ERC-7572)."""
        return {
            "name": name,
            "description": description,
            "image": image_url,
            "banner_image": banner_url,
            "external_link": "",
            "seller_fee_basis_points": 500,  # 5%
            "fee_recipient": "",
        }

    def export_all(self, collection: list[tuple[int, dict, str, float]],
                   output_dir: Path):
        """
        Export metadata for entire collection.

        Args:
            collection: [(token_id, dna, player_type, rarity_score), ...]
            output_dir: Target directory
        """
        meta_dir = output_dir / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)

        for token_id, dna, player_type, rarity_score in collection:
            metadata = self.generate_metadata(
                token_id, dna, player_type, rarity_score
            )
            self.save_metadata(metadata, meta_dir, token_id)

        # Also generate collection-level metadata
        collection_meta = self.generate_collection_metadata(
            total_supply=len(collection),
            name=self.collection_name,
            description=self.description,
            image_url=self.image_base_uri,
        )
        with open(meta_dir / "collection.json", "w") as f:
            json.dump(collection_meta, f, indent=2)
