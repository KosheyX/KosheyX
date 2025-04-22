from .. import loader, utils
from telethon.tl.types import Message, UserStatusOffline, UserStatusRecently
import time
import logging

logger = logging.getLogger(__name__)

@loader.tds
class SmartAutoResponderMod(loader.Module):
    """Умный автоответчик с таймерами"""
    strings = {
        "name": "SmartAutoResponder",
        "config_ar_text": "Текст автоответа",
        "config_ar_users": "ID пользователей (через запятую, 0 для всех)",
        "status_on": "✅ Автоответчик активен\nТекст: {}\nПользователи: {}",
        "status_off": "❌ Автоответчик неактивен\nТекст: {}\nПользователи: {}",
        "no_text": "⚠️ Текст автоответа не задан!",
        "args_error": "⚠️ Используйте: .ar <on/off> или .ar <текст>",
        "cooldown": "⏳ Автоответчик приостановлен на 30 минут (пользователь ответил)"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
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
        self.active = False
        self.cooldowns = {}  # {user_id: timestamp}

    async def client_ready(self, client, db):
        self._client = client

    async def arcmd(self, message: Message):
        """Управление автоответчиком. Используйте: .ar <on/off> или .ar <текст>"""
        args = utils.get_args_raw(message)
        
        if not args:
            status = self.strings["status_on"] if self.active else self.strings["status_off"]
            users = self.config["ar_users"] if self.config["ar_users"] != "0" else "все"
            await utils.answer(message, status.format(self.config["ar_text"], users))
            return
        
        if args.lower() in ["on", "вкл"]:
            if not self.config["ar_text"]:
                await utils.answer(message, self.strings["no_text"])
                return
            self.active = True
            await utils.answer(message, "✅ Автоответчик активирован")
        elif args.lower() in ["off", "выкл"]:
            self.active = False
            await utils.answer(message, "❌ Автоответчик деактивирован")
        else:
            self.config["ar_text"] = args
            await utils.answer(message, f"✅ Текст автоответа установлен: {args}")

    async def watcher(self, message: Message):
        if not isinstance(message, Message) or not self.active or not self.config["ar_text"]:
            return
        
        me = await message.client.get_me()
        if message.sender_id == me.id:
            return  # Игнорируем свои сообщения
        
        users = self.config["ar_users"]
        if users != "0" and str(message.sender_id) not in users.split(","):
            return  # Ответ только указанным пользователям
        
        if message.out:
            return  # Игнорируем исходящие сообщения
        
        # Проверяем статус пользователя
        user = await message.client.get_entity(message.sender_id)
        if isinstance(user.status, (UserStatusOffline, UserStatusRecently)):
            # Проверяем кд
            now = time.time()
            if message.sender_id in self.cooldowns:
                if now - self.cooldowns[message.sender_id] < 1800:  # 30 минут
                    return
                del self.cooldowns[message.sender_id]
            
            # Отправляем автоответ
            await message.reply(self.config["ar_text"])
            await message.client.send_read_acknowledge(message.chat_id)
    
    async def on_message(self, message: Message):
        """Отслеживаем ответы пользователя"""
        if not isinstance(message, Message) or not self.active:
            return
        
        # Если это ответ на наше сообщение (автоответ)
        if message.is_reply:
            replied = await message.get_reply_message()
            if replied.sender_id == (await message.client.get_me()).id:
                # Запоминаем время ответа пользователя
                self.cooldowns[message.sender_id] = time.time()
                logger.debug(f"User {message.sender_id} replied, cooldown started")
                
                # Уведомляем о паузе
                if message.sender_id not in self.cooldowns:
                    await message.reply(self.strings["cooldown"])
