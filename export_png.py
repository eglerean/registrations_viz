import sys
sys.path.insert(0, "/tmp/pylibs2")

import plotly.graph_objects as go

data = [
    ("Finland",          "FIN", 142),
    ("Denmark",          "DNK", 85),
    ("Norway",           "NOR", 71),
    ("Sweden",           "SWE", 67),
    ("United Kingdom",   "GBR", 61),
    ("Germany",          "DEU", 35),
    ("Estonia",          "EST", 29),
    ("Poland",           "POL", 26),
    ("Italy",            "ITA", 13),
    ("Iceland",          "ISL", 13),
    ("United States",    "USA", 8),
    ("Spain",            "ESP", 8),
    ("Nigeria",          "NGA", 8),
    ("India",            "IND", 7),
    ("Kenya",            "KEN", 6),
    ("Uganda",           "UGA", 3),
    ("France",           "FRA", 3),
    ("Austria",          "AUT", 3),
    ("South Africa",     "ZAF", 2),
    ("Singapore",        "SGP", 2),
    ("Portugal",         "PRT", 2),
    ("Peru",             "PER", 2),
    ("Pakistan",         "PAK", 2),
    ("Netherlands",      "NLD", 2),
    ("Ghana",            "GHA", 2),
    ("Côte d'Ivoire",    "CIV", 2),
    ("Chile",            "CHL", 2),
    ("Uruguay",          "URY", 1),
    ("Ukraine",          "UKR", 1),
    ("Türkiye",          "TUR", 1),
    ("Togo",             "TGO", 1),
    ("South Sudan",      "SSD", 1),
    ("Somalia",          "SOM", 1),
    ("Romania",          "ROU", 1),
    ("Qatar",            "QAT", 1),
    ("Mali",             "MLI", 1),
    ("Malaysia",         "MYS", 1),
    ("Lithuania",        "LTU", 1),
    ("Jordan",           "JOR", 1),
    ("Japan",            "JPN", 1),
    ("Israel",           "ISR", 1),
    ("Iran",             "IRN", 1),
    ("Indonesia",        "IDN", 1),
    ("Gambia",           "GMB", 1),
    ("Ethiopia",         "ETH", 1),
    ("Czechia",          "CZE", 1),
    ("Congo - Kinshasa", "COD", 1),
    ("China",            "CHN", 1),
    ("Cameroon",         "CMR", 1),
    ("Burundi",          "BDI", 1),
    ("Brazil",           "BRA", 1),
    ("Belgium",          "BEL", 1),
    ("Bangladesh",       "BGD", 1),
    ("Argentina",        "ARG", 1),
    ("Afghanistan",      "AFG", 1),
]

countries, isos, freqs = zip(*data)
text = [f"{c}<br>Frequency: {f}" for c, f in zip(countries, freqs)]

fig = go.Figure(go.Choropleth(
    locations=list(isos),
    z=list(freqs),
    text=text,
    hovertemplate="%{text}<extra></extra>",
    colorscale=[
        [0,    "#ffffcc"],
        [0.05, "#fed976"],
        [0.15, "#fd8d3c"],
        [0.35, "#f03b20"],
        [0.65, "#bd0026"],
        [1,    "#67000d"],
    ],
    zmin=0,
    zmax=142,
    colorbar=dict(
        title=dict(text="Frequency", font=dict(color="#222")),
        tickfont=dict(color="#222"),
        bgcolor="rgba(255,255,255,0)",
        outlinecolor="#aaa",
    ),
    marker=dict(line=dict(color="#999", width=0.5)),
))

fig.update_layout(
    title=dict(text="Country Frequency Map", x=0.5, font=dict(color="#222", size=16)),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#888",
        showland=True,
        landcolor="#f0f0f0",
        showocean=True,
        oceancolor="#cde5f5",
        showlakes=True,
        lakecolor="#cde5f5",
        showcountries=True,
        countrycolor="#aaa",
        projection_type="natural earth",
    ),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    margin=dict(t=50, b=10, l=10, r=10),
    font=dict(color="#222"),
)

fig.write_image("/Users/eglerean/code/country_viz/map.png", width=1600, height=900, scale=2)
print("Saved map.png")
