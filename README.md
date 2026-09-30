# Recipe Playlist Digests

Static cookbook site for Julius’s YouTube Recipes playlist cards (1–50).

- `index.html` — single-page site (station map, searchable ingredients/tools, recipe articles)
- `recipes.json` — data source
- `build.py` — regenerates JSON + HTML from `/workspace/artifacts/recipe-cards.md` (when present) or local `recipe-cards.md`

Warm printed-cookbook look (cream/paper, serif) with a teal accent. No food photos. Peanuts are never marked required; soy sauce is flagged as a legume.

## Search

Filter recipes by ingredient or tool in **Requires** / **Does not require** mode; ingredient and tool databases also have chip search and “show recipes that need / do not need this” buttons. Tools on each card are collapsed (`<details>`) but remain in the DOM for search.
