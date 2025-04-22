import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamUltimate(loader.Module):
    """Антиспам с полной обработкой ошибок"""

    strings = {
        "name": "AntiSpamUltimate",
        "banned": "🚨 <b>Вы заблокированы!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки</b>\n\n"
            "👤 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "📝 Сообщение: <code>{msg}</code>"
        ),
        "chat_error": "❌ Не удалось отправить лог",
        "user_error": "⚠️ Пользователь не найден"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить",
            "delete_messages", True, "Удалять сообщения",
            "delete_history", True, "Удалять переписку"
        )
        self._ban_count = 0

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info("Чат для логов подключен")
        except Exception as e:
            logger.error("Ошибка подключения чата: %s", e)
            self._log_chat = None

    async def safe_get_user(self, user_id: int):
        """Безопасное получение пользователя"""
        try:
            return await self.client.get_entity(types.PeerUser(user_id))
        except:
            return types.User(
                id=user_id,
                first_name="Unknown",
                last_name="",
                username=None,
                phone=None,
                bot=False,
                verified=False,
                restricted=False,
                deleted=True
            )

    async def delete_all_messages(self, user_id: int):
        """Удаление всей переписки"""
        try:
            await self.client(functions.messages.DeleteHistoryRequest(
                peer=user_id,
                max_id=0,
                revoke=True
            ))
            return True
        except Exception as e:
            logger.error("Ошибка удаления истории: %s", e)
            return False

    async def process_ban(self, message: Message, reason: str):
        user_id = message.sender_id
        user = await self.safe_get_user(user_id)
        
        try:
            # 1. Блокировка
            if self.config["ban_users"]:
                try:
                    await self.client(functions.contacts.BlockRequest(id=user_id))
                except Exception as e:
                    logger.error("Ошибка блокировки: %s", e)
                    await utils.answer(message, self.strings("user_error"))
                    return
            
            # 2. Удаление сообщения
            if self.config["delete_messages"]:
                await message.delete()
            
            # 3. Удаление истории
            if self.config["delete_history"]:
                await self.delete_all_messages(user_id)
            
            # 4. Отправка лога
            if hasattr(self, '_log_chat') and self._log_chat:
                try:
                    await self.client.send_message(
                        self._log_chat,
                        self.strings("log_msg").format(
                            user_id=user_id,
                            time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            reason=reason,
                            msg=utils.escape_html((message.text or "")[:200])
                        )
                    )
                except Exception as e:
                    logger.error("Ошибка отправки лога: %s", e)
            
            await utils.answer(message, self.strings("banned").format(reason=reason))
            self._ban_count += 1
            
        except Exception as e:
            logger.error("Критическая ошибка: %s", e)

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

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_triggers(message):
            await self.process_ban(message, reason)

    async def austatcmd(self, message: Message):
        """Показать статус модуля"""
        status = (
            "🔧 <b>AntiSpamUltimate Status</b>\n\n"
            f"• Чат логов: {'✅ Настроен' if hasattr(self, '_log_chat') and self._log_chat else '❌ Нет'}\n"
            f"• Забанено: {self._ban_count}\n"
            f"• Автобан: {'✅ Вкл' if self.config['ban_users'] else '❌ Выкл'}\n"
            f"• Удаление переписки: {'✅ Вкл' if self.config['delete_history'] else '❌ Выкл'}"
        )
        await utils.answer(message, status)
