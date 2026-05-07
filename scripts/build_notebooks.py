#!/usr/bin/env python3
"""Generate teaching notebooks (run once; outputs under notebooks/)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"

GITHUB_PLACEHOLDER = "YOUR_GITHUB_USER/YOUR_REPO_NAME"
EE_PROJECT = "ee-gee-hydro"

# Earth Engine Data Catalog — stable pages for students (dataset id → URL slug uses underscores).
_GEE_DATA_CATALOG = "https://developers.google.com/earth-engine/datasets/catalog"
DOC_CHIRPS_DAILY = f"{_GEE_DATA_CATALOG}/UCSB-CHG_CHIRPS_DAILY"
DOC_S2_SR_HARMONIZED = f"{_GEE_DATA_CATALOG}/COPERNICUS_S2_SR_HARMONIZED"
DOC_S1_GRD = f"{_GEE_DATA_CATALOG}/COPERNICUS_S1_GRD"
DOC_DEM_GLO30 = f"{_GEE_DATA_CATALOG}/COPERNICUS_DEM_GLO30"
DOC_SRTM = f"{_GEE_DATA_CATALOG}/USGS_SRTMGL1_003"
DOC_ESA_WORLDCOVER_V200 = f"{_GEE_DATA_CATALOG}/ESA_WorldCover_v200"
DOC_HYDROSHEDS_HYBAS8 = f"{_GEE_DATA_CATALOG}/WWF_HydroSHEDS_v1_Basins_hybas_8"


def colab_badge(filename: str) -> str:
    url = (
        f"https://colab.research.google.com/github/{GITHUB_PLACEHOLDER}/blob/main/"
        f"notebooks/{filename}"
    )
    return (
        f'<a target="_blank" href="{url}">'
        f'<img src="https://colab.research.google.com/assets/colab-badge.svg" '
        f'alt="Open in Colab"/></a>\n'
    )


def save(name: str, cells: list) -> None:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    path = NB_DIR / name
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }
    path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("Wrote", path)


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source: str) -> dict:
    c = {
        "cell_type": "code",
        "metadata": {},
        "source": source.splitlines(True),
        "outputs": [],
        "execution_count": None,
    }
    return c


# ---------------------------------------------------------------------------
# Shared snippets
# ---------------------------------------------------------------------------
INSTALL = """# Install packages (Colab often needs a fresh install each session)
!pip install -q earthengine-api geemap

import ee
import geemap
import pandas as pd
import matplotlib.pyplot as plt

# If you run this notebook locally, run `ee.Authenticate()` once before `ee.Initialize`.
# If the Colab pop-up fails, try: ee.Authenticate(auth_mode="colab")
# Mapping notebooks use `Map.add_basemap("SATELLITE")` so you always have photo context under EE layers.
"""

INIT = f"""# Connect to Google Earth Engine using the course cloud project
EE_PROJECT = "{EE_PROJECT}"

try:
    ee.Initialize(project=EE_PROJECT)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=EE_PROJECT)

print("Earth Engine initialised with project:", EE_PROJECT)
"""

AOI_PY_BASE = """# Study area: Moulouya basin — HydroSHEDS level-8 hydrological unit (WWF)
# Dataset: WWF/HydroSHEDS/v1/Basins/hybas_8 — use the same HYBAS_ID in every notebook for consistency.

HYBAS_ID = 1080030220

MOULOUYA_BASIN_H08 = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_8").filter(
    ee.Filter.eq("HYBAS_ID", HYBAS_ID)
)

# Geometry used for clips, filterBounds, reduceRegion, etc.
LOWER_MOULOUYA_AOI = MOULOUYA_BASIN_H08.geometry()
"""

# Wet-season date helper: notebooks 03–04, 06 (Sentinel / RF). Notebook 01 loads AOI_PY_BASE only.
AOI_PY_DATES = (
    AOI_PY_BASE
    + """
# Extended winter–spring wet season (December–April), named by the April that closes the window.


def wet_season_filter_dates(april_year: int) -> tuple[str, str]:
    # Returns filterDate(start, end) with end exclusive — April is fully included.
    start = f"{april_year - 1}-12-01"
    end = f"{april_year}-05-01"
    return (start, end)
"""
)

# CHIRPS totals + basin stats: notebook 02 (full) only.
AOI_PY_CHIRPS = (
    AOI_PY_DATES
    + """

def wet_season_total_chirps(april_year: int) -> ee.Image:
    # CHIRPS total rainfall (mm) for one wet season, clipped to the basin, band P.
    start, end = wet_season_filter_dates(april_year)
    return (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start, end)
        .sum()
        .clip(LOWER_MOULOUYA_AOI)
        .rename("P")
    )


def aoi_mean_mm(img: ee.Image) -> float:
    # Mean of band P over the basin (CHIRPS grid ~5.5 km).
    stats = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=LOWER_MOULOUYA_AOI,
        scale=5500,
        maxPixels=1e13,
        tileScale=4,
    )
    return float(stats.getInfo()["P"])


def aoi_max_p_mm(img: ee.Image) -> float:
    # Largest band-P value in the basin (wettest CHIRPS cell) — handy for map legend tops.
    stats = img.select("P").reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=LOWER_MOULOUYA_AOI,
        scale=5500,
        maxPixels=1e13,
        tileScale=4,
    )
    return float(stats.getInfo()["P"])
"""
)

# Every practical map: Google Satellite basemap, then centre on the basin.
MAP_SATELLITE_START = """Map = geemap.Map()
Map.add_basemap("SATELLITE")
Map.centerObject(LOWER_MOULOUYA_AOI, 9)
"""
MAP2_SATELLITE_START = """Map2 = geemap.Map()
Map2.add_basemap("SATELLITE")
Map2.centerObject(LOWER_MOULOUYA_AOI, 9)
"""
MAP4_SATELLITE_START = """Map4 = geemap.Map()
Map4.add_basemap("SATELLITE")
Map4.centerObject(LOWER_MOULOUYA_AOI, 9)
"""

def build_00():
    cells = [
        md(
            f"""# Set up Google Earth Engine for this course

{colab_badge("00_setup_google_earth_engine.ipynb")}

## Why this notebook?

