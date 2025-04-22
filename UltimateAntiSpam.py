import re
import logging
from datetime import datetime
from hikkatl.types import Message, PeerUser
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamNuclear(loader.Module):
    """Антиспам с полной зачисткой переписки"""

    strings = {
        "name": "AntiSpamNuclear",
        "banned": "🚨 <b>Вы заблокированы!</b>\nПричина: {reason}\nПереписка удалена!",
        "log_msg": (
            "💥 <b>Полная зачистка</b>\n\n"
            "👤 Пользователь: {user}\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "🗑 Удалено сообщений: ~{msg_count}"
        ),
        "chat_error": "❌ Не удалось отправить лог",
        "user_error": "⚠️ Не удалось получить данные пользователя"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить",
            "delete_history", True, "Удалять историю переписки",
            "report_to_chat", True, "Отправлять отчет в чат"
        )
        self._ban_count = 0

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info("Чат для логов подключен: %s", self._log_chat.title)
        except Exception as e:
            logger.error("Ошибка подключения чата: %s", e)
            self._log_chat = None

    async def nuclear_cleanup(self, user_id: int):
        """Полная зачистка переписки"""
        try:
            await self.client(functions.messages.DeleteHistoryRequest(
                peer=PeerUser(user_id),
                max_id=0,
                revoke=True
            ))
            return True
        except Exception as e:
            logger.error("Ошибка удаления истории: %s", e)
            return False

    async def get_user_info(self, message: Message):
        """Безопасное получение информации о пользователе"""
        try:
            return await message.get_sender()
        except:
            return types.User(
                id=message.sender_id,
                first_name="Unknown",
                last_name="",
                deleted=True
            )

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
        user = await self.get_user_info(message)
        msg_count = "много"  # Примерное количество, т.к. точное узнать сложно
        
        try:
            # 1. Блокировка
            if self.config["ban_users"]:
                await self.client(functions.contacts.BlockRequest(id=user.id))
            
            # 2. Удаление всей истории
            if self.config["delete_history"]:
                if await self.nuclear_cleanup(user.id):
                    msg_count = "все"
            
            # 3. Отправка отчета
            if self.config["report_to_chat"] and hasattr(self, '_log_chat') and self._log_chat:
                try:
                    await self.client.send_message(
                        self._log_chat,
                        self.strings("log_msg").format(
                            user=utils.escape_html(getattr(user, 'first_name', 'Unknown')),
                            user_id=user.id,
                            time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            reason=reason,
                            msg_count=msg_count
                        )
                    )
                except Exception as e:
                    logger.error("Ошибка отправки лога: %s", e)
            
            # 4. Уведомление пользователю
            await utils.answer(message, self.strings("banned").format(reason=reason))
            self._ban_count += 1
            
        except Exception as e:
            logger.error("Критическая ошибка: %s", e)

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_triggers(message):
            await self.process_ban(message, reason)

    async def nstatcmd(self, message: Message):
        """Показать статус модуля"""
        status = (
            "☢️ <b>AntiSpamNuclear Status</b>\n\n"
            f"• Чат логов: {'✅ ' + self._log_chat.title if hasattr(self, '_log_chat') and self._log_chat else '❌ Нет'}\n"
            f"• Забанено: {self._ban_count}\n"
            f"• Автобан: {'✅ Вкл' if self.config['ban_users'] else '❌ Выкл'}\n"
            f"• Зачистка: {'✅ Вкл' if self.config['delete_history'] else '❌ Выкл'}"
        )
        await utils.answer(message, status)
