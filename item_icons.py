#!/usr/bin/env python3
"""Nintendo-style animated item icons for the playlist cookbook.

Self-contained SVG sprites (~64x64) with soft inventory-icon styling.
No external images, fonts, or network. Same name always yields the same icon.

Public API
----------
item_icon(name, *, category=None, kind=None, size=64) -> str
    Return an HTML snippet: a <span class="item-icon"> wrapping an inline SVG.
item_icon_css() -> str
    Optional shared keyframe CSS (icons also embed scoped styles and work alone).
guess_shape(name, category=None, kind=None) -> str
    Shape recipe id used for the icon (useful for tests / debugging).
"""

from __future__ import annotations

import html as htmlmod
import re
from typing import Iterable

E = htmlmod.escape

# Soft, cream/paper-friendly midtones (fill, stroke/shadow, highlight).
_PALETTES: tuple[tuple[str, str, str], ...] = (
    ("#e8a87c", "#a86a42", "#f7dcc4"),  # peach
    ("#7eb8a2", "#3f7a66", "#c8e8dc"),  # sage
    ("#c9a227", "#8a6e14", "#f0e2a8"),  # gold
    ("#d4846a", "#9a4e38", "#f0c8b8"),  # terracotta
    ("#6a9bb8", "#3a6280", "#c0dcec"),  # sky
    ("#b88a9a", "#7a4e5e", "#e8c8d4"),  # rose
    ("#8a9a6a", "#566a3a", "#d4e0b8"),  # olive
    ("#c47a5a", "#8a4a32", "#ecc4b0"),  # copper
    ("#7a8ab8", "#44507a", "#c8d0e8"),  # periwinkle
    ("#a87858", "#6e4a32", "#e0c4a8"),  # cocoa
    ("#5a9a8a", "#2e6a5c", "#b8e0d4"),  # teal
    ("#d4a060", "#8a6830", "#f0dcb0"),  # honey
    ("#9a7ab0", "#5e4880", "#dcc8e8"),  # lilac
    ("#b07070", "#7a4040", "#e8c0c0"),  # brick
    ("#6a8a9a", "#3e5a68", "#c0d4e0"),  # slate
    ("#c89878", "#8a6040", "#ecd4bc"),  # sand
)

_ACCENTS = (
    "#fbf3e6", "#fff9f0", "#ffe8c8", "#e8f5f0", "#f0e8d8",
    "#fff0e0", "#e8f0e8", "#f5e6d0",
)


def _fnv(s: str) -> int:
    h = 2166136261
    for ch in s.lower().strip():
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _uid(name: str) -> str:
    return f"ii{_fnv(name):08x}"


# Well-known name tints (fill, stroke, highlight) — still cream-friendly.
_NAME_TINTS: tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...] = (
    (("black bean", "black beans"), ("#4a3a38", "#2a2018", "#8a7870")),
    (("red lentil", "red lentils", "lentil"), ("#c45a3a", "#8a3020", "#e8a090")),
    (("soy sauce",), ("#3a2a28", "#1a1210", "#8a6a58")),
    (("peanut butter", "peanut"), ("#d4a060", "#8a6830", "#f0dcb0")),
    (("chicken",), ("#e8b898", "#a87858", "#f5dcc8")),
    (("tuna",), ("#d4848a", "#8a484e", "#f0c8cc")),
    (("egg",), ("#f5eed8", "#c4a868", "#fffaf0")),
    (("rice",), ("#f0e8d8", "#a09070", "#fffaf0")),
    (("popcorn",), ("#f0e070", "#a89030", "#fff8c8")),
    (("cottage cheese", "cheese"), ("#f0e060", "#c9a227", "#fff8c0")),
    (("pasta", "lasagna", "noodle"), ("#e8c878", "#a88838", "#f8e8b8")),
)

def _colors(name: str) -> tuple[str, str, str, str]:
    h = _fnv(name)
    fill, stroke, hi = _PALETTES[h % len(_PALETTES)]
    accent = _ACCENTS[(h >> 8) % len(_ACCENTS)]
    n = _norm(name)
    for keys, tint in _NAME_TINTS:
        if any(k == n or k in n for k in keys):
            fill, stroke, hi = tint
            break
    return fill, stroke, hi, accent


def _specks(h: int, stroke: str) -> str:
    """Tiny hash-driven dots so same-shape icons still differ."""
    parts = []
    for i in range(3):
        x = 18 + ((h >> (i * 5)) % 28)
        y = 22 + ((h >> (i * 5 + 3)) % 24)
        r = 1.0 + ((h >> (i * 3)) % 3) * 0.4
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{stroke}" opacity=".22"/>'
        )
    return "".join(parts)


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())


