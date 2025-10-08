# 🌱 Terrace Extractor  
*A lightweight workflow for delineating terraced slopes from high-resolution imagery*  

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![GeoTools](https://img.shields.io/badge/GeoPackage-✔-brightgreen)](https://gdal.org/drivers/vector/gpkg.html)  

---

## 📖 Overview
This repository provides a minimal tool to **detect terraces from satellite imagery** and export them as GIS-ready vector files.  
The workflow uses:
- **Canny edge detection** → to capture terrace breaks,
- **Skeletonization** → to thin terrace edges, and
- **Vectorization** → to convert edges into polylines (`.gpkg` or `.shp`).  

This tool is designed for **terraced terrains formed by cutting (no fills)** and intended as a preprocessing step before DEM enhancement and physics-based slope stability modeling (e.g., TRIGRS).

---

## 🖼️ Example Workflow

**Input:** High-resolution satellite image of terraced terrain  
**Step 1:** Canny edge detection  
**Step 2:** Skeletonization  
**Step 3:** Terrace polylines exported to GeoPackage  

---

## ⚙️ Installation
Clone and install requirements:

```bash
git clone https://github.com/<your-username>/terrace-extractor.git
cd terrace-extractor
pip install -r requirements.txt
```

---

## 🚀 Usage

### With GeoTIFF (georeferenced)
```bash
python terrace_extractor/terrace_extractor.py   --image /path/to/image.tif   --out ./out   --t1 50 --t2 150 --kernel 3   --min-length 5   --as-gpkg
```

### With JPEG/PNG (no georeferencing)
```bash
python terrace_extractor/terrace_extractor.py   --image /path/to/image.jpg   --out ./out   --t1 50 --t2 150 --kernel 3   --min-length 5   --epsg 32643   --pixel-size 0.3   --origin-x 500000   --origin-y 1100000   --as-gpkg
```

---

## 📂 Outputs
- `terrace_edges.tif` / `.png` → binary edge raster  
- `terrace_skeleton.tif` / `.png` → thinned terrace skeleton  
- `terrace_lines.gpkg` or `.shp` → vectorized terrace polylines  

---

## 🔧 Next Steps (in GIS)
1. Open `terrace_lines.gpkg` in ArcGIS/QGIS.  
2. Attach **field-measured attributes** (bench width, spacing, depth).  
3. Rasterize terrace features and subtract measured depths from R-DEM → build **M-DEM**.  
4. Use M-DEM in physics-based models (TRIGRS, Scoops-3D, etc.).  

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).  

---

## 🙌 Citation
If you use this workflow, please cite:  
> Abhijith A. Kumar, et al. (2025). *A Novel DEM Enhancement Methodology to Improve Physics-Based Susceptibility Modeling of Rainfall-Induced Landslides Along Anthropogenically Modified Slopes*. **Canadian Geotechnical Journal.**

---

## ⭐ Acknowledgements
- Developed as part of PhD research at **IIT Palakkad**.  
- Built on open-source libraries: OpenCV, scikit-image, GeoPandas, Shapely, Rasterio.  
