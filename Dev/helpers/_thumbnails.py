import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.background_path = "Dev/helpers/l.jpg" 

        self.color_white = (255, 255, 255)
        self.color_grey = (180, 180, 180)
        self.color_accent = (200, 200, 200)

        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 45)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 30)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 20)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    def draw_icons(self, draw, x, y):
        # Previous Icon
        draw.polygon([(x, y), (x + 15, y - 10), (x + 15, y + 10)], fill=self.color_white)
        draw.polygon([(x + 15, y), (x + 30, y - 10), (x + 30, y + 10)], fill=self.color_white)
        
        # Pause Icon (Center)
        px, py = x + 70, y
        draw.rounded_rectangle((px, py - 15, px + 8, py + 15), radius=2, fill=self.color_white)
        draw.rounded_rectangle((px + 16, py - 15, px + 24, py + 15), radius=2, fill=self.color_white)

        # Next Icon
        nx, ny = x + 130, y
        draw.polygon([(nx, ny - 10), (nx + 15, ny), (nx, ny + 10)], fill=self.color_white)
        draw.polygon([(nx + 15, ny - 10), (nx + 30, ny), (nx + 15, ny + 10)], fill=self.color_white)

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_final.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            if os.path.exists(self.background_path):
                base = Image.open(self.background_path).convert("RGBA")
                base = base.resize((self.width, self.height), Image.Resampling.LANCZOS)
            else:
                base = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))

            original_art = Image.open(temp).convert("RGBA")

            screen_w, screen_h = 1100, 600
            blur_bg = original_art.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
            blur_bg = blur_bg.filter(ImageFilter.GaussianBlur(radius=20))
            enhancer = ImageEnhance.Brightness(blur_bg)
            blur_bg = enhancer.enhance(0.4) 

            screen_x, screen_y = 90, 50 
            base.paste(blur_bg, (screen_x, screen_y))

            art_size = (300, 300)
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=20, fill=255)
            
            art_x, art_y = 180, 210
            base.paste(art, (art_x, art_y), mask)

            draw = ImageDraw.Draw(base)
            text_x = 520
            center_y = 280

            title = song.title
            if len(title) > 20:
                title = title[:20] + "..."
            
            draw.text((text_x, center_y), title, font=self.font_title, fill=self.color_white)
            draw.text((text_x, center_y + 60), "Toxic Bots", font=self.font_artist, fill=self.color_accent)

            bar_x = text_x
            bar_y = center_y + 130
            bar_length = 500
            
            draw.line([(bar_x, bar_y), (bar_x + bar_length, bar_y)], fill=(100, 100, 100), width=4)
            draw.line([(bar_x, bar_y), (bar_x + 150, bar_y)], fill=self.color_white, width=4)
            draw.ellipse((bar_x + 145, bar_y - 6, bar_x + 157, bar_y + 6), fill=self.color_white)

            draw.text((bar_x, bar_y + 15), "0:45", font=self.font_small, fill=self.color_grey)
            draw.text((bar_x + bar_length - 40, bar_y + 15), "3:12", font=self.font_small, fill=self.color_grey)

            icon_y = bar_y + 70
            icon_start_x = text_x + 120
            self.draw_icons(draw, icon_start_x, icon_y)

            base.save(output)

            if os.path.exists(temp):
                os.remove(temp)

            return output

        except Exception as e:
            print(f"Error: {e}")
            return config.DEFAULT_THUMB
                         
