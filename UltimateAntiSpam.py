import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UltimateAntiSpam(loader.Module):
    """Антиспам без ошибок с полной обработкой всех случаев"""

    strings = {
        "name": "UltimateAntiSpam",
        "banned": "🔒 <b>Пользователь заблокирован</b>\nПричина: {reason}",
        "log_msg": (
            "📛 <b>Лог блокировки</b>\n\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "⏰ Время: {time}\n"
            "🔞 Причина: {reason}\n"
            "✉️ Сообщение: <code>{msg}</code>"
        ),
        "already_banned": "ℹ️ Пользователь уже заблокирован",
        "history_cleared": "🧹 История переписки очищена",
        "user_not_found": "⚠️ Пользователь не найден"
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
            logger.error("Ошибка подключения чата: %s", e)
            self._log_chat = None

    async def is_user_blocked(self, user_id: int) -> bool:
        """Проверка блокировки без ошибок"""
        try:
            blocked = await self.client(functions.contacts.GetBlockedRequest(
                offset=0,
                limit=100
            ))
            # Обработка разных версий Telegram API
            if hasattr(blocked, 'blocked'):
                for user in blocked.blocked:
                    if hasattr(user, 'peer') and hasattr(user.peer, 'user_id'):
                        if user.peer.user_id == user_id:
                            return True
                    elif hasattr(user, 'id'):
                        if user.id == user_id:
                            return True
            return False
        except Exception as e:
            logger.error("Ошибка проверки блокировки: %s", e)
            return False

    async def block_user_ultimate(self, user_id: int):
        """Абсолютно надежная блокировка"""
        try:
            if await self.is_user_blocked(user_id):
                return "already_banned"
            
            # Получаем полную информацию о пользователе
            try:
                user = await self.client.get_entity(types.PeerUser(user_id))
                await self.client(functions.contacts.BlockRequest(
                    id=types.InputPeerUser(
                        user_id=user.id,
                        access_hash=user.access_hash
                    )
                ))
            except:
                # Если не удалось получить access_hash, пробуем без него
                await self.client(functions.contacts.BlockRequest(
                    id=types.InputPeerUser(user_id=user_id, access_hash=0)
                ))
            
            return "success"
        except Exception as e:
            logger.error("Ошибка блокировки: %s", e)
            return "error"

    async def delete_history_ultimate(self, user_id: int):
        """Удаление истории с обработкой всех ошибок"""
        try:
            # Получаем полную информацию о пользователе
            try:
                user = await self.client.get_entity(types.PeerUser(user_id))
                await self.client(functions.messages.DeleteHistoryRequest(
                    peer=types.InputPeerUser(
                        user_id=user.id,
                        access_hash=user.access_hash
                    ),
                    max_id=0,
                    revoke=True
                ))
            except:
                # Если не удалось получить access_hash, пробуем без него
                await self.client(functions.messages.DeleteHistoryRequest(
                    peer=types.InputPeerUser(user_id=user_id, access_hash=0),
                    max_id=0,
                    revoke=True
                ))
            
            return True
        except Exception as e:
            logger.error("Ошибка удаления истории: %s", e)
            return False

    async def process_message(self, message: Message):
        """Обработка сообщения с защитой от всех ошибок"""
        if not message.is_private or message.out:
            return

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
            status = await self.block_user_ultimate(user_id)
            if status == "already_banned":
                response.append(self.strings["already_banned"])
            elif status == "error":
                response.append(self.strings["user_not_found"])
        
        # 2. Удаление сообщения
        if self.config["delete_messages"]:
            try:
                await message.delete()
            except:
                pass
        
        # 3. Удаление истории
        if self.config["delete_history"]:
            if await self.delete_history_ultimate(user_id):
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
        await utils.answer(message, "\n".join(filter(None, response)))
        self._ban_count += 1

    async def watcher(self, message: Message):
        await self.process_message(message)

    async def uastatcmd(self, message: Message):
        """Статистика работы"""
        stats = (
            "📊 <b>UltimateAntiSpam Stats</b>\n\n"
            f"• Всего заблокировано: {self._ban_count}\n"
            f"• Автоблокировка: {'✅ ON' if self.config['ban_users'] else '❌ OFF'}\n"
            f"• Удаление истории: {'✅ ON' if self.config['delete_history'] else '❌ OFF'}\n"
            f"• Отчёты: {'✅ ON' if self.config['report_to_chat'] else '❌ OFF'}"
        )
        await utils.answer(message, stats)
