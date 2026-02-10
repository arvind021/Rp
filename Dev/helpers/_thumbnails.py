import os
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)

from Dev import config
from Dev.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)

        # Fonts
        self.font1 = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 30)
        self.font2 = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 26)

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            thumb = Image.open(temp).convert("RGBA").resize(
                size, Image.Resampling.LANCZOS
            )

            # Background blur + dark
            blur = thumb.filter(ImageFilter.GaussianBlur(28))
            image = ImageEnhance.Brightness(blur).enhance(0.35)
            image = ImageEnhance.Contrast(image).enhance(1.2)

            # Center rounded image card
            _rect = ImageOps.fit(
                thumb, self.rect,
                method=Image.LANCZOS,
                centering=(0.5, 0.5)
            )

            mask_draw = ImageDraw.Draw(self.mask)
            mask_draw.rectangle((0, 0, *self.rect), fill=0)
            mask_draw.rounded_rectangle(
                (0, 0, self.rect[0], self.rect[1]),
                radius=25,
                fill=255
            )

            _rect.putalpha(self.mask)
            image.paste(_rect, (183, 30), _rect)

            draw = ImageDraw.Draw(image)

            # Channel + views
            draw.text(
                (50, 530),
                f"{song.channel_name[:25]}  •  {song.view_count}",
                font=self.font2,
                fill=(200, 200, 200)
            )

            # Song title
            draw.text(
                (50, 575),
                song.title[:50],
                font=self.font1,
                fill=(255, 255, 255)
            )

            # EXACT TEXT: Toxic Bots (under title)
            draw.text(
                (50, 615),
                "Toxic Bots",
                font=self.font2,
                fill=(255, 70, 70)  # red premium
            )

            # Progress bar
            draw.text((40, 650), "0:01", font=self.font1, fill=self.fill)
            draw.line([(140, 670), (1160, 670)], fill=self.fill, width=6)
            draw.text((1185, 650), song.duration, font=self.font1, fill=self.fill)

            image.save(output)
            os.remove(temp)

            return output

        except Exception as e:
            print(f"[Thumbnail Error] {e}")
            return config.DEFAULT_THUMB
