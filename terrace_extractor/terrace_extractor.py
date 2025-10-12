#!/usr/bin/env python3
"""
Terrace extractor (image → Canny → skeleton → polylines)
"""

import argparse, os
from typing import Optional, Tuple
import numpy as np
import cv2
from skimage.morphology import skeletonize
import geopandas as gpd
from shapely.geometry import LineString
from pathlib import Path

def _try_import_rasterio():
    try:
        import rasterio
        from rasterio.transform import Affine
        from rasterio.crs import CRS
        return rasterio, Affine, CRS
    except Exception:
        return None, None, None

def read_image(path: str):
    rasterio, Affine, CRS = _try_import_rasterio()
    ext = Path(path).suffix.lower()
    if rasterio is not None and ext in [".tif", ".tiff"]:
        with rasterio.open(path) as ds:
            arr = ds.read()
            if arr.shape[0] == 3:
                img = np.transpose(arr, (1, 2, 0))[:, :, ::-1].copy()
            elif arr.shape[0] >= 1:
                band = arr[0]
                img = np.stack([band, band, band], axis=-1).astype(band.dtype)
            transform = ds.transform
            crs = ds.crs
            return img, (transform, crs)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    return img, None

def save_binary(binary, out_path, transform=None, crs=None):
    rasterio, Affine, CRS = _try_import_rasterio()
    if rasterio is None or transform is None or crs is None:
        cv2.imwrite(out_path.replace(".tif", ".png"), (binary.astype(np.uint8) * 255))
        return
    with rasterio.open(out_path, "w", driver="GTiff",
        height=binary.shape[0], width=binary.shape[1], count=1,
        dtype="uint8", transform=transform, crs=crs, compress="lzw") as dst:
        dst.write((binary.astype(np.uint8)), 1)

def canny_and_skeleton(image_bgr, t1, t2, kernel):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (kernel, kernel), 0)
    edges = cv2.Canny(blurred, t1, t2)
    skel = skeletonize((edges > 0).astype(np.uint8)).astype(np.uint8)
    return (edges > 0).astype(np.uint8), skel

def vectorize_skeleton(skel, pixel_size, transform=None, crs=None, epsg=None, origin_xy=None):
    skel_u8 = (skel.astype(np.uint8) * 255)
    contours, _ = cv2.findContours(skel_u8, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    lines = []
    if transform is not None and crs is not None:
        a = transform.a; e = transform.e; c = transform.c; f = transform.f
        for cnt in contours:
            if len(cnt) < 2: continue
            pts = [(c + int(p[0][0]) * a, f + int(p[0][1]) * e) for p in cnt]
            try: lines.append(LineString(pts))
            except: pass
        gdf = gpd.GeoDataFrame(geometry=lines, crs=crs)
    else:
        if origin_xy is None: origin_xy = (0.0, 0.0)
        x0, y0 = origin_xy
        for cnt in contours:
            if len(cnt) < 2: continue
            pts = [(x0 + int(p[0][0]) * pixel_size, y0 - int(p[0][1]) * pixel_size) for p in cnt]
            try: lines.append(LineString(pts))
            except: pass
        gdf = gpd.GeoDataFrame(geometry=lines)
        if epsg is not None:
            gdf = gdf.set_crs(epsg)
    return gdf

def filter_by_length(gdf, min_length_m, project_epsg):
    if project_epsg is not None:
        gdf = gdf.to_crs(project_epsg)
    if gdf.crs is None or gdf.crs.is_geographic:
        return gdf
    return gdf[gdf.geometry.length >= min_length_m].copy()

def write_vectors(gdf, out_dir, as_gpkg):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    if as_gpkg:
        out_gpkg = out_dir / "terrace_lines.gpkg"
        gdf.to_file(out_gpkg, layer="terraces", driver="GPKG")
        return str(out_gpkg)
    else:
        out_shp = out_dir / "terrace_lines.shp"
        gdf.to_file(out_shp)
        return str(out_shp)

def main():
    ap = argparse.ArgumentParser(description="Terrace extractor: Canny + skeletonization -> polylines")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--t1", type=int, default=50)
    ap.add_argument("--t2", type=int, default=150)
    ap.add_argument("--kernel", type=int, default=3)
    ap.add_argument("--min-length", type=float, default=5.0)
    ap.add_argument("--as-gpkg", action="store_true")
    ap.add_argument("--epsg", type=int, default=None)
    ap.add_argument("--pixel-size", type=float, default=0.3)
    ap.add_argument("--origin-x", type=float, default=0.0)
    ap.add_argument("--origin-y", type=float, default=0.0)
    ap.add_argument("--project-epsg", type=int, default=None)
    args = ap.parse_args()

    img, geo = read_image(args.image)
    transform = crs = None
    if geo is not None: transform, crs = geo

    edges_bin, skel = canny_and_skeleton(img, args.t1, args.t2, args.kernel)
    save_binary(edges_bin, os.path.join(args.out, "terrace_edges.tif"), transform, crs)
    save_binary(skel, os.path.join(args.out, "terrace_skeleton.tif"), transform, crs)

    if transform is not None and crs is not None:
        gdf = vectorize_skeleton(skel, pixel_size=args.pixel_size, transform=transform, crs=crs)
    else:
        gdf = vectorize_skeleton(skel, args.pixel_size, epsg=args.epsg, origin_xy=(args.origin_x, args.origin_y))

    gdf = filter_by_length(gdf, args.min_length, args.project_epsg)
    vec_path = write_vectors(gdf, args.out, as_gpkg=args.as_gpkg)
    print("Outputs written to:", args.out)
    print("Vector file:", vec_path)

if __name__ == "__main__":
    main()
