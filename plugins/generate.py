from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid
from config import API_ID, API_HASH
from database.db import db

@Client.on_message(filters.private & filters.command(["logout"]))
async def logout(client, message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await message.reply("**You are not logged in.**")
        return
    await db.set_session(message.from_user.id, session=None)
    await message.reply("**Logged out successfully.**")

@Client.on_message(filters.private & filters.command(["login"]))
async def login(bot: Client, message: Message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is not None:
        await message.reply("**Already logged in. Use /logout first.**")
        return
    user_id = message.from_user.id
    phone_number_msg = await bot.ask(user_id, "<b>Send your phone number (with country code, e.g., +1234567890).</b>\nUse /cancel to stop.")
    if phone_number_msg.text == '/cancel':
        return await phone_number_msg.reply("**Process cancelled.**")
    phone_number = phone_number_msg.text
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    await phone_number_msg.reply("Sending OTP...")
    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "Enter the OTP (e.g., for 12345, send 1 2 3 4 5).\nUse /cancel to stop.", filters=filters.text, timeout=600)
    except PhoneNumberInvalid:
        await phone_number_msg.reply("**Invalid phone number.**")
        return
    if phone_code_msg.text == '/cancel':
        return await phone_code_msg.reply("**Process cancelled.**")
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await phone_code_msg.reply("**Invalid OTP.**")
        return
    except PhoneCodeExpired:
        await phone_code_msg.reply("**OTP expired.**")
        return
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, "**Enter your two-step verification password.**\nUse /cancel to stop.", filters=filters.text, timeout=300)
        if two_step_msg.text == '/cancel':
            return await two_step_msg.reply("**Process cancelled.**")
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply("**Invalid password.**")
            return
    string_session = await client.export_session_string()
    await client.disconnect()
    await db.set_session(message.from_user.id, string_session)
    await bot.send_message(user_id, "**Login successful. You can now forward restricted content.**")
