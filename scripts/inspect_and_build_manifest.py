import os
import json
import hashlib
from pathlib import Path
from PIL import Image

BASE_DIR = Path("ui-template-previews-30-images")

CATEGORY_MAPPING = {
    "01-minimal-professional": {
        "design_id": "DSGN-MIN-01",
        "name": "Alder Advisory",
        "category_slug": "minimal-professional",
        "category_name": "Minimal & Professional",
        "brand": "Alder Advisory",
        "purpose": "Professional strategy and operations consultancy",
        "palette": [
            {"name": "Warm Ivory", "hex": "#F5F3ED"},
            {"name": "Forest Green", "hex": "#233E33"},
            {"name": "Charcoal", "hex": "#202722"},
            {"name": "Muted Sage", "hex": "#7E8F84"}
        ],
        "typography": {
            "heading": "Newsreader / Editorial Serif",
            "body": "Inter",
            "accent": "Newsreader Italic",
            "style": "Refined Editorial Typography"
        },
        "description": "Clean architectural strategy consultancy with quiet grid pacing, generous ivory whitespace, and refined editorial typography.",
        "features": [
            "Quiet architectural grid layout",
            "Oversized serif editorial headline",
            "Spacious multi-column service breakdown",
            "Curated proof metrics (120+ projects, 18 industries, 12 years)"
        ]
    },
    "02-liquid-glass": {
        "design_id": "DSGN-APL-02",
        "name": "Auralis One",
        "category_slug": "apple-inspired",
        "category_name": "Apple-Inspired / Liquid Glass",
        "brand": "Auralis",
        "purpose": "Premium wireless headphone product landing page",
        "palette": [
            {"name": "Pearl White", "hex": "#FFFFFF"},
            {"name": "Translucent Silver", "hex": "#E2E8F0"},
            {"name": "Pale Ice Blue", "hex": "#E0F2FE"},
            {"name": "Graphite", "hex": "#1E293B"},
            {"name": "Cyan Accent", "hex": "#38BDF8"}
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "SF Pro Display style",
            "style": "Elegant Modern Sans-Serif"
        },
        "description": "Hardware-grade product landing page with translucent glassmorphic panels, floating frosted navigation, and airy white space.",
        "features": [
            "Sculptural hero product showcase",
            "Frosted glass floating navigation",
            "Technical specification cards (40-hr battery, adaptive silence, spatial audio)",
            "Direct e-commerce pricing and shopping action"
        ]
    },
    "03-dark-futuristic": {
        "design_id": "DSGN-DRK-03",
        "name": "Vector Forge",
        "category_slug": "dark-futuristic",
        "category_name": "Dark & Futuristic",
        "brand": "Vector Forge",
        "purpose": "AI inference and model deployment platform",
        "palette": [
            {"name": "Near-Black", "hex": "#111511"},
            {"name": "Warm Bone", "hex": "#E9E8DD"},
            {"name": "Acid Chartreuse", "hex": "#C8E65A"},
            {"name": "Steel Gray", "hex": "#4B5563"}
        ],
        "typography": {
            "heading": "Plus Jakarta Sans Neo-Grotesk",
            "body": "Inter",
            "accent": "JetBrains Mono",
            "style": "Technical Neo-Grotesk & Monospace"
        },
        "description": "High-performance AI inference infrastructure landing page with architectural terminal layout and acid chartreuse accents.",
        "features": [
            "Topology-inspired abstract interactive visualization",
            "Live deployment telemetry card with latency stats (42ms, 99.99%)",
            "Terminal-style code and model deployment controls",
            "Monospace technical status labels"
        ]
    },
    "04-modern-saas": {
        "design_id": "DSGN-SAS-04",
        "name": "Relay Workflow",
        "category_slug": "modern-saas",
        "category_name": "Modern SaaS",
        "brand": "Relay",
        "purpose": "Team project planning and workflow SaaS",
        "palette": [
            {"name": "Pure White", "hex": "#FFFFFF"},
            {"name": "Soft Sky Blue", "hex": "#EAF2FB"},
            {"name": "Ink Navy", "hex": "#1C2D46"},
            {"name": "Cobalt Blue", "hex": "#315FD6"},
            {"name": "Pale Coral", "hex": "#F87171"}
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Inter Medium",
            "style": "Crisp Humanist Sans-Serif"
        },
        "description": "Conversion-focused team collaboration SaaS landing page with interactive kanban preview board and integrations showcase.",
        "features": [
            "Interactive Kanban board (To Do, In Progress, Done)",
            "Team avatar assignments and tag pills",
            "Integration ecosystem teaser and seat pricing tiers ($12/seat)",
            "Customer trust quotes and workflow metrics"
        ]
    },
    "05-creative-experimental": {
        "design_id": "DSGN-EXP-05",
        "name": "Oddline Studio",
        "category_slug": "creative-experimental",
        "category_name": "Creative & Experimental",
        "brand": "Oddline Studio",
        "purpose": "Independent branding and digital design studio",
        "palette": [
            {"name": "Punchy Vermilion", "hex": "#F1462D"},
            {"name": "Pale Butter", "hex": "#F4EFAC"},
            {"name": "Black Ink", "hex": "#09090B"}
        ],
        "typography": {
            "heading": "Syne / Condensed Editorial",
            "body": "Inter",
            "accent": "Newsreader Italic",
            "style": "Asymmetric Condensed Sans & Expressive Italic"
        },
        "description": "Avant-garde editorial studio experience featuring punchy vermilion art panels, butter yellow background, and asymmetric project showcases.",
        "features": [
            "Asymmetric editorial composition with bold typography",
            "Sculptural art panel and tactile creative work tiles",
            "Interactive project case showcases (Forma, Paloma)",
            "Expressive kinetic typography rhythm"
        ]
    },
    "06-luxury-premium": {
        "design_id": "DSGN-LUX-06",
        "name": "Maison Solenne",
        "category_slug": "luxury-premium",
        "category_name": "Luxury & Premium",
        "brand": "Maison Solenne",
        "purpose": "Luxury leather goods and considered accessories storefront",
        "palette": [
            {"name": "Parchment", "hex": "#F5F0E7"},
            {"name": "Espresso", "hex": "#302821"},
            {"name": "Burgundy", "hex": "#562E32"},
            {"name": "Warm Cognac", "hex": "#C27847"}
        ],
        "typography": {
            "heading": "Cormorant Garamond / Editorial Serif",
            "body": "Inter",
            "accent": "Inter Uppercase Monospace",
            "style": "High-Contrast Luxury Serif"
        },
        "description": "Haute editorial accessories storefront featuring travertine and warm cognac aesthetics, fine rules, and deliberate magazine pacing.",
        "features": [
            "Cinematic atelier hero with architectural sunlight",
            "Sculptural product storytelling (The Arc Bag $680, The Fold Wallet $190)",
            "Minimalist luxury navigation and subtle collection links",
            "Artisanal heritage storytelling and materials breakdown"
        ]
    },
    "07-ecommerce-storefront": {
        "design_id": "DSGN-ECM-07",
        "name": "Hearth & Habit",
        "category_slug": "ecommerce",
        "category_name": "E-commerce Storefront",
        "brand": "Hearth & Habit",
        "purpose": "Contemporary homeware online store",
        "palette": [
            {"name": "Warm White", "hex": "#FAF8F5"},
            {"name": "Terracotta", "hex": "#BC6447"},
            {"name": "Olive Green", "hex": "#6E7357"},
            {"name": "Warm Sand", "hex": "#E4D8C7"}
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Inter Rounded",
            "style": "Approachable Rounded Sans-Serif"
        },
        "description": "Scandinavian-inspired homeware e-commerce storefront with integrated search, category chips, and interactive product card grids.",
        "features": [
            "Prominent live search and shopping announcement banner",
            "Horizontal category filter chips (Tableware, Lighting, Textiles, Objects)",
            "Four curated lifestyle product cards with real star ratings & pricing",
            "Quick add-to-cart interaction and cart badge counter"
        ]
    },
    "08-dashboard-admin": {
        "design_id": "DSGN-DSH-08",
        "name": "Northstar Analytics",
        "category_slug": "dashboard-admin",
        "category_name": "Dashboard & Admin UI",
        "brand": "Northstar Analytics",
        "purpose": "Subscription business analytics dashboard",
        "palette": [
            {"name": "Cool White", "hex": "#F7F9FC"},
            {"name": "Deep Navy", "hex": "#203047"},
            {"name": "Teal Accent", "hex": "#147F78"},
            {"name": "Slate Gray", "hex": "#64748B"},
            {"name": "Success Emerald", "hex": "#10B981"}
        ],
        "typography": {
            "heading": "Inter",
            "body": "Inter",
            "accent": "JetBrains Mono",
            "style": "Clean Data UI with Tabular Numerals"
        },
        "description": "Dense, professional SaaS analytics dashboard featuring revenue trend charts, customer cohort tables, and telemetry feeds.",
        "features": [
            "Collapsible navy app sidebar navigation",
            "4 key KPI metric cards ($84,320 Revenue, 2,418 Customers, 4.8% Conv, 1.9% Churn)",
            "Daily revenue trend chart with interactive tooltips",
            "Live customer subscription data table and real-time activity stream"
        ]
    },
    "09-portfolio-personal-branding": {
        "design_id": "DSGN-PRF-09",
        "name": "Maya Ellis Studio",
        "category_slug": "portfolio-personal",
        "category_name": "Portfolio & Personal Branding",
        "brand": "Maya Ellis",
        "purpose": "Creative developer portfolio",
        "palette": [
            {"name": "Warm Off-White", "hex": "#FDFBF7"},
            {"name": "Ink Black", "hex": "#111111"},
            {"name": "Cobalt Blue", "hex": "#294ED7"},
            {"name": "Pale Mint", "hex": "#E0F2E9"}
        ],
        "typography": {
            "heading": "Newsreader / Editorial Serif",
            "body": "Inter",
            "accent": "JetBrains Mono",
            "style": "Generous Serif & Utilitarian Code Metadata"
        },
        "description": "Creative developer portfolio featuring memorable typographic hero, kinetic orbital loop, and rich interactive project showcases.",
        "features": [
            "Memorable typographic hero with cobalt geometric orbital loop",
            "Live availability indicator pill ('Available for select projects')",
            "Editorial case study previews (Fieldnote, Kinfolk Studio)",
            "Capabilities taxonomy & experience timeline"
        ]
    },
    "10-corporate-business": {
        "design_id": "DSGN-COR-10",
        "name": "Meridian Works",
        "category_slug": "corporate-business",
        "category_name": "Corporate & Business",
        "brand": "Meridian Works",
        "purpose": "Industrial engineering and advanced manufacturing company",
        "palette": [
            {"name": "Deep Industrial Navy", "hex": "#152E43"},
            {"name": "Safety Orange", "hex": "#E47539"},
            {"name": "Pure White", "hex": "#FFFFFF"},
            {"name": "Cool Steel Gray", "hex": "#94A3B8"}
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Plus Jakarta Sans Bold",
            "style": "Robust Industrial Sans-Serif"
        },
        "description": "High-trust precision engineering enterprise portal with split industrial hero, proof statistics bar, and sector capability matrix.",
        "features": [
            "High-contrast navy and safety orange technical branding",
            "Proof metrics bar (35 years expertise, 240 specialists, 14 countries)",
            "Core capability columns (Precision Machining, Systems Integration, Quality Assurance)",
            "Industry focus selector (Energy, Mobility, Industrial Systems)"
        ]
    }
}


