import asyncio
from pyrogram import filters
from Dev import app, db


@app.on_message(filters.command([]) & filters.group)
async def auto_cmd_delete(_, message):
    try:
        chat_id = message.chat.id

        # settings check
        if not await db.get_cmd_delete(chat_id):
            return

        # delay (seconds)
        await asyncio.sleep(5)

        await message.delete()

    except Exception:
        pass
