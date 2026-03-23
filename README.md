# Workshop Registration Visualisation

Generates a social-media-ready dashboard (`dashboard.png`) from raw workshop
registration data, including a world map, descriptive statistics panels, and a
word cloud of affiliated institutions.

## Input data

| File | Description |
|------|-------------|
| `registrations.csv` | Raw anonymised registration data, semicolon-delimited |

Relevant columns used:
- `Country`
- `Affiliation or university`
- `Career stage/ position`
- `Academic discipline`
- `How did you find out about this workshop?`

## Environment setup

The project uses a mamba/conda environment stored in `./env/`.
Activate it before running any script:

```bash
conda activate ./env
# or, if using mamba:
mamba activate ./env
```

Install dependencies (only needed once):

```bash
pip install altair vega_datasets vl-convert-python pandas pycountry \
            rapidfuzz wordcloud matplotlib pillow
```

## File generation workflow

### Step 1 — Normalise university/affiliation names

```bash
python3 normalize_universities.py
```

Reads `registrations.csv` and applies two passes of normalisation:

1. **Explicit alias table** — maps known abbreviations and spelling variants to a
   canonical name (e.g. `DTU`, `dtu`, `DTU Energy` → `Technical University of
   Denmark (DTU)`).
2. **Fuzzy clustering** — groups remaining near-duplicate names using
   token-sort ratio ≥ 88; picks the most frequent raw name in each cluster as
   canonical.

Outputs:

| File | Description |
|------|-------------|
| `affiliation_map.csv` | **Human-editable** mapping: one row per unique raw name, columns `original` and `fixed` |
| `universities_normalized.csv` | Same mapping with an additional `raw_count` column (used internally) |

**Editing the mapping:** open `affiliation_map.csv`, correct any `fixed` value,
and save. Re-running `normalize_universities.py` will overwrite this file, so
make manual edits *after* running the script or add corrections to the `ALIASES`
dict inside the script to make them permanent.

### Step 2 — Generate per-row affiliation lookup (optional)

```bash
python3 make_affiliation_per_row.py
```

Joins every row of `registrations.csv` with `affiliation_map.csv` and writes:

| File | Description |
|------|-------------|
| `affiliation_per_row.csv` | 731 rows, columns `original` (raw) and `fixed` (consolidated) |

Useful for auditing or importing back into another tool.

### Step 3 — Generate the dashboard images

```bash
python3 visualize.py
```

Reads `registrations.csv` and `affiliation_map.csv` and produces **two files**:

| File | Description |
|------|-------------|
| `dashboard.png` | Dashboard with word cloud showing affiliations with ≥ 5 registrations |
| `dashboard_all_affiliations.png` | Same dashboard with word cloud showing all affiliations |

Both are ≈ 1528 × 1950 px at 200 dpi (portrait, suitable for social media).

The dashboard contains four panels:

```
┌──────────────────────────────────────────────────────┐
│  World choropleth map  (naturalEarth1 projection)    │
│  (colour bar overlaid bottom-right)                  │
├───────────────────┬──────────────────┬───────────────┤
│  Career stage     │  Top 10 academic │  How did you  │
│  (bar chart)      │  disciplines     │  find out?    │
│                   │  (bar chart)     │  (bar chart)  │
├───────────────────┴──────────────────┴───────────────┤
│  Affiliated institutions  (word cloud)               │
└──────────────────────────────────────────────────────┘
```

### Step 4 — Generate cross-distribution heatmaps (optional)

```bash
python3 heatmaps.py
```

Produces three heatmaps showing row-normalised cross-distributions (% within
each row category) for every pair of categorical variables:

| Heatmap | Rows | Columns |
|---------|------|---------|
| 1 | Career stage | Top 10 academic disciplines |
| 2 | Career stage | Top 8 discovery sources |
| 3 | Top 10 disciplines | Top 8 discovery sources |

Discovery source is multi-select, so percentages in heatmaps 2 & 3 can
exceed 100 % across a row.

| File | Description |
|------|-------------|
| `heatmaps.png` | Three heatmaps side by side, shared colour scale |

## Full pipeline (all steps in order)

```bash
conda activate ./env
python3 normalize_universities.py   # → affiliation_map.csv
# (optionally edit affiliation_map.csv here)
python3 visualize.py                # → dashboard.png, dashboard_all_affiliations.png
python3 heatmaps.py                 # → heatmaps.png  (optional)
```

`make_affiliation_per_row.py` is optional and independent of `visualize.py`.

## Legacy files

| File | Description |
|------|-------------|
| `export_png.py` | Original Plotly-based country map (uses hardcoded counts from `data.csv`) |
| `map.png` | Output of `export_png.py` |
| `data.csv` | Aggregated country counts used by the legacy script |
