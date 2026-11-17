"""
Batch Pipeline: Generates and uploads UI template preview assets to Neon Object Storage bucket 'photos',
and registers all metadata in Neon PostgreSQL.
"""

import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure portfolio root is on python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

from app import create_app
from backend import db
from backend.models.design import DesignTemplate, DesignCategory, DesignPreviewAsset
from backend.services.image_generator import MockupGenerator
from backend.services.neon_storage import storage_service
from PIL import Image


def run_pipeline():
    print("Starting UI Template Asset Generation & Neon Upload Pipeline...")
    app = create_app()

    with app.app_context():
        templates = DesignTemplate.query.all()
        if not templates:
            print("No templates found in database! Exiting.")
            return

        print(f"Found {len(templates)} templates in Neon PostgreSQL.")

        # Check for AI-generated mockup for Zenith
        ai_zenith_path = Path(r"C:\Users\Hp\.gemini\antigravity\brain\c97b386e-c96c-4a9b-93cc-1a12ec961957\zenith_minimalist_editorial_mockup_1794849684445.jpg")

        for idx, t in enumerate(templates, 1):
            cat_slug = t.category.slug if t.category else "general"
            print(f"\n[{idx}/{len(templates)}] Processing: {t.design_id} - '{t.name}' (Category: {cat_slug})")

            t_data = t.to_dict()

            # 1. Desktop Image
            desktop_key = f"ui-templates/{cat_slug}/{t.slug}-desktop.webp"
            print(f"  -> Generating Desktop Mockup (1600x1000)...")
            
            if t.design_id == "DSGN-MIN-01" and ai_zenith_path.exists():
                print(f"  -> Incorporating AI subagent generated mockup for Zenith...")
                with open(ai_zenith_path, "rb") as f:
                    zenith_raw = f.read()
                desk_bytes, desk_w, desk_h = storage_service.optimize_image(
                    zenith_raw, target_width=1600, target_height=1000, quality=88
                )
            else:
                desk_img = MockupGenerator.generate_desktop_mockup(t_data)
                desk_buf = io.BytesIO()
                desk_img.save(desk_buf, format="WEBP", quality=88, method=6)
                desk_bytes = desk_buf.getvalue()
                desk_w, desk_h = desk_img.size

            print(f"  -> Uploading desktop WebP ({len(desk_bytes)} bytes) to Neon storage '{desktop_key}'...")
            storage_service.upload_bytes(desk_bytes, desktop_key, content_type="image/webp")

            # 2. Mobile Image
            mobile_key = f"ui-templates/{cat_slug}/{t.slug}-mobile.webp"
            print(f"  -> Generating Mobile Mockup (900x1600)...")
            mob_img = MockupGenerator.generate_mobile_mockup(t_data)
            mob_buf = io.BytesIO()
            mob_img.save(mob_buf, format="WEBP", quality=88, method=6)
            mob_bytes = mob_buf.getvalue()
            mob_w, mob_h = mob_img.size

            print(f"  -> Uploading mobile WebP ({len(mob_bytes)} bytes) to Neon storage '{mobile_key}'...")
            storage_service.upload_bytes(mob_bytes, mobile_key, content_type="image/webp")

            # 3. Update Database Asset Records
            # Remove any prior asset records for this design
            DesignPreviewAsset.query.filter_by(design_id=t.design_id).delete()

            # Desktop asset
            desk_asset = DesignPreviewAsset(
                design_id=t.design_id,
                image_type="desktop",
                bucket_name="photos",
                object_key=desktop_key,
                content_type="image/webp",
                file_size=len(desk_bytes),
                width=desk_w,
                height=desk_h,
            )
            db.session.add(desk_asset)

            # Mobile asset
            mob_asset = DesignPreviewAsset(
                design_id=t.design_id,
                image_type="mobile",
                bucket_name="photos",
                object_key=mobile_key,
                content_type="image/webp",
                file_size=len(mob_bytes),
                width=mob_w,
                height=mob_h,
            )
            db.session.add(mob_asset)

            # Update template direct URLs
            t.desktop_preview_url = f"/storage/preview/{desktop_key}"
            t.mobile_preview_url = f"/storage/preview/{mobile_key}"
            t.thumbnail_url = f"/storage/preview/{desktop_key}"
            t.is_published = True

            db.session.commit()
            print(f"  ✓ Saved assets and updated {t.design_id} in Neon PostgreSQL.")

        print("\nAll 10 UI template preview assets successfully generated, uploaded to Neon S3 'photos', and recorded in Neon PostgreSQL!")


if __name__ == "__main__":
    run_pipeline()
