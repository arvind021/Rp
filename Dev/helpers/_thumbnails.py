import os
import aiohttp
import textwrap
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        # Canvas dimensions
        self.width = 1280
        self.height = 720

        # Fonts (Aapke existing fonts use kiye hain taaki error na aaye)
        # Title/Big Text ke liye Bold
        self.font_big = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 70) 
        self.font_med = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 40)
        # Details ke liye Light
        self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 30)

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
        return output_path

    async def generate(self, song: Track) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"

            if os.path.exists(output):
                return output

            # 1. Image Download
            await self.save_thumb(temp, song.thumbnail)

            # 2. Main Setup
            original = Image.open(temp).convert("RGBA")
            
            # Background banate hain (Blur + Dark)
            background = original.resize((self.width, self.height), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(15))
            background = ImageEnhance.Brightness(background).enhance(0.6)

            # 3. Logo/Image Processing (Alexa Style: Square with White Border)
            # Center Crop Logic
            width, height = original.size
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2
            
            logo = original.crop((left, top, right, bottom))
            logo = logo.resize((520, 520), Image.Resampling.LANCZOS)
            
            # White Border add karna (15px)
            logo = ImageOps.expand(logo, border=15, fill="white")
            
            # Image ko Left side paste karna (Coordinate: 50, 100)
            background.paste(logo, (50, 100))

            # 4. Text Drawing
            draw = ImageDraw.Draw(background)

            # Top Left Branding
            draw.text((20, 20), "Toxic MusicBot", fill="white", font=self.font_small)

            # "NOW PLAYING" Text (Right Side)
            draw.text(
                (600, 150),
                "NOW PLAYING",
                fill="white",
                stroke_width=3,
                stroke_fill="black",
                font=self.font_big,
            )

            # Song Title (Text Wrap ke sath)
            # Title ko wrap karenge taaki wo screen se bahar na jaye
            para = textwrap.wrap(song.title, width=30)
            
            current_h = 280
            for line in para[:2]: # Sirf top 2 lines dikhayenge
                draw.text(
                    (600, current_h),
                    line,
                    fill="white",
                    stroke_width=1,
                    stroke_fill="black",
                    font=self.font_med,
                )
                current_h += 50

            # Details (Views, Duration, Channel)
            # Views
            draw.text(
                (600, 450),
                f"Views : {song.view_count}",
                fill="white",
                font=self.font_small,
            )

            # Duration
            draw.text(
                (600, 500),
                f"Duration : {song.duration}",
                fill="white",
                font=self.font_small,
            )

            # Channel / Owner
            draw.text(
                (600, 550),
                f"Channel : {song.channel_name}",
                fill="white",
                font=self.font_small,
            )

            # 5. Save and Cleanup
            background.save(output)
            os.remove(temp)

            return output

        except Exception as e:
            print(f"[Thumbnail Error] {e}")
            return config.DEFAULT_THUMB
            
