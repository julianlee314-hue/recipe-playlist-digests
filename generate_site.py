#!/usr/bin/env python3
"""Rebuild ingredient/tool indexes and index.html from recipes.json."""
from __future__ import annotations

import html as htmlmod
import json
import re
from pathlib import Path

from item_icons import item_icon, item_icon_css

ROOT = Path(__file__).resolve().parent
E = htmlmod.escape


def rebuild_indexes(data: dict) -> None:
    old_ing = {i["name"]: i for i in data.get("ingredients", [])}

    ing_map: dict[str, dict] = {}
    tool_map: dict[str, dict] = {}

    for r in data["recipes"]:
        if r.get("not_recipe"):
            continue
        ref = {"id": r["id"], "title": r["title"], "num": r["num"]}
        seen_ing_req: set[str] = set()
        seen_ing_opt: set[str] = set()
        for i in r["ingredients"]:
            name = i["name"]
            if name not in ing_map:
                prev = old_ing.get(name, {})
                ing_map[name] = {
                    "name": name,
                    "variants": list(prev.get("variants") or []),
                    "recipes_required": [],
                    "recipes_optional": [],
                    "legume": bool(prev.get("legume")),
                    "peanut": bool(prev.get("peanut")),
                    "category": prev.get("category") or guess_category(name),
                    "count": 0,
                }
            entry = ing_map[name]
            if i.get("legume"):
                entry["legume"] = True
            if i.get("peanut"):
                entry["peanut"] = True
            var = i.get("variant")
            if var and var not in entry["variants"]:
                entry["variants"].append(var)
            if i.get("required"):
                if name not in seen_ing_req:
                    entry["recipes_required"].append(ref)
                    seen_ing_req.add(name)
            else:
                if name not in seen_ing_opt and name not in seen_ing_req:
                    entry["recipes_optional"].append(ref)
                    seen_ing_opt.add(name)

        seen_tools: set[str] = set()
        for t in r["tools"]:
            name = t["name"]
            if name not in tool_map:
                tool_map[name] = {"name": name, "recipes": [], "count": 0}
            if name not in seen_tools:
                tool_map[name]["recipes"].append(ref)
                seen_tools.add(name)

    for entry in ing_map.values():
        req_ids = {x["id"] for x in entry["recipes_required"]}
        entry["recipes_optional"] = [x for x in entry["recipes_optional"] if x["id"] not in req_ids]
        entry["count"] = len({x["id"] for x in entry["recipes_required"] + entry["recipes_optional"]})
        entry["recipes_required"].sort(key=lambda x: x["num"])
        entry["recipes_optional"].sort(key=lambda x: x["num"])

    for entry in tool_map.values():
        entry["count"] = len(entry["recipes"])
        entry["recipes"].sort(key=lambda x: x["num"])

    data["ingredients"] = sorted(ing_map.values(), key=lambda x: (-x["count"], x["name"].lower()))
    data["tools"] = sorted(tool_map.values(), key=lambda x: (-x["count"], x["name"].lower()))
    data["recipe_count"] = len(data["recipes"])