def main():
    subdirs = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()])
    print(f"Scanning {len(subdirs)} subdirectories in {BASE_DIR}...")

    manifest = {
        "source": "ui-template-previews-30-images",
        "total_templates": len(subdirs),
        "total_images": 0,
        "templates": []
    }

    for d in subdirs:
        folder_name = d.name
        meta = CATEGORY_MAPPING.get(folder_name, {})
        
        images = list(d.glob("*.png"))
        laptop_img = next((img for img in images if "laptop" in img.name.lower()), None)
        tablet_img = next((img for img in images if "tablet" in img.name.lower()), None)
        mobile_img = next((img for img in images if "mobile" in img.name.lower()), None)

        tpl_entry = {
            "folder": folder_name,
            "design_id": meta.get("design_id", "DSGN-00"),
            "slug": meta.get("category_slug", folder_name),
            "name": meta.get("name", folder_name),
            "category": meta.get("category_name", "General"),
            "brand": meta.get("brand", ""),
            "purpose": meta.get("purpose", ""),
            "description": meta.get("description", ""),
            "color_palette": meta.get("palette", []),
            "typography": meta.get("typography", {}),
            "features": meta.get("features", []),
            "references": {}
        }

        for dev_type, img_file in [("laptop", laptop_img), ("tablet", tablet_img), ("mobile", mobile_img)]:
            if img_file:
                with Image.open(img_file) as im:
                    w, h = im.size
                    fmt = im.format
                hasher = hashlib.sha256()
                with open(img_file, "rb") as f:
                    hasher.update(f.read())
                
                rel_path = str(img_file.relative_to(BASE_DIR)).replace("\\", "/")
                tpl_entry["references"][dev_type] = {
                    "filename": img_file.name,
                    "relative_path": rel_path,
                    "width": w,
                    "height": h,
                    "format": fmt,
                    "size_bytes": img_file.stat().st_size,
                    "sha256": hasher.hexdigest()
                }
                manifest["total_images"] += 1

        manifest["templates"].append(tpl_entry)

    out_file = BASE_DIR / "manifest.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully generated {out_file} with {manifest['total_images']} verified image references across {manifest['total_templates']} templates.")


if __name__ == "__main__":
    main()
