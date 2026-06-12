# Generative NFT Collection 🎨

> **AI-powered generative NFT collection engine** — multi-player layered art with random trait combination, rarity weighting, and OpenSea-ready metadata.

## Architecture

```
AI Art APIs ──→ Trait PNGs ──→ Layer Engine ──→ Collection
(Puter.js/      (assets/       (Python/          (images +
 Pollinations/    traits/)       Node.js)          metadata/
 Nano Banana)                                      output/)
```

### Core Components

| Component | Description |
|-----------|-------------|
| **AI Asset Generator** | Generates trait images via free AI APIs (Puter.js, Nano Banana, Pollinations) |
| **Layer Engine** | Python/Node.js compositor combining trait layers into final artwork |
| **Player System** | Multiple character categories (`warrior`, `mage`, `cyborg`, etc.) with distinct trait pools |
| **Rarity System** | Weighted random selection — supports `common/uncommon/rare/epic/legendary` tiers |
| **Metadata Generator** | ERC-721/OpenSea compliant JSON with trait attributes |
| **Upload Pipeline** | Batch upload to IPFS/Arweave + pinning |

### Supported AI Backends

All **free**, no GPU needed:

- **Puter.js** — 30+ models (Nano Banana, Flux Schnell, GPT Image, DALL-E 3, Seedream, SD3)
- **Nano Banana (Gemini API)** — gemini-3.1-flash-image, gemini-3-pro-image
- **Pollinations.AI** — Flux, GPT Image with free `pk_` key
- **Cloudflare Workers AI** — FLUX Schnell (10k images/day free)

---

## Quick Start

```bash
# Clone + install
git clone https://github.com/ghassan-gaidi/generative-nft-collection.git
cd generative-nft-collection

# Python deps
uv venv
source .venv/bin/activate
uv pip install pillow numpy requests

# Node deps (for Puter.js integration)
npm install @heyputer/puter.js puppeteer
```

### 1. Define Your Players

Edit `configs/players.yaml`:

```yaml
players:
  warrior:
    layers:
      - background
      - body
      - armor
      - helmet
      - weapon
      - accessory
    trait_pool:
      background: [sky, dungeon, forest, volcano]
      armor: [leather, chainmail, plate, dragonbone]
      weapon: [sword, axe, spear, hammer]

  mage:
    layers:
      - background
      - body
      - robe
      - staff
      - familiar
    trait_pool:
      robe: [apprentice, archmage, shadow, void]
      staff: [crystal, skull, rune, bone]
      familiar: [owl, cat, dragon, phoenix]
```

### 2. Generate Trait Assets (AI)

```bash
# Generate all trait PNGs via Puter.js (free, no key)
python scripts/generate_traits.py --backend puter --model flux-schnell

# Or via Nano Banana (your Gemini API key)
python scripts/generate_traits.py --backend nanobanana
```

### 3. Generate Collection

```bash
# Generate 10,000 NFTs with rarity weighting
python scripts/generate_collection.py --config configs/collection.yaml --count 10000

# Output: assets/output/images/{1..10000}.png
#         assets/output/metadata/{1..10000}.json
```

### 4. Upload & Mint

```bash
# Upload to IPFS
python scripts/upload_to_ipfs.py --input assets/output

# Deploy smart contract with ERC-721A
# (see docs/deployment.md)
```

---

## Project Structure

```
generative-nft-collection/
├── src/
│   ├── layers/           # Layer compositing engine
│   │   ├── compositor.py # Core image compositing
│   │   ├── player.py     # Player type definitions
│   │   └── traits.py     # Trait selection logic
│   ├── ai_generation/    # AI art API wrappers
│   │   ├── puter.py      # Puter.js integration
│   │   ├── nanobanana.py # Gemini API integration
│   │   └── pollinations.py # Pollinations integration
│   ├── metadata/         # Metadata generation
│   │   └── generator.py  # OpenSea-compliant JSON
│   └── rarity/           # Rarity system
│       └── weights.py    # Weighted random selection
├── configs/
│   ├── players.yaml      # Player type definitions
│   ├── collection.yaml   # Collection configuration
│   └── rarity.yaml       # Rarity tier definitions
├── assets/
│   ├── traits/           # Generated trait PNGs
│   ├── output/           # Generated NFT collection
│   └── players/          # Player-specific configs
├── scripts/
│   ├── generate_traits.py
│   ├── generate_collection.py
│   ├── upload_to_ipfs.py
│   └── deploy_contract.py
├── docs/
│   ├── architecture.md
│   ├── rarity.md
│   └── deployment.md
├── tests/
├── requirements.txt
├── package.json
└── README.md
```

---

## Key Features

- **Multi-Player System** — Distinct character types with separate trait pools
- **AI-Generated Traits** — All artwork created via free AI APIs (no design skills needed)
- **Weighted Rarity** — Legendary (1%) → Epic (5%) → Rare (15%) → Uncommon (30%) → Common (49%)
- **Incompatibility Rules** — Prevent impossible trait combinations
- **Forced Combinations** — Ensure certain traits appear together
- **OpenSea Metadata** — Full ERC-721 standard compliance
- **Batch Export** — Single ZIP with images + metadata
- **IPFS/Arweave** — Decentralized storage built-in

---

## Powered By

- [Puter.js](https://puter.com) — Free AI image generation, 30+ models, AGPL-3.0
- [HashLips Art Engine](https://github.com/HashLips/hashlips_art_engine) — OG layer compositing, MIT
- [nftchef/art-engine](https://github.com/nftchef/art-engine) — Advanced HashLips fork, MIT
- [ERC-721A](https://www.azuki.com/erc721a) — Gas-efficient minting by Azuki
