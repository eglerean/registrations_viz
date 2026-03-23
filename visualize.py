"""
Workshop registration dashboard for social media.
Produces dashboard.png: world map + career stage + disciplines + discovery source
                        + word cloud of affiliated institutions.
"""

import io
import altair as alt
from vega_datasets import data as vega_data
import pandas as pd
import pycountry
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from PIL import Image, ImageDraw, ImageFont

# ── Load & clean ──────────────────────────────────────────────────────────────
df = pd.read_csv("registrations.csv", sep=";")
df.columns = df.columns.str.strip()
for col in df.columns:
    df[col] = df[col].astype(str).str.strip().replace("nan", "")

TOTAL = len(df)

# ── Country → ISO numeric (for world topojson lookup) ─────────────────────────
MANUAL = {
    "Congo - Kinshasa": 180,   # DRC
    "Côte d\u2019Ivoire": 384,
    "Türkiye": 792,
    "Åland Islands": 248,      # part of Finland; likely absent from topo
    "American Samoa": 16,      # US territory; likely absent from topo
}

def to_iso_num(name):
    if not name:
        return None
    if name in MANUAL:
        return MANUAL[name]
    try:
        return int(pycountry.countries.search_fuzzy(name)[0].numeric)
    except Exception:
        print(f"  [WARN] no ISO match for: {name!r}")
        return None

country_counts = (
    df["Country"].replace("", pd.NA).dropna()
    .value_counts().reset_index()
)
country_counts.columns = ["Country", "count"]
country_counts["id"] = country_counts["Country"].apply(to_iso_num)
map_df = country_counts.dropna(subset=["id"]).copy()
map_df["id"] = map_df["id"].astype(int)

N_COUNTRIES = len(map_df)
print(f"Registrations: {TOTAL}  |  Mapped countries: {N_COUNTRIES}")

# ── Career stage ──────────────────────────────────────────────────────────────
OTHER = "Other / prefer not to say"
career = (
    df["Career stage/ position"]
    .fillna(OTHER)
    .replace({"": OTHER, "Other": OTHER})
    .value_counts().reset_index()
)
career.columns = ["stage", "count"]

# ── Academic disciplines (top 10) ─────────────────────────────────────────────
disc = (
    df["Academic discipline"].replace("", pd.NA).dropna()
    .value_counts().head(10).reset_index()
)
disc.columns = ["discipline", "count"]
# Shorten very long labels
ABBREV = {
    "Computer and Information Sciences": "Computer & Info. Sciences",
    "Earth and Related Environmental Sciences": "Earth & Env. Sciences",
    "Electrical Engineering, Electronic Engineering, Information Engineering":
        "Electrical & Electronic Eng.",
    "Other Engineering and Technologies": "Other Engineering",
}
disc["discipline"] = disc["discipline"].replace(ABBREV)

# ── Discovery sources (exploded on ";") ───────────────────────────────────────
src_series = (
    df["How did you find out about this workshop?"]
    .replace("", pd.NA).dropna()
    .str.split(";").explode().str.strip()
)
src_counts = src_series.value_counts().head(8).reset_index()
src_counts.columns = ["source", "count"]
# Shorten labels
SRC_ABBREV = {
    "Your university/ organization mailing list": "Uni/org mailing list",
    "Your university/ organization website": "Uni/org website",
    "National HPC center website or mailing list": "National HPC center",
    "CodeRefinery newsletter": "CR newsletter",
    "CodeRefinery website": "CR website",
    "Friend/ colleague": "Friend / colleague",
}
src_counts["source"] = src_counts["source"].replace(SRC_ABBREV)

# ── Colour palette ────────────────────────────────────────────────────────────
BG = "#fafafa"
ORANGE = "#e07b39"
BLUE   = "#3a7ebf"
GREEN  = "#2e8b57"
GRAY   = "#d8d8d8"
TEXT   = "#222222"

# ── 1. World map ──────────────────────────────────────────────────────────────
world = alt.topo_feature(vega_data.world_110m.url, "countries")