# Keyword → shape. First match wins; order matters (more specific first).
_SHAPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("peanut", ("peanut butter", "peanuts", "peanut")),
    ("bottle", ("soy sauce", "fish sauce", "oyster sauce", "vinegar", "mirin",
                "shaoxing", "teriyaki", "maggi", "worcester", "vanilla",
                "maple syrup", "honey", "wine", "oil spray")),
    ("oil", ("sesame oil", "oil", "ghee", "tallow")),
    ("jar", ("mayo", "paste", "ketchup", "gochujang", "hoisin", "bbq",
             "passata", "enchilada", "sriracha", "chili garlic", "jam", "nutella")),
    ("cheese", ("cottage cheese", "cheese", "mozzarella", "parmesan", "ricotta",
                "cheddar", "gouda", "nacho")),
    ("egg", ("egg",)),
    ("meat", ("chicken", "beef", "pork", "bacon", "steak", "sausage", "ham",
              "spam", "pepperoni", "salami", "tuna", "scallop")),
    ("broth", ("broth", "stock", "bouillon")),
    ("bean", ("black beans", "bean", "lentil", "chickpea", "edamame", "tofu")),
    ("grain", ("rice", "oat", "quinoa", "barley", "couscous", "popcorn")),
    ("pasta", ("lasagna", "pasta", "noodle", "spaghetti", "macaroni", "penne")),
    ("flour", ("flour", "cornstarch", "starch", "baking powder", "baking soda", "panko")),
    ("bread", ("bread", "tortilla", "bun", "bagel")),
    ("leaf", ("parsley", "cilantro", "basil", "mint", "bay", "thyme", "oregano",
              "kasoori", "methi", "scallion", "green onion", "spinach", "lettuce",
              "kale", "herb")),
    ("veg", ("onion", "garlic", "ginger", "carrot", "tomato", "potato", "pepper",
             "broccoli", "mushroom", "celery", "cabbage", "zucchini", "cucumber",
             "lemon", "lime", "avocado", "corn", "produce")),
    ("spice", ("salt", "pepper", "paprika", "cumin", "turmeric", "cinnamon",
               "chili", "cayenne", "powder", "flake", "seasoning", "spice",
               "sumac", "saffron", "clove", "nutmeg", "allspice", "coriander",
               "garam", "cajun", "chipotle", "kashmiri", "five-spice", "italian")),
    ("dairy", ("butter", "milk", "cream", "yogurt", "whey", "half-and-half", "sour cream")),
    ("sugar", ("sugar", "chocolate", "cocoa", "candy")),
    ("seed", ("sesame seeds", "chia", "almond", "cashew", "coconut", "seed", "nut")),
    ("water", ("water",)),
    # Tools
    ("wok", ("wok",)),
    ("skillet", ("skillet", "frying pan")),
    ("pan", ("muffin pan", "baking pan", "saucepan", "pan / tin", "baking sheet")),
    ("airfryer", ("air fryer",)),
    ("ricecooker", ("rice cooker",)),
    ("grill", ("grill", "smoker")),
    ("torch", ("torch",)),
    ("pot", ("dutch oven", "crockpot", "slow cooker", "instant pot", "pressure cooker", "pot")),
    ("oven", ("oven", "fridge", "freezer")),
    ("blender", ("blender", "ninja creami")),
    ("knife", ("knife", "cutter", "grater", "peeler")),
    ("bowl", ("bowl", "plate", "jar", "pitcher")),
    ("utensil", ("spatula", "spoon", "fork", "tongs", "whisk", "masher", "brush",
                 "rolling pin", "sieve", "strainer", "thermometer", "scale",
                 "skewers", "piping")),
    ("board", ("cutting board", "board", "rack", "foil", "parchment", "cloth",
               "paper towel", "toothpick", "lid")),
)


_CATEGORY_DEFAULTS: dict[str, str] = {
    "oils & fats": "oil",
    "sauces & condiments": "bottle",
    "dairy": "cheese",
    "proteins": "meat",
    "spices": "spice",
    "starches & grains": "grain",
    "legumes": "bean",
    "nuts & seeds": "seed",
    "aromatics & produce": "veg",
    "pantry staples": "jar",
    "tools": "utensil",
}


def guess_shape(name: str, category: str | None = None, kind: str | None = None) -> str:
    """Pick a shape recipe id from name keywords, then category/kind fallback."""
    n = _norm(name)
    for shape, keys in _SHAPE_RULES:
        for k in keys:
            if k == n or k in n:
                # Peanut garnish rule: only draw peanut when name is peanut-ish.
                if shape == "peanut" and "peanut" not in n:
                    continue
                return shape
    if kind and kind.lower() == "tool":
        return "utensil"
    if category:
        return _CATEGORY_DEFAULTS.get(category.lower().strip(), "generic")
    return "generic"


# --- SVG helpers -------------------------------------------------------------

def _shadow(cx: float = 32, cy: float = 56, rx: float = 18, ry: float = 4) -> str:
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
        f'fill="#1a2a28" opacity=".12"/>'
    )


def _glint(uid: str, x: float, y: float, r: float = 3) -> str:
    return (
        f'<circle class="{uid}-glint" cx="{x}" cy="{y}" r="{r}" '
        f'fill="#fff" opacity=".85"/>'
    )


