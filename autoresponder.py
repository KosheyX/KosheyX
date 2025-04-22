from .. import loader, utils
from telethon.tl.types import Message
import logging

logger = logging.getLogger(__name__)

@loader.tds
class AutoResponderMod(loader.Module):
    """Автоответчик с настройками"""
    strings = {
        "name": "AutoResponder",
        "config_ar_enabled": "Включен ли автоответчик",
        "config_ar_text": "Текст автоответа",
        "config_ar_users": "ID пользователей (через запятую, 0 для всех)",
        "status_on": "✅ Автоответчик включен\nТекст: {}\nПользователи: {}",
        "status_off": "❌ Автоответчик выключен\nТекст: {}\nПользователи: {}",
        "no_text": "⚠️ Текст автоответа не задан!",
        "args_error": "⚠️ Используйте: .ar <on/off> или .ar <текст>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ar_enabled",
                False,
                lambda: self.strings["config_ar_enabled"],
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "ar_text",
                "Привет! Я сейчас не доступен, отвечу позже.",
                lambda: self.strings["config_ar_text"],
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "ar_users",
                "0",
                lambda: self.strings["config_ar_users"],
                validator=loader.validators.String()
            ),
        )

    async def client_ready(self, client, db):
        self._client = client

    async def arcmd(self, message: Message):
        """Управление автоответчиком. Используйте: .ar <on/off> или .ar <текст>"""
        args = utils.get_args_raw(message)
        
        if not args:
            status = self.strings["status_on"] if self.config["ar_enabled"] else self.strings["status_off"]
            users = self.config["ar_users"] if self.config["ar_users"] != "0" else "все"
            await utils.answer(message, status.format(self.config["ar_text"], users))
            return
        
        if args.lower() in ["on", "вкл"]:
            if not self.config["ar_text"]:
                await utils.answer(message, self.strings["no_text"])
                return
            self.config["ar_enabled"] = True
            await utils.answer(message, "✅ Автоответчик включен")
        elif args.lower() in ["off", "выкл"]:
            self.config["ar_enabled"] = False
            await utils.answer(message, "❌ Автоответчик выключен")
        else:
            self.config["ar_text"] = args
            await utils.answer(message, f"✅ Текст автоответа установлен: {args}")

    async def watcher(self, message: Message):
        if not isinstance(message, Message) or not self.config["ar_enabled"] or not self.config["ar_text"]:
            return
        
        if message.sender_id == (await message.client.get_me()).id:
            return  # Игнорируем свои сообщения
        
        users = self.config["ar_users"]
        if users != "0" and str(message.sender_id) not in users.split(","):
            return  # Ответ только указанным пользователям
        
        if message.out:
            return  # Игнорируем исходящие сообщения
        
        await message.reply(self.config["ar_text"])
        await message.client.send_read_acknowledge(message.chat_id)
