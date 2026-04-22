# Physical Climate Risk: LGD Migration Prototype (Netherlands)

## Project Overview

This repository contains a Python-based **Climate Stress Testing** prototype that quantifies the financial impact of coastal flooding on a proxy portfolio of commercial real estate loans in the Netherlands, projected to the year **2050**.

The core question it answers: *If a 1-in-100-year coastal flood event occurs in 2050, how much does the Loss Given Default (LGD) migrate for each loan in the portfolio — and which assets are most exposed?*

The methodology is aligned with the DNB physical climate risk framework and ECB supervisory expectations for climate stress testing.
---

## Methodology

The model follows a three-stage pipeline: **Hazard → Damage → Financial Impact**.

### 1. Hazard: Flood Inundation Data
- **Source:** WRI Aqueduct coastal flood inundation rasters (1-in-100 year return period, year 2050, no subsidence).
- **Scenarios:** Two emissions pathways are compared:
  - **RCP 4.5** — Moderate mitigation (Paris-aligned trajectory)
  - **RCP 8.5** — Severe / Business-as-Usual (no mitigation)
- The rasters are clipped to the Netherlands national boundary and flood depth (in metres) is extracted at each asset's GPS coordinates.

### 2. Damage: SSM Depth-Damage Curve
- A **1.5-metre dike protection offset** is subtracted from the raw flood depth to reflect Dutch flood defense standards. If the effective depth is ≤0, the asset is considered protected.
- For assets where effective depth exceeds zero, the **Standard Methode Schade (SSM)** damage function computes a physical damage factor (`alpha`):

  ```
  alpha = min(1.0, sqrt(effective_depth) / 3.0)
  ```

  This is a **non-linear** relationship — shallow flooding causes proportionally less damage than deep flooding, reflecting real-world building resilience.

### 3. Financial: LGD Migration
- Collateral value is modelled at 120% of loan value (80% LTV base).
- Physical damage reduces collateral, with an additional 15% liquidation haircut.
- The resulting stressed LGD is floored at the **20% regulatory minimum**:

  ```
  LGD_stress = max(20%, (Loan - Recovery) / Loan)
  ```

---

## Portfolio

A proxy portfolio of six Dutch commercial real estate loans, spanning the main economic regions:

| Asset | Loan Value (€M) | Location |
|---|---|---|
| Amsterdam Office | 55 | Amsterdam, North Holland |
| Rotterdam Port | 92 | Rotterdam, South Holland |
| Utrecht Hub | 34 | Utrecht |
| Almere Res. | 18 | Almere, Flevoland |
| The Hague HQ | 48 | The Hague, South Holland |
| Groningen Log. | 22 | Groningen |

---

## Results

### Hazard Maps (RCP 4.5 vs RCP 8.5)

![RCP 4.5 vs 8.5](RCP%204.5%20vs%208.5.png)

The two hazard maps show that the **spatial pattern of flood risk is consistent across both scenarios** — the same regions are at risk (IJsselmeer coastline, Zeeland, the Rhine-Maas delta near Rotterdam, and Groningen). The key difference between RCP 4.5 and RCP 8.5 is **depth intensity**, not geography: the worst-case scenario produces deeper inundation in the same zones.

All six portfolio assets sit in or near flood-exposed zones in western and northern Netherlands, consistent with the country's low-lying topography.

### Financial Impact: LGD Migration

![Financial Impact](Financial%20Impact.png)

| Asset | Loan (€M) | Baseline LGD | Stress LGD (RCP 4.5) | Stress LGD (RCP 8.5) |
|---|---|---|---|---|
| Amsterdam Office | 55 | 20% | 20% | 20% |
| Rotterdam Port | 92 | 20% | 20% | 20% |
| Utrecht Hub | 34 | 20% | 20% | 20% |
| **Almere Res.** | **18** | **20%** | **~47%** | **~48%** |
| The Hague HQ | 48 | 20% | 20% | 20% |
| Groningen Log. | 22 | 20% | 20% | 20% |

**Five of six assets remain at the 20% regulatory floor** — the 1.5m dike offset absorbs the flood depth at those locations, leaving zero effective depth and no incremental loss.

**Almere Res. is the critical outlier.** Its LGD more than doubles from 20% to ~47–48% under both scenarios. This is geographically intuitive: Almere sits in the **Flevopolder**, reclaimed land lying several metres below sea level. If flood defenses are overtopped, it faces some of the deepest inundation in the portfolio.

---

## Key Conclusions

**1. Dutch flood defenses dominate the outcome.**
The 1.5m dike offset is the single most influential parameter in the model. For 5 of 6 assets, it fully absorbs the projected flood depth, preventing any LGD migration. The model's results are highly sensitive to this assumption — a 0.5m change to the offset could materially alter the conclusions for multiple assets.

**2. Almere is the portfolio's primary climate vulnerability.**
Despite being the smallest loan (€18M), Almere is the only asset that breaks through the dike protection threshold, generating a ~135–140% LGD increase above the baseline. Under a regulatory stress-testing context, this asset would warrant watch-list classification or increased provisioning.

**3. RCP 4.5 and RCP 8.5 produce near-identical financial outcomes.**
The marginal difference in inundation depth between the two emissions scenarios — at a 1-in-100-year return period by 2050 — is not large enough to drive materially different LGDs at these asset locations. The flood risk is already largely crystallized under moderate warming; the incremental severity of the worst-case scenario does not add significant financial exposure beyond what RCP 4.5 already implies.

**4. Rotterdam Port carries unmodelled residual risk.**
Rotterdam Port represents the largest single exposure (€92M) and sits in an "outside-the-dike" location by definition — yet its LGD stays at the regulatory floor. This is a likely model limitation: the point-extraction may land on a raster cell that credits full dike protection, missing the true waterside exposure. In a production model, this asset would require manual overrides or higher-resolution local flood data.

**5. Subsidence exclusion likely understates long-run risk.**
The flood data uses the `nosub` (no subsidence) variant. The Netherlands experiences ongoing land subsidence, particularly in peat-heavy areas of western Holland. Including subsidence would raise effective flood depths and likely push additional assets — particularly Amsterdam Office and The Hague HQ — above the dike protection threshold.

---

## Limitations

| Limitation | Impact |
|---|---|
| Uniform 1.5m dike offset applied to all assets | Overstates protection for assets with weaker local defenses |
| Subsidence excluded from hazard data | Understates long-run flood depth, especially in western Netherlands |
| Six-asset proxy portfolio | Not statistically representative of a real loan book |
| Point-based depth extraction | Sensitive to raster resolution; may miss local flood features |
| No transition risk modelled | Only physical risk is captured; regulatory/carbon repricing is out of scope |

---

## Tech Stack

| Purpose | Library |
|---|---|
| Spatial raster analysis | `rioxarray`, `xarray` |
| Vector / boundary data | `GeoPandas` |
| Memory-efficient raster loading | `Dask` |
| Visualization | `Matplotlib` |

---

## Usage

1. Download WRI Aqueduct inundation rasters for RCP 4.5 and RCP 8.5 (2050, RP100) and place them in the project root.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python "Climate Stress Test Netherlands.py"`
4. Outputs: hazard maps, LGD migration chart, and `dutch_portfolio_stress_test_results.csv`

---                                                      

## Development                                           

Built in Python. Improved iteratively using Claude Code.