Earth Observation (EO) data for this module live in **Google Earth Engine (GEE)**. Before you can load rainfall, satellite images, or maps, you must:

1. Have a **Google account** accepted on the Earth Engine platform.
2. Tell the Python library **which GEE cloud project** to bill and store assets under.

This course uses the cloud project **`{EE_PROJECT}`**. Your instructor will add your account to that project if needed.

## What you will do

- Install the Python libraries used in all other notebooks.
- Run a one-line **authentication** step (browser sign-in).
- **Initialise** Earth Engine with the course project.
- Run a **tiny test**: load one public dataset and print a statistic for Morocco.

## Research link

You are not answering a science question here. You are checking that the **data plumbing** works so later notebooks can focus on drought, rainfall, water, and vegetation.

---

### Before you start (first time only)

1. Go to [Earth Engine signup](https://earthengine.google.com/signup/) if you have never used GEE before.
2. Wait until you can open the [Earth Engine Code Editor](https://code.earthengine.google.com/) without errors.

When those work, continue below.
"""
        ),
        md("""## Step 1 — Install libraries

Run the cell below. On Google Colab this takes about a minute the first time.
"""),
        code(INSTALL),
        md("""## Step 2 — Authenticate and initialise

**Authenticate:** the first time in a new environment, Earth Engine opens a browser window. Approve access for the account that has been added to the course project.

**Initialise:** the line `ee.Initialize(project=...)` selects **`ee-gee-hydro`** so all requests use the correct cloud project.

If you see an error about permissions, contact your instructor with the **e-mail address** of the Google account you used.
"""),
        code(INIT),
        md(
            f"""## Step 3 — Small test (CHIRPS rainfall)

We load **December 2025** daily [**CHIRPS Daily**]({DOC_CHIRPS_DAILY}) (the same product used later) and compute the **mean grid-cell total rainfall** over Morocco for that month (millimetres summed over the month, then averaged spatially). This matches the course focus on the **extended winter–spring wet season** (December–April).

If you see a number printed (not an error), your setup is working.
"""
        ),
        code(
            """# Quick test: December 2025 total CHIRPS rainfall (mm), spatial mean over Morocco
morocco = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq("ADM0_NAME", "Morocco"))

chirps = (
    ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    .filterDate("2025-12-01", "2026-01-01")
    .sum()
)

mean_mm = chirps.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=morocco.geometry(),
    scale=5500,
    maxPixels=1e13,
    tileScale=4,
).get("precipitation")

print("Mean December 2025 total rainfall over Morocco (mm, approximate):", mean_mm.getInfo())
"""
        ),
        md("""## Step 4 — Optional: check your account string

This prints the **client e-mail** Earth Engine sees (useful if authentication fails).
"""),
        code(
            """# Optional: confirm which cloud project the client is using (API versions vary)
try:
    print("Asset roots:", ee.data.getAssetRoots())
except Exception as exc:
    print("Could not list asset roots (this is normal on some Colab setups):", exc)
"""
        ),
        md(
            f"""## Suggested timing for the whole 3-hour practical

| Block (minutes) | Notebook | Focus |
|---:|---|---|
| 0–15 | `00` | Setup and authentication |
| 15–45 | `01` | AOI and landscape context |
| 45–80 | `02` | CHIRPS rainfall totals and anomaly |
| 80–120 | `03` | Surface water (Sentinel-2 / optional Sentinel-1) |
| 120–155 | `04` | NDVI and green-up |
| 155–200 | `05` | RF ponds from markers (binary) |
| 200–210 | — | Group conclusion paragraph |

Notebook `05` now contains the full ponds workflow.

---

## Checklist before the next notebook

- [ ] `ee.Initialize` ran without errors.
- [ ] The [**CHIRPS**]({DOC_CHIRPS_DAILY}) test printed a rainfall value.
- [ ] You know which Google account you used.

**Next:** open `01_aoi_explore_lower_moulouya.ipynb` to map the study area.
"""
        ),
    ]
    save("00_setup_google_earth_engine.ipynb", cells)


def build_01():
    cells = [
        md(
            f"""# Notebook 1 — Build the study area and explore the Lower Moulouya

{colab_badge("01_aoi_explore_lower_moulouya.ipynb")}

## Big picture

We study **northeastern Morocco**, where the **Lower Moulouya** river reaches the Mediterranean. The **2025–2026** rainy period was unusually wet. Later notebooks compare the **extended winter–spring wet season (December–April)** — labelled by the **April** that closes each window (e.g. wet season **2025/26** ends April 2026) — using [**CHIRPS**]({DOC_CHIRPS_DAILY}), [**Sentinel-2**]({DOC_S2_SR_HARMONIZED}), and related layers.

## Main research question (whole module)

> How did the unusually wet **2025/26** wet season affect **surface water** and **vegetation** in the Lower Moulouya compared with the **2024/25** wet season and a **long-term baseline of wet seasons ending April 2017–April 2024**?

## Objective in *this* notebook

- What an **AOI** (area of interest) is, and why we use a **hydrological basin** from HydroSHEDS instead of an arbitrary bounding box or the whole country.
- How to use **geemap** with a **Google Satellite** basemap for geographic context.
- How to split [**Copernicus DEM GLO-30**]({DOC_DEM_GLO30}) (the data) from **hillshade** (the visualisation) in two clear steps.

## Research questions

1. Which parts of the AOI appear **flat and irrigated** versus **hilly or dry**?
2. Where are the main **river-connected lowlands** likely to concentrate wet-season change?
3. Which landscape contrasts (plain / upland, urban / rural) are most relevant for later water and vegetation analysis?

**Time tip (3 h module):** spend about **25–30 minutes** here, including discussion with your group.
"""
        ),
        code(INSTALL),
        code(INIT),
        md(
            f"""## Define the AOI — HydroSHEDS hydrological unit

Instead of drawing a **bounding box**, we load a **pre-defined basin polygon** from **HydroSHEDS** (WWF). This is a **level-08** sub-basin: one step in a global hierarchy of nested catchments. Everyone uses the same **`HYBAS_ID`**, so your maps match other notebooks and published basin codes.

This notebook only defines the **basin** (no rainfall code here — [**CHIRPS Daily**]({DOC_CHIRPS_DAILY}) starts in notebook **02**).

