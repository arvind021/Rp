import os
import re
import yt_dlp
import asyncio
from pathlib import Path
from typing import Optional, Union

from pyrogram import enums, types
from py_yt import Playlist, VideosSearch

from Dev import logger
from Dev.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Union[str, None]:
        messages = [message_1]
        link = None
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            text = message.text or message.caption or ""

            if message.entities:
                for entity in message.entities:
                    if entity.type == enums.MessageEntityType.URL:
                        link = text[entity.offset : entity.offset + entity.length]
                        break

            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == enums.MessageEntityType.TEXT_LINK:
                        link = entity.url
                        break

        if link:
            return link.split("&si")[0].split("?si")[0]
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        _search = VideosSearch(query, limit=1)
        results = await _search.next()
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> Optional[str]:
        url = self.base + video_id
        
        # Check existing files blindly to save time
        if video:
            if Path(f"downloads/{video_id}.mp4").exists():
                return f"downloads/{video_id}.mp4"
        else:
            # Audio check order
            for ext in ["m4a", "webm", "mp3"]:
                if Path(f"downloads/{video_id}.{ext}").exists():
                    return f"downloads/{video_id}.{ext}"

        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True, # Prevents crash on minor errors
            # BYPASS CONFIGURATION: Using iOS client to avoid "Sign in" error
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios"], 
                    "skip": ["dash", "hls"],
                }
            },
            # Spoofing User Agent
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            }
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                # Force m4a/aac for speed and compatibility, fallback to best available
                "format": "bestaudio[ext=m4a]/bestaudio/best",
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        return None
                    return ydl.prepare_filename(info)
                except Exception as ex:
                    # Log only critical errors, avoid spamming console
                    logger.error(f"Download Error for {video_id}: {ex}")
                    return None

        return await asyncio.to_thread(_download)
        