def guess_category(name: str) -> str:
    n = name.lower()
    if n in {"oil", "sesame oil", "beef tallow", "ghee"} or "oil" == n:
        return "Oils & Fats"
    if any(
        x in n
        for x in (
            "cheese",
            "butter",
            "milk",
            "cream",
            "yogurt",
            "parmesan",
            "mozzarella",
            "ricotta",
            "gouda",
            "cheddar",
            "whey",
            "nacho",
        )
    ):
        return "Dairy"
    if any(
        x in n
        for x in (
            "sauce",
            "paste",
            "ketchup",
            "mayo",
            "hoisin",
            "mirin",
            "vinegar",
            "worcester",
            "bbq",
            "maggi",
            "oyster",
            "fish sauce",
            "sriracha",
            "chili garlic",
            "passata",
            "enchilada",
            "teriyaki",
            "gochujang",
            "nuoc",
        )
    ):
        return "Sauces & Condiments"
    if any(
        x in n
        for x in (
            "flour",
            "pasta",
            "noodle",
            "rice",
            "oat",
            "panko",
            "cornstarch",
            "starch",
            "bread",
            "tortilla",
            "pancake",
            "baking",
            "nori",
        )
    ):
        return "Starches & Grains"
    if any(
        x in n
        for x in (
            "chicken",
            "beef",
            "pork",
            "spam",
            "bacon",
            "steak",
            "sausage",
            "ham",
            "stock",
            "broth",
            "bouillon",
            "scallop",
            "whey protein",
        )
    ):
        return "Proteins"
    if any(
        x in n
        for x in (
            "salt",
            "pepper",
            "paprika",
            "cumin",
            "turmeric",
            "garam",
            "cinnamon",
            "chili",
            "cayenne",
            "thyme",
            "oregano",
            "bay",
            "sumac",
            "saffron",
            "seasoning",
            "powder",
            "flake",
            "kasoori",
            "methi",
            "cajun",
            "coriander",
            "allspice",
            "clove",
            "nutmeg",
            "five-spice",
            "italian",
            "chipotle",
            "kashmiri",
        )
    ):
        return "Spices"
    if any(x in n for x in ("lentil", "bean", "chickpea", "tofu", "edamame")):
        return "Legumes"
    if any(x in n for x in ("tuna", "rib")):
        return "Proteins"
    if any(x in n for x in ("mustard", "relish", "caper", "verjuice")):
        return "Sauces & Condiments"
    if "cornflake" in n:
        return "Starches & Grains"
    if any(x in n for x in ("peanut", "almond", "sesame seed", "chia", "cashew", "coconut")):
        return "Nuts & Seeds"
    if any(
        x in n
        for x in (
            "sugar",
            "honey",
            "vanilla",
            "water",
            "wine",
            "beer",
            "juice",
            "chocolate",
            "cocoa",
            "date",
            "ice",
            "maple",
            "dashi",
            "shaoxing",
            "red wine",
        )
    ):
        return "Pantry Staples"
    return "Aromatics & Produce"


def score_line(scores: dict) -> str:
    def fmt(k):
        v = scores.get(k)
        return "—" if v is None else str(v)

    return f"Taste {fmt('taste')} · Nutrition {fmt('nutrition')} · Unique {fmt('unique')}"



_STEP_PREFIX = re.compile(r"^\s*\d+[\.\)\:]\s+")


def strip_step_prefix(s: str) -> str:
    """Drop a redundant leading list marker if Do prose already includes one."""
    return _STEP_PREFIX.sub("", s, count=1)


def allergy_flags(r: dict) -> str:
    a = r["allergy"]
    bits = []
    if a.get("peanut_required"):
        bits.append('<span class="flag warn">Peanuts required</span>')
    elif a.get("peanut_optional"):
        bits.append('<span class="flag peanut">Peanuts optional — never required</span>')
    else:
        bits.append('<span class="flag ok">No peanuts required</span>')
    if a.get("incomplete"):
        bits.append('<span class="flag warn">Legumes incomplete / unknown</span>')
    elif a.get("legumes_required"):
        bits.append(
            '<span class="flag legume">Legume: ' + E(", ".join(a["legumes_required"])) + "</span>"
        )
    else:
        bits.append('<span class="flag ok">No legumes required</span>')
    return "".join(bits)


def ing_pills(r: dict) -> str:
    pills = []
    for i in r["ingredients"]:
        name = i["name"]
        warn = " ⚠" if i.get("legume") or i.get("peanut") else ""
        if i.get("required"):
            pills.append(f'<span class="pill req">{E(name)}{warn}</span>')
        else:
            pills.append(f'<span class="pill opt">{E(name)} *{warn}</span>')
    return "".join(pills)