**Target basin — Moulouya (Lower Moulouya in HydroBASINS terms):** `HYBAS_ID = 1080030220` on [**HydroSHEDS hybas level 8**]({DOC_HYDROSHEDS_HYBAS8}) (`WWF/HydroSHEDS/v1/Basins/hybas_8`).

Why hydrological units?

- The boundary follows **drainage** (ridges and outlets), not an arbitrary rectangle.
- The same **`HYBAS_ID`** is easy to **look up**, cite, and **re-use** in the next notebook (clip, zonal stats, exports).

Run the code cell below, then check the **feature count** prints **1**. If it prints **0**, the filter or dataset path is wrong — ask your instructor.
"""
        ),
        code(AOI_PY_BASE),
        code(
            """print("HydroSHEDS hybas_8 features with HYBAS_ID =", HYBAS_ID, ":", MOULOUYA_BASIN_H08.size().getInfo())
"""
        ),
        md(
            f"""## Step 1 — Build the Copernicus DEM (data only)

Here we create one **elevation image** over the basin: `DEM_GLO30` (metres, [**Copernicus DEM GLO-30**]({DOC_DEM_GLO30})). This cell is **only** about loading data and fixing the **native projection** after `mosaic()` — a requirement for sensible `Terrain` outputs (see the catalogue **Description** tab for caveats).

The **next** section adds the **map** (satellite basemap + hillshade). Keeping **data** and **visualisation** apart is good practice and easier to debug.
"""
        ),
        code(
            '''glo30 = ee.ImageCollection("COPERNICUS/DEM/GLO30")
native_proj = glo30.first().projection()
DEM_GLO30 = (
    glo30.select("DEM")
    .mosaic()
    .setDefaultProjection(native_proj)
    .rename("elevation_m")
    .clip(LOWER_MOULOUYA_AOI)
)
print("DEM ready: Copernicus GLO-30, one band elevation_m, clipped to the basin.")
'''
        ),
        md(
            f"""## Step 2 — Visualise on a **satellite** basemap

**Basemap:** `Map.add_basemap("SATELLITE")` adds **Google Satellite** imagery (true colour context; not an Earth Engine `Image`).

**Overlay:** **Hillshade** is computed from `DEM_GLO30` for **display only**. Multiplying elevations by **20** before `Terrain.hillshade` follows the [**DEM GLO-30**]({DOC_DEM_GLO30}) catalogue recipe so gentle relief shows up — it is **not** a physical change to the DEM.

**On top:** the [**HydroSHEDS**]({DOC_HYDROSHEDS_HYBAS8}) basin outline in bright yellow so you can match drainage limits to fields and settlements.

Use the layer control to turn **DEM** on or off (hidden by default so the tutorial stays uncluttered).

**Tip:** if the map does not appear in Colab, run the cell again or click “Show map” if Colab collapses the widget.
"""
        ),
        code(
            MAP_SATELLITE_START
            + """basin_vis = {"fillColor": "00000000", "color": "ffff00", "width": 3}

hillshade_display = ee.Terrain.hillshade(DEM_GLO30.multiply(20.0))
Map.addLayer(
    hillshade_display,
    {"min": 0, "max": 255},
    "Hillshade",
    opacity=0.55,
)
Map.addLayer(MOULOUYA_BASIN_H08.style(**basin_vis), {}, "Basin")
Map.addLayer(
    DEM_GLO30,
    {"min": 0, "max": 2500, "palette": ["232359", "1d91c0", "8ed368", "fcfdb5"]},
    "DEM m",
    shown=False,
)

Map
"""
        ),
        md("""## Export the AOI as an Earth Engine asset (optional, instructor-led)

Only run this if your instructor asks you to save the AOI to the **course cloud project**. You need **write** permission on `ee-gee-hydro`.

Otherwise, every notebook can rebuild the same geometry from code (as we do here).
"""),
        code(
            """# OPTIONAL — uncomment only if you have write access and want a saved asset (attributes preserved)
# task = ee.batch.Export.table.toAsset(
#     collection=MOULOUYA_BASIN_H08,
#     description="moulouya_hybas_h08_1080030220",
#     assetId="projects/ee-gee-hydro/assets/MOULOUYA_BASIN_H08",
# )
# task.start()
# print("Export started — check Tasks tab in the Earth Engine Code Editor")
print("Skipping export by default.")
"""
        ),
        md("""## Short written task (5 minutes)

In your own words, list **three land-cover / land-use** types you expect to see inside the AOI (for example: irrigated fields, urban, bare soil). Say **where** in the AOI each type is most likely.

**Next notebook:** `02_rainfall_chirps_anomaly.ipynb`.
"""),
    ]
    save("01_aoi_explore_lower_moulouya.ipynb", cells)


def build_02():
    cells = [
        md(
            f"""# Notebook 2 — Rainfall: was the 2025/26 wet season wetter?

{colab_badge("02_rainfall_chirps_anomaly.ipynb")}

## Why rainfall first?

**Vegetation** and **temporary water** (floods, soil moisture) usually follow **rainfall** with a time lag. [**CHIRPS Daily**]({DOC_CHIRPS_DAILY}) gives a **daily gridded rainfall** estimate suitable for regional comparisons.

**Season name:** we use the **extended winter–spring wet season (December–April)**. Each window is identified by the **April** that closes it — for example **wet season 2025/26** runs from **1 December 2025** through **30 April 2026**. Dates are built in **`wet_season_filter_dates`** in the AOI cell.

## Research questions

1. Was the **wet season ending April 2026** wetter than the **wet season ending April 2025** inside the AOI?
2. How do both compare to the **mean of wet seasons ending April 2017 through April 2024**?

## What you will produce

- **Geemap** maps of **total wet-season rainfall** ([**CHIRPS Daily**]({DOC_CHIRPS_DAILY})) for **2024/25**, **2025/26**, and the baseline mean, each with a **colour bar** in millimetres.
- A map of **2025/26 vs baseline** as **percentage change** (with a **colour bar** in **%**).
- A **simple bar chart** of AOI-mean rainfall for the three cases.

**Time tip:** about **30–35 minutes**.
"""
        ),
        code(INSTALL),
        code(INIT),
        code(AOI_PY_CHIRPS),
        md(
            f"""## Wet-season rainfall (CHIRPS)

