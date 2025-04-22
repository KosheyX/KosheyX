import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AntiSpamFinalSolution(loader.Module):
    """Финальное решение для антиспама с полной обработкой ошибок"""

    strings = {
        "name": "AntiSpamFinal",
        "banned": "🚨 <b>Блокировка завершена!</b>\nПричина: {reason}",
        "log_msg": (
            "🛡 <b>Лог блокировки</b>\n\n"
            "👤 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "📝 Сообщение: <code>{msg}</code>"
        ),
        "already_banned": "⚠️ Пользователь уже заблокирован",
        "history_cleared": "🗑️ Переписка удалена"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить",
            "delete_messages", True, "Удалять сообщения",
            "delete_history", True, "Удалять переписку",
            "report_to_chat", True, "Отправлять отчет"
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

    async def safe_block(self, user_id: int):
        """Безопасная блокировка с проверкой"""
        try:
            # Проверяем, не заблокирован ли уже пользователь
            result = await self.client(functions.contacts.GetBlockedRequest(
                offset=0,
                limit=100
            ))
            if any(user_id == user.id for user in result.blocked):
                return False, "already_banned"
            
            await self.client(functions.contacts.BlockRequest(id=user_id))
            return True, "success"
        except Exception as e:
            logger.error("Ошибка блокировки: %s", e)
            return False, str(e)

    async def safe_delete_history(self, user_id: int):
        """Безопасное удаление истории"""
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
        response_msg = ""
        
        try:
            # 1. Блокировка пользователя
            if self.config["ban_users"]:
                success, status = await self.safe_block(user_id)
                if not success:
                    response_msg += self.strings["already_banned"] + "\n" if status == "already_banned" else ""
            
            # 2. Удаление текущего сообщения
            if self.config["delete_messages"]:
                try:
                    await message.delete()
                except:
                    pass
            
            # 3. Удаление всей истории
            if self.config["delete_history"]:
                if await self.safe_delete_history(user_id):
                    response_msg += self.strings["history_cleared"] + "\n"
            
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
                    logger.error("Ошибка отправки лога: %s", e)
            
            # 5. Финалное уведомление
            response_msg += self.strings["banned"].format(reason=reason)
            await utils.answer(message, response_msg)
            self._ban_count += 1
            
        except Exception as e:
            logger.error("Критическая ошибка обработки: %s", e)

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

    async def afstatcmd(self, message: Message):
        """Показать статус модуля"""
        status = (
            "🔧 <b>AntiSpamFinal Status</b>\n\n"
            f"• Забанено: {self._ban_count}\n"
            f"• Автобан: {'✅ Вкл' if self.config['ban_users'] else '❌ Выкл'}\n"
            f"• Удаление переписки: {'✅ Вкл' if self.config['delete_history'] else '❌ Выкл'}\n"
            f"• Отчеты: {'✅ Вкл' if self.config['report_to_chat'] else '❌ Выкл'}"
        )
        await utils.answer(message, status)
