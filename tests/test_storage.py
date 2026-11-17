import io
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from backend.services.image_generator import MockupGenerator
from backend.services.neon_storage import NeonStorageService
from backend.models.design import DesignTemplate, DesignCategory, DesignPreviewAsset
from backend import db


def test_mockup_generator_desktop():
    sample_data = {
        "name": "Test Modern Studio",
        "slug": "test-modern-studio",
        "category_slug": "modern-saas",
        "color_palette": [
            {"name": "Navy", "hex": "#0F172A"},
            {"name": "Blue", "hex": "#2563EB"},
            {"name": "Cyan", "hex": "#38BDF8"},
            {"name": "White", "hex": "#FFFFFF"},
        ],
        "features": ["High Conversion", "Fast Performance", "Accessible"],
    }
    img = MockupGenerator.generate_desktop_mockup(sample_data)
    assert img.size == (1600, 1000)
    assert img.mode == "RGB"


def test_mockup_generator_mobile():
    sample_data = {
        "name": "Test Mobile App",
        "slug": "test-mobile-app",
        "category_slug": "minimal-professional",
        "color_palette": [
            {"name": "Black", "hex": "#000000"},
            {"name": "Gray", "hex": "#333333"},
            {"name": "Accent", "hex": "#10B981"},
            {"name": "White", "hex": "#FFFFFF"},
        ],
        "features": ["Fluid Touch", "Offline First"],
    }
    img = MockupGenerator.generate_mobile_mockup(sample_data)
    assert img.size == (900, 1600)
    assert img.mode == "RGB"