The AOI cell already defines **`wet_season_total_chirps(april_year)`** (sums [**CHIRPS Daily**]({DOC_CHIRPS_DAILY}) over each wet season), **`aoi_mean_mm(image)`** (basin mean of band **P**), and **`aoi_max_p_mm(image)`** (wettest grid cell in the basin). This cell **calls** the first two for the printed means; **`aoi_max_p_mm`** is used in the map cell for the legend top.

**Baseline:** mean of eight wet seasons **ending April 2017 … April 2024**.
"""
        ),
        code(
            '''P_apr2025 = wet_season_total_chirps(2025)
P_apr2026 = wet_season_total_chirps(2026)

baseline_years = list(range(2017, 2025))
baseline_mean = ee.ImageCollection([wet_season_total_chirps(yr) for yr in baseline_years]).mean().rename("P")

m_apr2025 = aoi_mean_mm(P_apr2025)
m_apr2026 = aoi_mean_mm(P_apr2026)
mbase = aoi_mean_mm(baseline_mean)

print(f"AOI mean wet-season total (mm) — 2024/25: {m_apr2025:.1f}")
print(f"AOI mean wet-season total (mm) — 2025/26: {m_apr2026:.1f}")
print(f"AOI mean wet-season total (mm) — baseline (Apr 2017–2024): {mbase:.1f}")
'''
        ),
        md(
            f"""## Maps

**Basemap:** Google Satellite sits under the [**CHIRPS**]({DOC_CHIRPS_DAILY}) layers so you can relate rainfall to real land cover.

**Legend max (`max_p`):** the AOI cell defines **`aoi_max_p_mm(image)`** — the **wettest CHIRPS cell** in the basin for that layer. We take the **largest** of the three seasons and set **`vis["max"]`** a little above that so the palette is not washed out. **`Map.remove_colorbars()`** before **`add_colorbar`** avoids stacking duplicate scales when you **re-run** the cell (geemap would otherwise keep adding another colour bar each time).
"""
        ),
        code(
            MAP_SATELLITE_START
            + """max_p = max(
    aoi_max_p_mm(P_apr2025),
    aoi_max_p_mm(P_apr2026),
    aoi_max_p_mm(baseline_mean),
)
vis = {
    "min": 0,
    "max": min(900, max(100, int(max_p + 50))),
    "palette": ["fff7d6", "6baed6", "08306b"],
}
print("Wettest cell in AOI (mm), max of three layers:", round(max_p, 1), "| legend max (mm):", vis["max"])

Map.addLayer(P_apr2025, vis, "P Apr25")
Map.addLayer(P_apr2026, vis, "P Apr26")
Map.addLayer(baseline_mean, vis, "P base")
Map.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.25)
Map.remove_colorbars()
Map.add_colorbar(vis, label="mm", orientation="horizontal", position="bottomright")
Map
"""
        ),
        md(
            f"""## Anomaly map (wet season 2025/26 vs baseline, **% change**)

We map **relative** departure from the [**CHIRPS**]({DOC_CHIRPS_DAILY}) baseline mean, not millimetres:

**100 × (wet season 2025/26 − baseline) ÷ baseline** (per pixel).

Dividing by **very small** baseline totals would blow up percentages, so the denominator uses **`baseline_mean.max(10)`** — treat each pixel’s baseline as **at least 10 mm** before dividing. **Positive** values = wetter than the long-term reference; **negative** = drier.

**`vis_anom`** is a **symmetric** **±100 %** palette; **`Map2.add_colorbar(vis_anom, …)`** uses **`label="%"`**. Values beyond ±100 % clip to the palette ends.
"""
        ),
        code(
            """# Percent change vs baseline (mm → %); floor baseline at 10 mm to limit divide-by-near-zero.
den = baseline_mean.max(10)
anom = P_apr2026.subtract(baseline_mean).divide(den).multiply(100).rename("dP_pct")

"""
            + MAP2_SATELLITE_START
            + """vis_anom = {"min": -100, "max": 100, "palette": ["d73027", "ffffbf", "1a9850"]}
Map2.addLayer(anom, vis_anom, "P % Apr26")
Map2.addLayer(LOWER_MOULOUYA_AOI, {"color": "333333"}, "AOI", opacity=0.2)
Map2.remove_colorbars()
Map2.add_colorbar(vis_anom, label="%", orientation="horizontal", position="bottomright")
Map2
"""
        ),
        md("""## Bar chart (AOI means)
"""),
        code(
            """df = pd.DataFrame(
    {
        "Season": ["Wet season 2024/25", "Wet season 2025/26", "Baseline mean\\n(Apr endings 2017–2024)"],
        "Rainfall_mm": [m_apr2025, m_apr2026, mbase],
    }
)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(df["Season"], df["Rainfall_mm"], color=["#fdae61", "#2c7bb6", "#abd9e9"])
ax.set_ylabel("Total December–April rainfall (mm)")
ax.set_title("Lower Moulouya AOI — CHIRPS wet-season totals")
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
plt.show()
"""
        ),
        md("""## Discuss

1. Is **2025/26** clearly wetter than **2024/25** in the AOI mean? On the **% change** map, is **2025/26** above baseline **everywhere**, or only in patches?
2. Where might **orography** (terrain) concentrate rainfall inside the AOI?
3. Where the baseline is **naturally low**, does the **%** map overstate the story compared to the **absolute** totals map?

**Next:** `03_surface_water_change.ipynb`.
"""),
    ]
    save("02_rainfall_chirps_anomaly.ipynb", cells)


def build_03():
    cells = [
        md(
            f"""# Notebook 3 — Surface water: did rivers and wet areas expand?

{colab_badge("03_surface_water_change.ipynb")}

## Why this matters

Heavy rain can widen **river channels**, refill **reservoirs**, and expand **wetlands** or **temporary ponds**. Optical [**Sentinel-2 SR Harmonized**]({DOC_S2_SR_HARMONIZED}) composites are easy to interpret but **clouds** block the view. [**Sentinel-1 GRD**]({DOC_S1_GRD}) radar sees through clouds and is sensitive to **rough water** and **wet soil** (interpret with care).

## Research questions

