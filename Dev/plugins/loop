from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Dev import app, lang


# ================= LOOP STORAGE =================
# chat_id : loop_count
loop_db = {}


async def get_loop(chat_id: int) -> int:
    return loop_db.get(chat_id, 0)


async def set_loop(chat_id: int, count: int):
    loop_db[chat_id] = max(0, int(count))


# ================= CLOSE MARKUP =================
def close_markup():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Close", callback_data="loop_close")]]
    )


@app.on_callback_query(filters.regex("^loop_close$"))
async def close_cb(_, q: CallbackQuery):
    try:
        await q.message.delete()
    except Exception:
        await q.answer("Can't close.", show_alert=True)


# ================= LOOP COMMAND =================
@app.on_message(filters.command(["loop", "cloop"]) & filters.group & ~app.bl_users)
@lang.language()
async def loop_cmd(_, m: types.Message):
    usage = (
        "**Loop Usage:**\n\n"
        "`/loop 1-10` → repeat current song\n"
        "`/loop enable` → max loop\n"
        "`/loop disable` → stop loop"
    )

    if len(m.command) != 2:
        return await m.reply_text(usage, reply_markup=close_markup())

    arg = m.command[1].lower().strip()
    chat_id = m.chat.id
    user = m.from_user.mention

    # 🔢 numeric loop
    if arg.isdigit():
        count = int(arg)
        if not 1 <= count <= 10:
            return await m.reply_text(
                "❌ Loop value must be between **1 – 10**",
                reply_markup=close_markup(),
            )

        await set_loop(chat_id, count)
        return await m.reply_text(
            f"🔁 Loop set to **{count}**\nBy {user}",
            reply_markup=close_markup(),
        )

    # ✅ enable loop
    if arg == "enable":
        await set_loop(chat_id, 10)
        return await m.reply_text(
            f"✅ Loop **enabled**\nBy {user}",
            reply_markup=close_markup(),
        )

    # 🛑 disable loop
    if arg == "disable":
        await set_loop(chat_id, 0)
        return await m.reply_text(
            f"🛑 Loop **disabled**\nBy {user}",
            reply_markup=close_markup(),
        )

    return await m.reply_text(usage, reply_markup=close_markup())
