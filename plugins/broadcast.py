from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked
from database.db import db
from config import ADMINS
import asyncio
import datetime
import time

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(user_id)
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(user_id)
        return False, "Blocked"
    except Exception:
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply("**Reply to a message to broadcast.**")
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply("Broadcasting...")
    start_time = time.time()
    total_users = await db.total_users_count()
    done = success = blocked = deleted = failed = 0
    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif sh == "Blocked":
                blocked += 1
            elif sh == "Deleted":
                deleted += 1
            else:
                failed += 1
            done += 1
            if done % 20 == 0:
                await sts.edit(f"Broadcast in progress:\nTotal: {total_users}\nDone: {done}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")
        else:
            done += 1
            failed += 1
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(f"Broadcast Complete:\nTime: {time_taken}\nTotal: {total_users}\nDone: {done}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")
