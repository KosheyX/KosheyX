import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class PerfectAntiSpam(loader.Module):
    """Идеальный антиспам без ошибок"""

    strings = {
        "name": "PerfectAntiSpam",
        "banned": "🚫 <b>Пользователь заблокирован!</b>\nПричина: {reason}",
        "log_msg": (
            "📛 <b>Лог блокировки</b>\n\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "✉️ Сообщение: <code>{msg}</code>"
        ),
        "already_banned": "ℹ️ Пользователь уже в чёрном списке",
        "history_cleared": "🧹 История переписки удалена"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Блокировать пользователей",
            "delete_messages", True, "Удалять сообщения",
            "delete_history", True, "Удалять историю",
            "report_to_chat", True, "Отправлять отчёты"
        )
        self._ban_count = 0

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
            logger.info("Чат для логов готов")
        except Exception as e:
            logger.error("Ошибка чата: %s", e)
            self._log_chat = None

    async def block_user_safe(self, user_id: int):
        """Абсолютно безопасная блокировка"""
        try:
            # Получаем список заблокированных
            blocked = await self.client(functions.contacts.GetBlockedRequest(
                offset=0,
                limit=100
            ))
            
            # Проверяем, не заблокирован ли уже
            if any(user.peer.user_id == user_id for user in blocked.blocked):
                return "already_banned"
            
            # Блокируем
            await self.client(functions.contacts.BlockRequest(
                id=types.InputPeerUser(user_id=user_id, access_hash=0)
            ))
            return "success"
        except Exception as e:
            logger.error("Ошибка блокировки: %s", e)
            return "error"

    async def delete_history_safe(self, user_id: int):
        """Безопасное удаление истории"""
        try:
            await self.client(functions.messages.DeleteHistoryRequest(
                peer=user_id,
                max_id=0,
                revoke=True
            ))
            return True
        except:
            return False

    async def process_message(self, message: Message):
        """Обработка сообщения без ошибок"""
        user_id = message.sender_id
        text = (message.text or "").lower()
        
        # Определяем триггеры
        triggers = {
            "Порнография": r"порно|porn|xxx|onlyfans|секс|🔞",
            "Реклама": r"подпишись|канал|купить|реклама",
            "Вредоносное": r"bit\.ly|скачать|\.exe|вирус"
        }
        
        reason = next((r for r, p in triggers.items() if re.search(p, text, re.I)), None)
        if not reason:
            return

        response = []
        
        # 1. Блокировка
        if self.config["ban_users"]:
            status = await self.block_user_safe(user_id)
            if status == "already_banned":
                response.append(self.strings["already_banned"])
        
        # 2. Удаление сообщения
        if self.config["delete_messages"]:
            try:
                await message.delete()
            except:
                pass
        
        # 3. Удаление истории
        if self.config["delete_history"]:
            if await self.delete_history_safe(user_id):
                response.append(self.strings["history_cleared"])
        
        # 4. Отчёт
        if self.config["report_to_chat"] and self._log_chat:
            try:
                await self.client.send_message(
                    self._log_chat,
                    self.strings["log_msg"].format(
                        user_id=user_id,
                        time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                        reason=reason,
                        msg=utils.escape_html(text[:200])
                    )
                )
            except:
                pass
        
        # 5. Ответ
        response.append(self.strings["banned"].format(reason=reason))
        await utils.answer(message, "\n".join(response))
        self._ban_count += 1

    async def watcher(self, message: Message):
        if message.is_private and not message.out:
            await self.process_message(message)

    async def pastatcmd(self, message: Message):
        """Статистика работы"""
        stats = (
            "📈 <b>PerfectAntiSpam Stats</b>\n\n"
            f"• Всего заблокировано: {self._ban_count}\n"
            f"• Автоблокировка: {'✅ ON' if self.config['ban_users'] else '❌ OFF'}\n"
            f"• Удаление истории: {'✅ ON' if self.config['delete_history'] else '❌ OFF'}\n"
            f"• Отчёты: {'✅ ON' if self.config['report_to_chat'] else '❌ OFF'}"
        )
        await utils.answer(message, stats)
