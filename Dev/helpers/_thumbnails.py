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
        self.fill = (255, 255, 255)
        self.secondary_fill = (200, 200, 200) 
        
        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 60)
            self.font_artist = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 40)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25)
            self.font_bot_name = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 20)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_bot_name = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    def draw_player_icons(self, draw, center_x, center_y):
        draw.rounded_rectangle((center_x - 15, center_y - 25, center_x - 5, center_y + 25), radius=5, fill=self.fill)
        draw.rounded_rectangle((center_x + 5, center_y - 25, center_x + 15, center_y + 25), radius=5, fill=self.fill)

        prev_x = center_x - 100
        draw.polygon([(prev_x, center_y), (prev_x + 25, center_y - 20), (prev_x + 25, center_y + 20)], fill=self.fill)
        draw.polygon([(prev_x - 20, center_y), (prev_x + 5, center_y - 20), (prev_x + 5, center_y + 20)], fill=self.fill)

        next_x = center_x + 100
        draw.polygon([(next_x, center_y), (next_x - 25, center_y - 20), (next_x - 25, center_y + 20)], fill=self.fill)
        draw.polygon([(next_x + 20, center_y), (next_x - 5, center_y - 20), (next_x - 5, center_y + 20)], fill=self.fill)

        vol_x = center_x - 150
        vol_y = center_y + 100
        draw.polygon([(vol_x, vol_y), (vol_x + 10, vol_y - 10), (vol_x + 10, vol_y + 10)], fill=self.fill)
        draw.rectangle((vol_x - 5, vol_y - 5, vol_x, vol_y + 5), fill=self.fill)
        draw.line([(vol_x + 25, vol_y), (vol_x + 300, vol_y)], fill=self.fill, width=3)
        draw.ellipse((vol_x + 200, vol_y - 6, vol_x + 212, vol_y + 6), fill=self.fill)
        
        list_x = center_x + 200
        list_y = center_y + 100
        draw.line([(list_x, list_y - 10), (list_x + 30, list_y - 10)], fill=self.fill, width=3)
        draw.line([(list_x, list_y), (list_x + 30, list_y)], fill=self.fill, width=3)
        draw.line([(list_x, list_y + 10), (list_x + 30, list_y + 10)], fill=self.fill, width=3)

    async def generate(self, song: Track) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            original = Image.open(temp).convert("RGBA")
            background = original.resize((self.width, self.height), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(30))
            background = ImageEnhance.Brightness(background).enhance(0.40)

            art_size = (550, 550)
            art = ImageOps.fit(original, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=30, fill=255)
            art.putalpha(mask)
            
            background.paste(art, (60, 85), art)

            draw = ImageDraw.Draw(background)
            
            text_start_x = 660
            center_right = text_start_x + (1280 - text_start_x) // 2 

            draw.text((text_start_x, 150), song.title[:35], font=self.font_title, fill=self.fill)
            
            draw.text((text_start_x, 230), song.channel_name[:30], font=self.font_artist, fill=self.secondary_fill)

            bar_y = 350
            draw.line([(text_start_x, bar_y), (1220, bar_y)], fill=(100, 100, 100), width=4)
            draw.line([(text_start_x, bar_y), (text_start_x + 200, bar_y)], fill=self.fill, width=4)
            draw.ellipse((text_start_x + 194, bar_y - 6, text_start_x + 206, bar_y + 6), fill=self.fill)

            draw.text((center_right - 50, bar_y + 20), "Toxic Bots", font=self.font_bot_name, fill=self.secondary_fill)

            self.draw_player_icons(draw, center_right, 480)
            
            draw.text((1150, bar_y + 20), song.duration, font=self.font_small, fill=self.fill)
            draw.text((text_start_x, bar_y + 20), "0:00", font=self.font_small, fill=self.fill)

            background.save(output)
            os.remove(temp)
            return output
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB
          
