import os
import asyncio
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)
from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        
        # --- COLORS ---
        self.color_bg = (10, 10, 15)
        self.color_white = (255, 255, 255)
        self.color_grey = (160, 160, 160)
        self.color_accent = (255, 46, 99)    # Neon Red/Pink for "Toxic"
        self.color_primary = (0, 255, 213)   # Cyan
        self.color_lyrics_dim = (255, 255, 255, 100) # Faded lyrics
        self.color_lyrics_active = (255, 255, 255, 255) # Bright lyrics

        # --- FONTS ---
        # Ensure paths are correct, fallback to default if missing
        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 45)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 30)
            self.font_lyrics = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 55) # Big Lyrics font
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 22)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_lyrics = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
            return output_path

    def make_rounded(self, img, radius=30):
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
        output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp_dl = f"cache/temp_{song.id}.jpg"
            output_gif = f"cache/{song.id}_lyrics.gif"

            if os.path.exists(output_gif):
                return output_gif

            await self.save_thumb(temp_dl, song.thumbnail)

            # 1. Prepare Base Background
            original_art = Image.open(temp_dl).convert("RGBA")
            
            # Dark blurred background
            base_bg = original_art.resize((1280, 720), Image.Resampling.LANCZOS)
            base_bg = base_bg.filter(ImageFilter.GaussianBlur(50))
            base_bg = ImageEnhance.Brightness(base_bg).enhance(0.3) # Darker for contrast

            # 2. Prepare Left Side Art (Small & Rounded)
            art_size = (350, 350)
            cover_art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS)
            cover_art = self.make_rounded(cover_art, radius=40)
            
            # Art Shadow (Glow)
            shadow = Image.new("RGBA", (390, 390), (0,0,0,0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle((20, 20, 370, 370), radius=40, fill=(0,0,0,180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(15))

            # 3. Text Preparation
            title = song.title
            if len(title) > 18: title = title[:18] + "..."
            duration_text = "00:45 / 03:20" # Example, you can use song.duration

            # FAKE LYRICS LIST (To simulate the right side animation)
            # Agar real lyrics nahi hain, toh ye vibe banayega
            lyrics_lines = [
                "",
                "Now Playing...",
                f"{song.title}",
                "Feel the beat",
                "Toxic Bots Music",
                "Stereo Sound 🎧",
                "Vibe check passed",
                "Volume up 🔊",
                "Enjoy the rhythm",
                "Loading next verse...",
                ""
            ]

            frames = []
            total_frames = 20 # Animation smoothness
            scroll_speed = 6  # Pixels to move per frame

            # =========================
            # 🎬 ANIMATION LOOP
            # =========================
            for i in range(total_frames):
                frame = base_bg.copy()
                draw = ImageDraw.Draw(frame)

                # --- LEFT SIDE LAYOUT ---
                left_margin = 80
                art_y = 100

                # Draw Shadow & Art
                frame.paste(shadow, (left_margin - 20, art_y - 20), shadow)
                frame.paste(cover_art, (left_margin, art_y), cover_art)

                # Text Below Art
                text_start_y = art_y + 350 + 40
                
                # Title
                draw.text((left_margin, text_start_y), title, font=self.font_title, fill=self.color_white)
                
                # Branding (Toxic Bots)
                draw.text((left_margin, text_start_y + 60), "Toxic Bots", font=self.font_artist, fill=self.color_accent)
                
                # Duration Icon & Text
                draw.rounded_rectangle((left_margin, text_start_y + 110, left_margin + 160, text_start_y + 145), radius=10, fill=(255,255,255,30))
                draw.text((left_margin + 20, text_start_y + 115), duration_text, font=self.font_small, fill=self.color_primary)

                # Separator Line (Vertical)
                draw.line([(550, 100), (550, 620)], fill=(255,255,255,50), width=2)

                # --- RIGHT SIDE (SCROLLING LYRICS) ---
                # Hum lyrics ko crop karne ke liye ek transparent layer banayenge
                lyrics_layer = Image.new("RGBA", (700, 600), (0,0,0,0))
                lyric_draw = ImageDraw.Draw(lyrics_layer)

                lyric_x = 20
                start_y = 200 - (i * scroll_speed) # Scrolling logic

                for idx, line in enumerate(lyrics_lines):
                    line_y = start_y + (idx * 90) # Gap between lines
                    
                    # Highlighting effect (Center line is bright, others dim)
                    # Simple simulation: Middle of the box is roughly y=300
                    if 250 < line_y < 350:
                        color = self.color_lyrics_active
                        font_size = 60 # Active line slightly bigger? (Optional, requires complex font handling)
                    else:
                        color = self.color_lyrics_dim
                    
                    lyric_draw.text((lyric_x, line_y), line, font=self.font_lyrics, fill=color)

                # Paste Lyrics on Frame (Right side)
                frame.paste(lyrics_layer, (600, 80), lyrics_layer)

                frames.append(frame)

            # =========================
            # 💾 SAVE ANIMATION
            # =========================
            frames[0].save(
                output_gif,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=120,
                loop=0
            )

            if os.path.exists(temp_dl):
                os.remove(temp_dl)

            return output_gif

        except Exception as e:
            print(f"Thumbnail Error: {e}")
            return config.DEFAULT_THUMB
                
