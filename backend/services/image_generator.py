"""
UI Template Preview Image Generation Pipeline.
Generates realistic, high-fidelity website interface mockups (Desktop 1600x1000 and Mobile 900x1600)
tailored to each design template's category, color palette, typography and layout.
"""

import io
import math
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def get_default_font(size: int = 16) -> ImageFont.ImageFont:
    """Safely returns a TrueType font or fallback."""
    font_names = [
        "arial.ttf", "segoeui.ttf", "calibri.ttf", "tahoma.ttf", "DejaVuSans.ttf"
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts hex color string to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    try:
        return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (30, 41, 59)


def blend(c1: Tuple[int, int, int], c2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Linearly blends two RGB colors."""
    factor = max(0.0, min(1.0, factor))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * factor) for i in range(3))


class MockupGenerator:
    """Generates bespoke, production-grade UI preview images."""

    @staticmethod
    def generate_desktop_mockup(template_data: Dict[str, Any]) -> Image.Image:
        """
        Generates a 1600x1000 desktop browser mockup reflecting the template's
        theme, colors, typography and layout.
        """
        W, H = 1600, 1000
        palette = template_data.get("color_palette", [])
        colors = [hex_to_rgb(c.get("hex", "#3B82F6")) for c in palette] if palette else [
            (15, 23, 42), (30, 41, 59), (59, 130, 246), (248, 250, 252)
        ]
        
        bg_color = colors[0] if len(colors) > 0 else (15, 23, 42)
        card_bg = colors[1] if len(colors) > 1 else (30, 41, 59)
        accent_color = colors[2] if len(colors) > 2 else (59, 130, 246)
        text_color = colors[3] if len(colors) > 3 else (255, 255, 255)
        
        # Determine if dark or light theme
        brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
        is_dark = brightness < 128
        
        # Create canvas with subtle gradient backdrop
        img = Image.new("RGBA", (W, H), (*bg_color, 255))
        draw = ImageDraw.Draw(img)
        
        # Add ambient glow in background
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse([W - 500, -100, W + 300, 700], fill=(*accent_color, 45 if is_dark else 30))
        glow_draw.ellipse([-200, H - 500, 500, H + 200], fill=(*blend(accent_color, card_bg, 0.5), 35 if is_dark else 20))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        img = Image.alpha_composite(img, glow)
        draw = ImageDraw.Draw(img)

        # Outer browser window frame
        pad_x, pad_y = 60, 50
        browser_w, browser_h = W - (pad_x * 2), H - (pad_y * 2)
        browser_box = [pad_x, pad_y, pad_x + browser_w, pad_y + browser_h]
        
        # Window shadow
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle([pad_x + 5, pad_y + 12, pad_x + browser_w - 5, pad_y + browser_h + 16], radius=16, fill=(0, 0, 0, 110))
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        img = Image.alpha_composite(img, shadow)
        draw = ImageDraw.Draw(img)

        # Window body
        body_bg = (18, 22, 32) if is_dark else (255, 255, 255)
        window_border = (50, 60, 80) if is_dark else (220, 225, 235)
        draw.rounded_rectangle(browser_box, radius=14, fill=body_bg, outline=window_border, width=1)

        # Browser header bar
        header_h = 48
        draw.rounded_rectangle([pad_x, pad_y, pad_x + browser_w, pad_y + header_h], radius=14, fill=(28, 33, 46) if is_dark else (241, 245, 249))
        draw.rectangle([pad_x, pad_y + header_h - 10, pad_x + browser_w, pad_y + header_h], fill=(28, 33, 46) if is_dark else (241, 245, 249))
        draw.line([pad_x, pad_y + header_h, pad_x + browser_w, pad_y + header_h], fill=window_border, width=1)

        # Traffic light window buttons
        draw.ellipse([pad_x + 20, pad_y + 17, pad_x + 32, pad_y + 29], fill=(239, 68, 68))    # Close
        draw.ellipse([pad_x + 40, pad_y + 17, pad_x + 52, pad_y + 29], fill=(245, 158, 11))   # Minimize
        draw.ellipse([pad_x + 60, pad_y + 17, pad_x + 72, pad_y + 29], fill=(16, 185, 129))   # Maximize

        # URL address pill
        url_box = [pad_x + 100, pad_y + 10, pad_x + browser_w - 100, pad_y + 38]
        draw.rounded_rectangle(url_box, radius=8, fill=(15, 18, 26) if is_dark else (255, 255, 255), outline=window_border, width=1)
        font_sm = get_default_font(13)
        slug = template_data.get("slug", "template")
        draw.text((pad_x + 120, pad_y + 16), f"🔒 https://prajapatidax.co.in/designs/{slug}", fill=(148, 163, 184), font=font_sm)

        # Navbar inside page
        nav_y = pad_y + header_h + 1
        nav_h = 70
        draw.rectangle([pad_x, nav_y, pad_x + browser_w, nav_y + nav_h], fill=body_bg)
        draw.line([pad_x, nav_y + nav_h, pad_x + browser_w, nav_y + nav_h], fill=blend(body_bg, window_border, 0.4), width=1)

        # Brand / Logo
        font_bold_lg = get_default_font(20)
        draw.rounded_rectangle([pad_x + 40, nav_y + 18, pad_x + 76, nav_y + 54], radius=8, fill=accent_color)
        draw.text((pad_x + 52, nav_y + 22), "✦", fill=(255, 255, 255), font=font_bold_lg)
        
        name = template_data.get("name", "Modern Studio UI")
        draw.text((pad_x + 90, nav_y + 24), name[:22], fill=text_color if is_dark else (15, 23, 42), font=font_bold_lg)

        # Nav links
        nav_items = ["Overview", "Features", "Case Studies", "Pricing", "Documentation"]
        font_nav = get_default_font(14)
        nx = pad_x + 420
        for item in nav_items:
            draw.text((nx, nav_y + 26), item, fill=(148, 163, 184), font=font_nav)
            nx += 120

        # Nav CTA button
        cta_box = [pad_x + browser_w - 170, nav_y + 16, pad_x + browser_w - 40, nav_y + 54]
        draw.rounded_rectangle(cta_box, radius=8, fill=accent_color)
        draw.text((pad_x + browser_w - 146, nav_y + 24), "Get Started", fill=(255, 255, 255), font=get_default_font(13))

        # Hero Section
        content_y = nav_y + nav_h + 40
        cat_name = template_data.get("category_slug", "Minimal & Professional").replace("-", " ").title()
        
        # Category Badge
        badge_box = [pad_x + 60, content_y, pad_x + 280, content_y + 32]
        draw.rounded_rectangle(badge_box, radius=16, fill=(*accent_color, 35) if is_dark else (*accent_color, 25), outline=accent_color, width=1)
        draw.text((pad_x + 80, content_y + 7), f"✦  {cat_name}", fill=accent_color, font=get_default_font(13))

        # Hero Heading
        font_hero = get_default_font(38)
        draw.text((pad_x + 60, content_y + 50), name, fill=text_color if is_dark else (15, 23, 42), font=font_hero)

        # Hero Subtitle / Description
        desc = template_data.get("description", "Engineered for high conversion and modern aesthetics.")
        font_desc = get_default_font(16)
        draw.text((pad_x + 60, content_y + 110), desc[:95], fill=(148, 163, 184), font=font_desc)

        # Action Buttons
        btn1_box = [pad_x + 60, content_y + 160, pad_x + 220, content_y + 210]
        draw.rounded_rectangle(btn1_box, radius=10, fill=accent_color)
        draw.text((pad_x + 95, content_y + 175), "Explore Demo", fill=(255, 255, 255), font=get_default_font(15))

        btn2_box = [pad_x + 240, content_y + 160, pad_x + 400, content_y + 210]
        draw.rounded_rectangle(btn2_box, radius=10, fill=blend(body_bg, window_border, 0.4), outline=window_border, width=1)
        draw.text((pad_x + 275, content_y + 175), "Documentation", fill=text_color if is_dark else (15, 23, 42), font=get_default_font(15))

        # Interactive Feature Grid / Cards (3 cards below hero)
        cards_y = content_y + 245
        card_w = (browser_w - 180) // 3
        card_h = 240
        features = template_data.get("features", ["Clean typography", "Responsive grid", "Fast performance"])

        for i in range(3):
            cx = pad_x + 60 + i * (card_w + 30)
            cbox = [cx, cards_y, cx + card_w, cards_y + card_h]
            card_fill = card_bg if is_dark else (248, 250, 252)
            draw.rounded_rectangle(cbox, radius=12, fill=card_fill, outline=window_border, width=1)

            # Card accent top line
            draw.line([cx + 20, cards_y + 1, cx + 80, cards_y + 1], fill=accent_color, width=3)

            # Icon circle
            draw.ellipse([cx + 24, cards_y + 24, cx + 64, cards_y + 64], fill=(*accent_color, 40) if is_dark else (*accent_color, 30))
            draw.text((cx + 38, cards_y + 32), ["⚡", "🛡️", "🚀"][i], font=get_default_font(18))

            # Card title
            feat_title = features[i] if i < len(features) else f"Feature {i + 1}"
            draw.text((cx + 24, cards_y + 80), feat_title[:24], fill=text_color if is_dark else (15, 23, 42), font=get_default_font(17))

            # Card text dummy lines
            for line_idx in range(3):
                ly = cards_y + 120 + line_idx * 18
                lw = card_w - 50 if line_idx < 2 else card_w - 110
                draw.rounded_rectangle([cx + 24, ly, cx + 24 + lw, ly + 8], radius=4, fill=blend(card_fill, (148, 163, 184), 0.25))

            # Micro Metric Pill
            metric_val = ["+99.8% Uptime", "AAA Contrast", "< 300ms LCP"][i]
            draw.rounded_rectangle([cx + 24, cards_y + card_h - 44, cx + 160, cards_y + card_h - 18], radius=6, fill=(*accent_color, 25), outline=accent_color, width=1)
            draw.text((cx + 34, cards_y + card_h - 38), metric_val, fill=accent_color, font=get_default_font(12))

        # Color palette swatches in bottom right
        swatch_x = pad_x + browser_w - 240
        swatch_y = content_y + 60
        draw.text((swatch_x, swatch_y - 22), "COLOR PALETTE", fill=(148, 163, 184), font=get_default_font(11))
        for idx, col in enumerate(colors[:4]):
            bx = swatch_x + idx * 45
            draw.rounded_rectangle([bx, swatch_y, bx + 36, swatch_y + 36], radius=8, fill=col, outline=window_border, width=1)

        # Convert back to RGB for crisp WebP export
        final_img = Image.new("RGB", (W, H), bg_color)
        final_img.paste(img, (0, 0), img)
        return final_img

    @staticmethod
    def generate_mobile_mockup(template_data: Dict[str, Any]) -> Image.Image:
        """
        Generates a 900x1600 mobile phone interface mockup reflecting the template's
        theme, colors, typography and mobile-first layout.
        """
        W, H = 900, 1600
        palette = template_data.get("color_palette", [])
        colors = [hex_to_rgb(c.get("hex", "#3B82F6")) for c in palette] if palette else [
            (15, 23, 42), (30, 41, 59), (59, 130, 246), (248, 250, 252)
        ]
        
        bg_color = colors[0] if len(colors) > 0 else (15, 23, 42)
        card_bg = colors[1] if len(colors) > 1 else (30, 41, 59)
        accent_color = colors[2] if len(colors) > 2 else (59, 130, 246)
        text_color = colors[3] if len(colors) > 3 else (255, 255, 255)

        brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
        is_dark = brightness < 128

        img = Image.new("RGBA", (W, H), (*bg_color, 255))
        draw = ImageDraw.Draw(img)

        # Ambient glow behind mobile frame
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse([W // 2 - 350, H // 2 - 400, W // 2 + 350, H // 2 + 400], fill=(*accent_color, 50))
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        img = Image.alpha_composite(img, glow)
        draw = ImageDraw.Draw(img)

        # Phone Chassis dimensions
        phone_w, phone_h = 660, 1380
        phone_x, phone_y = (W - phone_w) // 2, (H - phone_h) // 2
        phone_box = [phone_x, phone_y, phone_x + phone_w, phone_y + phone_h]

        # Shadow
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle([phone_x + 10, phone_y + 20, phone_x + phone_w - 10, phone_y + phone_h + 30], radius=50, fill=(0, 0, 0, 140))
        shadow = shadow.filter(ImageFilter.GaussianBlur(24))
        img = Image.alpha_composite(img, shadow)
        draw = ImageDraw.Draw(img)

        # Chassis outer border
        chassis_border = (60, 70, 90) if is_dark else (200, 210, 225)
        draw.rounded_rectangle(phone_box, radius=48, fill=(10, 12, 16), outline=chassis_border, width=4)

        # Screen area
        bezel = 16
        screen_x = phone_x + bezel
        screen_y = phone_y + bezel
        screen_w = phone_w - (bezel * 2)
        screen_h = phone_h - (bezel * 2)
        screen_box = [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h]

        screen_bg = (18, 22, 32) if is_dark else (255, 255, 255)
        draw.rounded_rectangle(screen_box, radius=38, fill=screen_bg)

        # Dynamic Island (punch hole camera)
        notch_w, notch_h = 160, 36
        notch_x = screen_x + (screen_w - notch_w) // 2
        notch_y = screen_y + 14
        draw.rounded_rectangle([notch_x, notch_y, notch_x + notch_w, notch_y + notch_h], radius=18, fill=(0, 0, 0))

        # Status Bar
        font_stat = get_default_font(16)
        draw.text((screen_x + 36, screen_y + 20), "9:41", fill=(148, 163, 184), font=font_stat)
        draw.text((screen_x + screen_w - 95, screen_y + 20), "5G  100%", fill=(148, 163, 184), font=font_stat)

        # Mobile App Bar
        appbar_y = screen_y + 65
        appbar_h = 60
        draw.rectangle([screen_x, appbar_y, screen_x + screen_w, appbar_y + appbar_h], fill=screen_bg)
        
        # Hamburger menu icon
        draw.line([screen_x + 30, appbar_y + 22, screen_x + 58, appbar_y + 22], fill=text_color if is_dark else (15, 23, 42), width=3)
        draw.line([screen_x + 30, appbar_y + 30, screen_x + 50, appbar_y + 30], fill=text_color if is_dark else (15, 23, 42), width=3)
        draw.line([screen_x + 30, appbar_y + 38, screen_x + 58, appbar_y + 38], fill=text_color if is_dark else (15, 23, 42), width=3)

        # Brand on mobile
        name = template_data.get("name", "Mobile Design")
        font_brand = get_default_font(18)
        draw.text((screen_x + 80, appbar_y + 22), name[:18], fill=text_color if is_dark else (15, 23, 42), font=font_brand)

        # Notification bell
        draw.ellipse([screen_x + screen_w - 60, appbar_y + 18, screen_x + screen_w - 28, appbar_y + 50], fill=(*accent_color, 40) if is_dark else (*accent_color, 30))
        draw.text((screen_x + screen_w - 49, appbar_y + 24), "✦", fill=accent_color, font=get_default_font(16))

        # Mobile Hero
        m_content_y = appbar_y + appbar_h + 30
        cat_name = template_data.get("category_slug", "Minimal & Professional").replace("-", " ").title()

        # Category pill
        draw.rounded_rectangle([screen_x + 30, m_content_y, screen_x + 220, m_content_y + 30], radius=15, fill=(*accent_color, 30), outline=accent_color, width=1)
        draw.text((screen_x + 48, m_content_y + 6), cat_name[:20], fill=accent_color, font=get_default_font(13))

        # Heading
        font_m_hero = get_default_font(28)
        draw.text((screen_x + 30, m_content_y + 45), name[:22], fill=text_color if is_dark else (15, 23, 42), font=font_m_hero)

        # Description
        desc = template_data.get("description", "Engineered for high conversion.")
        draw.text((screen_x + 30, m_content_y + 85), desc[:55], fill=(148, 163, 184), font=get_default_font(14))

        # Mobile CTA
        m_cta_box = [screen_x + 30, m_content_y + 120, screen_x + screen_w - 30, m_content_y + 170]
        draw.rounded_rectangle(m_cta_box, radius=12, fill=accent_color)
        draw.text((screen_x + (screen_w // 2) - 55, m_content_y + 135), "Get In Touch", fill=(255, 255, 255), font=get_default_font(16))

        # Mobile Metric Carousel Card
        card1_y = m_content_y + 195
        card1_h = 240
        c1_box = [screen_x + 30, card1_y, screen_x + screen_w - 30, card1_y + card1_h]
        draw.rounded_rectangle(c1_box, radius=16, fill=card_bg if is_dark else (248, 250, 252), outline=chassis_border, width=1)
        
        # Metric graph mock inside card
        draw.text((screen_x + 50, card1_y + 20), "Performance Pulse", fill=text_color if is_dark else (15, 23, 42), font=get_default_font(16))
        draw.text((screen_x + 50, card1_y + 44), "+42.8% Conversion Rate", fill=accent_color, font=get_default_font(14))

        # Curve lines
        graph_pts = [
            (screen_x + 50, card1_y + 180),
            (screen_x + 150, card1_y + 140),
            (screen_x + 280, card1_y + 160),
            (screen_x + 400, card1_y + 110),
            (screen_x + screen_w - 50, card1_y + 80),
        ]
        for idx in range(len(graph_pts) - 1):
            draw.line([graph_pts[idx], graph_pts[idx + 1]], fill=accent_color, width=3)
            draw.ellipse([graph_pts[idx][0] - 4, graph_pts[idx][1] - 4, graph_pts[idx][0] + 4, graph_pts[idx][1] + 4], fill=(255, 255, 255))
        draw.ellipse([graph_pts[-1][0] - 5, graph_pts[-1][1] - 5, graph_pts[-1][0] + 5, graph_pts[-1][1] + 5], fill=accent_color)

        # Feature List Cards on mobile (2 cards)
        f_card_y = card1_y + card1_h + 20
        features = template_data.get("features", ["Clean typography", "Fast performance"])
        for i, feat in enumerate(features[:2]):
            fy = f_card_y + i * 110
            fbox = [screen_x + 30, fy, screen_x + screen_w - 30, fy + 95]
            draw.rounded_rectangle(fbox, radius=12, fill=card_bg if is_dark else (248, 250, 252), outline=chassis_border, width=1)
            draw.ellipse([screen_x + 46, fy + 26, screen_x + 86, fy + 66], fill=(*accent_color, 40) if is_dark else (*accent_color, 30))
            draw.text((screen_x + 58, fy + 34), "✓", fill=accent_color, font=get_default_font(18))
            draw.text((screen_x + 100, fy + 24), feat[:28], fill=text_color if is_dark else (15, 23, 42), font=get_default_font(15))
            draw.text((screen_x + 100, fy + 52), "Optimized for mobile interfaces", fill=(148, 163, 184), font=get_default_font(12))

        # Bottom Mobile Nav Bar
        bnav_y = screen_y + screen_h - 95
        draw.rounded_rectangle([screen_x, bnav_y, screen_x + screen_w, screen_y + screen_h], radius=38, fill=(12, 15, 22) if is_dark else (241, 245, 249))
        draw.rectangle([screen_x, bnav_y, screen_x + screen_w, bnav_y + 40], fill=(12, 15, 22) if is_dark else (241, 245, 249))

        b_icons = ["🏠", "🔍", "⚡", "👤"]
        for idx, icon in enumerate(b_icons):
            bx = screen_x + 55 + idx * (screen_w // 4)
            draw.text((bx, bnav_y + 18), icon, font=get_default_font(20))

        # Home Indicator pill
        home_bar_w, home_bar_h = 160, 5
        home_bar_x = screen_x + (screen_w - home_bar_w) // 2
        home_bar_y = screen_y + screen_h - 16
        draw.rounded_rectangle([home_bar_x, home_bar_y, home_bar_x + home_bar_w, home_bar_y + home_bar_h], radius=3, fill=(148, 163, 184))

        final_img = Image.new("RGB", (W, H), bg_color)
        final_img.paste(img, (0, 0), img)
        return final_img
