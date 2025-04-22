import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamStable(loader.Module):
    """Стабильный антиспам с полной обработкой ошибок блокировки"""

    strings = {
        "name": "AntiSpamStable",
        "banned": "🚨 <b>Блокировка выполнена!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки</b>\n\n"
            "👤 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "📝 Сообщение: <code>{msg}</code>"
        ),
        "already_banned": "ℹ️ Пользователь уже был заблокирован ранее",
        "history_cleared": "🗑️ История переписки очищена"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Блокировать пользователей",
            "delete_messages", True, "Удалять сообщения",
            "delete_history", True, "Удалять историю переписки",
            "report_to_chat", True, "Отправлять отчеты"
        )
        self._ban_count = 0

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info("Чат для логов успешно подключен")
        except Exception as e:
            logger.error("Ошибка подключения чата: %s", e)
            self._log_chat = None

    async def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        try:
            blocked = await self.client(functions.contacts.GetBlockedRequest(
                offset=0,
                limit=100
            ))
            return any(user_id == user.id for user in blocked.blocked)
        except Exception as e:
            logger.error("Ошибка проверки блокировки: %s", e)
            return False

    async def safe_block_user(self, user_id: int):
        """Безопасная блокировка с обработкой ошибок"""
        try:
            if await self.is_user_blocked(user_id):
                return False, "already_blocked"
            
            await self.client(functions.contacts.BlockRequest(id=user_id))
            return True, "success"
        except Exception as e:
            logger.error("Ошибка при блокировке: %s", e)
            return False, str(e)

    async def safe_delete_history(self, user_id: int):
        """Безопасное удаление истории переписки"""
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

    async def process_spam(self, message: Message, reason: str):
        user_id = message.sender_id
        response_lines = []
        
        # 1. Блокировка пользователя
        if self.config["ban_users"]:
            success, status = await self.safe_block_user(user_id)
            if not success:
                if status == "already_blocked":
                    response_lines.append(self.strings["already_banned"])
        
        # 2. Удаление текущего сообщения
        if self.config["delete_messages"]:
            try:
                await message.delete()
            except:
                pass
        
        # 3. Удаление истории переписки
        if self.config["delete_history"]:
            if await self.safe_delete_history(user_id):
                response_lines.append(self.strings["history_cleared"])
        
        # 4. Отправка отчета
        if self.config["report_to_chat"] and self._log_chat:
            try:
                await self.client.send_message(
                    self._log_chat,
                    self.strings["log_msg"].format(
                        user_id=user_id,
                        time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                        reason=reason,
                        msg=utils.escape_html((message.text or "")[:200])
                    )
                )
            except Exception as e:
                logger.error("Ошибка отправки отчета: %s", e)
        
        # 5. Финалное уведомление
        response_lines.append(self.strings["banned"].format(reason=reason))
        await utils.answer(message, "\n".join(response_lines))
        self._ban_count += 1

    async def detect_spam(self, message: Message) -> str:
        text = (message.text or "").lower()
        patterns = {
            "Порнография": r"порно|porn|xxx|onlyfans|секс|🔞",
            "Реклама": r"подпишись|канал|купить|реклама",
            "Вредоносное": r"bit\.ly|скачать|\.exe|вирус"
        }
        for reason, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return reason
        return None

    async def watcher(self, message: Message):
        if not message.is_private or message.out:
            return
            
        if reason := await self.detect_spam(message):
            await self.process_spam(message, reason)

    async def assstatcmd(self, message: Message):
        """Показать статистику работы"""
        stats = (
            "📊 <b>Статистика AntiSpamStable</b>\n\n"
            f"• Всего заблокировано: {self._ban_count}\n"
            f"• Автоблокировка: {'✅ Вкл' if self.config['ban_users'] else '❌ Выкл'}\n"
            f"• Удаление истории: {'✅ Вкл' if self.config['delete_history'] else '❌ Выкл'}\n"
            f"• Отчеты: {'✅ Вкл' if self.config['report_to_chat'] else '❌ Выкл'}"
        )
        await utils.answer(message, stats)
