"""
Uploads the 30 ChatGPT UI design reference images to Neon Object Storage ('photos' bucket)
and registers the metadata and checksums in Neon Serverless PostgreSQL.
"""

import io
import json
import hashlib
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

from PIL import Image
from sqlalchemy import text
from app import create_app
from backend import db
from backend.models.design import DesignTemplate, DesignCategory, DesignPreviewAsset
from backend.services.neon_storage import storage_service

MANIFEST_PATH = BASE_DIR / "ui-template-previews-30-images" / "manifest.json"


def ensure_db_columns():
    """Ensure checksum column exists on design_preview_assets."""
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE design_preview_assets ADD COLUMN IF NOT EXISTS checksum VARCHAR(64);"))
            conn.commit()
            print("Verified 'checksum' column exists on design_preview_assets.")
        except Exception as e:
            print(f"Column check note: {e}")


def run():
    print("Loading manifest...")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    app = create_app()
    with app.app_context():
        ensure_db_columns()

        total_uploaded = 0
        total_records = 0

        for t_meta in manifest["templates"]:
            folder = t_meta["folder"]
            design_id = t_meta["design_id"]
            cat_slug = t_meta["slug"]

            template = DesignTemplate.query.filter_by(design_id=design_id).first()
            if not template:
                print(f"Warning: Template {design_id} not found in DB! Skipping.")
                continue

            print(f"\n=======================================================")
            print(f"Processing {design_id}: {t_meta['name']} (Category: {cat_slug})")
            print(f"=======================================================")

            # Update template rich metadata to match the reference images
            template.name = t_meta["name"]
            template.description = t_meta["description"]
            template.color_palette = t_meta["color_palette"]
            template.typography = t_meta["typography"]
            template.features = t_meta["features"]

            # Remove prior assets for this template to avoid duplicates
            DesignPreviewAsset.query.filter_by(design_id=design_id).delete()

            for dev_type in ["laptop", "tablet", "mobile"]:
                ref = t_meta["references"].get(dev_type)
                if not ref:
                    continue

                img_path = BASE_DIR / "ui-template-previews-30-images" / ref["relative_path"]
                if not img_path.exists():
                    print(f"Error: Image {img_path} does not exist!")
                    continue

                # Read raw PNG and calculate SHA-256 checksum
                with open(img_path, "rb") as f:
                    raw_bytes = f.read()
                file_checksum = hashlib.sha256(raw_bytes).hexdigest()

                # Open with PIL
                with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                    w, h = pil_img.size
                    # Convert to RGB WebP with quality 90 preserving high fidelity
                    webp_buf = io.BytesIO()
                    rgb_img = pil_img.convert("RGB")
                    rgb_img.save(webp_buf, format="WEBP", quality=90, method=6)
                    webp_bytes = webp_buf.getvalue()

                # Deterministic object key in Neon storage
                object_key = f"ui-templates/{cat_slug}/{dev_type}.webp"
                print(f"Uploading {dev_type} image -> {object_key} ({len(webp_bytes)} bytes, {w}x{h})...")

                storage_service.upload_bytes(webp_bytes, object_key, content_type="image/webp")
                total_uploaded += 1

                # Record in Neon PostgreSQL
                asset = DesignPreviewAsset(
                    design_id=design_id,
                    image_type=dev_type,
                    bucket_name="photos",
                    object_key=object_key,
                    content_type="image/webp",
                    file_size=len(webp_bytes),
                    width=w,
                    height=h,
                    checksum=file_checksum,
                )
                db.session.add(asset)
                total_records += 1

                # If laptop, also create 'desktop' image_type for backwards compatibility
                if dev_type == "laptop":
                    desktop_asset = DesignPreviewAsset(
                        design_id=design_id,
                        image_type="desktop",
                        bucket_name="photos",
                        object_key=object_key,
                        content_type="image/webp",
                        file_size=len(webp_bytes),
                        width=w,
                        height=h,
                        checksum=file_checksum,
                    )
                    db.session.add(desktop_asset)
                    template.desktop_preview_url = f"/storage/preview/{object_key}"
                    template.thumbnail_url = f"/storage/preview/{object_key}"

                elif dev_type == "mobile":
                    template.mobile_preview_url = f"/storage/preview/{object_key}"

            template.is_published = True
            db.session.commit()
            print(f"✓ Saved 3 assets for {design_id} in Neon PostgreSQL.")

        print(f"\nCompleted! Total images uploaded: {total_uploaded}. Total asset records created: {total_records}.")


if __name__ == "__main__":
    run()
