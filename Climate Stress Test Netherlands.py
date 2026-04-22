import os
!pip install rioxarray
import rioxarray
import xarray as xr
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION & BANKING PARAMETERS ---
DIKE_OFFSET = 1.5       # Accounts for Dutch flood defenses
SSM_CONSTANT = 3.0      # Standard Methode Schade (building resilience)
LGD_BASE = 0.20         # Regulatory floor (20%)
HAIRCUT = 0.15          # Liquidation cost (15%)
ING_ORANGE = '#FF6600'
ING_BLUE = '#000066'

# --- 2. SPATIAL DATA INGESTION ---
# Define filenames (Ensure these match your sidebar exactly)
path_45 = "inuncoast_rcp4p5_nosub_2050_rp0100_0.tif"
path_85 = "inuncoast_rcp8p5_nosub_2050_rp0100_0.tif"
json_path = "netherlands_boundary.json"

def process_hazard_map(path, boundary_gdf):
    # Load using Dask for memory efficiency
    raster = rioxarray.open_rasterio(path, chunks={'x': 1000, 'y': 1000})
    # Align CRS
    boundary_gdf = boundary_gdf.to_crs(raster.rio.crs)
    # Mask to National Boundary
    masked = raster.rio.clip(boundary_gdf.geometry, boundary_gdf.crs, drop=True)
    # Clean No-Data values
    return masked.where(masked > 0, 0)

# Load boundary and maps
nl_shape = gpd.read_file(json_path)
map_rcp45 = process_hazard_map(path_45, nl_shape)
map_rcp85 = process_hazard_map(path_85, nl_shape)

print("✅ Spatial Hazard Maps Loaded and Masked.")

# --- 3. PORTFOLIO DEFINITION & RISK EXTRACTION ---
data = {
    'Asset_Name': ['Amsterdam Office', 'Rotterdam Port', 'Utrecht Hub', 'Almere Res.', 'The Hague HQ', 'Groningen Log.'],
    'Loan_Value_EUR': [55_000_000, 92_000_000, 34_000_000, 18_000_000, 48_000_000, 22_000_000],
    'Lat': [52.3676, 51.9225, 52.0907, 52.3702, 52.0705, 53.2192],
    'Lon': [4.9041, 4.4792, 5.1214, 5.2141, 4.3007, 6.5665]
}
portfolio = gpd.GeoDataFrame(pd.DataFrame(data),
                             geometry=gpd.points_from_xy(data['Lon'], data['Lat']),
                             crs="EPSG:4326")

def extract_depth(row, hazard_map):
    return float(hazard_map.sel(x=row.geometry.x, y=row.geometry.y, method="nearest").values)

portfolio['Depth_45'] = portfolio.apply(extract_depth, axis=1, hazard_map=map_rcp45)
portfolio['Depth_85'] = portfolio.apply(extract_depth, axis=1, hazard_map=map_rcp85)

# --- 4. FINANCIAL RISK ENGINE (SSM -> LGD) ---
def calculate_stress_lgd(raw_depth, loan_value):
    # Apply Dike Offset
    eff_depth = max(0, raw_depth - DIKE_OFFSET)
    # Physical Damage Factor (SSM)
    alpha = min(1.0, np.sqrt(eff_depth) / SSM_CONSTANT)
    # Financial Recovery logic
    collateral_val = loan_value * 1.2 # 80% LTV base
    recovery = (collateral_val * (1 - alpha)) * (1 - HAIRCUT)
    # Calculate migration
    lgd_stress = (loan_value - recovery) / loan_value
    return max(LGD_BASE, lgd_stress)

portfolio['LGD_45'] = portfolio.apply(lambda x: calculate_stress_lgd(x['Depth_45'], x['Loan_Value_EUR']), axis=1)
portfolio['LGD_85'] = portfolio.apply(lambda x: calculate_stress_lgd(x['Depth_85'], x['Loan_Value_EUR']), axis=1)

print("✅ Financial Risk Engine: LGD Migration Calculated.")

# --- 5. VISUALIZATION A: HAZARD MAPS ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# RCP 4.5 Map
map_rcp45.plot(ax=ax1, cmap="Blues", vmax=5, cbar_kwargs={'label': 'Depth (m)'})
nl_shape.boundary.plot(ax=ax1, color="black", linewidth=0.5)
portfolio.plot(ax=ax1, color='red', markersize=40)
ax1.set_title("Physical Hazard: RCP 4.5 (Moderate 2050)")

# RCP 8.5 Map
map_rcp85.plot(ax=ax2, cmap="Blues", vmax=5, cbar_kwargs={'label': 'Depth (m)'})
nl_shape.boundary.plot(ax=ax2, color="black", linewidth=0.5)
portfolio.plot(ax=ax2, color='red', markersize=40)
ax2.set_title("Physical Hazard: RCP 8.5 (Severe 2050)")

plt.tight_layout()
plt.show()

# --- 6. VISUALIZATION B: FINANCIAL IMPACT ---
fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(portfolio['Asset_Name']))
width = 0.25

ax.bar(x - width, [LGD_BASE*100]*len(portfolio), width, label='Baseline LGD', color='grey', alpha=0.5)
ax.bar(x, portfolio['LGD_45']*100, width, label='Stress LGD: RCP 4.5', color='#FFCC00')
ax.bar(x + width, portfolio['LGD_85']*100, width, label='Stress LGD: RCP 8.5', color=ING_ORANGE)

ax.set_ylabel('Loss Given Default (%)')
ax.set_title('Financial Impact: LGD Migration across Climate Scenarios', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(portfolio['Asset_Name'], rotation=30)
ax.legend()
plt.grid(axis='y', alpha=0.2)
plt.show()

# --- 7. EXPORT DELIVERABLE ---
portfolio.to_csv("ING_Climate_Stress_Test_Results.csv", index=False)
print("📂 Deliverable exported to CSV.")