bg_map = (
    alt.Chart(world)
    .mark_geoshape(fill=GRAY, stroke="white", strokeWidth=0.4)
    .project("naturalEarth1")
)

choropleth = (
    alt.Chart(world)
    .mark_geoshape(stroke="white", strokeWidth=0.3)
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(map_df, "id", ["count", "Country"]),
    )
    .encode(
        color=alt.Color(
            "count:Q",
            scale=alt.Scale(scheme="yelloworangered", domainMin=1),
            legend=alt.Legend(
                title="# registrations",
                orient="none",
                legendX=440, legendY=300,   # bottom-right of the map view
                direction="horizontal",
                gradientLength=140,
                gradientThickness=10,
                titleFontSize=10,
                labelFontSize=9,
                titleOrient="left",
                padding=6,
                fillColor=BG,
                cornerRadius=4,
            ),
        ),
        tooltip=[
            alt.Tooltip("Country:N", title="Country"),
            alt.Tooltip("count:Q", title="Registrations"),
        ],
    )
    .project("naturalEarth1")
)

# Shared chart width — all panels match the map width
CHART_W  = 750
ROW_GAP  = 12                        # spacing between the 3 side-by-side charts
BAR_W    = (CHART_W - 2 * ROW_GAP) // 3   # ≈ 242 px each
BAR_STEP = 26                        # px per bar+gap (controls bar height)

map_chart = (
    (bg_map + choropleth)
    .properties(
        width=CHART_W,
        height=360,
        title=alt.TitleParams(
            text=f"CodeRefinery Workshop — {TOTAL} registrations from {N_COUNTRIES} countries",
            fontSize=18,
            fontWeight="bold",
            color=TEXT,
            anchor="middle",
            offset=8,
        ),
    )
)

def _hbar(data, cat_col, val_col, color, title, height):
    """Horizontal bar chart with category labels overlaid on the bar."""
    sorted_cats = data.sort_values(val_col, ascending=False)[cat_col].tolist()
    y_enc = alt.Y(f"{cat_col}:N", sort=sorted_cats, title=None, axis=None)
    base = alt.Chart(data)

    bars = base.mark_bar(
        color=color, cornerRadiusTopRight=3, cornerRadiusBottomRight=3
    ).encode(
        x=alt.X(f"{val_col}:Q", title="count",
                axis=alt.Axis(tickMinStep=1, labelFontSize=9)),
        y=y_enc,
        tooltip=[f"{cat_col}:N", f"{val_col}:Q"],
    )

    # Category label overlaid at the left of each bar.
    # White fill + dark stroke makes the text readable on both the
    # coloured bar and the white background (for short bars).
    cat_labels = base.mark_text(
        align="left", baseline="middle", dx=5,
        fontSize=9.5, fontWeight="normal",
        color=TEXT,
    ).encode(
        x=alt.value(0),
        y=y_enc,
        text=f"{cat_col}:N",
    )

    return (
        alt.layer(bars, cat_labels)
        .properties(
            width=BAR_W,
            height=height,
            title=alt.TitleParams(text=title, fontSize=12,
                                  fontWeight="bold", color=TEXT),
        )
    )

# ── 2–4. Bar charts ───────────────────────────────────────────────────────────
# Shared height = tallest chart so all three are the same.
BAR_H = max(len(career), len(disc), len(src_counts)) * BAR_STEP

career_chart = _hbar(career,     "stage",      "count", ORANGE, "Career stage",                    BAR_H)
disc_chart   = _hbar(disc,       "discipline", "count", BLUE,   "Top 10 academic disciplines",     BAR_H)
src_chart    = _hbar(src_counts, "source",     "count", GREEN,  "How did participants find out?",  BAR_H)

# ── Compose ───────────────────────────────────────────────────────────────────
bottom_row = (
    alt.hconcat(career_chart, disc_chart, src_chart, spacing=ROW_GAP)
    .resolve_scale(y="independent")
)

dashboard = (
    alt.vconcat(map_chart, bottom_row, spacing=20)
    .configure(background=BG)
    .configure_view(stroke=None)
    .configure_axis(
        grid=False,
        labelColor=TEXT,
        titleColor=TEXT,
        domainColor="#cccccc",
        tickColor="#cccccc",
    )
)

