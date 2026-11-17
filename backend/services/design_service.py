from backend import db
from backend.models.design import DesignCategory, DesignTemplate

DEFAULT_CATEGORIES = [
    {
        "name": "Minimal & Professional",
        "slug": "minimal-professional",
        "description": "Clean lines, generous whitespace, razor-sharp typography, and distilled aesthetics for leaders and studios.",
        "display_order": 1,
    },
    {
        "name": "Apple-Inspired / Liquid Glass",
        "slug": "apple-inspired",
        "description": "Frosted glassmorphism, fluid micro-interactions, subtle blurs, and hyper-refined hardware-grade design.",
        "display_order": 2,
    },
    {
        "name": "Dark & Futuristic",
        "slug": "dark-futuristic",
        "description": "Deep obsidian backgrounds, glowing accents, cyber grids, and high-contrast developer & tech aesthetics.",
        "display_order": 3,
    },
    {
        "name": "Modern SaaS",
        "slug": "modern-saas",
        "description": "Conversion-focused landing pages, interactive product previews, social proof, and clean feature breakdowns.",
        "display_order": 4,
    },
    {
        "name": "Creative & Experimental",
        "slug": "creative-experimental",
        "description": "Bold editorial layouts, asymmetric grids, dynamic typography, and avant-garde visual storytelling.",
        "display_order": 5,
    },
    {
        "name": "Luxury & Premium",
        "slug": "luxury-premium",
        "description": "Muted gold, rich serif typography, generous margins, and opulent editorial pacing for elite brands.",
        "display_order": 6,
    },
    {
        "name": "E-commerce",
        "slug": "ecommerce",
        "description": "High-conversion product showcases, quick carts, visual galleries, and frictionless checkout flows.",
        "display_order": 7,
    },
    {
        "name": "Dashboard & Admin UI",
        "slug": "dashboard-admin",
        "description": "Data-dense metrics cards, interactive graphs, tabular analytics, dark/light modes, and command palettes.",
        "display_order": 8,
    },
    {
        "name": "Portfolio & Personal Branding",
        "slug": "portfolio-personal",
        "description": "Personalized digital resumes, project case studies, interactive terminal/code cards, and bio spotlights.",
        "display_order": 9,
    },
    {
        "name": "Corporate & Business",
        "slug": "corporate-business",
        "description": "Trustworthy enterprise design, leadership bios, case studies, compliance certifications, and contact channels.",
        "display_order": 10,
    },
]

