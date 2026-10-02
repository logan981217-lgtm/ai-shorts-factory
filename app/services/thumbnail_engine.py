import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, List
from app.config import THUMBNAILS_DIR, DEFAULT_FONT_PATH

class ThumbnailEngine:
    def __init__(self):
        self.font_path = DEFAULT_FONT_PATH

    def generate_thumbnail(self, project_id: str, topic: str, title: str) -> str:
        """
        Creates an eye-catching 1080x1920 vertical Shorts thumbnail with high CTR aesthetics.
        """
        width, height = 1080, 1920
        thumb_path = THUMBNAILS_DIR / f"{project_id}.jpg"

        # Theme color palettes (Shorts high CTR styles)
        palettes = [
            {"top": (20, 10, 40), "bottom": (80, 20, 120), "accent": (255, 230, 0), "badge": (255, 50, 80)}, # Cyber purple & gold
            {"top": (10, 25, 45), "bottom": (20, 80, 110), "accent": (0, 255, 200), "badge": (255, 100, 0)},  # Electric blue & cyan
            {"top": (35, 10, 10), "bottom": (120, 20, 30), "accent": (255, 240, 50), "badge": (255, 20, 60)}, # Impact crimson & yellow
            {"top": (15, 20, 25), "bottom": (40, 50, 60), "accent": (50, 230, 120), "badge": (0, 180, 255)},  # Stealth dark & emerald
        ]
        chosen = random.choice(palettes)

        # 1. Base gradient
        img = Image.new("RGB", (width, height), chosen["top"])
        draw = ImageDraw.Draw(img)

        # Draw vertical smooth gradient
        for y in range(height):
            ratio = y / height
            r = int(chosen["top"][0] * (1 - ratio) + chosen["bottom"][0] * ratio)
            g = int(chosen["top"][1] * (1 - ratio) + chosen["bottom"][1] * ratio)
            b = int(chosen["top"][2] * (1 - ratio) + chosen["bottom"][2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 2. Add modern geometric glow background effects
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_layer)

        # Central radiant circle
        center_y = int(height * 0.45)
        radius = 420
        gdraw.ellipse(
            [(width // 2 - radius, center_y - radius), (width // 2 + radius, center_y + radius)],
            fill=(*chosen["accent"], 40)
        )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(80))
        img.paste(glow_layer, (0, 0), glow_layer)
        draw = ImageDraw.Draw(img)

        # 3. Decorative grid / framing lines
        draw.rectangle([(40, 60), (width - 40, height - 60)], outline=(255, 255, 255, 40), width=3)
        
        # 4. Top Category Badge
        badge_text = "⚡ SHORTS SPECIAL"
        if any(k in topic for k in ["돈", "재테크", "주식", "부자"]):
            badge_text = "💰 자본주의 생존 꿀팁"
        elif any(k in topic for k in ["역사", "비밀", "미스터리"]):
            badge_text = "🕵️ 아무도 모르는 진실"
        elif any(k in topic for k in ["AI", "테크", "기술"]):
            badge_text = "🤖 2026 미래 기술 리포트"

        try:
            badge_font = ImageFont.truetype(self.font_path, 38)
            title_font = ImageFont.truetype(self.font_path, 76)
            sub_font = ImageFont.truetype(self.font_path, 54)
        except Exception:
            badge_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        # Badge pill
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx, by = (width - bw) // 2, 380
        pad_x, pad_y = 35, 18
        draw.rounded_rectangle(
            [(bx - pad_x, by - pad_y), (bx + bw + pad_x, by + bh + pad_y)],
            radius=25,
            fill=chosen["badge"]
        )
        draw.text((bx, by), badge_text, fill=(255, 255, 255), font=badge_font)

        # 5. Main Title Typography (Word wrapped & 2-3 lines max)
        clean_title = title.replace("#Shorts", "").replace("#쇼츠", "").strip()
        words = clean_title.split(" ")
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            test_line = " ".join(cur_line)
            t_bbox = draw.textbbox((0, 0), test_line, font=title_font)
            if t_bbox[2] - t_bbox[0] > width - 180:
                cur_line.pop()
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))
        
        # Limit to 3 lines
        lines = lines[:3]
        line_height = 100
        start_y = by + bh + 140

        for i, line in enumerate(lines):
            l_bbox = draw.textbbox((0, 0), line, font=title_font)
            lw = l_bbox[2] - l_bbox[0]
            lx = (width - lw) // 2
            ly = start_y + (i * line_height)
            
            # Thick black outline for maximum readability
            for ox in range(-5, 6):
                for oy in range(-5, 6):
                    draw.text((lx + ox, ly + oy), line, font=title_font, fill=(0, 0, 0))
            
            # First line is accented color, rest are clean white
            fill_color = chosen["accent"] if i == 0 else (255, 255, 255)
            draw.text((lx, ly), line, font=title_font, fill=fill_color)

        # 6. Bottom Attention Hook Callout
        hook_box_y = height - 450
        draw.rounded_rectangle(
            [(80, hook_box_y), (width - 80, hook_box_y + 130)],
            radius=20,
            fill=(0, 0, 0, 180),
            outline=chosen["accent"],
            width=4
        )
        hook_text = "👇 지금 바로 확인하기 (30초 요약)"
        h_bbox = draw.textbbox((0, 0), hook_text, font=sub_font)
        hw = h_bbox[2] - h_bbox[0]
        draw.text(((width - hw) // 2, hook_box_y + 35), hook_text, font=sub_font, fill=(255, 255, 255))

        # Save thumbnail
        img.save(str(thumb_path), format="JPEG", quality=95)
        return str(thumb_path)
