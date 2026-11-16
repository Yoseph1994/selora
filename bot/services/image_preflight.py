import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def inspect_image_metadata(file_path: Path) -> Dict[str, Any]:
    """Inspect customer print artwork file for resolution, DPI, dimensions, and print quality rating."""
    try:
        from PIL import Image
        with Image.open(file_path) as im:
            width, height = im.size
            format_name = im.format or file_path.suffix.lstrip(".").upper()
            mode = im.mode
            dpi_info = im.info.get("dpi")
            dpi_val = int(dpi_info[0]) if dpi_info and isinstance(dpi_info, tuple) else None

            min_dim = min(width, height)
            file_size_kb = round(file_path.stat().st_size / 1024) if file_path.exists() else 0

            # Categorize print quality rating:
            # - sharp: min dimension >= 1000px (ideal for crisp 300+ DPI print)
            # - medium: min dimension >= 600px (standard quality for medium prints)
            # - low: min dimension < 600px (small photo or compressed thumbnail)
            if min_dim >= 1000:
                quality_rating = "sharp"
                quality_label = "High Resolution (300+ DPI)"
            elif min_dim >= 600:
                quality_rating = "medium"
                quality_label = "Standard Quality"
            else:
                quality_rating = "low"
                quality_label = "Low Resolution / Blurry"

            return {
                "width": width,
                "height": height,
                "megapixels": round((width * height) / 1_000_000, 1),
                "format": format_name,
                "mode": mode,
                "dpi": dpi_val,
                "size_kb": file_size_kb,
                "quality_rating": quality_rating,
                "quality_label": quality_label
            }
    except Exception as e:
        logger.warning(f"Image pre-flight inspector notice for {file_path}: {e}")
        return {
            "width": None,
            "height": None,
            "quality_rating": "unknown",
            "quality_label": "Document / Unchecked File"
        }
