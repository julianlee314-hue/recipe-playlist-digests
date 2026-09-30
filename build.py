#!/usr/bin/env python3
"""Validate recipes.json and report counts. Optionally rebuild HTML via generate_site."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "recipes.json").read_text())
for r in data["recipes"]:
    for i in r["ingredients"]:
        if i.get("peanut") and i.get("required"):
            raise SystemExit(f"peanut marked required: {r['id']}")
print(f"recipes={data['recipe_count']} ingredients={len(data['ingredients'])} tools={len(data['tools'])}")
print("thin=", [r["num"] for r in data["recipes"] if r["thin"]])
print("index.html present=", (ROOT / "index.html").exists())
