import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UltimateAntiSpamFixed(loader.Module):
    """Исправленный антиспам модуль для ЛС"""

    strings = {
        "name": "UltimateAntiSpamFixed",
        "banned": "🚨 <b>Вы были заблокированы!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки в ЛС</b>\n\n"
            "👤 Пользователь: {user}\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "📝 Сообщение: <code>{msg}</code>"
        ),
        "chat_error": "❌ Не удалось отправить лог в чат",
        "setup_error": "⚠️ Чат для логов не настроен"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить",
            "delete_messages", True, "Удалять сообщения",
        )
        self._log_chat = None
        self._ban_count = 0

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info(f"Чат для логов подключен: {self._log_chat.title}")
        except Exception as e:
            logger.error(f"Ошибка подключения чата: {e}")
            self._log_chat = None

    async def detect_triggers(self, message: Message) -> str:
        text = (message.text or "").lower()
        triggers = {
            "Порнография": r"порно|porn|xxx|onlyfans|секс|🔞",
            "Реклама": r"подпишись|канал|купить|реклама",
            "Вредоносное": r"bit\.ly|скачать|\.exe|вирус"
        }
        for reason, pattern in triggers.items():
            if re.search(pattern, text, re.IGNORECASE):
                return reason
        return None

    async def process_ban(self, message: Message, reason: str):
        user = await message.get_sender()
        
        try:
            # Блокировка пользователя
            if self.config["ban_users"]:
                await self.client(functions.contacts.BlockRequest(id=user.id))
            
            # Удаление сообщения
            if self.config["delete_messages"]:
                await message.delete()
            
            # Отправка лога
            if self._log_chat:
                try:
                    await self.client.send_message(
                        entity=self._log_chat,
                        message=self.strings("log_msg").format(
                            user=utils.escape_html(user.first_name),
                            user_id=user.id,
                            time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            reason=reason,
                            msg=utils.escape_html((message.text or "")[:200])
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки лога: {e}")
                    await utils.answer(message, self.strings("chat_error"))
            else:
                await utils.answer(message, self.strings("setup_error"))

            await utils.answer(message, self.strings("banned").format(reason=reason))
            self._ban_count += 1

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_triggers(message):
            await self.process_ban(message, reason)

    async def uafstatcmd(self, message: Message):
        """Показать статус модуля"""
        status = (
            "🔧 <b>UltimateAntiSpamFixed Status</b>\n\n"
            f"• Чат логов: {'✅ ' + self._log_chat.title if self._log_chat else '❌ Не подключен'}\n"
            f"• Всего забанено: {self._ban_count}\n"
            f"• Автобан: {'✅ Вкл' if self.config['ban_users'] else '❌ Выкл'}\n"
            f"• Удаление сообщений: {'✅ Вкл' if self.config['delete_messages'] else '❌ Выкл'}"
        )
        await utils.answer(message, status)