def _sparkles(uid: str, pts: Iterable[tuple[float, float]]) -> str:
    parts = []
    for i, (x, y) in enumerate(pts):
        parts.append(
            f'<g class="{uid}-spark" style="animation-delay:{i * 0.35}s">'
            f'<path d="M{x} {y - 3}l1 2.2 2.4.2-1.8 1.6.6 2.4-2.2-1.2-2.2 1.2.6-2.4'
            f'-1.8-1.6 2.4-.2z" fill="#f0e2a8" stroke="#c9a227" stroke-width=".4"/>'
            f"</g>"
        )
    return "".join(parts)


def _steam(uid: str, x: float = 32) -> str:
    return (
        f'<g class="{uid}-steam" fill="none" stroke="#9bbfb3" stroke-width="1.6" '
        f'stroke-linecap="round" opacity=".7">'
        f'<path d="M{x - 6} 14c0-4 3-4 3-8"/>'
        f'<path d="M{x} 12c0-4 3-4 3-8"/>'
        f'<path d="M{x + 6} 14c0-4 3-4 3-8"/>'
        f"</g>"
    )


# --- Shape bodies (viewBox 0 0 64 64) ----------------------------------------

def _body_bottle(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    label = ("#5a1010", "#1a4a3c", "#8a5a20", "#2a4a80")[h % 4]
    return f"""
{_shadow(32, 57, 10, 3)}
<path d="M26 10h12v6l4 4v30a6 6 0 0 1-6 6H28a6 6 0 0 1-6-6V20l4-4z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<rect x="28" y="6" width="8" height="6" rx="1.5" fill="{stroke}"/>
<rect x="24" y="28" width="16" height="12" rx="2" fill="{label}" opacity=".9"/>
<path d="M28 14h8" stroke="{hi}" stroke-width="2" stroke-linecap="round" opacity=".7"/>
"""


def _body_oil(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 12, 3)}
<path d="M30 8h4v8l8 6v26a8 8 0 0 1-8 8h-8a8 8 0 0 1-8-8V22l8-6z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<ellipse cx="32" cy="36" rx="7" ry="10" fill="{hi}" opacity=".45"/>
<path d="M30 10h4" stroke="{hi}" stroke-width="2" opacity=".8"/>
"""


def _body_jar(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 14, 3)}
<rect x="18" y="18" width="28" height="32" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>
<rect x="16" y="14" width="32" height="8" rx="2" fill="{stroke}"/>
<rect x="20" y="16" width="24" height="3" rx="1" fill="{hi}" opacity=".5"/>
<ellipse cx="32" cy="34" rx="8" ry="6" fill="{accent}" opacity=".55"/>
"""


def _body_cheese(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Soft cheese wedge
    return f"""
{_shadow(34, 56, 16, 3.5)}
<path d="M12 44 L48 44 L52 28 L28 16 Z" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8" stroke-linejoin="round"/>
<path d="M28 16 L52 28 L48 44 L12 44 Z" fill="{hi}" opacity=".35"/>
<circle cx="30" cy="34" r="2.2" fill="{stroke}" opacity=".35"/>
<circle cx="38" cy="38" r="1.6" fill="{stroke}" opacity=".3"/>
<circle cx="34" cy="28" r="1.8" fill="{stroke}" opacity=".28"/>
"""


def _body_egg(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 12, 3)}
<ellipse cx="32" cy="34" rx="14" ry="18" fill="{accent}" stroke="{stroke}"
  stroke-width="1.8"/>
<ellipse cx="32" cy="36" rx="7" ry="8" fill="#e8a020"/>
<ellipse cx="28" cy="24" rx="4" ry="5" fill="#fff" opacity=".55"/>
"""


def _body_meat(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Bone-in cut / drumstick-ish or steak slab from hash
    if h % 2 == 0:
        return f"""
{_shadow(34, 56, 16, 3)}
<path d="M18 40c0-14 10-26 22-26 4 0 6 4 6 8 0 14-8 26-20 28-6 1-8-2-8-10z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<ellipse cx="44" cy="20" rx="5" ry="4" fill="{accent}" stroke="{stroke}" stroke-width="1.2"/>
<path d="M24 34c4-2 8-2 12 0" stroke="{hi}" stroke-width="2" fill="none"
  stroke-linecap="round" opacity=".7"/>
"""
    return f"""
{_shadow(32, 56, 16, 3)}
<path d="M14 28c2-10 12-16 24-14 8 2 14 10 12 18-2 10-12 16-22 14-10-2-16-8-14-18z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M22 30c6-4 14-4 20 0" stroke="{hi}" stroke-width="2.2" fill="none"
  stroke-linecap="round" opacity=".65"/>
<ellipse cx="30" cy="36" rx="3" ry="2" fill="{stroke}" opacity=".25"/>
"""


def _body_broth(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 14, 3)}
<path d="M18 24h28l-2 26a8 8 0 0 1-8 8H28a8 8 0 0 1-8-8z" fill="{fill}"
  stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<rect x="16" y="20" width="32" height="8" rx="2" fill="{stroke}"/>
<ellipse cx="32" cy="36" rx="9" ry="4" fill="{hi}" opacity=".4"/>
"""