1. Where was **open water / very wet surfaces** in the **wet season ending April 2025** versus **ending April 2026**?
2. Which areas look **new or expanded** in **2025/26** compared with **2024/25**?

## Outputs

- **MNDWI** median composites from [**Sentinel-2 SR Harmonized**]({DOC_S2_SR_HARMONIZED}) (wet seasons **2024/25** vs **2025/26**), on the map in a separate cell.
- A simple **mask** of “more water-like in 2026” using a fixed MNDWI threshold (demonstration level, not an operational flood map).
- Optional [**Sentinel-1 GRD**]({DOC_S1_GRD}) **VH** wet-season medians and a **blue** demo layer for **lower VH in 2026** (radar sees through clouds; interpret with care).

**Time tip:** about **35–40 minutes**.
"""
        ),
        code(INSTALL),
        code(INIT),
        code(AOI_PY_DATES),
        md(
            f"""## Sentinel-2: cloud-screened wet-season median

We use [**Harmonised Sentinel-2 SR**]({DOC_S2_SR_HARMONIZED}) (`COPERNICUS/S2_SR_HARMONIZED`). MNDWI combines **green** and **SWIR** bands (roughly: bright water → higher values). We take a **median** across all **December–April** images in each wet season to reduce cloud noise.

**Scale factor:** reflectance values are divided by **10_000** in the harmonised collection. The **next cell** builds the two median images; the **cell after that** opens the map.
"""
        ),
        code(
            """SCALE = 1 / 10_000


def add_mndwi(img: ee.Image) -> ee.Image:
    g = img.select("B3").multiply(SCALE)
    s = img.select("B11").multiply(SCALE)
    mndwi = g.subtract(s).divide(g.add(s)).rename("MNDWI")
    return img.addBands(mndwi)


def s2_wet_season_mndwi_median(april_year: int) -> ee.Image:
    start, end = wet_season_filter_dates(april_year)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(LOWER_MOULOUYA_AOI)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
        .map(add_mndwi)
    )
    return s2.median().clip(LOWER_MOULOUYA_AOI).select("MNDWI")


mndwi_apr2025 = s2_wet_season_mndwi_median(2025)
mndwi_apr2026 = s2_wet_season_mndwi_median(2026)
"""
        ),
        code(
            MAP_SATELLITE_START
            + """visw = {"min": -0.5, "max": 0.6, "palette": ["c9940c", "fff7bc", "74add1", "023858"]}
Map.addLayer(mndwi_apr2025, visw, "MNDWI Apr25")
Map.addLayer(mndwi_apr2026, visw, "MNDWI Apr26")
Map.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.2)
Map
"""
        ),
        md(
            f"""## Simple “more water in 2026” mask

We subtract the two MNDWI images from [**Sentinel-2**]({DOC_S2_SR_HARMONIZED}). Pixels with a **positive difference** above a small cutoff are highlighted. This is a **teaching threshold**, not calibrated for legal or emergency use.
"""
        ),
        code(
            """d_mndwi = mndwi_apr2026.subtract(mndwi_apr2025).rename("dMNDWI")
water_gain = d_mndwi.gt(0.12)

"""
            + MAP2_SATELLITE_START
            + """Map2.addLayer(d_mndwi, {"min": -0.3, "max": 0.3, "palette": ["b35806", "f7f7f7", "542788"]}, "dMNDWI")
Map2.addLayer(water_gain.updateMask(water_gain), {"palette": ["0033ff"]}, "H2O+ demo")
Map2.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.2)
Map2
"""
        ),
        md(
            f"""## Optional — Sentinel-1 VH (cloud-free cross-check)

[**Sentinel-1 GRD**]({DOC_S1_GRD}) **VH** is often **lower** on smooth **open water** than on rough land (very simplified). **Wet soil** and **irrigation** also change VH, so treat this as a **qualitative** check next to MNDWI — not a second copy of the same story.

The **next cell** builds wet-season **VH medians** and a **blue** mask where VH **drops** from **2024/25** to **2025/26** (demo threshold, same idea as the MNDWI “more water-like” mask). The **cell after** draws the map.
"""
        ),
        code(
            """def s1_vh_wet_season_median(april_year: int) -> ee.Image:
    start, end = wet_season_filter_dates(april_year)
    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(LOWER_MOULOUYA_AOI)
        .filterDate(start, end)
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .select("VH")
    )
    return s1.median().clip(LOWER_MOULOUYA_AOI).rename("VH")


vh2025 = s1_vh_wet_season_median(2025)
vh2026 = s1_vh_wet_season_median(2026)
d_vh = vh2026.subtract(vh2025).rename("dVH")
# Demo: stronger VH decrease in 2026 → flag as “more water-like” in blue (tune dB step for your AOI).
s1_water_demo = d_vh.lt(-1.5)
"""
        ),
        code(
            MAP4_SATELLITE_START
            + """vh_vis = {"min": -25, "max": -5, "palette": ["#0d0d0d", "#bdbdbd", "#ffffff"]}
Map4.addLayer(vh2025, vh_vis, "VH Apr25")
Map4.addLayer(vh2026, vh_vis, "VH Apr26")
Map4.addLayer(d_vh, {"min": -4, "max": 4, "palette": ["2166ac", "f7f7f7", "b2182b"]}, "dVH", opacity=0.55)
Map4.addLayer(s1_water_demo.updateMask(s1_water_demo), {"palette": ["0066ff"]}, "S1 H2O+")
Map4.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.2)
Map4
"""
        ),
        md("""## Discuss

1. Do **river corridors** and the **coastal lowlands** show the clearest **MNDWI increase**?
2. Name **one limitation** of using a **fixed MNDWI threshold** across crops, soil, and urban areas.
3. Does the optional **S1** blue mask line up with **MNDWI** water hints, or diverge (and why might radar disagree with green/SWIR optics)?

**Next:** `04_vegetation_ndvi_recovery.ipynb`.
"""),
    ]
    save("03_surface_water_change.ipynb", cells)


def build_04():
    cells = [
        md(
            f"""# Notebook 4 — Vegetation greenness: recovery in the 2025/26 wet season?

{colab_badge("04_vegetation_ndvi_recovery.ipynb")}

## Concept