def render_recipe(r: dict) -> str:
    thin = "true" if r["thin"] else "false"
    req = sorted({i["name"] for i in r["ingredients"] if i.get("required")})
    all_ings = sorted({i["name"] for i in r["ingredients"]})
    tools = [t["name"] for t in r["tools"]]
    data_req = E("||".join(req))
    data_all = E("||".join(all_ings))
    data_tools = E("||".join(tools))
    thin_badge = '<span class="thin-badge">THIN CARD</span>' if r["thin"] else ""
    extras = "".join(f'<p class="extra">{E(x)}</p>' for x in r.get("extras") or [])
    remember = "".join(f"<li>{E(x)}</li>" for x in r["remember"])
    do = "".join(f"<li>{E(strip_step_prefix(x))}</li>" for x in r["do"])
    watch = "".join(f"<li>{E(x)}</li>" for x in r["watch"])
    tool_lis = "".join(f"<li>{E(t['name'])}</li>" for t in r["tools"])
    tools_block = ""
    if tools:
        tools_block = (
            '<details class="tools-hide" data-tools-block>\n'
            '<summary>Tools <span class="muted">(hidden by default — still searchable)</span></summary>\n'
            f'<ul class="tool-list">{tool_lis}</ul></details>\n'
        )
    yt = ""
    if r.get("youtube"):
        yt = (
            f'<p class="head-links"><a class="yt" href="{E(r["youtube"])}" target="_blank" '
            f'rel="noopener">Watch on YouTube</a></p>'
        )
    return (
        f'<article class="recipe" id="{E(r["id"])}" data-num="{r["num"]}" data-title="{E(r["title"])}" '
        f'data-thin="{thin}" data-req-ings="{data_req}" data-all-ings="{data_all}" data-tools="{data_tools}">\n'
        f'<div class="head"><div class="head-row"><h2>{r["num"]}. {E(r["title"])}</h2>{thin_badge}</div>\n'
        f'<p class="chef">{E(r["meta"])}</p>\n'
        f"{yt}</div>\n"
        f'<div class="grid">\n'
        f'<div class="flags">{allergy_flags(r)}</div>\n'
        f'<div class="ing-pills">{ing_pills(r)}</div>\n'
        f"{extras}"
        f"<h3>Remember</h3><ul>{remember}</ul>\n"
        f"<h3>Do</h3><ol class='steps'>{do}</ol>\n"
        f"<h3>Watch</h3><ul>{watch}</ul>\n"
        f"{tools_block}"
        f'<div class="scores"><strong>{E(score_line(r["scores"]))}</strong></div>\n'
        f'<p class="reaction">{E(r["reaction"])}</p>\n'
        f"</div></article>\n"
        f'<p class="back-top"><a href="#top">↑ Back to top</a></p>'
    )



def render_not_recipe(r: dict) -> str:
    why = r.get("not_recipe_why") or (r.get("remember") or ["Set aside — not a cooking recipe."])[0]
    yt = ""
    if r.get("youtube"):
        yt = (
            f'<a class="yt" href="{E(r["youtube"])}" target="_blank" rel="noopener">Watch on YouTube</a>'
        )
    return (
        f'<article class="not-recipe" id="{E(r["id"])}" data-num="{r["num"]}">\n'
        f'<div class="nr-row"><h3>{r["num"]}. {E(r["title"])}</h3>'
        f'<span class="nr-badge">Set aside</span></div>\n'
        f'<p class="nr-meta">{E(r.get("channel") or "")}</p>\n'
        f'<p class="nr-why">{E(why)}</p>\n'
        f'<p class="nr-links">{yt}</p>\n'
        f"</article>"
    )


def render_ing_card(ing: dict) -> str:
    name = ing["name"]
    cat = ing["category"]
    variants = ing.get("variants") or []
    note_parts = []
    if variants:
        note_parts.append("Variants grouped: " + ", ".join(variants) + ".")
    if ing.get("legume"):
        note_parts.append("LEGUME flag (soy/beans/peas/lentils/chickpeas/tofu).")
    if ing.get("peanut"):
        note_parts.append("PEANUT flag.")
    note_parts.append(f"Seen across {ing['count']} card(s).")
    note = " ".join(note_parts)
    legume_span = ' <span class="flag legume">LEGUME</span>' if ing.get("legume") else ""
    peanut_span = ' <span class="flag peanut">PEANUT</span>' if ing.get("peanut") else ""
    req_links = (
        ", ".join(f'<a href="#{E(x["id"])}">{E(x["title"])}</a>' for x in ing["recipes_required"])
        or "—"
    )
    opt_links = (
        ", ".join(f'<a href="#{E(x["id"])}">{E(x["title"])}</a>' for x in ing["recipes_optional"])
        or "—"
    )
    nreq = len(ing["recipes_required"])
    icon = item_icon(name, category=cat, kind="ingredient", size=48)
    return (
        f'<article class="ing-card" data-cat="{E(cat)}" data-name="{E(name)}" data-note="{E(note)}" data-kind="ingredient">\n'
        f'<div class="top"><div class="top-name">{icon}<h4>{E(name)}{legume_span}{peanut_span}</h4></div><span class="ing-badge">{E(cat)}</span></div>\n'
        f'<p class="note">{E(note)}</p>\n'
        f'<div class="meta">In {ing["count"]} recipe(s) · required in {nreq}</div>\n'
        f'<div class="links"><strong>Requires:</strong> {req_links}</div>\n'
        f'<div class="links"><strong>Optional / incomplete:</strong> {opt_links}</div>\n'
        f'<div class="card-actions">\n'
        f'<button type="button" class="mini" data-filter-req="{E(name)}">Show recipes that need this</button>\n'
        f'<button type="button" class="mini ghost" data-filter-not="{E(name)}">Show recipes that do not</button>\n'
        f"</div></article>"
    )