def test_storage_validation_and_optimization():
    service = NeonStorageService()

    # Valid image
    img = Image.new("RGB", (400, 300), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_png = buf.getvalue()

    w, h, fmt = service.validate_image_bytes(raw_png, "test.png")
    assert w == 400
    assert h == 300
    assert fmt.upper() in ("PNG", "WEBP")

    # Optimization to WebP
    opt_bytes, opt_w, opt_h = service.optimize_image(raw_png, target_width=200)
    assert opt_w == 200
    assert opt_h == 150  # 400x300 scaled to 200 width preserves 4:3 ratio -> 150
    assert len(opt_bytes) > 0

    # Test invalid / corrupted content rejection
    with pytest.raises(ValueError, match="Invalid or corrupted"):
        service.validate_image_bytes(b"not-a-real-image-payload", "corrupt.jpg")

    # Test extension validation
    with pytest.raises(ValueError, match="Unsupported file extension"):
        service.validate_image_bytes(raw_png, "badfile.exe")


def test_storage_s3_mocked_operations():
    service = NeonStorageService()
    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_s3.head_object.return_value = {
        "ContentLength": 5432,
        "ContentType": "image/webp",
        "ETag": '"abcdef"',
    }
    mock_s3.generate_presigned_url.return_value = "https://mock.neon.storage/photos/test.webp?sig=123"

    with patch.object(service, "get_client", return_value=mock_s3):
        # Test upload_bytes
        img = Image.new("RGB", (100, 100), color=(50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        res = service.upload_bytes(buf.getvalue(), "ui-templates/test.webp", "image/webp")

        assert res["bucket_name"] == "photos"
        assert res["object_key"] == "ui-templates/test.webp"
        mock_s3.put_object.assert_called_once()

        # Test exists
        assert service.check_object_exists("ui-templates/test.webp") is True

        # Test metadata
        meta = service.get_object_metadata("ui-templates/test.webp")
        assert meta["content_length"] == 5432

        # Test presigned URL
        url = service.generate_presigned_url("ui-templates/test.webp", expires_in=1800)
        assert "https://mock.neon.storage" in url


def test_design_preview_asset_db_model(app):
    with app.app_context():
        # Setup category and template
        cat = DesignCategory(name="Test Category", slug="test-cat", display_order=99)
        db.session.add(cat)
        db.session.commit()

        tpl = DesignTemplate(
            design_id="DSGN-TST-99",
            slug="test-template-99",
            name="Test Template 99",
            category_id=cat.id,
            description="Test design description",
            color_palette=[{"name": "Blue", "hex": "#0000FF"}],
            typography={"heading": "Inter", "body": "Inter"},
            features=["Test Feature"],
            pages_available=["Home"],
        )
        db.session.add(tpl)
        db.session.commit()

        # Add DesignPreviewAsset
        asset_desk = DesignPreviewAsset(
            design_id=tpl.design_id,
            image_type="desktop",
            bucket_name="photos",
            object_key="ui-templates/test-cat/test-desk.webp",
            content_type="image/webp",
            file_size=45000,
            width=1600,
            height=1000,
        )
        asset_mob = DesignPreviewAsset(
            design_id=tpl.design_id,
            image_type="mobile",
            bucket_name="photos",
            object_key="ui-templates/test-cat/test-mob.webp",
            content_type="image/webp",
            file_size=25000,
            width=900,
            height=1600,
        )
        db.session.add_all([asset_desk, asset_mob])
        db.session.commit()

        # Test relationships and helper methods
        assert tpl.assets.count() == 2
        assert tpl.get_asset_url("desktop") == "/storage/preview/ui-templates/test-cat/test-desk.webp"
        assert tpl.get_asset_url("laptop") == "/storage/preview/ui-templates/test-cat/test-desk.webp"
        assert tpl.get_asset_url("mobile") == "/storage/preview/ui-templates/test-cat/test-mob.webp"

        data = tpl.to_dict()
        assert len(data["assets"]) == 2
        assert data["desktop_preview_url"] == "/storage/preview/ui-templates/test-cat/test-desk.webp"
        assert data["laptop_preview_url"] == "/storage/preview/ui-templates/test-cat/test-desk.webp"
        assert data["mobile_preview_url"] == "/storage/preview/ui-templates/test-cat/test-mob.webp"


def test_storage_preview_route_redirect(client):
    with patch("backend.services.neon_storage.storage_service.generate_presigned_url", return_value="https://neon-storage.test/photos/image.webp?sig=abc"):
        res = client.get("/storage/preview/ui-templates/minimal/desk.webp")
        assert res.status_code == 307
        assert res.headers["Location"] == "https://neon-storage.test/photos/image.webp?sig=abc"
        assert "Cache-Control" in res.headers


def test_manifest_json_indexing():
    import json
    from pathlib import Path
    manifest_file = Path("ui-template-previews-30-images/manifest.json")
    assert manifest_file.exists(), "manifest.json must exist"

    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_templates"] == 10
    assert data["total_images"] == 30
    for tpl in data["templates"]:
        assert "laptop" in tpl["references"]
        assert "tablet" in tpl["references"]
        assert "mobile" in tpl["references"]
        assert tpl["references"]["laptop"]["width"] == 1920
        assert tpl["references"]["tablet"]["width"] == 1600
        assert tpl["references"]["mobile"]["width"] == 1080


def test_all_10_interactive_frames_render(client, app):
    from backend.services.design_service import DEFAULT_TEMPLATES
    with app.app_context():
        for t_def in DEFAULT_TEMPLATES:
            slug = t_def["slug"]
            res = client.get(f"/design-showcase/frame/{slug}")
            assert res.status_code == 200, f"Frame for {slug} must return 200"
            html = res.data.decode("utf-8")
            assert len(html) > 500, f"Frame for {slug} should have rich content"


def test_design_details_page_renders_design_reference_only(client, app):
    """Verify that all details UI pages strictly render design reference artwork, not an interactive iframe."""
    from backend.services.design_service import DEFAULT_TEMPLATES
    with app.app_context():
        for t_def in DEFAULT_TEMPLATES:
            slug = t_def["slug"]
            res = client.get(f"/design-showcase/preview/{slug}")
            assert res.status_code == 200, f"Preview page for {slug} must return 200"
            html = res.data.decode("utf-8")
            # Must NOT contain an iframe
            assert "<iframe" not in html.lower(), f"Preview page for {slug} must not contain an interactive iframe"
            # Must contain the active design reference image and device switcher controls
            assert 'id="active-reference-img"' in html
            assert 'btn-view-laptop' in html
            assert 'btn-view-tablet' in html
            assert 'btn-view-mobile' in html
            assert 'Design Reference' in html