**NDVI** (Normalised Difference Vegetation Index) from [**Sentinel-2 SR Harmonized**]({DOC_S2_SR_HARMONIZED}) uses **red** and **near-infrared** reflectance. Healthy **green leaves** have **high NDVI**; **bare soil** and **urban** surfaces are lower.

## Research questions

1. Which areas had **lower NDVI in the wet season ending April 2025** (drier / less green)?
2. Where is **ΔNDVI** (wet season **2025/26** minus **2024/25**) largest (strongest green-up)?
3. Does the spatial pattern **look similar** to the rainfall and water maps from earlier notebooks?

## Output

- Median **NDVI** maps for wet seasons **2024/25** and **2025/26** (compute medians in one cell, map in the next).
- A **difference map**, then a **sampled scatter** (Apr26 vs Apr25) **in addition to** a **histogram** of ΔNDVI (run the scatter cell first so both use the same `df_ndvi`).

**Time tip:** about **30 minutes**.
"""
        ),
        code(INSTALL),
        code(INIT),
        code(AOI_PY_DATES),
        code(
            '''SCALE = 1 / 10_000


def add_ndvi(img: ee.Image) -> ee.Image:
    nir = img.select("B8").multiply(SCALE)
    red = img.select("B4").multiply(SCALE)
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    return img.addBands(ndvi)


def s2_wet_season_ndvi_median(april_year: int) -> ee.Image:
    start, end = wet_season_filter_dates(april_year)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(LOWER_MOULOUYA_AOI)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
        .map(add_ndvi)
    )
    return s2.median().clip(LOWER_MOULOUYA_AOI).select("NDVI")


ndvi_apr2025 = s2_wet_season_ndvi_median(2025)
ndvi_apr2026 = s2_wet_season_ndvi_median(2026)
dndvi = ndvi_apr2026.subtract(ndvi_apr2025).rename("dNDVI")
'''
        ),
        code(
            MAP_SATELLITE_START
            + """visv = {"min": 0.0, "max": 0.85, "palette": ["#ffffcc", "#78c679", "#006837"]}
Map.addLayer(ndvi_apr2025, visv, "NDVI Apr25")
Map.addLayer(ndvi_apr2026, visv, "NDVI Apr26")
Map.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.2)
Map
"""
        ),
        md("""## Difference map
"""),
        code(
            MAP2_SATELLITE_START
            + """Map2.addLayer(
    dndvi,
    {"min": -0.35, "max": 0.35, "palette": ["d73027", "ffffbf", "1a9850"]},
    "dNDVI",
)
Map2.addLayer(LOWER_MOULOUYA_AOI, {"color": "333333"}, "AOI", opacity=0.2)
Map2
"""
        ),
        md("""## Scatter — Apr26 vs Apr25 (sampled)

**2500** pixels, **`scale=100` m**, **`seed=42`**. **Above** the dashed **y = x** line → higher NDVI in **Apr26**; **below** → lower. Point **colour** is **ΔNDVI** (same scale idea as the map).
"""),
        code(
            r"""ndvi_pair = (
    ndvi_apr2025.rename("NDVI_Apr25")
    .addBands(ndvi_apr2026.rename("NDVI_Apr26"))
    .addBands(dndvi)
)
pts_fc = ndvi_pair.sample(
    region=LOWER_MOULOUYA_AOI,
    scale=100,
    numPixels=2500,
    geometries=False,
    seed=42,
)
df_ndvi = geemap.ee_to_df(pts_fc)

import numpy as np

x = df_ndvi["NDVI_Apr25"].to_numpy(dtype=float)
y = df_ndvi["NDVI_Apr26"].to_numpy(dtype=float)
dz = df_ndvi["dNDVI"].to_numpy(dtype=float)
ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(dz)
x, y, dz = x[ok], y[ok], dz[ok]

fig, ax = plt.subplots(figsize=(5.5, 5.2))
lim = (0.0, 0.9)
ax.plot(lim, lim, "k--", linewidth=1.0, label="y = x")
sc = ax.scatter(
    x,
    y,
    c=dz,
    cmap="RdYlGn",
    vmin=-0.35,
    vmax=0.35,
    s=16,
    alpha=0.55,
    edgecolors="none",
)
ax.set_aspect("equal", adjustable="box")
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_xlabel("NDVI Apr25")
ax.set_ylabel("NDVI Apr26")
ax.set_title("Sampled pixels")
ax.legend(loc="lower right", fontsize=8)
fig.colorbar(sc, ax=ax, shrink=0.82, label="ΔNDVI")
plt.tight_layout()
plt.show()
"""
        ),
        md("""## Histogram — ΔNDVI (same sample)

Uses **`df_ndvi`** from the **scatter cell** (run that cell first).
"""),
        code(
            r"""import numpy as np

if "df_ndvi" not in globals():
    raise RuntimeError("Run the scatter cell above first (it builds df_ndvi).")

dz = df_ndvi["dNDVI"].to_numpy(dtype=float)
dz = dz[np.isfinite(dz)]

dz_lo, dz_hi, n_bins = -0.4, 0.4, 30
counts, edges = np.histogram(dz, bins=n_bins, range=(dz_lo, dz_hi))
centres = (edges[:-1] + edges[1:]) / 2.0
bin_w = (dz_hi - dz_lo) / n_bins

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(centres, counts, width=bin_w * 0.92, color="#31a354", edgecolor="white", linewidth=0.3)
ax.axvline(0.0, color="0.35", linestyle=":", linewidth=0.9)
ax.set_xlabel("ΔNDVI")
ax.set_ylabel("Count")
ax.set_title("ΔNDVI distribution")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            f"""## Optional extension — EVI

EVI is less saturated than NDVI in **dense** vegetation. If you finish early, duplicate the NDVI function on [**Sentinel-2 SR Harmonized**]({DOC_S2_SR_HARMONIZED}) using:

`EVI = 2.5 * (NIR − Red) / (NIR + 6*Red − 7.5*Blue + 1)` with scaled reflectances.

**Next:** `05_optional_random_forest_land_cover.ipynb`.
"""
        ),
    ]
    save("04_vegetation_ndvi_recovery.ipynb", cells)


