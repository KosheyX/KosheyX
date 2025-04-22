import re
import logging
from datetime import datetime
from hikkatl.types import Message
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamDMLogs(loader.Module):
    """Антиспам с логами в указанный чат"""

    strings = {
        "name": "AntiSpamDMLogs",
        "banned": "🚨 <b>Забанен в ЛС!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки в ЛС</b>\n\n"
            "👤 <b>Отправитель:</b> {user}\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "⏰ <b>Время:</b> {time}\n"
            "🔞 <b>Триггер:</b> {reason}\n"
            "📝 <b>Сообщение:</b> <code>{msg_preview}</code>"
        ),
        "chat_error": "❌ Не удалось отправить лог в чат",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить",
            "delete_messages", True, "Удалять сообщения",
        )
        self._log_chat_link = "https://t.me/+ve_fxQ6dYj9hOTJi"  # Жёстко прописан ваш чат

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await client.get_entity(self._log_chat_link)
            logger.success(f"Чат для логов подключен: {self._log_chat.title}")
        except Exception as e:
            logger.error(f"Ошибка подключения к чату: {e}")
            self._log_chat = None

    async def detect_triggers(self, message: Message) -> str:
        text = (message.text or "").lower()
        triggers = {
            "Порнография": r"порно|porn|xxx|onlyfans|секс|🔞|🍑|nude",
            "Реклама": r"подпишись|канал|купить|реклама|@[a-z0-9_]{5,}|t\.me/",
            "Вредоносное": r"bit\.ly|скачать бесплатно|\.exe|\.js|вирус"
        }
        for reason, pattern in triggers.items():
            if re.search(pattern, text, re.IGNORECASE):
                return reason
        return None

    async def ban_and_log(self, message: Message, reason: str):
        user = await message.get_sender()
        
        # Блокировка
        if self.config["ban_users"]:
            await self.client.edit_permissions(
                user.id,
                view_messages=False,
            )
        
        # Удаление сообщения
        if self.config["delete_messages"]:
            await message.delete()
        
        # Отправка лога в чат
        if self._log_chat:
            try:
                await self.client.send_message(
                    entity=self._log_chat,
                    message=self.strings("log_msg").format(
                        user=utils.escape_html(user.first_name),
                        user_id=user.id,
                        time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                        reason=reason,
                        msg_preview=utils.escape_html((message.text or "")[:100])
                    )
                )
            except Exception as e:
                logger.error(f"Ошибка отправки лога: {e}")
                await utils.answer(message, self.strings("chat_error"))

        await utils.answer(message, self.strings("banned").format(reason=reason))

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_triggers(message):
            await self.ban_and_log(message, reason)

    async def aspamcmd(self, message: Message):
        """Проверить статус модуля"""
        status = (
            "🔧 <b>AntiSpamDMLogs Status</b>\n\n"
            f"• Чат логов: {'✅ ' + self._log_chat.title if self._log_chat else '❌ Не подключен'}\n"
            f"• Всего забанено: {getattr(self, '_ban_count', 0)}"
        )
        await utils.answer(message, status)
