"""
config.py
---------
Central place for every dropdown option shown in the UI, plus model/API
settings. Keeping this separate from app.py means you can add a new
material, color, or style without touching any logic.
"""

# ---------------------------------------------------------------------------
# API / model settings
# ---------------------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"          # fast + strong reasoning, good for prompt writing
HF_IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"  # actively served across multiple providers
HF_PROVIDER = "auto"  # let HF route to whichever provider (fal-ai, replicate, together, etc.) currently serves the model

# ---------------------------------------------------------------------------
# Room types (matches the rooms in your FP1031 floor plan)
# ---------------------------------------------------------------------------
ROOM_TYPES = [
    "Bedroom",
    "Hall / Living Room",
    "Kitchen",
    "Toilet / Bathroom",
    "Store Room",
]

# ---------------------------------------------------------------------------
# Fields common to every room
# ---------------------------------------------------------------------------
DOOR_MATERIALS = ["Wood", "Teak Wood", "Steel", "Glass", "PVC", "Aluminium"]

DOOR_COLORS = [
    "Natural Wood Brown", "Walnut Finish", "Matte White", "Matte Black",
    "Charcoal Grey", "Glossy Red", "Navy Blue",
]

WALL_TEXTURES = [
    "Smooth Matte Paint", "Textured Paint", "Wallpaper",
    "Exposed Brick", "Wood Paneling", "Stone Cladding",
]

WALL_COLORS = [
    "Warm White", "Beige", "Pastel Blue", "Sage Green",
    "Light Grey", "Terracotta", "Charcoal",
]

FLOORING_TYPES = [
    "Italian Marble", "Wooden / Laminate", "Vitrified Tiles",
    "Granite", "Ceramic Tiles", "Polished Concrete",
]

FURNITURE_STYLES = [
    "Modern Minimalist", "Traditional Indian", "Scandinavian",
    "Industrial", "Luxury Classic", "Bohemian", "Contemporary",
]

LIGHTING_STYLES = [
    "Warm Ambient", "Cool White", "LED Strip Accent",
    "Natural Daylight", "Mood / Dim Lighting", "Chandelier Statement",
]

COLOR_THEMES = [
    "Neutral Earthy", "Monochrome", "Pastel", "Bold & Vibrant",
    "Contemporary Grey", "Warm Wood Tones",
]

# ---------------------------------------------------------------------------
# Room-specific extra fields: {room_type: {field_label: [options]}}
# ---------------------------------------------------------------------------
ROOM_SPECIFIC_FIELDS = {
    "Bedroom": {
        "Bed Style": [
            "King-size Wooden Bed", "Upholstered Bed",
            "Platform Bed", "Storage Bed", "Four-Poster Bed",
        ],
        "Wardrobe Style": [
            "Sliding Door Wardrobe", "Hinged Wooden Wardrobe",
            "Walk-in Closet", "Modular Wardrobe with Mirror",
        ],
        "Curtain Style": [
            "Sheer White", "Blackout Grey", "Printed Cotton",
            "Velvet Maroon", "Roman Blinds",
        ],
    },
    "Hall / Living Room": {
        "Sofa Style": [
            "L-Shaped Modern Sofa", "3+2 Fabric Sofa Set",
            "Leather Recliner Set", "Low-Seating Wooden Sofa",
        ],
        "TV Unit Style": [
            "Wall-Mounted Floating Unit", "Wooden Cabinet Unit",
            "Backlit Panel Unit", "Minimalist Console",
        ],
        "Ceiling Style": [
            "False Ceiling with Cove Lighting", "Plain Painted Ceiling",
            "Wooden Beam Ceiling", "POP Design Ceiling",
        ],
    },
    "Kitchen": {
        "Cabinet Style": [
            "Modular High-Gloss Cabinets", "Wooden Shaker Cabinets",
            "Handleless Matte Cabinets", "Two-Tone Cabinets",
        ],
        "Countertop Material": [
            "Granite", "Quartz", "Marble", "Stainless Steel",
        ],
        "Backsplash Style": [
            "Subway Tile", "Mosaic Tile", "Plain Glass Panel", "Stone Cladding",
        ],
    },
    "Toilet / Bathroom": {
        "Fittings Style": [
            "Matte Black Fittings", "Chrome Fittings", "Rose Gold Fittings",
        ],
        "Sanitary Ware Style": [
            "Wall-Mounted Modern", "Freestanding Bathtub Setup", "Compact Standard",
        ],
        "Shower Type": [
            "Rain Shower Enclosure", "Standard Shower Curtain Area", "Walk-in Glass Shower",
        ],
    },
    "Store Room": {
        "Shelving Style": [
            "Open Metal Racks", "Wooden Built-in Shelves", "Modular Storage Units",
        ],
    },
}
