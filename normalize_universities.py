"""
normalize_universities.py
─────────────────────────
Pass 1 – explicit abbreviation / alias table.
Pass 2 – fuzzy clustering (token_sort_ratio ≥ 88) to merge near-duplicates.
Pass 3 – choose canonical name = most-frequent raw name inside each cluster.

Output: universities_normalized.csv  (columns: raw_name, canonical_name)
The CSV is the heuristic list — review / edit before using for the word cloud.
"""

import pandas as pd
from rapidfuzz import fuzz, process

# ── Load raw names ────────────────────────────────────────────────────────────
df = pd.read_csv("registrations.csv", sep=";")
df.columns = df.columns.str.strip()
col = "Affiliation or university"
raw_series = df[col].astype(str).str.strip().replace("nan", "")
raw_series = raw_series[raw_series != ""]

raw_counts = raw_series.value_counts()  # {name: count}

# ── Pass 1: explicit alias → canonical ───────────────────────────────────────
# Keys are the raw variants; values are canonical forms.
ALIASES: dict[str, str] = {
    # ── DTU ──────────────────────────────────────────────────────────────────
    "DTU":                                    "Technical University of Denmark (DTU)",
    "dtu":                                    "Technical University of Denmark (DTU)",
    "Technical University of Denmark":        "Technical University of Denmark (DTU)",
    "Technical university of Denmark":        "Technical University of Denmark (DTU)",
    "Technical University Of Denmark":        "Technical University of Denmark (DTU)",
    "Technical Universtiy of Denmark (DTU)":  "Technical University of Denmark (DTU)",
    "Technical University of Denmark - DTU":  "Technical University of Denmark (DTU)",
    "DTU - Technical University of Denmark":  "Technical University of Denmark (DTU)",
    "DTU - Technical university of denmark":  "Technical University of Denmark (DTU)",
    "Technical University of Denmark, DTU Library":       "Technical University of Denmark (DTU)",
    "Technical University of Denmark (DTU)":  "Technical University of Denmark (DTU)",
    "DTU Biosustain (BRIGHT)":                "Technical University of Denmark (DTU)",
    "DTU Construct":                          "Technical University of Denmark (DTU)",
    "DTU Department of Civil and Mechanical Engineering": "Technical University of Denmark (DTU)",
    "DTU Energy":                             "Technical University of Denmark (DTU)",
    "BRIGHT":                                 "Technical University of Denmark (DTU)",

    # ── Aalto ─────────────────────────────────────────────────────────────────
    "Aalto":                                  "Aalto University",
    "Aalto university":                       "Aalto University",
    "Aalto Universtiy":                       "Aalto University",
    "Aalto University School of Science":     "Aalto University",
    "Finnish Geospatial Research Institute and Aalto University": "Aalto University",

    # ── KTH ──────────────────────────────────────────────────────────────────
    "KTH":                                    "KTH Royal Institute of Technology",
    "kth":                                    "KTH Royal Institute of Technology",
    "KTH Royal Institute Of Technology":      "KTH Royal Institute of Technology",
    "KTH Royal Institute of technology":      "KTH Royal Institute of Technology",

    # ── UiO / Oslo ────────────────────────────────────────────────────────────
    "UiO":                                    "University of Oslo",
    "UiO, Sigma2":                            "University of Oslo",

    # ── UiT ──────────────────────────────────────────────────────────────────
    "UiT":                                    "UiT – The Arctic University of Norway",
    "UiT - The Arctic University of Norway":  "UiT – The Arctic University of Norway",
    "UiT the Arctic University of Norway":    "UiT – The Arctic University of Norway",
    "UiT - Arctic University of Norway":      "UiT – The Arctic University of Norway",
    "University of Tromsø":                   "UiT – The Arctic University of Norway",

    # ── Karolinska ────────────────────────────────────────────────────────────
    "karolinska institutet":                  "Karolinska Institutet",
    "Karolinska Institute":                   "Karolinska Institutet",
    "Uppsala Universitet, SciLifeLab, och Karolinska Institutet": "Karolinska Institutet",

    # ── ICR ───────────────────────────────────────────────────────────────────
    "ICR":                                    "Institute of Cancer Research",
    "RMH":                                    "Institute of Cancer Research",
    "The Institute of Cancer Research":       "Institute of Cancer Research",
    "Institute of Cancer research":           "Institute of Cancer Research",
    "Institute of cancer research":           "Institute of Cancer Research",
    "Institute of Cancer Research London":    "Institute of Cancer Research",

    # ── LSHTM ─────────────────────────────────────────────────────────────────
    "LSHTM":                                  "London School of Hygiene & Tropical Medicine",
    "London School of Hygiene and Tropical Medicine": "London School of Hygiene & Tropical Medicine",
    "London school of hygiene and tropical medicine": "London School of Hygiene & Tropical Medicine",
    "London school of Hygiene and tropical medicine": "London School of Hygiene & Tropical Medicine",
    "london school of hygiene and tropical medicine": "London School of Hygiene & Tropical Medicine",

    # ── NINA ──────────────────────────────────────────────────────────────────
    "NINA":                                   "Norwegian Institute for Nature Research (NINA)",
    "nina":                                   "Norwegian Institute for Nature Research (NINA)",
    "Norwegian Institute for Nature Research":"Norwegian Institute for Nature Research (NINA)",
    "Norsk Institutt for Naturforskning NINA":"Norwegian Institute for Nature Research (NINA)",
    "Norsk institutt for naturforskning (NINA)": "Norwegian Institute for Nature Research (NINA)",
    "Norsk institutt for naturforskning":     "Norwegian Institute for Nature Research (NINA)",

    # ── KIT ───────────────────────────────────────────────────────────────────
    "KIT":                                    "Karlsruhe Institute of Technology (KIT)",
    "Karlsruhe Institute of Technology":      "Karlsruhe Institute of Technology (KIT)",
    "Karlsruhe Institute for Technology":     "Karlsruhe Institute of Technology (KIT)",
    "Karlsruher Institut fuer Technologie":   "Karlsruhe Institute of Technology (KIT)",

    # ── AGH ───────────────────────────────────────────────────────────────────
    "AGH":                                    "AGH University of Krakow",
    "AGH University":                         "AGH University of Krakow",
    "AGH University of Kraków":               "AGH University of Krakow",
    "Akademia Górniczo-hutnicza":             "AGH University of Krakow",
    "ACC Cyfronet AGH":                       "AGH University of Krakow",

    # ── NTNU ──────────────────────────────────────────────────────────────────
    "NTNU":                                   "NTNU – Norwegian University of Science and Technology",

    # ── Chalmers ──────────────────────────────────────────────────────────────
    "Chalmers":                               "Chalmers University of Technology",
    "Chalmers University":                    "Chalmers University of Technology",

    # ── Stockholm University ──────────────────────────────────────────────────
    "Stockholm university":                   "Stockholm University",

    # ── Uppsala University ────────────────────────────────────────────────────
    "Uppsala university":                     "Uppsala University",
    "Uppsala Universitet":                    "Uppsala University",
    "Uppsala Universite":                     "Uppsala University",
    "uppsala university":                     "Uppsala University",
    "Inter Arts Center, Lund University":     "Uppsala University",  # actually Lund — handled below

    # ── Lund ──────────────────────────────────────────────────────────────────
    "Inter Arts Center, Lund University":     "Lund University",

    # ── University of Oulu ────────────────────────────────────────────────────
    "university of Oulu":                     "University of Oulu",
    "Oulun yliopisto":                        "University of Oulu",
    "University of Eastern Finland Kuopio":   "University of Eastern Finland",

    # ── Reykjavík University ─────────────────────────────────────────────────
    "Reykjavík University":                   "Reykjavik University",
    "Háskóli Íslands":                        "University of Iceland",

    # ── University of Helsinki ────────────────────────────────────────────────
    "university of helsinki":                 "University of Helsinki",

    # ── King's College London ─────────────────────────────────────────────────
    "KCL":                                    "King's College London",
    "king's college london":                  "King's College London",
    "King's College London":                  "King's College London",

    # ── ECMWF ─────────────────────────────────────────────────────────────────
    "Ecmwf":                                  "ECMWF",
    "European Centre for Medium-Range Weather Forecasts": "ECMWF",
    "ECMWF, research department & University of Maryland": "ECMWF",

    # ── CSC ───────────────────────────────────────────────────────────────────
    "CSC – IT Center for Science":            "CSC – IT Center for Science",
    "CSC - IT Center for Science":            "CSC – IT Center for Science",
    "CSC":                                    "CSC – IT Center for Science",

    # ── Åbo Akademi ───────────────────────────────────────────────────────────
    "Abo Akademi University":                 "Åbo Akademi University",

    # ── Jagiellonian ──────────────────────────────────────────────────────────
    "Jagiellonian University in Krakow":      "Jagiellonian University",

    # ── University of Tartu ───────────────────────────────────────────────────
    "Tartu University":                       "University of Tartu",
    "University of tartu":                    "University of Tartu",
    "University of Tartu, Estonia":           "University of Tartu",
    "University of Tartu, Tartu Observatory": "University of Tartu",

    # ── University of Bergen ──────────────────────────────────────────────────
    "Universitetet i Bergen":                 "University of Bergen",

    # ── University of Bologna ─────────────────────────────────────────────────
    "Università di Bologna":                  "University of Bologna",

    # ── Linköping University ──────────────────────────────────────────────────
    "Linköping Universite":                   "Linköping University",
    "Linköping universitet":                  "Linköping University",

    # ── Gothenburg ───────────────────────────────────────────────────────────
    "Göteborgs universitet":                  "University of Gothenburg",

    # ── Tampere ───────────────────────────────────────────────────────────────
    "Tampere university":                     "Tampere University",

    # ── Arcada ────────────────────────────────────────────────────────────────
    "Arcada UAS":                             "Arcada University of Applied Sciences",

    # ── Imperial College ──────────────────────────────────────────────────────
    "Imperial":                               "Imperial College London",
    "Imperial College, London and University of California, Berkeley": "Imperial College London",

    # ── Queen Mary ────────────────────────────────────────────────────────────
    "Queen Mary University of London":        "Queen Mary, University of London",

    # ── Sano ──────────────────────────────────────────────────────────────────
    "Sano - Centrum Zindywidualizowanej Medycyny Obliczeniowej - Międzynarodowa Fundacja Badawcza":
        "Sano Centre for Computational Medicine",
    "Sano Centre for Computational Medicine, Nawojki 11, 30-072 Krakow":
        "Sano Centre for Computational Medicine",

    # ── Marine and Freshwater Research Institute (Iceland) ───────────────────
    "Marine and Freshwater Institute - Iceland": "Marine and Freshwater Research Institute",
    "Marine and Freshwater research Institute":  "Marine and Freshwater Research Institute",

    # ── CINECA ────────────────────────────────────────────────────────────────
    "Cineca":                                 "CINECA",

    # ── University of Genoa ───────────────────────────────────────────────────
    "university of genoa":                    "University of Genoa",

    # ── Karelia ───────────────────────────────────────────────────────────────
    "Karelia AMK":                            "Karelia University of Applied Sciences",

    # ── OsloMet ───────────────────────────────────────────────────────────────
    # (already correct, no alias needed)

    # ── UEF ───────────────────────────────────────────────────────────────────
    "uef":                                    "University of Eastern Finland",
    "UEF":                                    "University of Eastern Finland",

    # ── SDU ───────────────────────────────────────────────────────────────────
    "SDU":                                    "University of Southern Denmark",

    # ── Charité ───────────────────────────────────────────────────────────────
    "Berliner Institut für Gesundheitsforschung (BIH) @ Charité   QUEST – Center for Responsible Research":
        "Charité",

    # ── IFJ PAN ───────────────────────────────────────────────────────────────
    "IFJPAN":                                 "IFJ PAN",
    "Instytutem od nuclear physics PAN":      "IFJ PAN",
    "Institute of Nuclear Physics PAN, Kraków": "IFJ PAN",
    "Institute of Nuclear Physics Polish Academy of Sciences": "IFJ PAN",

    # ── FSU Jena ──────────────────────────────────────────────────────────────
    "Friedrich-Schiller-University Jena":     "University of Jena",
    "FSU Jena":                               "University of Jena",

    # ── AHRI ──────────────────────────────────────────────────────────────────
    "AHRI":                                   "Africa Health Research Institute",

    # ── Makerere ──────────────────────────────────────────────────────────────
    "Makerere University & Avance International University": "Makerere University",
    "Makerere University school of Public Health": "Makerere University",

    # ── Misc one-offs ─────────────────────────────────────────────────────────
    "JAIN(Deemed-to-be) University, School of Science, Bangalore, India": "JAIN University",
    "INESC TEC, University of Porto":         "University of Porto",
    "National University of Singapore, Singapore": "National University of Singapore",
    "Strahlenheilkunde Universität Freiburg": "University of Freiburg",
    "Uni Freiburg, Freiburg, Germany":        "University of Freiburg",
    "Aarhus university":                      "Aarhus University",
    "Ceanapse ~ The Technical University of Kenya": "Technical University of Kenya",
    "RWTH Aachen - DWD":                      "RWTH Aachen University",
    "Indian Institute of Information Technology , Allahabad": "Indian Institute of Information Technology Allahabad",
    "Karelia AMK":                            "Karelia University of Applied Sciences",
    "İzmir Institute of Technology":          "Izmir Institute of Technology",

    # ── Protect institutions that fuzzy-matching confuses with others ─────────
    # (self-aliases bypass the fuzzy clustering pass entirely)
    "Aalborg University":                     "Aalborg University",       # ≠ Aalto
    "University of Oslo":                     "University of Oslo",       # ≠ University of Oulu
    "University of Turku":                    "University of Turku",      # ≠ University of Tartu
    "Ulm University":                         "Ulm University",           # ≠ Umeå University
    "Karelia University of Applied Sciences": "Karelia University of Applied Sciences",  # ≠ Arcada
    "Kristiania University of Applied Sciences": "Kristiania University of Applied Sciences",  # ≠ Karelia

    # ── Case fixes & remaining abbreviations ─────────────────────────────────
    "Qatar university":                       "Qatar University",
    "Stuttgart uni":                          "University of Stuttgart",
    "tu delft":                               "TU Delft",
    "university ulm":                         "Ulm University",
    "Utsunomiya university":                  "Utsunomiya University",
    "TalTech":                                "Tallinn University of Technology",
    "SLU":                                    "Swedish University of Agricultural Sciences",
    "LMU":                                    "Ludwig Maximilian University Munich",
    "FHI":                                    "Norwegian Institute of Public Health",
    "NIPH":                                   "Norwegian Institute of Public Health",
    "Norwegian Institute of Public Health (Folkehelseinstituttet)": "Norwegian Institute of Public Health",
    "Oamk":                                   "Oulu University of Applied Sciences",
    "NMBU":                                   "Norwegian University of Life Sciences (NMBU)",
    "INDIAN INSTITUTE OF TECHNOLOGY KHARAGPUR": "IIT Kharagpur",
    "IIT kanpur":                             "IIT Kanpur",
    "Univeristy of Jaén":                     "University of Jaén",
    "Univerait":                              "Unknown",
    "UCSC Extn":                              "UC Santa Cruz",
    "Ucr":                                    "UC Riverside",
    "KU":                                     "University of Copenhagen",
    "LUKE":                                   "Natural Resources Institute Finland (LUKE)",
    "VTT":                                    "VTT Technical Research Centre of Finland",
    "SMHI":                                   "Swedish Meteorological and Hydrological Institute (SMHI)",
    "RISE":                                   "Research Institutes of Sweden (RISE)",
    "MUW":                                    "Medical University of Warsaw",
    "PUC":                                    "Pontifical Catholic University",
    "USTTB":                                  "University of Science Techniques and Technologies of Bamako (USTTB)",
    "TFTAK":                                  "TFTAK (Centre of Food and Fermentation Technologies)",
    "HZB":                                    "Helmholtz-Zentrum Berlin (HZB)",
    "DKFZ":                                   "German Cancer Research Center (DKFZ)",
    "TU/e - Eindhoven University of Technology": "TU Eindhoven",
}