def _body_bean(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 14, 3)}
<ellipse cx="24" cy="34" rx="9" ry="12" fill="{fill}" stroke="{stroke}"
  stroke-width="1.6" transform="rotate(-18 24 34)"/>
<ellipse cx="40" cy="36" rx="9" ry="12" fill="{fill}" stroke="{stroke}"
  stroke-width="1.6" transform="rotate(14 40 36)"/>
<ellipse cx="32" cy="28" rx="8" ry="11" fill="{hi}" stroke="{stroke}"
  stroke-width="1.6"/>
<path d="M32 20v14" stroke="{stroke}" stroke-width="1.2" opacity=".45"/>
"""


def _body_grain(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Sack of grain / rice mound
    return f"""
{_shadow(32, 57, 16, 3)}
<path d="M16 28c0-2 4-6 16-6s16 4 16 6l-2 24H18z" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8" stroke-linejoin="round"/>
<path d="M20 28c2-6 8-10 12-10s10 4 12 10" fill="none" stroke="{stroke}" stroke-width="1.5"/>
<rect x="26" y="34" width="12" height="10" rx="2" fill="{accent}" opacity=".7"/>
<circle cx="24" cy="40" r="1.4" fill="{stroke}" opacity=".35"/>
<circle cx="40" cy="42" r="1.2" fill="{stroke}" opacity=".3"/>
"""


def _body_pasta(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Nested pasta sheets / wavy noodles
    return f"""
{_shadow(32, 56, 16, 3)}
<path d="M14 22c6 4 12 4 18 0s12-4 18 0v6c-6-4-12-4-18 0s-12 4-18 0z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>
<path d="M14 32c6 4 12 4 18 0s12-4 18 0v6c-6-4-12-4-18 0s-12 4-18 0z"
  fill="{hi}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>
<path d="M14 42c6 4 12 4 18 0s12-4 18 0v6c-6-4-12-4-18 0s-12 4-18 0z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>
"""


def _body_flour(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 14, 3)}
<path d="M20 20h24l4 8v20a6 6 0 0 1-6 6H22a6 6 0 0 1-6-6V28z" fill="{accent}"
  stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M22 20c2-6 6-10 10-10s8 4 10 10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
<circle cx="28" cy="36" r="2" fill="{stroke}" opacity=".2"/>
<circle cx="36" cy="40" r="1.5" fill="{stroke}" opacity=".2"/>
"""


def _body_bread(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 16, 3)}
<path d="M12 36c0-12 8-20 20-20s20 8 20 20v6H12z" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8" stroke-linejoin="round"/>
<path d="M16 36c2-8 8-14 16-14s14 6 16 14" fill="none" stroke="{hi}" stroke-width="2"
  opacity=".6"/>
<ellipse cx="32" cy="40" rx="12" ry="4" fill="{stroke}" opacity=".12"/>
"""


def _body_leaf(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(34, 56, 12, 3)}
<path d="M32 50c-14-6-20-22-12-34 14-4 28 6 28 20-2 10-10 16-16 14z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M28 44c4-8 8-16 12-28" fill="none" stroke="{stroke}" stroke-width="1.4"
  stroke-linecap="round"/>
<path d="M30 34c4-2 8-2 10 2M28 40c5-1 9 0 11 3" fill="none" stroke="{hi}"
  stroke-width="1.2" opacity=".7"/>
"""


def _body_veg(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Round produce (onion/tomato-ish) with leaf top
    return f"""
{_shadow(32, 56, 14, 3)}
<circle cx="32" cy="36" r="16" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>
<path d="M28 20c2-6 6-8 8-6 0 4-2 8-4 10" fill="{fill}" stroke="{stroke}"
  stroke-width="1.4" stroke-linejoin="round"/>
<path d="M34 18c4-2 8 0 8 4-4 2-8 2-10 0" fill="#7eb8a2" stroke="#3f7a66"
  stroke-width="1.2"/>
<ellipse cx="26" cy="30" rx="4" ry="5" fill="{hi}" opacity=".45"/>
"""


def _body_spice(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 10, 3)}
<rect x="22" y="18" width="20" height="32" rx="4" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<path d="M24 18c0-6 4-10 8-10s8 4 8 10" fill="{stroke}"/>
<circle cx="32" cy="34" r="5" fill="{accent}" stroke="{stroke}" stroke-width="1"/>
<rect x="26" y="44" width="12" height="3" rx="1" fill="{hi}" opacity=".5"/>
"""


def _body_dairy(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Butter stick / cream carton
    return f"""
{_shadow(32, 56, 14, 3)}
<rect x="16" y="22" width="32" height="26" rx="4" fill="{accent}" stroke="{stroke}"
  stroke-width="1.8"/>