# ── Save Altair dashboard to in-memory buffer ─────────────────────────────────
_buf = io.BytesIO()
dashboard.save(_buf, format="png", scale_factor=2)
_buf.seek(0)
altair_img = Image.open(_buf).copy()
_buf.close()
W = altair_img.width          # actual pixel width after scale_factor

# ── Word cloud helpers ────────────────────────────────────────────────────────
aff_map = pd.read_csv("affiliation_map.csv")   # columns: original, fixed

raw_affiliations = (
    df["Affiliation or university"]
    .replace("", pd.NA).dropna()
)
merged = raw_affiliations.to_frame("original").merge(aff_map, on="original", how="left")
merged["fixed"] = merged["fixed"].fillna(merged["original"])

EXCLUDE = {
    "Unknown", "Freelancer", "Independent Researcher", "Denmark",
    "CodeRefinery", "Department of Botany", "Ministry of Health", "MoH",
    "Satori", "Rannis.", "VOTO", "Diglossia", "Amrec",
}
all_canon_counts = (
    merged[~merged["fixed"].isin(EXCLUDE)]
    .groupby("fixed").size()
    .sort_values(ascending=False)
)

import random as _random
_WC_COLORS = [
    "#b84c0a",   # dark orange
    "#1f5f99",   # dark blue
    "#1a6e3c",   # dark green
    "#7b2d8b",   # dark purple
    "#8b1a1a",   # dark red
    "#1a6e6e",   # dark teal
    "#8b6914",   # dark gold
]

def _wc_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return _random.choice(_WC_COLORS)

def _build_dashboard(canon_counts, out):
    """Composite Altair image + word-cloud panel and save to *out*."""
    WC_H = int(W * 0.30)
    wc = WordCloud(
        width=W, height=WC_H,
        background_color=BG,
        color_func=_wc_color_func,
        prefer_horizontal=0.80,
        max_words=80,
        relative_scaling=0.55,
        min_font_size=18,
        max_font_size=int(WC_H * 0.40),
        collocations=False,
        margin=8,
    ).generate_from_frequencies(dict(canon_counts))
    wc_img = wc.to_image()

    TITLE_H = int(W * 0.018)
    panel_h = TITLE_H + WC_H + int(W * 0.005)
    wc_panel = Image.new("RGB", (W, panel_h), BG)

    fig_t, ax_t = plt.subplots(figsize=(W / 200, TITLE_H / 200), dpi=200)
    fig_t.patch.set_facecolor(BG)
    ax_t.set_facecolor(BG)
    ax_t.axis("off")
    ax_t.text(0.5, 0.5, "Affiliated institutions",
              transform=ax_t.transAxes, ha="center", va="center",
              fontsize=14, fontweight="bold", color=TEXT)
    _tbuf = io.BytesIO()
    fig_t.savefig(_tbuf, format="png", dpi=200, bbox_inches="tight",
                  facecolor=BG, pad_inches=0.02)
    plt.close(fig_t)
    _tbuf.seek(0)
    title_img = Image.open(_tbuf).copy().resize((W, TITLE_H), Image.LANCZOS)
    _tbuf.close()

    wc_panel.paste(title_img, (0, 0))
    wc_panel.paste(wc_img, (0, TITLE_H))

    GAP = int(W * 0.004)
    total_h = altair_img.height + GAP + wc_panel.height
    final = Image.new("RGB", (W, total_h), BG)
    final.paste(altair_img, (0, 0))
    final.paste(wc_panel, (0, altair_img.height + GAP))
    final.save(out, dpi=(200, 200))
    print(f"Saved {out}  ({final.width}×{final.height} px)")

# ── Version 1: affiliations with ≥5 registrations ────────────────────────────
_build_dashboard(all_canon_counts[all_canon_counts >= 5], "dashboard.png")

# ── Version 2: all affiliations ───────────────────────────────────────────────
_build_dashboard(all_canon_counts, "dashboard_all_affiliations.png")