def build_05():
    cells = [
        md(
            f"""# Notebook 5 (optional) — Find irrigation ponds with a Random Forest

{colab_badge("05_optional_random_forest_land_cover.ipynb")}

## Objective

This notebook presents a **self-contained** supervised workflow: collect marker points on **pond** and **non-pond** pixels, train a **binary Random Forest** (**pond = 1**, **not pond = 0**), then map likely ponds and count separate patches (each patch → **one centroid** on the map).

## Data and masks

- **Satellite:** a **cloud-masked mean Sentinel-2 image** from [**Sentinel-2 SR Harmonized**]({DOC_S2_SR_HARMONIZED}) over **March-April 2026**. We keep a relatively high scene cloud threshold, then mask cloud/shadow pixels per image and take the mean for stable full-AOI coverage.
- **Where we run the model:** we remove **urban** pixels with [**ESA WorldCover v200**]({DOC_ESA_WORLDCOVER_V200}) (class **50**) and keep only gentle terrain from [**SRTM DEM**]({DOC_SRTM}) using a user-set **`SLOPE_MAX_DEG`** threshold.

The classifier uses **scaled reflectance** plus **NDVI** and **NDWI** — the same spectral contrast that makes ponds look **dark** in false colour (**B8, B4, B3** on screen).

**Time tip:** about **30–40 minutes**. **Prerequisite:** notebooks **00** and **01** (Earth Engine + AOI).
"""
        ),
        code(INSTALL),
        code(INIT),
        code(AOI_PY_DATES),
        md(
            """## Build one consistent Sentinel-2 image (mean composite)

We use **March-April 2026**, allow scene metadata cloud up to **40 %**, mask cloud/shadow pixels with **SCL**, then take the **mean**. This keeps code simple and usually gives full basin coverage.
"""
        ),
        code(
            r"""YEAR_SCENE = 2026
CLOUD_MAX = 40
N_MEAN = 20


def mask_s2_clouds(img: ee.Image) -> ee.Image:
    scl = img.select("SCL")
    bad = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(11))
    return img.updateMask(bad.Not())


s2_col = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(LOWER_MOULOUYA_AOI)
    .filterDate(f"{YEAR_SCENE}-03-01", f"{YEAR_SCENE}-05-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD_MAX))
    .sort("CLOUDY_PIXEL_PERCENTAGE")
)

n_scenes = int(s2_col.size().getInfo())
if n_scenes < 1:
    raise RuntimeError("No Sentinel-2 scenes found for March-April 2026.")

scene = (
    s2_col.limit(N_MEAN)
    .map(mask_s2_clouds)
    .select(["B2", "B3", "B4", "B8", "B11"])
    .mean()
    .clip(LOWER_MOULOUYA_AOI)
)
print("Scenes used in mean:", min(N_MEAN, n_scenes))
"""
        ),
        md(
            """## Quick check — composite coverage

Run this map now to confirm there are no tile-edge gaps before moving on.
"""
        ),
        code(
            r"""SCALE = 1 / 10_000
vis_rgb = {"bands": ["B8", "B4", "B3"], "min": 0.06, "max": 0.45, "gamma": 1.05}
rgb_preview = scene.multiply(SCALE).select(["B8", "B4", "B3"])

Map_scene = geemap.Map()
Map_scene.add_basemap("SATELLITE")
Map_scene.centerObject(LOWER_MOULOUYA_AOI, 9)
Map_scene.addLayer(rgb_preview, vis_rgb, "False colour preview (Mar-Apr mean)")
Map_scene.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.22)
Map_scene.add_layer_control()
Map_scene
"""
        ),
        md(
            f"""## Work mask: remove urban, then apply slope

We exclude **urban** using [**ESA WorldCover v200**]({DOC_ESA_WORLDCOVER_V200}) class **50**, then keep only gentle terrain from [**SRTM DEM**]({DOC_SRTM}).

You can tune **`SLOPE_MAX_DEG`** to widen or narrow the final mask.
"""
        ),
        code(
            r"""# User options
SLOPE_MAX_DEG = 15

wc = (
    ee.ImageCollection("ESA/WorldCover/v200")
    .filterDate("2021-01-01", "2022-01-01")
    .first()
    .select("Map")
    .clip(LOWER_MOULOUYA_AOI)
)
urban = wc.eq(50)

dem = ee.Image("USGS/SRTMGL1_003").clip(LOWER_MOULOUYA_AOI)
slope_deg = ee.Terrain.slope(dem)
gentle = slope_deg.lt(SLOPE_MAX_DEG)

work_mask = urban.Not().And(gentle).rename("work").byte()
"""
        ),
        md(
            """## Map — mask components and final work mask

- **Grey**: urban (excluded)
- **Green**: gentle slope (kept)
- **Orange**: final mask used by the Random Forest
"""
        ),
        code(
            r"""Map_plain = geemap.Map()
Map_plain.add_basemap("SATELLITE")
Map_plain.centerObject(LOWER_MOULOUYA_AOI, 9)
Map_plain.addLayer(urban.selfMask(), {"palette": ["#969696"], "opacity": 0.65}, "Urban (WorldCover class 50)")
Map_plain.addLayer(gentle.selfMask(), {"palette": ["#74c476"], "opacity": 0.35}, f"Gentle slope < {SLOPE_MAX_DEG} deg")
Map_plain.addLayer(work_mask.selfMask(), {"palette": ["#fecc5c"], "opacity": 0.85}, "Final work mask")
Map_plain.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.22)
Map_plain.add_layer_control()
Map_plain
"""
        ),
        md(
            """## Spectral stack for the Random Forest

Bands are scaled with **`SCALE = 1 / 10_000`**. Indices help separate **open water** from **bright vegetation** in the plains.
"""
        ),
        code(
            r"""SCALE = 1 / 10_000


def stack_for_rf(img: ee.Image) -> ee.Image:
    x = img.multiply(SCALE)
    ndvi = x.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = x.normalizedDifference(["B3", "B8"]).rename("NDWI")
    return x.addBands(ndvi).addBands(ndwi)


stack_img = stack_for_rf(scene)
bands = ["B2", "B3", "B4", "B8", "B11", "NDVI", "NDWI"]

vis_rgb = {"bands": ["B8", "B4", "B3"], "min": 0.06, "max": 0.45, "gamma": 1.05}
rgb = scene.multiply(SCALE).select(["B8", "B4", "B3"])


def safe_clear_drawn(map_widget):
    # Clear user drawings; tolerates geemap/ipyleaflet layer list desynchronisation.
    try:
        map_widget.remove_drawn_features()
    except Exception:
        dc = getattr(map_widget, "_draw_control", None)
        if dc is None:
            return
        try:
            lyr = dc.layer
            if lyr is not None and lyr in map_widget.layers:
                map_widget.remove_layer(lyr)
        except Exception:
            pass
        dc.geometries = []
        dc.properties = []
        dc.last_geometry = None
        dc.layer = None
        ee_layers = getattr(map_widget, "ee_layers", None)
        if ee_layers is not None:
            ee_layers.pop("Drawn Features", None)
        if hasattr(dc, "data"):
            dc.data = []
            dc.send_state(key="data")


Map = geemap.Map()
Map.add_basemap("SATELLITE")
Map.centerObject(LOWER_MOULOUYA_AOI, 11)
Map.addLayer(rgb, vis_rgb, "False colour (Mar-Apr mean)")
Map.addLayer(work_mask.selfMask(), {"palette": ["#ffeda0"], "opacity": 0.35}, "Work mask (not urban, gentle slope)")
Map.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.12)
Map.add_layer_control()
Map
"""
        ),
        md(
            """## Step 1 — Marker points on **ponds** (`class = 1`)

Use the **point / marker** tool. Place **≥ 8** markers on **dark pond** pixels inside the yellow plains mask, then run the next cell.
"""
        ),
        code(
            r"""pond_markers = ee.FeatureCollection(Map.draw_features).map(lambda f: f.set("class", 1))
if pond_markers.size().getInfo() < 8:
    raise ValueError("Add at least 8 pond markers, then re-run.")
safe_clear_drawn(Map)
print("Pond markers:", pond_markers.size().getInfo())
"""
        ),
        md(
            """## Step 2 — Markers on land that is **not** a pond (`class = 0`)

Place **≥ 8** markers on **crop**, **soil**, or **tracks** (clearly **not** open water) within the same yellow mask, then run the next cell.
"""
        ),
        code(
            r"""other_markers = ee.FeatureCollection(Map.draw_features).map(lambda f: f.set("class", 0))
if other_markers.size().getInfo() < 8:
    raise ValueError("Add at least 8 non-pond markers, then re-run.")
safe_clear_drawn(Map)
print("Non-pond markers:", other_markers.size().getInfo())
"""
        ),
        md(
            """## Step 3 — Train, classify, vectorise, count

`sampleRegions` reads spectra at **10 m** under your markers. We train on **all labelled points** and predict directly. Predictions are limited to **`work_mask`**. **`reduceToVectors`** builds polygons; **centroids** are one point per patch for mapping and **patch count**.
"""
        ),
        code(
            r"""train_fc = pond_markers.merge(other_markers)

training = stack_img.select(bands).sampleRegions(
    collection=train_fc,
    properties=["class"],
    scale=10,
    geometries=True,
)
print("Training samples:", int(training.size().getInfo()))

classifier = ee.Classifier.smileRandomForest(numberOfTrees=80, seed=5).train(
    features=training,
    classProperty="class",
    inputProperties=bands,
)

pred = stack_img.select(bands).classify(classifier).rename("label").byte()
pond_mask = pred.eq(1).updateMask(work_mask).rename("pond")

AREA_MIN_M2 = 300.0
vectors = pond_mask.selfMask().reduceToVectors(
    geometry=LOWER_MOULOUYA_AOI,
    scale=20,
    geometryType="polygon",
    eightConnected=False,
    maxPixels=1e10,
    tileScale=4,
    labelProperty="pond",
)
with_area = vectors.map(lambda f: f.set("area_m2", f.geometry().area(maxError=10)))
pond_patches = with_area.filter(ee.Filter.gte("area_m2", AREA_MIN_M2))
pond_points = pond_patches.map(
    lambda f: ee.Feature(f.geometry().centroid(10), {"area_m2": f.get("area_m2")})
)

n_patches = int(pond_patches.size().getInfo())
print("Predicted pond patches (minimum area filter):", n_patches)
"""
        ),
        md(
            """## Map — ponds, patch centres, training markers

**Magenta:** predicted **patch centres**. **Cyan / yellow:** your **pond / not-pond** training markers. Compare **RF pond mask** and **plains mask** against false colour.
"""
        ),
        code(
            r"""train_pond = train_fc.filter(ee.Filter.eq("class", 1))
train_other = train_fc.filter(ee.Filter.eq("class", 0))

Map2 = geemap.Map()
Map2.add_basemap("SATELLITE")
Map2.centerObject(LOWER_MOULOUYA_AOI, 11)
Map2.addLayer(rgb, vis_rgb, "False colour (April mean)")
Map2.addLayer(work_mask.selfMask(), {"palette": ["#ffeda0"], "opacity": 0.25}, "Plains mask", shown=False)
Map2.addLayer(pond_mask.selfMask(), {"palette": ["#225ea8"], "opacity": 0.45}, "RF pond mask")
Map2.addLayer(pond_points, {"color": "#ff00ff", "pointRadius": 5}, "Pond patch centres")
Map2.addLayer(train_pond, {"color": "#00ffff", "pointRadius": 6}, "Training: pond")
Map2.addLayer(train_other, {"color": "#ffff00", "pointRadius": 6}, "Training: not pond")
Map2.addLayer(LOWER_MOULOUYA_AOI, {"color": "red"}, "AOI", opacity=0.1)
Map2.add_layer_control()
Map2
"""
        ),
        md(
            """## Reflect

1. Why does **patch count** depend on both the **model** and the **`reduceToVectors` scale**?
2. If river lines still leak through, how would you add a **manual river centreline buffer** before vectorising, without changing the Random Forest training code?

**Congratulations** — you have finished the optional **Random Forest** exercise for this module.
"""
        ),
    ]
    save("05_optional_random_forest_land_cover.ipynb", cells)


def main():
    NB_DIR.mkdir(parents=True, exist_ok=True)
    build_00()
    build_02()
    build_01()
    build_03()
    build_04()
    build_05()


if __name__ == "__main__":
    main()
