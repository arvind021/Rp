import os
import asyncio
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)
import lyricsgenius  # pip install lyricsgenius

from Dev import config
from Dev.helpers import Track

# ==========================================
# ⚙️ CONFIGURATION (API KEY YAHAN DAALO)
# ==========================================
GENIUS_API_TOKEN = "YAHAN_APNA_GENIUS_TOKEN_PASTE_KARO"
# Agar token nahi hai toh ise empty chhod do (""), fake lyrics chalengi.

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        
        # --- PRO COLORS ---
        self.color_bg = (10, 10, 15)
        self.color_white = (255, 255, 255)
        self.color_grey = (180, 180, 180)
        self.color_accent = (255, 20, 147)  # Deep Pink (Toxic Vibe)
        self.color_primary = (0, 255, 255) # Cyan for Duration

        # --- FONTS SETUP ---
        try:
            # Main Bold Font
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 50)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 35)
            # Lyrics Font (Thoda clean rakhna)
            self.font_lyrics = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 40)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_lyrics = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

        # Initialize Genius
        self.genius = None
        if GENIUS_API_TOKEN and GENIUS_API_TOKEN != "YAHAN_APNA_GENIUS_TOKEN_PASTE_KARO":
            self.genius = lyricsgenius.Genius(GENIUS_API_TOKEN)
            self.genius.verbose = False # Logs band karne ke liye
            self.genius.remove_section_headers = True # [Chorus] wagera hatane ke liye

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
            return output_path

    def get_lyrics(self, song_name, artist_name):
        """Lyrics fetch karega, agar fail hua toh fallback dega"""
        if self.genius:
            try:
                # Search song
                song = self.genius.search_song(song_name, artist_name)
                if song:
                    # Lyrics ko clean karo aur lines me todo
                    lyrics = song.lyrics.split("\n")
                    # Starting ki faltu lines hatao (jo Genius credits hoti hain)
                    clean_lyrics = [l for l in lyrics if l.strip() and "Contributors" not in l]
                    return clean_lyrics[:20] # Sirf top 20 lines lo taaki GIF size na phate
            except Exception as e:
                print(f"Lyrics Error: {e}")
        
        # Fallback (Agar API nahi hai ya fail ho gayi)
        return [
            "Fetching Lyrics...",
            f"Now Playing: {song_name}",
            "Toxic Bots Music",
            "Feel the Rhythm 🎧",
            "Pure Bass Boost",
            "Stereo Sound",
            "Volume Up 🔊",
            "Vibe Check: Passed",
            "Live Streaming...",
            "Enjoy the Music ❤️"
        ]

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp_dl = f"cache/temp_{song.id}.jpg"
            output_gif = f"cache/{song.id}_live.gif"

            if os.path.exists(output_gif):
                return output_gif

            await self.save_thumb(temp_dl, song.thumbnail)

            # 1. LOAD & BLUR BACKGROUND (Smooth Gradient)
            original_art = Image.open(temp_dl).convert("RGBA")
            
            # Resize to Full HD
            base = original_art.resize((self.width, self.height), Image.Resampling.LANCZOS)
            # HEAVY Blur for smooth look
            base = base.filter(ImageFilter.GaussianBlur(radius=50))
            # Darken it (Overlay black layer)
            dark_overlay = Image.new("RGBA", base.size, (0, 0, 0, 140))
            base = Image.alpha_composite(base, dark_overlay)

            # 2. LEFT SIDE: ALBUM ART
            art_size = (380, 380)
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS)
            
            # Rounded Corners for Art
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=30, fill=255)
            
            # Draw Art on Base
            art_x, art_y = 80, 100
            base.paste(art, (art_x, art_y), mask)

            # 3. TEXT INFO (Left Side)
            draw_static = ImageDraw.Draw(base)
            
            text_x = art_x
            text_y = art_y + 400
            
            # Title
            title_text = song.title
            if len(title_text) > 20: title_text = title_text[:20] + "..."
            draw_static.text((text_x, text_y), title_text, font=self.font_title, fill=self.color_white)

            # Branding
            draw_static.text((text_x, text_y + 60), "Toxic Bots", font=self.font_artist, fill=self.color_accent)

            # Duration (Simple Text, No Ugly Box)
            draw_static.text((text_x, text_y + 110), "00:00  /  03:45", font=self.font_small, fill=self.color_grey)

            # Vertical Separator Line
            draw_static.line([(550, 80), (550, 640)], fill=(255, 255, 255, 80), width=2)

            # 4. PREPARE LYRICS
            # Song name se lyrics nikalo
            lyrics_list = self.get_lyrics(song.title, "Unknown")
            
            frames = []
            total_frames = 15  # Total animation frames
            
            # =========================
            # 🎬 ANIMATION LOOP
            # =========================
            # Lyrics area coordinates
            lyric_x = 600
            lyric_start_y = 600 # Start from bottom
            
            for i in range(total_frames):
                frame = base.copy()
                draw = ImageDraw.Draw(frame)
                
                # Header for Lyrics
                draw.text((lyric_x, 80), "Lyrics", font=self.font_small, fill=self.color_primary)

                # Scroll Logic: Move text up by 'i * speed'
                scroll_offset = i * 20 
                
                # Draw Lyrics Line by Line
                current_y = 200 - scroll_offset # Initial Y position
                
                for line in lyrics_list:
                    # Fade Effect logic based on Y position
                    # Center (approx 360) should be bright, Top/Bottom faded
                    if 250 < current_y < 450:
                        fill_color = (255, 255, 255, 255) # Bright White
                    else:
                        fill_color = (255, 255, 255, 100) # Dimmed
                    
                    # Draw only if within bounds (Performance optimization)
                    if 50 < current_y < 680:
                        draw.text((lyric_x, current_y), line, font=self.font_lyrics, fill=fill_color)
                    
                    current_y += 70 # Line spacing

                frames.append(frame)

            # Save GIF
            frames[0].save(
                output_gif,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=150,
                loop=0
            )

            if os.path.exists(temp_dl):
                os.remove(temp_dl)

            return output_gif

        except Exception as e:
            print(f"Thumbnail Error: {e}")
            return config.DEFAULT_THUMB
            