# ── Apply Pass 1 ─────────────────────────────────────────────────────────────
def apply_aliases(name: str) -> str:
    return ALIASES.get(name, name)

mapped = {name: apply_aliases(name) for name in raw_counts.index}

# ── Pass 2: fuzzy clustering on still-unresolved names ───────────────────────
# Build a lookup: canonical → list of raw names already pointing to it
THRESHOLD = 88  # token_sort_ratio threshold

# Collect names that were NOT touched by aliases (their mapped == raw)
# Names in ALIASES (even self-aliases) are excluded from fuzzy clustering.
untouched = {name for name, canon in mapped.items()
             if canon == name and name not in ALIASES}

# Work with the canonical forms of untouched names
canon_pool = list(untouched)

# Group by fuzzy similarity
clusters: list[set] = []
assigned: set = set()

for name in sorted(canon_pool, key=lambda n: -raw_counts.get(n, 0)):
    if name in assigned:
        continue
    matches = process.extract(
        name, canon_pool, scorer=fuzz.token_sort_ratio, limit=None, score_cutoff=THRESHOLD
    )
    group = {m[0] for m in matches}
    clusters.append(group)
    assigned.update(group)

# For each cluster choose the canonical = the raw name with highest count
fuzzy_map: dict[str, str] = {}
for cluster in clusters:
    canonical = max(cluster, key=lambda n: raw_counts.get(n, 0))
    for name in cluster:
        fuzzy_map[name] = canonical