<rect x="16" y="22" width="32" height="8" rx="4" fill="{fill}"/>
<path d="M20 38h24" stroke="{hi}" stroke-width="2" stroke-linecap="round" opacity=".6"/>
<path d="M20 44h16" stroke="{stroke}" stroke-width="1.5" opacity=".3" stroke-linecap="round"/>
"""


def _body_sugar(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 12, 3)}
<path d="M20 24h24l4 28H16z" fill="{accent}" stroke="{stroke}" stroke-width="1.8"
  stroke-linejoin="round"/>
<path d="M22 24c2-8 6-12 10-12s8 4 10 12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
<circle cx="28" cy="40" r="2" fill="{hi}"/>
<circle cx="36" cy="44" r="1.6" fill="{hi}"/>
"""


def _body_seed(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 14, 3)}
<ellipse cx="22" cy="34" rx="7" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"
  transform="rotate(-25 22 34)"/>
<ellipse cx="32" cy="30" rx="7" ry="11" fill="{hi}" stroke="{stroke}" stroke-width="1.5"/>
<ellipse cx="42" cy="36" rx="7" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"
  transform="rotate(20 42 36)"/>
"""


def _body_peanut(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Only used when name contains peanut
    return f"""
{_shadow(32, 56, 12, 3)}
<path d="M24 20c-6 2-8 10-4 16 2 4 2 8-2 12 6 6 18 6 22 0-4-4-4-8-2-12 4-6 2-14-4-16-4-2-8-2-10 0z"
  fill="#d4a060" stroke="#8a6830" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M26 28c2 6 4 8 6 14M34 26c1 6 2 10 4 16" fill="none" stroke="#8a6830"
  stroke-width="1" opacity=".45"/>
<circle cx="28" cy="24" r="1.5" fill="#f0dcb0" opacity=".7"/>
"""


def _body_water(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 12, 3)}
<path d="M32 10c-10 14-14 22-14 30a14 14 0 0 0 28 0c0-8-4-16-14-30z"
  fill="#6a9bb8" stroke="#3a6280" stroke-width="1.8" stroke-linejoin="round"/>
<ellipse cx="28" cy="36" rx="4" ry="6" fill="#c0dcec" opacity=".55"/>
"""


def _body_wok(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 18, 3)}
{_steam("STEAM")}
<path d="M10 34c4 12 14 18 22 18s18-6 22-18" fill="{fill}" stroke="{stroke}"
  stroke-width="2" stroke-linejoin="round"/>
<path d="M8 34h48" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round"/>
<path d="M4 34h6M54 34h6" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round"/>
<ellipse cx="32" cy="36" rx="14" ry="3" fill="{hi}" opacity=".35"/>
""".replace("STEAM", "WOKSTEAM")


def _body_skillet(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(30, 56, 16, 3)}
{_steam("STEAM")}
<ellipse cx="28" cy="36" rx="18" ry="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>
<ellipse cx="28" cy="34" rx="12" ry="6" fill="{hi}" opacity=".3"/>
<path d="M44 34h16c2 0 3 2 2 4l-4 2" fill="none" stroke="{stroke}" stroke-width="2.5"
  stroke-linecap="round"/>
""".replace("STEAM", "SKSTEAM")


def _body_pan(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Rectangular baking / muffin tray vibe
    cups = ""
    if "muffin" in str(h):  # unused; real check below
        pass
    return f"""
{_shadow(32, 56, 18, 3)}
<rect x="10" y="22" width="44" height="28" rx="4" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<rect x="14" y="26" width="10" height="8" rx="2" fill="{hi}" opacity=".5"/>
<rect x="27" y="26" width="10" height="8" rx="2" fill="{hi}" opacity=".5"/>
<rect x="40" y="26" width="10" height="8" rx="2" fill="{hi}" opacity=".5"/>
<rect x="14" y="38" width="10" height="8" rx="2" fill="{accent}" opacity=".55"/>
<rect x="27" y="38" width="10" height="8" rx="2" fill="{accent}" opacity=".55"/>
<rect x="40" y="38" width="10" height="8" rx="2" fill="{accent}" opacity=".55"/>
"""


def _body_muffin(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return _body_pan(fill, stroke, hi, accent, h)


def _body_airfryer(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 16, 3)}
<rect x="14" y="14" width="36" height="38" rx="6" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<rect x="18" y="20" width="28" height="20" rx="3" fill="{stroke}" opacity=".35"/>
<rect x="20" y="44" width="24" height="4" rx="2" fill="{hi}" opacity=".6"/>
<circle cx="40" cy="18" r="2" fill="#c9a227"/>
{_sparkles("SP", [(22, 26), (36, 30), (28, 34)])}
""".replace("SP", "AFSP")


def _body_ricecooker(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 14, 3)}
{_steam("STEAM")}
<path d="M18 28h28v20a8 8 0 0 1-8 8H26a8 8 0 0 1-8-8z" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<path d="M16 24h32a4 4 0 0 0-4-6H20a4 4 0 0 0-4 6z" fill="{stroke}"/>
<circle cx="32" cy="40" r="4" fill="{hi}" opacity=".7"/>
""".replace("STEAM", "RCSTEAM")


def _body_grill(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 18, 3)}
<rect x="12" y="24" width="40" height="24" rx="4" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<path d="M16 30h32M16 36h32M16 42h32" stroke="{stroke}" stroke-width="1.6" opacity=".55"/>
<path d="M18 48v6M46 48v6M32 48v6" stroke="{stroke}" stroke-width="2" stroke-linecap="round"/>
{_sparkles("SP", [(20, 20), (40, 18), (30, 16)])}
""".replace("SP", "GRSP")


def _body_torch(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 10, 3)}
<path d="M28 30h8v22a4 4 0 0 1-8 0z" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>
<path d="M26 28h12l-2-6H28z" fill="{stroke}"/>
<path d="M32 8c4 6 6 10 0 16-6-6-4-10 0-16z" fill="#e8a020" stroke="#c47a20"
  stroke-width="1.2"/>
<path d="M32 12c2 3 3 5 0 8" fill="#ffe8a0" opacity=".85"/>
{_glint("GL", 34, 14, 2)}
""".replace("GL", "TORCHGL")


