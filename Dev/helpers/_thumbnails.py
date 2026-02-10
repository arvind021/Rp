import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        # ये आपके "Music Player" (Screen) की साइज है
        self.width = 1280
        self.height = 720
        
        # लैपटॉप इमेज का नाम (आपको ये फोटो अपने फोल्डर में रखनी होगी)
        self.laptop_bg_path = "laptop.jpg" 
        
        self.fill = (255, 255, 255)
        self.secondary_fill = (200, 200, 200) 

        # Fonts setup
        try:
            # बड़े फोंट्स ताकि लैपटॉप स्क्रीन पर साफ़ दिखें
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 55)
            self.font_artist = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 35)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25)
            # "Toxic Bots" ब्रांडिंग के लिए स्टाइलिश फोंट
            self.font_brand = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 40)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_brand = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    # आइकन्स ड्रा करने का फंक्शन (Play, Pause etc)
    def draw_player_icons(self, draw, start_x, center_y):
        # यहाँ start_x वो पॉइंट है जहाँ से बटन शुरू होंगे (Right Side)
        
        # Previous (<<)
        prev_x = start_x
        draw.polygon([(prev_x, center_y), (prev_x + 20, center_y - 15), (prev_x + 20, center_y + 15)], fill=self.fill)
        draw.polygon([(prev_x + 20, center_y), (prev_x + 40, center_y - 15), (prev_x + 40, center_y + 15)], fill=self.fill)

        # Pause (||) - Center Main Button
        pause_x = start_x + 80
        draw.rounded_rectangle((pause_x, center_y - 25, pause_x + 10, center_y + 25), radius=3, fill=self.fill)
        draw.rounded_rectangle((pause_x + 20, center_y - 25, pause_x + 30, center_y + 25), radius=3, fill=self.fill)

        # Next (>>)
        next_x = start_x + 150
        draw.polygon([(next_x + 20, center_y), (next_x, center_y - 15), (next_x, center_y + 15)], fill=self.fill)
        draw.polygon([(next_x + 40, center_y), (next_x + 20, center_y - 15), (next_x + 20, center_y + 15)], fill=self.fill)

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_laptop.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            # --- STEP 1: UI बनाना (जो स्क्रीन के अंदर दिखेगा) ---
            original = Image.open(temp).convert("RGBA")
            
            # Background Blur Effect
            screen = original.resize((self.width, self.height), Image.Resampling.LANCZOS)
            screen = screen.filter(ImageFilter.GaussianBlur(20))
            screen = ImageEnhance.Brightness(screen).enhance(0.5) # Dark Background

            draw = ImageDraw.Draw(screen)

            # 1. Album Art (Left Side - Big & Rounded)
            art_size = (450, 450)
            art = ImageOps.fit(original, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # Rounded Corners Mask
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=30, fill=255)
            art.putalpha(mask)
            
            # Paste Album Art (Left side padding: 80)
            screen.paste(art, (80, 135), art)

            # 2. Text Info (Right Side)
            text_x = 600
            
            # "Toxic Bots" Branding (Top Left of Text area - like 'Noor' in reference)
            draw.text((text_x, 150), "TOXIC BOTS", font=self.font_brand, fill=(255, 20, 147)) # Deep Pink color branding
            
            # Song Title
            title = song.title
            if len(title) > 25:
                title = title[:25] + "..."
            draw.text((text_x, 220), title, font=self.font_title, fill=self.fill)
            
            # Artist Name
            channel = song.channel_name
            if len(channel) > 30:
                channel = channel[:30] + "..."
            draw.text((text_x, 290), channel, font=self.font_artist, fill=self.secondary_fill)

            # 3. Progress Bar
            bar_start_x = text_x
            bar_y = 400
            draw.line([(bar_start_x, bar_y), (1150, bar_y)], fill=(100, 100, 100), width=6) # Grey path
            draw.line([(bar_start_x, bar_y), (bar_start_x + 180, bar_y)], fill=self.fill, width=6) # White progress
            draw.ellipse((bar_start_x + 170, bar_y - 8, bar_start_x + 190, bar_y + 8), fill=self.fill) # Dot

            # Duration
            draw.text((bar_start_x, bar_y + 20), "0:00", font=self.font_small, fill=self.secondary_fill)
            draw.text((1100, bar_y + 20), song.duration, font=self.font_small, fill=self.secondary_fill)

            # 4. Controls (Centered below text)
            self.draw_player_icons(draw, text_x + 100, 520)

            # --- STEP 2: Laptop के अंदर फिट करना ---
            
            # चेक करें कि laptop.jpg मौजूद है या नहीं
            if os.path.exists(self.laptop_bg_path):
                laptop = Image.open(self.laptop_bg_path).convert("RGBA")
                
                # नोट: ये Co-ordinates आपको अपनी laptop photo के हिसाब से बदलने पड़ेंगे
                # मान लीजिये लैपटॉप की फोटो 1920x1080 है और स्क्रीन एरिया (300, 100) पर शुरू होता है
                # स्क्रीन को थोड़ा छोटा करके (जैसे 70%) लैपटॉप की स्क्रीन साइज में फिट करें
                
                # यहाँ हम मान रहे हैं कि आप एक ऐसी फोटो यूज़ करेंगे जिसमें स्क्रीन सीधी है
                target_screen_width = 750  # आपकी लैपटॉप इमेज में स्क्रीन की चौड़ाई
                target_screen_height = 422 # 16:9 ratio maintain
                
                # स्क्रीन को रिसाइज करें
                screen_resized = screen.resize((target_screen_width, target_screen_height), Image.Resampling.LANCZOS)
                
                # स्क्रीन को लैपटॉप इमेज पर पेस्ट करें (Co-ordinates X, Y बदलें अपनी फोटो के हिसाब से)
                # मान लीजिये लैपटॉप इमेज में स्क्रीन (585, 250) पिक्सेल पर शुरू होती है
                screen_pos_x = 585 
                screen_pos_y = 250
                
                # लैपटॉप पर स्क्रीन पेस्ट करें
                laptop.paste(screen_resized, (screen_pos_x, screen_pos_y))
                
                # फाइनल इमेज सेव करें
                laptop.save(output)
            else:
                # अगर laptop.jpg नहीं मिली तो सिर्फ स्क्रीन वाली इमेज भेज दें
                print("Warning: laptop.jpg not found. Sending flat UI.")
                screen.save(output)

            if os.path.exists(temp):
                os.remove(temp)
                
            return output
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB
          