def render_tool_card(tool: dict) -> str:
    name = tool["name"]
    note = f"Named on {tool['count']} recipe card(s)."
    links = ", ".join(f'<a href="#{E(x["id"])}">{E(x["title"])}</a>' for x in tool["recipes"])
    icon = item_icon(name, category="Tools", kind="tool", size=48)
    return (
        f'<article class="ing-card tool-db-card" data-cat="Tools" data-name="{E(name)}" data-note="Named tool" data-kind="tool">\n'
        f'<div class="top"><div class="top-name">{icon}<h4>{E(name)}</h4></div><span class="ing-badge">Tools</span></div>\n'
        f'<p class="note">{E(note)}</p>\n'
        f'<div class="meta">In {tool["count"]} recipe(s)</div>\n'
        f'<div class="links">{links}</div>\n'
        f'<div class="card-actions">\n'
        f'<button type="button" class="mini" data-filter-tool-req="{E(name)}">Show recipes that need this</button>\n'
        f'<button type="button" class="mini ghost" data-filter-tool-not="{E(name)}">Show recipes that do not</button>\n'
        f"</div></article>"
    )


def build_html(data: dict) -> str:
    css = (ROOT / "_css.txt").read_text()
    js = (ROOT / "_js.txt").read_text()
    all_cards = data["recipes"]
    recipes = [r for r in all_cards if not r.get("not_recipe")]
    set_aside = [r for r in all_cards if r.get("not_recipe")]
    n_total = len(all_cards)
    n_recipes = len(recipes)
    n_aside = len(set_aside)
    n_ing = len(data["ingredients"])
    n_tool = len(data["tools"])
    # Keep recipe_count as total cards for badge range; site text uses split counts.
    n = data["recipe_count"]

    toc = "".join(
        f'<li><a href="#{E(r["id"])}"><span class="toc-num">{r["num"]}</span>'
        f'<span class="toc-title">{E(r["title"])}'
        + (" <em>(thin)</em>" if r["thin"] else "")
        + "</span></a></li>"
        for r in recipes
    )

    equip = [t for t in data["tools"] if t["count"] >= 2][:14]
    pantry = data["ingredients"][:12]
    ency_equip = "".join(
        f'<article class="ency-card"><div class="ency-glyph" aria-hidden="true">{item_icon(t["name"], category="Tools", kind="tool", size=64)}</div>'
        f'<div class="body"><h4>{E(t["name"])}</h4><p>Named on {t["count"]} recipe(s).</p></div></article>'
        for t in equip
    )
    ency_pantry = "".join(
        f'<article class="ency-card"><div class="ency-glyph" aria-hidden="true">{item_icon(i["name"], category=i.get("category"), kind="ingredient", size=64)}</div>'
        f'<div class="body"><h4>{E(i["name"])}</h4><p>In {i["count"]} recipe(s).</p></div></article>'
        for i in pantry
    )

    cats = [
        "Aromatics & Produce",
        "Dairy",
        "Nuts & Seeds",
        "Oils & Fats",
        "Pantry Staples",
        "Proteins",
        "Sauces & Condiments",
        "Spices",
        "Starches & Grains",
        "Legumes",
    ]
    # keep only cats that exist
    present = {i["category"] for i in data["ingredients"]}
    cats = [c for c in cats if c in present]
    chips = (
        '<button type="button" class="ing-chip active" data-ing-chip="all">All</button>'
        + "".join(
            f'<button type="button" class="ing-chip" data-ing-chip="{E(c)}">{E(c)}</button>' for c in cats
        )
    )

    ing_cards = "".join(render_ing_card(i) for i in data["ingredients"])
    tool_cards = "".join(render_tool_card(t) for t in data["tools"])

    ing_opts = "".join(
        f'<option value="{E(i["name"])}">{E(i["name"])} ({i["count"]})</option>'
        for i in data["ingredients"]
    )
    tool_opts = "".join(
        f'<option value="{E(t["name"])}">{E(t["name"])} ({t["count"]})</option>'
        for t in data["tools"]
    )

    recipes_html = "\n".join(render_recipe(r) for r in recipes)
    not_recipes_html = "\n".join(render_not_recipe(r) for r in set_aside)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>YouTube Recipes — Playlist Digests</title>