def _body_pot(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 16, 3)}
{_steam("STEAM")}
<path d="M16 28h32v18a10 10 0 0 1-10 10H26a10 10 0 0 1-10-10z" fill="{fill}"
  stroke="{stroke}" stroke-width="1.8"/>
<path d="M14 26h36" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round"/>
<path d="M8 26h8M48 26h8" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round"/>
<ellipse cx="32" cy="38" rx="10" ry="3" fill="{hi}" opacity=".35"/>
""".replace("STEAM", "POTSTEAM")


def _body_oven(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 16, 3)}
<rect x="14" y="12" width="36" height="40" rx="4" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<rect x="18" y="20" width="28" height="18" rx="2" fill="{stroke}" opacity=".3"/>
<circle cx="22" cy="16" r="2" fill="{hi}"/>
<circle cx="30" cy="16" r="2" fill="{hi}"/>
<rect x="20" y="42" width="24" height="5" rx="1.5" fill="{accent}" opacity=".6"/>
"""


def _body_blender(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 57, 12, 3)}
<path d="M22 18h20l4 22H18z" fill="{hi}" stroke="{stroke}" stroke-width="1.6"
  stroke-linejoin="round" opacity=".9"/>
<rect x="20" y="40" width="24" height="12" rx="3" fill="{fill}" stroke="{stroke}"
  stroke-width="1.6"/>
<path d="M28 14h8v6h-8z" fill="{stroke}"/>
"""


def _body_knife(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(34, 56, 14, 3)}
<path d="M12 40 L44 16c4-2 8 2 6 6L22 48z" fill="{accent}" stroke="{stroke}"
  stroke-width="1.5" stroke-linejoin="round"/>
<path d="M12 40c-2 4 2 8 6 6l4-2" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
<rect x="10" y="38" width="10" height="6" rx="2" fill="{fill}" stroke="{stroke}"
  stroke-width="1.2" transform="rotate(-30 15 41)"/>
"""


def _body_bowl(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 16, 3)}
<path d="M14 30c2 14 10 22 18 22s16-8 18-22" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8" stroke-linejoin="round"/>
<path d="M12 30h40" stroke="{stroke}" stroke-width="2" stroke-linecap="round"/>
<ellipse cx="32" cy="30" rx="16" ry="4" fill="{hi}" opacity=".4"/>
"""


def _body_utensil(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 12, 3)}
<rect x="28" y="28" width="8" height="24" rx="3" fill="{fill}" stroke="{stroke}"
  stroke-width="1.5"/>
<ellipse cx="32" cy="20" rx="12" ry="10" fill="{hi}" stroke="{stroke}" stroke-width="1.6"/>
<path d="M24 18h16M26 22h12" stroke="{stroke}" stroke-width="1.2" opacity=".4"/>
"""


