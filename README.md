# Physical Climate Risk: LGD Migration Prototype (Netherlands)

## Project Overview
This repository contains a Python-based **Climate Stress Testing** prototype. The goal is to quantify the financial impact of coastal flooding on a proxy portfolio of commercial real estate in the Netherlands for the year 2050.

## Methodology
- **Hazard Data:** Coastal flood inundation maps from **WRI Aqueduct** (1-in-100 year return period).
- **Scenarios:** Comparison between **RCP 4.5** (Moderate) and **RCP 8.5** (Severe/Business-as-Usual).
- **Calibration:** Applied a **1.5-meter dike protection offset** to account for Dutch flood defense standards.
- **Financial Logic:** Used the **Standard Methode Schade (SSM)** damage function to calculate collateral impairment and subsequent **Loss Given Default (LGD)** migration from a 20% regulatory floor.

## Tech Stack
- **Spatial Analysis:** `rioxarray`, `GeoPandas`, `xarray`
- **Parallel Processing:** `Dask` (for handling large raster files)
- **Visualization:** `Matplotlib`

## Key Results
- Successfully identified **Residual Risk** in "outside-the-dike" locations (e.g., Rotterdam Port).
- Modeled non-linear LGD migration based on depth-damage curves.