<style>
{css}
{item_icon_css()}
.ing-card .top-name{{display:flex;align-items:center;gap:.45rem}}
</style>
</head>
<body>
<div class="wrap" id="top">
<header class="cover">
<svg class="hero-cook" viewBox="0 0 120 120" aria-hidden="true" width="108" height="108">
  <circle cx="60" cy="60" r="56" fill="#0f3f38"/>
  <circle cx="60" cy="60" r="50" fill="none" stroke="#c9a227" stroke-width="3"/>
  <ellipse cx="60" cy="98" rx="18" ry="5" fill="#1a2a28" opacity=".45"/>
  <g class="hc-flame">
    <path d="M46 96 C48 84 54 76 60 68 C66 76 72 84 74 96 Z" fill="#e87a20"/>
    <path d="M53 96 C55 88 58 82 60 76 C62 82 65 88 67 96 Z" fill="#f5d060"/>
  </g>
  <g class="hc-pot">
    <path d="M34 54 Q24 54 24 60 Q24 66 34 66" fill="none" stroke="#c9a227" stroke-width="3.2" stroke-linecap="round"/>
    <path d="M86 54 Q96 54 96 60 Q96 66 86 66" fill="none" stroke="#c9a227" stroke-width="3.2" stroke-linecap="round"/>
    <rect x="36" y="50" width="48" height="34" rx="6" fill="#1f7a6a" stroke="#c9a227" stroke-width="2"/>
    <rect x="32" y="46" width="56" height="9" rx="3.5" fill="#0f3f38" stroke="#c9a227" stroke-width="1.8"/>
    <ellipse cx="60" cy="50" rx="20" ry="4" fill="#2a9a86" opacity=".55"/>
  </g>
  <g class="hc-steam" fill="none" stroke="#fbf3e6" stroke-width="2.4" stroke-linecap="round">
    <path class="hc-s1" d="M48 42 C46 34 50 28 48 22"/>
    <path class="hc-s2" d="M60 40 C58 32 62 26 60 18"/>
    <path class="hc-s3" d="M72 42 C70 34 74 28 72 22"/>
  </g>
  <circle class="hc-bubble hc-b1" cx="50" cy="62" r="2.2" fill="#fbf3e6" opacity=".55"/>
  <circle class="hc-bubble hc-b2" cx="66" cy="58" r="1.7" fill="#fbf3e6" opacity=".45"/>
  <circle class="hc-bubble hc-b3" cx="58" cy="68" r="1.4" fill="#fbf3e6" opacity=".4"/>
</svg>
<div class="badge">Playlist Digests · Cards 1–{n_total}</div>
<h1>YouTube Recipes</h1>
<p class="sub">Searchable ingredients &amp; tools · peanut-aware · printed-cookbook warm</p>
<div class="sermon">
<p>Every card keeps Remember / Do / Watch, taste scores, and a reaction line. Peanuts are never required; soy sauce counts as soy. Tutorials follow the recipes; the full tools glossary is at the back.</p>
</div>
<p class="legal">YouTube Recipes playlist cards — searchable ingredients and tools. · {n_recipes} recipes · {n_aside} set aside · {n_ing} ingredients · {n_tool} tools</p>
</header>