def _body_board(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    return f"""
{_shadow(32, 56, 18, 3)}
<rect x="10" y="18" width="44" height="32" rx="4" fill="{fill}" stroke="{stroke}"
  stroke-width="1.8"/>
<path d="M16 28h32M16 36h24" stroke="{stroke}" stroke-width="1.2" opacity=".3"
  stroke-linecap="round"/>
<circle cx="48" cy="24" r="2" fill="{hi}" opacity=".7"/>
"""


def _body_generic(fill: str, stroke: str, hi: str, accent: str, h: int) -> str:
    # Soft rounded gem / pouch — unique via color + corner notch from hash
    notch = 4 + (h % 5)
    return f"""
{_shadow(32, 56, 14, 3)}
<path d="M20 18h24a6 6 0 0 1 6 6v20a6 6 0 0 1-6 6H20a6 6 0 0 1-6-6V24a6 6 0 0 1 6-6z"
  fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>
<circle cx="32" cy="34" r="{8 + h % 4}" fill="{hi}" opacity=".45"/>
<path d="M24 22h{notch * 2}" stroke="{accent}" stroke-width="2.5" stroke-linecap="round"/>
{_glint("GL", 24, 26, 2.5)}
""".replace("GL", "GENGL")


_BODIES = {
    "bottle": _body_bottle,
    "oil": _body_oil,
    "jar": _body_jar,
    "cheese": _body_cheese,
    "egg": _body_egg,
    "meat": _body_meat,
    "broth": _body_broth,
    "bean": _body_bean,
    "grain": _body_grain,
    "pasta": _body_pasta,
    "flour": _body_flour,
    "bread": _body_bread,
    "leaf": _body_leaf,
    "veg": _body_veg,
    "spice": _body_spice,
    "dairy": _body_dairy,
    "sugar": _body_sugar,
    "seed": _body_seed,
    "peanut": _body_peanut,
    "water": _body_water,
    "wok": _body_wok,
    "skillet": _body_skillet,
    "pan": _body_pan,
    "muffin": _body_muffin,
    "airfryer": _body_airfryer,
    "ricecooker": _body_ricecooker,
    "grill": _body_grill,
    "torch": _body_torch,
    "pot": _body_pot,
    "oven": _body_oven,
    "blender": _body_blender,
    "knife": _body_knife,
    "bowl": _body_bowl,
    "utensil": _body_utensil,
    "board": _body_board,
    "generic": _body_generic,
}

# Animations attached per shape family
_ANIM = {
    "bottle": ("bob", "glint"),
    "oil": ("bob", "glint"),
    "jar": ("bob", "glint"),
    "cheese": ("bob", "sparkle"),
    "egg": ("bob", "glint"),
    "meat": ("bob",),
    "broth": ("bob", "steam"),
    "bean": ("bob",),
    "grain": ("bob",),
    "pasta": ("bob", "glint"),
    "flour": ("bob",),
    "bread": ("bob",),
    "leaf": ("bob", "sparkle"),
    "veg": ("bob",),
    "spice": ("bob", "sparkle"),
    "dairy": ("bob", "glint"),
    "sugar": ("bob", "sparkle"),
    "seed": ("bob",),
    "peanut": ("bob",),
    "water": ("bob", "glint"),
    "wok": ("bob", "steam"),
    "skillet": ("bob", "steam"),
    "pan": ("bob",),
    "muffin": ("bob",),
    "airfryer": ("bob", "sparkle"),
    "ricecooker": ("bob", "steam"),
    "grill": ("bob", "sparkle"),
    "torch": ("bob", "glint"),
    "pot": ("bob", "steam"),
    "oven": ("bob",),
    "blender": ("bob",),
    "knife": ("bob", "glint"),
    "bowl": ("bob",),
    "utensil": ("bob", "glint"),
    "board": ("bob",),
    "generic": ("bob", "glint"),
}


def _scoped_style(uid: str, anims: tuple[str, ...]) -> str:
    """Minimal scoped CSS. Keyframes are unique per uid to avoid collisions."""
    rules = [
        f"#{uid}{{display:inline-block;vertical-align:middle;line-height:0}}",
        f"#{uid} svg{{display:block;overflow:visible}}",
    ]
    if "bob" in anims:
        rules += [
            f"#{uid} .{uid}-bob{{animation:{uid}-bob 2.4s ease-in-out infinite;"
            f"transform-origin:center bottom}}",
            f"@keyframes {uid}-bob{{0%,100%{{transform:translateY(0)}}"
            f"50%{{transform:translateY(-2.5px)}}}}",
        ]
    if "glint" in anims:
        rules += [
            f"#{uid} .{uid}-glint{{animation:{uid}-glint 2.8s ease-in-out infinite}}",
            f"@keyframes {uid}-glint{{0%,70%,100%{{opacity:.15;transform:scale(.6)}}"
            f"85%{{opacity:.95;transform:scale(1.15)}}}}",
        ]
    if "steam" in anims:
        rules += [
            f"#{uid} .{uid}-steam{{animation:{uid}-steam 2.2s ease-in-out infinite;"
            f"transform-origin:center bottom}}",
            f"@keyframes {uid}-steam{{0%,100%{{opacity:.15;transform:translateY(2px)}}"
            f"50%{{opacity:.75;transform:translateY(-3px)}}}}",
        ]
    if "sparkle" in anims:
        rules += [
            f"#{uid} .{uid}-spark{{animation:{uid}-spark 2s ease-in-out infinite;"
            f"transform-origin:center}}",
            f"@keyframes {uid}-spark{{0%,100%{{opacity:.1;transform:scale(.5) rotate(0deg)}}"
            f"50%{{opacity:1;transform:scale(1) rotate(18deg)}}}}",
        ]
    return "".join(rules)


def _fix_steam_spark_ids(body: str, uid: str) -> str:
    """Rewrite placeholder class hooks that shape bodies may embed."""
    # Shape helpers use hard-coded class prefixes for steam/spark/glint in a few places;
    # normalize any *-steam / *-spark / *-glint to uid-scoped classes.
    body = re.sub(r'class="[^"]*-steam"', f'class="{uid}-steam"', body)
    body = re.sub(r'class="[^"]*-spark"', f'class="{uid}-spark"', body)
    body = re.sub(r'class="[^"]*-glint"', f'class="{uid}-glint"', body)
    return body


def _shape_for_name(name: str, category: str | None, kind: str | None) -> str:
    n = _norm(name)
    # Explicit tool overrides that share words with ingredients (rice cooker vs rice)
    if kind and kind.lower() == "tool":
        tool_first = (
            ("air fryer", "airfryer"),
            ("rice cooker", "ricecooker"),
            ("muffin", "muffin"),
            ("kitchen torch", "torch"),
            ("torch", "torch"),
            ("wok", "wok"),
            ("skillet", "skillet"),
            ("grill", "grill"),
            ("smoker", "grill"),
            ("dutch oven", "pot"),
            ("crockpot", "pot"),
            ("slow cooker", "pot"),
            ("instant pot", "pot"),
            ("pressure cooker", "pot"),
            ("saucepan", "pan"),
            ("baking pan", "pan"),
            ("baking sheet", "pan"),
            ("muffin pan", "muffin"),
            ("oven", "oven"),
            ("fridge", "oven"),
            ("freezer", "oven"),
            ("blender", "blender"),
            ("ninja creami", "blender"),
            ("knife", "knife"),
            ("cutter", "knife"),
            ("grater", "knife"),
            ("bowl", "bowl"),
            ("plate", "bowl"),
            ("pot", "pot"),
            ("pan", "skillet"),
        )
        for key, shape in tool_first:
            if key in n:
                return shape
    # Ingredient: peanut only when peanut in name
    if "peanut" in n:
        return "peanut"
    # muffin pan before generic pan via rules
    if "muffin" in n:
        return "muffin"
    return guess_shape(name, category=category, kind=kind)


def item_icon(
    name: str,
    *,
    category: str | None = None,
    kind: str | None = None,
    size: int = 64,
) -> str:
    """Return a self-contained animated item icon (HTML span + inline SVG).

    Parameters
    ----------
    name : str
        Ingredient or tool name (stable hash source for color).
    category : str, optional
        Cookbook category (e.g. "Dairy", "Tools") for shape fallback.
    kind : str, optional
        "ingredient" or "tool" — tools prefer cookware shapes.
    size : int
        CSS pixel size (default 64).
    """
    if not name or not str(name).strip():
        name = "?"
    name = str(name).strip()
    uid = _uid(name)
    h = _fnv(name)
    fill, stroke, hi, accent = _colors(name)
    shape = _shape_for_name(name, category, kind)
    body_fn = _BODIES.get(shape, _body_generic)
    anims = _ANIM.get(shape, ("bob", "glint"))

    raw_body = body_fn(fill, stroke, hi, accent, h)
    # Inject steam/sparkle nodes when the body didn't already include them
    extra = ""
    if "steam" in anims and f"{uid}-steam" not in raw_body and "-steam" not in raw_body:
        extra += _steam(uid)
    if "sparkle" in anims and "-spark" not in raw_body:
        # Deterministic sparkle positions from hash
        pts = (
            (12 + (h % 8), 12 + ((h >> 3) % 6)),
            (48 - ((h >> 5) % 8), 14 + ((h >> 7) % 5)),
            (30 + ((h >> 9) % 6), 10 + ((h >> 11) % 4)),
        )
        extra += _sparkles(uid, pts)
    if "glint" in anims and "-glint" not in raw_body:
        extra += _glint(uid, 22 + (h % 10), 18 + ((h >> 4) % 8), 2.5)

    marks = _specks(h, stroke)
    body = _fix_steam_spark_ids(extra + raw_body + marks, uid)
    style = _scoped_style(uid, anims)
    label = E(name)

    return (
        f'<span class="item-icon" id="{uid}" data-shape="{E(shape)}" '
        f'data-name="{label}" role="img" aria-label="{label}" '
        f'style="width:{int(size)}px;height:{int(size)}px">'
        f"<style>{style}</style>"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{int(size)}" '
        f'height="{int(size)}" aria-hidden="true">'
        f'<g class="{uid}-bob">{body}</g>'
        f"</svg></span>"
    )


def item_icon_css() -> str:
    """Optional shared utility CSS for layout; icons animate via scoped styles."""
    return (
        ".item-icon{flex-shrink:0;display:inline-block;line-height:0;"
        "filter:drop-shadow(0 1px 0 rgba(26,42,40,.06))}"
        ".ing-card > .item-icon,.tool-db-card > .item-icon,"
        ".ency-card > .item-icon{margin:0 0 .35rem}"
        ".ing-card .top .item-icon{margin-right:.4rem}"
        ".ency-glyph .item-icon{margin:0}"
        "@media (prefers-reduced-motion:reduce){.item-icon *{"
        "animation:none!important}}"
    )


__all__ = ["item_icon", "item_icon_css", "guess_shape"]
