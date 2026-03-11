# backend/app/utils/raster_utils.py
import os
from typing import Tuple
import numpy as np
from PIL import Image
import rasterio
from rasterio.enums import Resampling

def get_tif_metadata(tif_path: str) -> dict:
    """Return basic raster metadata (bounds, crs, width, height, count)."""
    with rasterio.open(tif_path) as src:
        return {
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "bounds": tuple(src.bounds),
            "transform": tuple(src.transform)
        }

def _read_rgb_window(src, out_shape: Tuple[int,int]):
    """
    Read raster and return an (H,W,3) numpy array in 0-255.
    Handles 1-band (grayscale) and >=3 band rasters (assumes RGB in first 3).
    """
    # target shape: (bands, H, W)
    bands = src.count
    if bands >= 3:
        arr = src.read([1,2,3], out_shape=(3, out_shape[0], out_shape[1]), resampling=Resampling.bilinear)
    else:
        # read first band and stack into 3
        a = src.read(1, out_shape=(out_shape[0], out_shape[1]), resampling=Resampling.bilinear)
        arr = np.stack([a,a,a], axis=0)
    # normalize per-band to 0-255
    img = np.zeros((out_shape[0], out_shape[1], 3), dtype=np.uint8)
    for i in range(3):
        band = arr[i].astype(np.float32)
        # scale robustly: clip percentiles to avoid outliers
        lo, hi = np.percentile(band, (2, 98))
        if hi - lo <= 0:
            scaled = np.clip(band, 0, 255)
        else:
            scaled = (band - lo) / (hi - lo) * 255.0
        img[:, :, i] = np.clip(scaled, 0, 255).astype(np.uint8)
    return img

def generate_png_preview(tif_path: str, out_png: str, max_size: int = 1024) -> str:
    """
    Generate a PNG preview for the GeoTIFF at `tif_path`.
    - out_png: full output path for PNG (will overwrite).
    - max_size: max width or height in pixels (keeps aspect).
    Returns out_png path.
    """
    if not os.path.exists(tif_path):
        raise FileNotFoundError(tif_path)

    with rasterio.open(tif_path) as src:
        # compute target size keeping aspect ratio
        h, w = src.height, src.width
        scale = min(1.0, max_size / max(h, w))
        out_h = max(1, int(h * scale))
        out_w = max(1, int(w * scale))

        img = _read_rgb_window(src, out_shape=(out_h, out_w))

    im = Image.fromarray(img)
    # optionally convert to RGB mode explicitly
    im = im.convert("RGB")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    im.save(out_png, format="PNG", optimize=True)
    return out_png

def generate_previews_for_storage(storage_dir: str, thumbs_dir: str = None, max_size: int = 1024) -> int:
    """
    Scan storage_dir for .tif files and produce PNG thumbnails under thumbs_dir.
    Returns number of previews generated.
    """
    if thumbs_dir is None:
        thumbs_dir = os.path.join(storage_dir, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)

    count = 0
    for fn in os.listdir(storage_dir):
        if not fn.lower().endswith((".tif", ".tiff")):
            continue
        key = os.path.splitext(fn)[0]
        tif_path = os.path.join(storage_dir, fn)
        out_png = os.path.join(thumbs_dir, f"{key}.png")
        try:
            generate_png_preview(tif_path, out_png, max_size=max_size)
            count += 1
        except Exception as e:
            # skip problematic files but print reason
            print(f"[raster_utils] Failed preview for {tif_path}: {e}")
            continue
    return count
