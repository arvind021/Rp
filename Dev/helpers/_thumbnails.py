import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        # 1280x720 Canvas
        self.width = 1280
        self.height = 720
        self.fill = (255, 255, 255)
        self.secondary_fill = (200, 200, 200) 
        
        # फॉन्ट लोड करने की कोशिश, अगर नहीं मिले तो डिफ़ॉल्ट
        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 60)
            self.font_artist = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 40)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25)
        except:
            print("Warning: Custom fonts not found, using default.")
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    # प्लेयर के बटन (Play, Pause, Next) बनाने का फंक्शन
    def draw_player_icons(self, draw, center_x, center_y):
        # Pause Icon (||)
        draw.rounded_rectangle((center_x - 15, center_y - 25, center_x - 5, center_y + 25), radius=5, fill=self.fill)
        draw.rounded_rectangle((center_x + 5, center_y - 25, center_x + 15, center_y + 25), radius=5, fill=self.fill)

        # Previous Icon (<<)
        prev_x = center_x - 100
        draw.polygon([(prev_x, center_y), (prev_x + 25, center_y - 20), (prev_x + 25, center_y + 20)], fill=self.fill)
        draw.polygon([(prev_x - 20, center_y), (prev_x + 5, center_y - 20), (prev_x + 5, center_y + 20)], fill=self.fill)

        # Next Icon (>>)
        next_x = center_x + 100
        draw.polygon([(next_x, center_y), (next_x - 25, center_y - 20), (next_x - 25, center_y + 20)], fill=self.fill)
        draw.polygon([(next_x + 20, center_y), (next_x - 5, center_y - 20), (next_x - 5, center_y + 20)], fill=self.fill)

        # Volume Icon
        vol_x = center_x - 150
        vol_y = center_y + 100
        draw.polygon([(vol_x, vol_y), (vol_x + 10, vol_y - 10), (vol_x + 10, vol_y + 10)], fill=self.fill)
        draw.rectangle((vol_x - 5, vol_y - 5, vol_x, vol_y + 5), fill=self.fill)
        draw.line([(vol_x + 25, vol_y), (vol_x + 300, vol_y)], fill=self.fill, width=3)
        draw.ellipse((vol_x + 200, vol_y - 6, vol_x + 212, vol_y + 6), fill=self.fill)
        
        # List Icon
        list_x = center_x + 200
        list_y = center_y + 100
        draw.line([(list_x, list_y - 10), (list_x + 30, list_y - 10)], fill=self.fill, width=3)
        draw.line([(list_x, list_y), (list_x + 30, list_y)], fill=self.fill, width=3)
        draw.line([(list_x, list_y + 10), (list_x + 30, list_y + 10)], fill=self.fill, width=3)

    async def generate(self, song: Track) -> str:
        try:
            # Cache directory check
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_v2.png" # नाम बदल दिया ताकि पुराना cache लोड न हो
            
            # अगर पहले से फाइल है तो वही रिटर्न करें
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            # --- Background Logic ---
            original = Image.open(temp).convert("RGBA")
            background = original.resize((self.width, self.height), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(30))
            background = ImageEnhance.Brightness(background).enhance(0.40) # थोड़ा डार्क

            # --- Album Art (Left Side) ---
            # Fallen Style: फोटो लेफ्ट में बड़ी होती है
            art_size = (500, 500)
            art = ImageOps.fit(original, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # गोल कोने (Rounded Corners)
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=40, fill=255)
            art.putalpha(mask)
            
            # फोटो को लेफ्ट साइड (x=100, y=110) पर पेस्ट करें
            background.paste(art, (100, 110), art)

            # --- Text & Controls (Right Side) ---
            draw = ImageDraw.Draw(background)
            
            text_x = 650
            center_control_x = text_x + (1280 - text_x) // 2 

            # Title
            title = song.title
            if len(title) > 30:
                title = title[:30] + "..."
            draw.text((text_x, 180), title, font=self.font_title, fill=self.fill)
            
            # Artist / Channel Name
            channel = song.channel_name
            if len(channel) > 30:
                channel = channel[:30] + "..."
            draw.text((text_x, 260), channel, font=self.font_artist, fill=self.secondary_fill)

            # Progress Bar
            bar_y = 380
            draw.line([(text_x, bar_y), (1200, bar_y)], fill=(100, 100, 100), width=5) # Gray Line
            draw.line([(text_x, bar_y), (text_x + 220, bar_y)], fill=self.fill, width=5) # White Progress
            draw.ellipse((text_x + 210, bar_y - 8, text_x + 230, bar_y + 8), fill=self.fill) # Dot

            # Duration Times
            draw.text((text_x, bar_y + 20), "0:00", font=self.font_small, fill=self.fill)
            draw.text((1140, bar_y + 20), song.duration, font=self.font_small, fill=self.fill)

            # Controls Draw Karen
            self.draw_player_icons(draw, center_control_x, 520)

            # Final Save
            background.save(output)
            if os.path.exists(temp):
                os.remove(temp)
                
            return output
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            # अगर एरर आए तो कम से कम डिफॉल्ट न भेजें, कोशिश करें temp भेजने की
            return config.DEFAULT_THUMB
          
