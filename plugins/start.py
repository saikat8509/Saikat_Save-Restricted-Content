import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UsernameNotOccupied, OSError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, ERROR_MESSAGE, TARGET_CHANNEL
from database.db import db
from plugins.strings import HELP_TXT

class BatchTemp:
    IS_BATCH = {}

async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Downloaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Uploaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url="https://t.me/kingvj01")
    ],[
        InlineKeyboardButton('🔍 Support Group', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 Update Channel', url='https://t.me/vj_botz')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id,
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot. I forward restricted content to your channel using post links.\n\nLogin with /login to access private channels.\n\nLearn more with /help.</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id,
        text=HELP_TXT
    )

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    BatchTemp.IS_BATCH[message.from_user.id] = True
    await client.send_message(
        chat_id=message.chat.id,
        text="**Batch Processing Cancelled.**"
    )

@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    if not TARGET_CHANNEL:
        await message.reply("**Error: TARGET_CHANNEL not configured.**")
        return
    if "https://t.me/" not in message.text:
        await message.reply("**Invalid link. Use: https://t.me/c/xxxx/123 or https://t.me/c/xxxx/123-125**")
        return
    if BatchTemp.IS_BATCH.get(message.from_user.id, True) == False:
        await message.reply("**One task is processing. Use /cancel to stop it.**")
        return
    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    try:
        fromID = int(temp[0].strip())
        toID = int(temp[1].strip()) if len(temp) > 1 else fromID
    except:
        await message.reply("**Invalid link format.**")
        return
    BatchTemp.IS_BATCH[message.from_user.id] = False
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await message.reply("**Please /login to access restricted content.**")
        BatchTemp.IS_BATCH[message.from_user.id] = True
        return
    try:
        acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
        await acc.connect()
    except Exception as e:
        await message.reply(f"**Session expired. Error: {e}. Use /logout and /login again.**")
        BatchTemp.IS_BATCH[message.from_user.id] = True
        return
    for msgid in range(fromID, toID + 1):
        if BatchTemp.IS_BATCH.get(message.from_user.id, False):
            break
        if "https://t.me/c/" in message.text:
            chatid = int("-100" + datas[4])
            await handle_private(client, acc, message, chatid, msgid)
        elif "https://t.me/b/" in message.text:
            username = datas[4]
            await handle_private(client, acc, message, username, msgid)
        else:
            username = datas[3]
            try:
                msg = await client.get_messages(username, msgid)
                await client.copy_message(TARGET_CHANNEL, msg.chat.id, msg.id, disable_notification=True)
                await db.save_file(msg, TARGET_CHANNEL, msgid)  # Save to DB
            except UsernameNotOccupied:
                await client.send_message(message.chat.id, "Username not found.")
            except Exception as e:
                await handle_private(client, acc, message, username, msgid)
        await asyncio.sleep(3)
    BatchTemp.IS_BATCH[message.from_user.id] = True

async def handle_private(client: Client, acc, message: Message, chatid, msgid: int):
    for attempt in range(3):
        try:
            msg = await acc.get_messages(chatid, msgid)
            if msg.empty:
                return
            msg_type = get_message_type(msg)
            if not msg_type:
                return
            chat = TARGET_CHANNEL
            if BatchTemp.IS_BATCH.get(message.from_user.id):
                return
            if "Text" == msg_type:
                await client.send_message(chat, msg.text, entities=msg.entities, disable_notification=True, parse_mode=enums.ParseMode.HTML)
                await db.save_file(msg, TARGET_CHANNEL, msgid)
                return
            smsg = await client.send_message(message.chat.id, '**Downloading**', reply_to_message_id=message.id)
            asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id))
            try:
                file = await acc.download_media(
                    msg, progress=progress, progress_args=[message, "down"],
                    block=False, file_name=f"download_{msgid}.tmp"
                )
                os.remove(f'{message.id}downstatus.txt')
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error: {e}")
                await smsg.delete()
                return
            if BatchTemp.IS_BATCH.get(message.from_user.id):
                return
            asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id))
            caption = msg.caption if msg.caption else None
            if "Document" == msg_type:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
                await client.send_document(chat, file, thumb=ph_path, caption=caption, disable_notification=True, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
                if ph_path:
                    os.remove(ph_path)
            elif "Video" == msg_type:
                ph_path = await acc.download_media(msg.video.thumbs[0].file_id) if msg.video.thumbs else None
                await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, disable_notification=True, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
                if ph_path:
                    os.remove(ph_path)
            elif "Animation" == msg_type:
                await client.send_animation(chat, file, disable_notification=True, parse_mode=enums.ParseMode.HTML)
            elif "Sticker" == msg_type:
                await client.send_sticker(chat, file, disable_notification=True, parse_mode=enums.ParseMode.HTML)
            elif "Voice" == msg_type:
                await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, disable_notification=True, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
            elif "Audio" == msg_type:
                ph_path = await acc.download_media(msg.audio.thumbs[0].file_id) if msg.audio.thumbs else None
                await client.send_audio(chat, file, thumb=ph_path, caption=caption, disable_notification=True, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
                if ph_path:
                    os.remove(ph_path)
            elif "Photo" == msg_type:
                await client.send_photo(chat, file, caption=caption, disable_notification=True, parse_mode=enums.ParseMode.HTML)
            await db.save_file(msg, TARGET_CHANNEL, msgid)  # Save to DB
            if os.path.exists(f'{message.id}upstatus.txt'):
                os.remove(f'{message.id}upstatus.txt')
                os.remove(file)
            await client.delete_messages(message.chat.id, [smsg.id])
            break
        except (OSError, FloodWait) as e:
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
            if attempt == 2:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error after retries: {e}")
                break
            await asyncio.sleep(2 ** attempt)

def get_message_type(msg):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass
    try:
        msg.text
        return "Text"
    except:
        pass