# Merge pass-2 results into final map (only update untouched names)
for name in untouched:
    if name in fuzzy_map:
        mapped[name] = fuzzy_map[name]

# ── Build output dataframe ────────────────────────────────────────────────────
records = []
for raw_name, count in raw_counts.items():
    canon = mapped.get(raw_name, raw_name)
    records.append({"raw_name": raw_name, "canonical_name": canon, "raw_count": count})

out = pd.DataFrame(records).sort_values(["canonical_name", "raw_count"], ascending=[True, False])
out.to_csv("universities_normalized.csv", index=False)
print(f"Saved universities_normalized.csv  ({len(out)} rows)")

# ── affiliation_map.csv: one row per unique raw value, two columns ─────────────
# Sorted by fixed name so all variants of the same institution cluster together.
aff_map = (
    out[["raw_name", "canonical_name"]]
    .rename(columns={"raw_name": "original", "canonical_name": "fixed"})
    .sort_values(["fixed", "original"], key=lambda s: s.str.lower())
    .reset_index(drop=True)
)
aff_map.to_csv("affiliation_map.csv", index=False)
print(f"Saved affiliation_map.csv  ({len(aff_map)} rows, columns: original, fixed)")

# ── Summary ───────────────────────────────────────────────────────────────────
canon_counts = out.groupby("canonical_name")["raw_count"].sum().sort_values(ascending=False)
print(f"\nTop 20 canonical universities:")
for name, cnt in canon_counts.head(20).items():
    print(f"  {cnt:4d}  {name}")
print(f"\nUnique canonical names: {len(canon_counts)} (from {len(out)} raw names)")
