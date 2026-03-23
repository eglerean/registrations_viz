"""
heatmaps.py
───────────
Three cross-distribution heatmaps for pairs of categorical variables:
  1. Career stage  ×  Academic discipline
  2. Career stage  ×  Discovery source
  3. Academic discipline  ×  Discovery source

Cells show row-normalised percentages (% within the row category).
Discovery source is multi-select per respondent, so percentages in
heatmaps 2 & 3 can exceed 100 % across a row — each cell reads as
"X % of people in [row category] mentioned this source".

Output: heatmaps.png
"""

import altair as alt
import pandas as pd

# ── Load & clean (mirrors visualize.py) ──────────────────────────────────────
df = pd.read_csv("registrations.csv", sep=";")
df.columns = df.columns.str.strip()
for col in df.columns:
    df[col] = df[col].astype(str).str.strip().replace("nan", "")

BG   = "#fafafa"
TEXT = "#222222"

# ── Label abbreviations (same as visualize.py) ────────────────────────────────
DISC_ABBREV = {
    "Computer and Information Sciences": "Computer & Info. Sciences",
    "Earth and Related Environmental Sciences": "Earth & Env. Sciences",
    "Electrical Engineering, Electronic Engineering, Information Engineering":
        "Electrical & Electronic Eng.",
    "Other Engineering and Technologies": "Other Engineering",
}
SRC_ABBREV = {
    "Your university/ organization mailing list": "Uni/org mailing list",
    "Your university/ organization website":      "Uni/org website",
    "National HPC center website or mailing list":"National HPC center",
    "CodeRefinery newsletter": "CR newsletter",
    "CodeRefinery website":    "CR website",
    "Friend/ colleague":       "Friend / colleague",
}

# ── Derived columns ───────────────────────────────────────────────────────────
df["career"] = df["Career stage/ position"].replace("", "Not specified")

df["discipline_raw"] = df["Academic discipline"].replace("", pd.NA)
df["discipline"] = df["discipline_raw"].map(lambda x: DISC_ABBREV.get(x, x))

# Top-10 disciplines (by overall count)
top_disc = (
    df["discipline"].dropna().value_counts().head(10).index.tolist()
)

# Explode multi-select discovery source
df["source_raw"] = df["How did you find out about this workshop?"].replace("", pd.NA)
src_exploded = (
    df[["career", "discipline", "source_raw"]]
    .assign(source=df["source_raw"].str.split(";"))
    .explode("source")
    .assign(source=lambda d: d["source"].str.strip())
)
src_exploded["source"] = src_exploded["source"].map(
    lambda x: SRC_ABBREV.get(x, x) if pd.notna(x) else x
)

# Top-8 discovery sources (by exploded count)
top_src = (
    src_exploded["source"].dropna().value_counts().head(8).index.tolist()
)

# Career order (by overall frequency, descending)
career_order = (
    df["career"].value_counts().index.tolist()
)

# ── Helper: build long-form cross-tab with row-normalised % ──────────────────
def crosstab_pct(row_series, col_series, row_order, col_order):
    """Return long-form DataFrame with columns row, col, count, pct."""
    ct = pd.crosstab(row_series, col_series)
    # Keep only wanted columns/rows
    ct = ct[[c for c in col_order if c in ct.columns]]
    ct = ct.reindex([r for r in row_order if r in ct.index])
    ct = ct.fillna(0)
    pct = ct.div(ct.sum(axis=1).replace(0, pd.NA), axis=0).mul(100)
    long = (
        ct.stack().reset_index()
        .rename(columns={ct.index.name or "row": "row",
                         ct.columns.name or "col": "col",
                         0: "count"})
    )
    long_pct = (
        pct.stack().reset_index()
        .rename(columns={pct.index.name or "row": "row",
                         pct.columns.name or "col": "col",
                         0: "pct"})
    )
    return long.merge(long_pct, on=["row", "col"])

# ── Cross-tabs ────────────────────────────────────────────────────────────────
# 1. Career × Discipline  (single-select × single-select)
df_filt = df[df["discipline"].isin(top_disc) & df["career"].notna()]
ct1 = crosstab_pct(df_filt["career"], df_filt["discipline"],
                   career_order, top_disc)
