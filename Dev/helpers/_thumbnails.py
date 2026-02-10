import os
import random
import asyncio
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps, ImageSequence
)

# Aapke existing modules
from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        # Neon & Dark Theme Colors
        self.color_bg = (15, 15, 25)
        self.color_white = (255, 255, 255)
        self.color_grey = (180, 180, 180)
        self.color_accent = (0, 255, 213)  # Cyberpunk Cyan
        self.color_secondary = (255, 0, 110) # Neon Pink for contrast

        try:
            # Font paths check kar lena
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 55)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 35)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 24)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
                with open(output_path, "wb") as f:
                    f.write(data)
            return output_path

    def make_circle(self, img):
        """Image ko gol (circle) shape me katne ke liye"""
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output

    def draw_visualizer(self, draw, x, y, width, height, color):
        """Random music bars generate karne ke liye"""
        num_bars = 20
        gap = 8
        bar_w = (width - (gap * (num_bars - 1))) / num_bars
        
        for i in range(num_bars):
            bar_h = random.randint(10, height) # Random height for animation
            bx = x + i * (bar_w + gap)
            by = y + height - bar_h
            # Draw glow bar
            draw.rectangle([bx, by, bx + bar_w, y + height], fill=color)

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp_dl = f"cache/temp_{song.id}.jpg"
            # Output ab GIF hoga
            output_gif = f"cache/{song.id}_anim.gif"

            if os.path.exists(output_gif):
                return output_gif

            await self.save_thumb(temp_dl, song.thumbnail)

            # 1. Prepare Base Art
            original_art = Image.open(temp_dl).convert("RGBA")
            
            # --- Background Blur Effect ---
            screen_w, screen_h = 1280, 720
            bg = original_art.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(40)) # Heavy blur
            bg = ImageEnhance.Brightness(bg).enhance(0.4) # Darken

            # --- Prepare Vinyl Record Art ---
            art_size = (380, 380)
            vinyl_art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS)
            vinyl_art = self.make_circle(vinyl_art)
            
            # Vinyl Disc Background (Black Circle)
            vinyl_disc = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
            draw_disc = ImageDraw.Draw(vinyl_disc)
            draw_disc.ellipse((0, 0, 400, 400), fill=(10, 10, 10, 255), outline=(30,30,30), width=2)
            
            # Paste Art on Disc center
            vinyl_disc.paste(vinyl_art, (10, 10), vinyl_art)

            # --- Text Info ---
            title = song.title
            if len(title) > 20: title = title[:20] + "..."
            
            artist = "Toxic Bots" # Ya song.artist
            
            frames = []
            total_frames = 15  # Kam frames rakhna taaki file size chota rahe aur jaldi bane

            # =========================
            # 🎬 ANIMATION LOOP
            # =========================
            for i in range(total_frames):
                # Create frame base
                frame = bg.copy()
                draw = ImageDraw.Draw(frame)

                # 1. Draw Card Background (Glass effect)
                overlay = Image.new("RGBA", (self.width, self.height), (0,0,0,0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rounded_rectangle((50, 50, 1230, 670), radius=30, fill=(0, 0, 0, 100))
                overlay_draw.rounded_rectangle((50, 50, 1230, 670), radius=30, outline=self.color_accent, width=2)
                frame = Image.alpha_composite(frame, overlay)
                draw = ImageDraw.Draw(frame) # Re-init draw on composite

                # 2. Rotate Vinyl (Spin Animation)
                # Har frame me 360/total_frames degree ghumao
                rotation = (360 / total_frames) * i
                rotated_vinyl = vinyl_disc.rotate(rotation, resample=Image.Resampling.BICUBIC)
                
                # Vinyl Shadow
                shadow_x, shadow_y = 120, 160
                draw.ellipse((shadow_x-10, shadow_y+10, shadow_x+410, shadow_y+420), fill=(0,0,0,150))
                frame.paste(rotated_vinyl, (shadow_x, shadow_y), rotated_vinyl)

                # 3. Draw Text
                text_x = 600
                text_y = 180
                draw.text((text_x, text_y), title, font=self.font_title, fill=self.color_white)
                draw.text((text_x, text_y + 70), artist, font=self.font_artist, fill=self.color_accent)

                # 4. Animated Visualizer (Fake Spectrum)
                # Ye har frame me random height banayega
                self.draw_visualizer(draw, text_x, text_y + 140, 500, 60, self.color_secondary)

                # 5. Moving Progress Bar
                bar_x = text_x
                bar_y = text_y + 240
                bar_len = 500
                
                # Progress calculation (Loop simulation)
                progress_pct = (i + 1) / total_frames
                current_bar_w = int(bar_len * (0.3 + (progress_pct * 0.1))) # Thoda sa move karega 30% to 40%

                draw.line([(bar_x, bar_y), (bar_x + bar_len, bar_y)], fill=(60, 60, 60), width=6)
                draw.line([(bar_x, bar_y), (bar_x + current_bar_w, bar_y)], fill=self.color_accent, width=6)
                
                # Dot with Glow
                dot_x = bar_x + current_bar_w
                draw.ellipse((dot_x - 8, bar_y - 8, dot_x + 8, bar_y + 8), fill=self.color_white)
                
                # Time Text
                draw.text((bar_x, bar_y + 20), "1:20", font=self.font_small, fill=self.color_grey)
                draw.text((bar_x + bar_len - 50, bar_y + 20), "3:45", font=self.font_small, fill=self.color_grey)

                frames.append(frame)

            # =========================
            # 💾 SAVE AS GIF
            # =========================
            frames[0].save(
                output_gif,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=100, # Speed of animation (ms)
                loop=0
            )

            if os.path.exists(temp_dl):
                os.remove(temp_dl)

            return output_gif

        except Exception as e:
            print(f"Animation Error: {e}")
            return config.DEFAULT_THUMB
                
