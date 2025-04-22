import re
import logging
from datetime import datetime
from hikkatl.types import Message
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamDMSecure(loader.Module):
    """Улучшенный антиспам для ЛС с логами в чат"""

    strings = {
        "name": "AntiSpamDMSecure",
        "banned": "🚨 <b>Вы были заблокированы!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки</b>\n\n"
            "👤 <b>Пользователь:</b> {user}\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "⏰ <b>Время:</b> {time}\n"
            "🔞 <b>Причина:</b> {reason}\n"
            "📝 <b>Сообщение:</b> <code>{msg}</code>"
        ),
        "chat_error": "❌ Не удалось отправить лог",
        "not_connected": "⚠️ Чат для логов не подключен"
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
        await self.connect_log_chat()

    async def connect_log_chat(self):
        """Подключаемся к чату для логов"""
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info(f"Успешно подключен чат для логов: {self._log_chat.title}")
        except Exception as e:
            logger.error(f"Ошибка подключения к чату: {e}")
            self._log_chat = None

    async def detect_triggers(self, message: Message) -> str:
        text = (message.text or "").lower()
        triggers = {
            "Порнография": r"порно|porn|xxx|onlyfans|секс|🔞|🍑|nude",
            "Реклама": r"подпишись|канал|купить|реклама|@[a-z0-9_]{5,}|t\.me/",
            "Вредоносное": r"bit\.ly|скачать бесплатно|\.exe|\.js|вирус|взлом"
        }
        for reason, pattern in triggers.items():
            if re.search(pattern, text, re.IGNORECASE):
                return reason
        return None

    async def process_ban(self, message: Message, reason: str):
        """Обработка бана и логирования"""
        user = await message.get_sender()
        
        try:
            # Блокировка пользователя
            if self.config["ban_users"]:
                await self.client(
                    functions.contacts.BlockRequest(id=user.id)
                )
            
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
                            msg=utils.escape_html(message.text[:200] if message.text else "Файл/медиа")
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки лога: {e}")
                    await utils.answer(message, self.strings("chat_error"))
            else:
                await utils.answer(message, self.strings("not_connected"))

            await utils.answer(message, self.strings("banned").format(reason=reason))
            self._ban_count += 1

        except Exception as e:
            logger.error(f"Ошибка при обработке бана: {e}")

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_triggers(message):
            await self.process_ban(message, reason)

    async def asdstatcmd(self, message: Message):
        """Показать статистику работы"""
        status = (
            "🔧 <b>AntiSpamDMSecure Status</b>\n\n"
            f"• Чат логов: {'✅ ' + self._log_chat.title if self._log_chat else '❌ Не подключен'}\n"
            f"• Всего забанено: {self._ban_count}\n"
            f"• Автобан: {'Вкл' if self.config['ban_users'] else 'Выкл'}\n"
            f"• Удаление сообщений: {'Вкл' if self.config['delete_messages'] else 'Выкл'}"
        )
        await utils.answer(message, status)