DEFAULT_TEMPLATES = [
    {
        "design_id": "DSGN-MIN-01",
        "slug": "zenith-minimal",
        "name": "Zenith Minimalist Editorial",
        "category_slug": "minimal-professional",
        "description": "Monochrome architectural precision with generous negative space, bespoke type hierarchy, and whisper-quiet transitions.",
        "status": "Popular",
        "is_featured": True,
        "color_palette": [
            {"name": "Pure White", "hex": "#FFFFFF"},
            {"name": "Zinc Gray", "hex": "#F4F4F5"},
            {"name": "Graphite", "hex": "#71717A"},
            {"name": "Pitch Black", "hex": "#09090B"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Lora Italic",
            "style": "Modern Swiss Typography",
        },
        "features": [
            "Whisper-quiet scroll reveals",
            "Monochrome high-contrast typography",
            "Dynamic split-screen project showcases",
            "Accessibility AAA certified contrast",
        ],
        "pages_available": ["Home", "About Studio", "Case Studies", "Contact"],
    },
    {
        "design_id": "DSGN-APL-02",
        "slug": "aura-liquid-glass",
        "name": "Aura Liquid Glassmorphism",
        "category_slug": "apple-inspired",
        "description": "Multi-layer backdrop filters, translucent frosted glass cards, dynamic light reflections, and tactile iOS-style button feedback.",
        "status": "Trending",
        "is_featured": True,
        "color_palette": [
            {"name": "Cosmic Blue", "hex": "#2563EB"},
            {"name": "Glass White", "hex": "#FFFFFFB3"},
            {"name": "Ice Fog", "hex": "#F0F5FA"},
            {"name": "Deep Space", "hex": "#0F172A"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Plus Jakarta Sans",
            "accent": "SF Pro Display",
            "style": "Cupertino Fluid Elegance",
        },
        "features": [
            "Real-time backdrop-blur CSS glass cards",
            "Smooth rubber-band spring animations",
            "Ambient colored aura glow backdrops",
            "Dynamic light and dark sheen effects",
        ],
        "pages_available": ["Overview", "Hardware Specs", "Pricing Tier", "Interactive Demo"],
    },
    {
        "design_id": "DSGN-DRK-03",
        "slug": "cyber-obsidian-matrix",
        "name": "Cyber Obsidian Matrix",
        "category_slug": "dark-futuristic",
        "description": "Immersive deep-space dark mode with neon cyan highlights, animated grid canvas, developer-first code terminal badges, and radar telemetry.",
        "status": "Available",
        "is_featured": True,
        "color_palette": [
            {"name": "True Void", "hex": "#030712"},
            {"name": "Obsidian Surface", "hex": "#111827"},
            {"name": "Neon Cyan", "hex": "#06B6D4"},
            {"name": "Matrix Lime", "hex": "#10B981"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans Extrabold",
            "body": "JetBrains Mono / Inter",
            "accent": "Fira Code",
            "style": "Cyberpunk Engineering",
        },
        "features": [
            "Subtle matrix grid pattern overlay",
            "Glowing neon border gradient hover",
            "Live system status pulse indicator",
            "Integrated terminal syntax styling",
        ],
        "pages_available": ["Mission", "Telemetry", "Protocol Architecture", "API Specs"],
    },
    {
        "design_id": "DSGN-SAS-04",
        "slug": "saas-velocity",
        "name": "Velocity SaaS Engine",
        "category_slug": "modern-saas",
        "description": "High-velocity conversion machine with interactive live pricing calculator, customer logo cloud, tabbed feature previews, and sticky checkout CTA.",
        "status": "Popular",
        "is_featured": True,
        "color_palette": [
            {"name": "Electric Indigo", "hex": "#4F46E5"},
            {"name": "Violet Tint", "hex": "#EEF2FF"},
            {"name": "Slate Dark", "hex": "#1E293B"},
            {"name": "Emerald Accent", "hex": "#10B981"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Plus Jakarta Sans Semibold",
            "style": "Product-Led Growth",
        },
        "features": [
            "Interactive monthly/annual billing switch",
            "Bento-box feature grid layout",
            "Customer testimonial carousel slider",
            "One-click signup modal integration",
        ],
        "pages_available": ["Home", "Features", "Pricing", "Integrations", "Docs"],
    },
    {
        "design_id": "DSGN-EXP-05",
        "slug": "avant-garde-kinetic",
        "name": "Avant-Garde Kinetic Studio",
        "category_slug": "creative-experimental",
        "description": "Explorative art direction featuring oversized typographic collisions, horizontal marquee ribbons, non-standard grid systems, and magnetic cursor states.",
        "status": "Customizable",
        "is_featured": False,
        "color_palette": [
            {"name": "Acid Lime", "hex": "#CCFF00"},
            {"name": "Off-Black", "hex": "#121212"},
            {"name": "Raw Linen", "hex": "#F5F3EF"},
            {"name": "Signal Orange", "hex": "#FF4500"},
        ],
        "typography": {
            "heading": "Syne / Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Lora Italic",
            "style": "Brutalist Editorial",
        },
        "features": [
            "Infinite marquee typography ticker",
            "Asymmetric diagonal card alignments",
            "Magnetic interactive hover magnets",
            "Interactive audio toggle ready",
        ],
        "pages_available": ["Exhibition", "Manifesto", "Works Index", "Colophon"],
    },
    {
        "design_id": "DSGN-LUX-06",
        "slug": "olympia-haute-luxe",
        "name": "Olympia Haute Luxury",
        "category_slug": "luxury-premium",
        "description": "Bespoke high-fashion atmosphere engineered with warm champagne foils, classical serif typography, slow-motion scroll transitions, and regal symmetry.",
        "status": "Available",
        "is_featured": False,
        "color_palette": [
            {"name": "Champagne Gold", "hex": "#D4AF37"},
            {"name": "Warm Cream", "hex": "#FAF8F3"},
            {"name": "Tuscan Charcoal", "hex": "#1C1917"},
            {"name": "Soft Bronze", "hex": "#78716C"},
        ],
        "typography": {
            "heading": "Lora Serif",
            "body": "Plus Jakarta Sans Light",
            "accent": "Playfair Display",
            "style": "Royal European Editorial",
        },
        "features": [
            "Subtle gold-foil shimmer borders",
            "Generous editorial white margins",
            "Refined image zoom on mouse hover",
            "VIP concierge request form",
        ],
        "pages_available": ["Heritage", "Private Collection", "Bespoke Services", "Atelier"],
    },
    {
        "design_id": "DSGN-ECM-07",
        "slug": "nordic-craft-market",
        "name": "Nordic Craft E-Commerce",
        "category_slug": "ecommerce",
        "description": "Streamlined Scandinavian retail interface with quick slide-over bag preview, sticky product specifications, instant variant selectors, and trust badges.",
        "status": "Popular",
        "is_featured": False,
        "color_palette": [
            {"name": "Warm Sand", "hex": "#E7E5E4"},
            {"name": "Forest Sage", "hex": "#065F46"},
            {"name": "Muted Charcoal", "hex": "#292524"},
            {"name": "Alabaster", "hex": "#FAFAF9"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Lora",
            "style": "Clean Scandi Retail",
        },
        "features": [
            "Slide-over mini cart drawer",
            "Interactive product gallery thumbnails",
            "Color swatch variant switcher",
            "Accordion FAQ and shipping specs",
        ],
        "pages_available": ["Storefront", "Product Detail", "Collection Grid", "Cart & Checkout"],
    },
    {
        "design_id": "DSGN-DSH-08",
        "slug": "nexus-command-dashboard",
        "name": "Nexus Enterprise Command UI",
        "category_slug": "dashboard-admin",
        "description": "High-density operational dashboard featuring real-time KPI metrics, sparkline widgets, status tags, collapsible sub-nav, and full keyboard quick-actions.",
        "status": "Available",
        "is_featured": False,
        "color_palette": [
            {"name": "Royal Cobalt", "hex": "#1D4ED8"},
            {"name": "Emerald Success", "hex": "#059669"},
            {"name": "Crimson Alert", "hex": "#DC2626"},
            {"name": "Canvas Ice", "hex": "#F8FAFC"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "JetBrains Mono",
            "style": "Data-Dense Modern Admin",
        },
        "features": [
            "Interactive summary metric cards with sparklines",
            "Sortable, filterable responsive tables",
            "Status pill badges with pulse dots",
            "Collapsible icon sidebar with tooltips",
        ],
        "pages_available": ["Overview", "Transactions", "Customer CRM", "System Settings"],
    },
    {
        "design_id": "DSGN-PRF-09",
        "slug": "craftsman-dev-portfolio",
        "name": "Craftsman Dev Portfolio",
        "category_slug": "portfolio-personal",
        "description": "Bespoke digital persona showcase with interactive live project previews, skill radar, dynamic experience timeline, and fast coffee-chat CTA.",
        "status": "Popular",
        "is_featured": True,
        "color_palette": [
            {"name": "Dax Royal Blue", "hex": "#2563EB"},
            {"name": "Accent Amber", "hex": "#FBBF24"},
            {"name": "Coral Accent", "hex": "#FF5A65"},
            {"name": "Paper White", "hex": "#FFFFFF"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Lora",
            "style": "Personal Brand Signature",
        },
        "features": [
            "Filterable project portfolio cards",
            "Integrated resume download CTA",
            "Interactive experience milestones",
            "Direct calendar booking widget integration",
        ],
        "pages_available": ["Homepage", "Projects Archive", "About / Story", "Direct Contact"],
    },
    {
        "design_id": "DSGN-COR-10",
        "slug": "apex-corporate-consulting",
        "name": "Apex Enterprise Advisory",
        "category_slug": "corporate-business",
        "description": "Solid, institutional confidence featuring executive leadership matrices, global office maps, client case metrics, and structured inquiry workflows.",
        "status": "Available",
        "is_featured": False,
        "color_palette": [
            {"name": "Navy Authority", "hex": "#1E3A8A"},
            {"name": "Steel Blue", "hex": "#3B82F6"},
            {"name": "Platinum Gray", "hex": "#F1F5F9"},
            {"name": "Charcoal Ink", "hex": "#0F172A"},
        ],
        "typography": {
            "heading": "Plus Jakarta Sans",
            "body": "Inter",
            "accent": "Lora",
            "style": "Fortune 500 Enterprise",
        },
        "features": [
            "Institutional client logos carousel",
            "Case study metrics counter cards",
            "Multi-office global location tabs",
            "Compliance & security trust seal badges",
        ],
        "pages_available": ["Corporate Home", "Capabilities", "Leadership", "Global Offices"],
    },
]


def seed_default_designs():
    """Populate default design categories and templates if not already present."""
    # 1. Seed categories
    category_map = {}
    for cat_data in DEFAULT_CATEGORIES:
        cat = DesignCategory.query.filter_by(slug=cat_data["slug"]).first()
        if not cat:
            cat = DesignCategory(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                display_order=cat_data["display_order"],
                is_active=True,
            )
            db.session.add(cat)
            db.session.flush()
        category_map[cat.slug] = cat.id

    # 2. Seed templates
    for tpl_data in DEFAULT_TEMPLATES:
        cat_id = category_map.get(tpl_data["category_slug"])
        if not cat_id:
            continue

        tpl = DesignTemplate.query.filter_by(design_id=tpl_data["design_id"]).first()
        if not tpl:
            tpl = DesignTemplate(
                design_id=tpl_data["design_id"],
                slug=tpl_data["slug"],
                name=tpl_data["name"],
                category_id=cat_id,
                description=tpl_data["description"],
                status=tpl_data["status"],
                is_featured=tpl_data["is_featured"],
                is_published=True,
                color_palette=tpl_data["color_palette"],
                typography=tpl_data["typography"],
                features=tpl_data["features"],
                pages_available=tpl_data["pages_available"],
            )
            db.session.add(tpl)

    db.session.commit()
