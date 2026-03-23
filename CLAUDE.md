# CLAUDE.md — project notes for Claude Code

## What this project does
Visualises workshop registration data from `registrations.csv` (semicolon-
delimited, 731 rows). Produces social-media-ready PNG dashboards and heatmaps.

## Key scripts and their outputs

| Script | Outputs | Run after |
|--------|---------|-----------|
| `normalize_universities.py` | `affiliation_map.csv`, `universities_normalized.csv` | — |
| `make_affiliation_per_row.py` | `affiliation_per_row.csv` | `normalize_universities.py` |
| `visualize.py` | `dashboard.png`, `dashboard_all_affiliations.png` | `normalize_universities.py` |
| `heatmaps.py` | `heatmaps.png` | — (standalone) |

## Pandas 3.0 gotcha — NaN vs empty string
After `pd.read_csv`, missing values in string columns remain as `pd.NA`
(not `""`) even if you do `.astype(str).str.strip().replace("nan", "")`.
Always use `.fillna(value)` to handle missing values before `.replace()`.
Example from career stage handling:
```python
col.fillna("Other / prefer not to say").replace({"Other": "Other / prefer not to say"})
```

## Affiliation normalisation
Two-pass approach in `normalize_universities.py`:
1. **ALIASES dict** — explicit raw → canonical mappings, including self-aliases
   to protect institutions from fuzzy clustering (e.g. "Aalborg University",
   "University of Oslo", "University of Turku", "Ulm University").
2. **Fuzzy clustering** (RapidFuzz token_sort_ratio ≥ 88) — only runs on names
   NOT in ALIASES. Picks the most frequent raw name in each cluster as canonical.

To permanently fix a wrong mapping: add it to the `ALIASES` dict in
`normalize_universities.py`, then re-run the script. Do NOT edit
`affiliation_map.csv` for permanent fixes — it gets overwritten on re-run.

To make a one-off manual correction: edit `affiliation_map.csv` directly
(the `fixed` column), then re-run `visualize.py` without re-running
`normalize_universities.py`.

Known false-positive fuzzy merges that are protected via self-aliases:
- Aalborg University ≠ Aalto University
- University of Oslo ≠ University of Oulu
- University of Turku ≠ University of Tartu
- Ulm University ≠ Umeå University
- Karelia University of Applied Sciences ≠ Arcada University of Applied Sciences
- Kristiania University of Applied Sciences ≠ Karelia University of Applied Sciences

## Colour palette (visualize.py)
```python
BG     = "#fafafa"   # background
TEXT   = "#222222"   # text / axis labels
ORANGE = "#e07b39"   # career stage bars
BLUE   = "#3a7ebf"   # discipline bars
GREEN  = "#2e8b57"   # discovery source bars
GRAY   = "#d8d8d8"   # world map land fill (no data)
```
Word cloud uses 7 high-contrast accent colours defined in `_WC_COLORS`.
Map uses the `yelloworangered` Vega colour scheme.

## Layout constants (visualize.py)
- `CHART_W = 750` — Altair spec width in px; with `scale_factor=2` the PNG
  is ≈ 1528 px wide.
- `BAR_W = (CHART_W - 2 * ROW_GAP) // 3` — each of the 3 histogram charts.
- `BAR_STEP = 26` — pixels per bar row; shared height = `max(n_bars) * BAR_STEP`.
- Word cloud height = `W * 0.30` where `W` is the actual rendered PNG width.

## Altair 6 notes
- `alt.Scale(step=...)` does not exist — set chart `height` explicitly instead.
- Colour legend position: use `orient="none"` with `legendX` / `legendY` for
  absolute placement inside the map view.
- Horizontal colour bar: `direction="horizontal"`, `titleOrient="left"`.

## Environment
Mamba/conda env at `./env/` (Python 3.11). Activate before running scripts.
All dependencies installed in the env; do not use `--user` or `sudo pip`.