<nav class="toc">
<h2>Table of contents</h2>
<p class="toc-jumps"><a href="#equipment">Tools &amp; pantry</a> · <a href="#recipes-part">Recipes</a> · <a href="#not-recipes">Tutorials</a> · <a href="#ingredients">Ingredient glossary</a> · <a href="#tools-db">All tools</a></p>
<ul class="toc-list">{toc}</ul>
</nav>

<section class="part" id="equipment">
<h2>Tools &amp; pantry</h2>
<p>Frequent tools and pantry heroes from the playlist cards.</p>
</section>
<div class="ency-equip" id="equipment-body">
<p class="ency-intro">No fake food photos. Encyclopedia cards track gear and staples from the playlist cards.</p>
<h3 class="ency-sub">Equipment</h3>
<div class="ency-grid">{ency_equip}</div>
<h3 class="ency-sub">Pantry Heroes</h3>
<div class="ency-grid">{ency_pantry}</div>
</div>

<section class="part" id="recipes-part">
<h2>Recipes</h2>
<p>Thin cards stay visible and labeled. Quantities are never invented. {n_recipes} cooking recipes ({n_aside} tutorials set aside after this section).</p>
</section>

<div class="filter-bar" id="recipe-filter">
<div class="filter-row">
<div><label for="filter-mode">Match</label>
<select id="filter-mode"><option value="require">Requires</option><option value="not">Does not require</option></select></div>
<div><label for="filter-ing">Ingredient</label>
<select id="filter-ing"><option value="">— any —</option>{ing_opts}</select></div>
<div><label for="filter-tool">Tool</label>
<select id="filter-tool"><option value="">— any —</option>{tool_opts}</select></div>
<div style="flex:1"><label for="filter-text">Text search</label>
<input type="search" id="filter-text" placeholder="Search recipe text…"/></div>
<button type="button" id="filter-apply">Apply</button>
<button type="button" class="ghost" id="filter-clear">Clear</button>
</div>
<div class="filter-status" id="filter-status"></div>
</div>

{recipes_html}

<section class="part" id="not-recipes">
<h2>Tutorials</h2>
<p>Not cooking recipes — kept with their original card numbers for review. They do not count in recipe search.</p>
</section>
<div class="not-recipes-body" id="not-recipes-body">
{not_recipes_html}
</div>

<section class="part" id="ingredients">
<h2>Ingredient glossary</h2>
<p>Every ingredient. Counts, required versus optional, and the recipes that use each one.</p>
</section>
<div class="ency-ings" id="ingredients-body">
<p class="ency-intro">One entry per ingredient. Salted butter folds under butter; light soy under soy sauce. The number is how many cards use it.</p>
<div class="ing-controls">
<input type="search" placeholder="Search the glossary…" data-ing-search aria-label="Search ingredients"/>
<div class="ing-chips">{chips}</div>
</div>
<div class="ing-stats"><span data-ing-count>{n_ing} ingredients shown</span> · {n_recipes} recipes indexed</div>
<div class="ing-db">{ing_cards}</div>
</div>

<section class="part" id="tools-db">
<h2>All tools</h2>
<p>Every tool named on the cards, with counts.</p>
</section>
<div class="ency-tools-db" id="tools-db-body">
<p class="ency-intro">Filter recipes by gear you have — or skip recipes that need a smoker, Creami, or Instant Pot.</p>
<div class="ing-controls">
<input type="search" placeholder="Search tools…" data-ing-search aria-label="Search tools"/>
<div class="ing-chips"><button type="button" class="ing-chip active" data-ing-chip="all">All</button></div>
</div>
<div class="ing-stats"><span data-ing-count>{n_tool} tools shown</span></div>
<div class="ing-db">{tool_cards}</div>
</div>

</div>
<script>
{js}
</script>
</body>
</html>
"""


def main():
    path = ROOT / "recipes.json"
    data = json.loads(path.read_text())
    rebuild_indexes(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "index.html").write_text(build_html(data))
    n_aside = sum(1 for r in data["recipes"] if r.get("not_recipe"))
    n_real = data["recipe_count"] - n_aside
    print(f"recipes={n_real} set_aside={n_aside} total={data['recipe_count']} ingredients={len(data['ingredients'])} tools={len(data['tools'])}")


if __name__ == "__main__":
    main()