ct1.columns = ["career", "discipline", "count", "pct"]

# 2. Career × Discovery  (single-select × multi-select, exploded)
src2 = (src_exploded[src_exploded["source"].isin(top_src) &
                     src_exploded["career"].notna()]
        .reset_index(drop=True))
ct2 = crosstab_pct(src2["career"], src2["source"],
                   career_order, top_src)
ct2.columns = ["career", "source", "count", "pct"]

# 3. Discipline × Discovery  (single-select × multi-select, exploded)
src3 = (src_exploded[src_exploded["source"].isin(top_src) &
                     src_exploded["discipline"].isin(top_disc)]
        .reset_index(drop=True))
ct3 = crosstab_pct(src3["discipline"], src3["source"],
                   top_disc, top_src)
ct3.columns = ["discipline", "source", "count", "pct"]

# ── Shared colour scale (same domain across all three heatmaps) ───────────────
max_pct = max(ct1["pct"].max(), ct2["pct"].max(), ct3["pct"].max())
color_scale = alt.Scale(scheme="blues", domain=[0, max_pct])

CELL_W = 38   # px per column cell
CELL_H = 30   # px per row cell

def _heatmap(data, x_col, y_col, x_order, y_order, title, x_label, y_label):
    w = len(x_order) * CELL_W
    h = len(y_order) * CELL_H
    base = alt.Chart(data).encode(
        x=alt.X(f"{x_col}:N", sort=x_order, title=x_label,
                axis=alt.Axis(labelAngle=-40, labelLimit=160,
                              labelFontSize=9, titleFontSize=10)),
        y=alt.Y(f"{y_col}:N", sort=y_order, title=y_label,
                axis=alt.Axis(labelLimit=180, labelFontSize=9,
                              titleFontSize=10)),
    )
    rects = base.mark_rect().encode(
        color=alt.Color("pct:Q",
                        scale=color_scale,
                        legend=alt.Legend(title="% of row",
                                          orient="bottom",
                                          direction="horizontal",
                                          gradientLength=120,
                                          gradientThickness=8,
                                          titleFontSize=9,
                                          labelFontSize=8)),
        tooltip=[
            alt.Tooltip(f"{y_col}:N", title=y_label),
            alt.Tooltip(f"{x_col}:N", title=x_label),
            alt.Tooltip("count:Q",    title="count"),
            alt.Tooltip("pct:Q",      title="% of row", format=".1f"),
        ],
    )
    text = base.mark_text(fontSize=7.5, color=TEXT).encode(
        text=alt.Text("pct:Q", format=".0f"),
        # White text on dark cells for readability
        color=alt.condition(
            alt.datum.pct > max_pct * 0.6,
            alt.value("white"),
            alt.value(TEXT),
        ),
    )
    return (
        alt.layer(rects, text)
        .properties(
            width=w, height=h,
            title=alt.TitleParams(text=title, fontSize=12,
                                  fontWeight="bold", color=TEXT),
        )
    )

hm1 = _heatmap(ct1, "discipline", "career",
               top_disc, career_order,
               "Career stage × Academic discipline",
               "Discipline", "Career stage")

hm2 = _heatmap(ct2, "source", "career",
               top_src, career_order,
               "Career stage × Discovery source",
               "Discovery source", "Career stage")

hm3 = _heatmap(ct3, "source", "discipline",
               top_src, top_disc,
               "Academic discipline × Discovery source",
               "Discovery source", "Discipline")

# ── Compose & export ──────────────────────────────────────────────────────────
dashboard = (
    alt.hconcat(hm1, hm2, hm3, spacing=40)
    .configure(background=BG)
    .configure_view(stroke="lightgray", strokeWidth=0.5)
    .configure_axis(grid=False, domainColor="#cccccc",
                    tickColor="#cccccc", labelColor=TEXT, titleColor=TEXT)
)

out = "heatmaps.png"
dashboard.save(out, scale_factor=2)
print(f"Saved {out}")
