import motor.motor_asyncio
from config import DB_URI, DB_NAME

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db.users
        self.files = self.db.files

    def new_user(self, id, name):
        return {
            "id": id,
            "name": name,
            "session": None
        }

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.users.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.users.find_one({"id": int(id)})
        return bool(user)

    async def total_users_count(self):
        return await self.users.count_documents({})

    async def get_all_users(self):
        return self.users.find({})

    async def delete_user(self, user_id):
        await self.users.delete_many({"id": int(user_id)})

    async def set_session(self, id, session):
        await self.users.update_one({"id": int(id)}, {"$set": {"session": session}})

    async def get_session(self, id):
        user = await self.users.find_one({"id": int(id)})
        return user.get("session") if user else None

    async def save_file(self, msg, channel_id, message_id):
        file_data = {
            "channel_id": channel_id,
            "message_id": message_id,
            "type": self.get_message_type(msg),
            "caption": msg.caption if msg.caption else None,
            "file_id": self.get_file_id(msg),
            "timestamp": msg.date
        }
        await self.files.insert_one(file_data)

    def get_message_type(self, msg):
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

    def get_file_id(self, msg):
        try:
            return msg.document.file_id
        except:
            pass
        try:
            return msg.video.file_id
        except:
            pass
        try:
            return msg.animation.file_id
        except:
            pass
        try:
            return msg.sticker.file_id
        except:
            pass
        try:
            return msg.voice.file_id
        except:
            pass
        try:
            return msg.audio.file_id
        except:
            pass
        try:
            return msg.photo.file_id
        except:
            pass
        return None

db = Database(DB_URI, DB_NAME)
