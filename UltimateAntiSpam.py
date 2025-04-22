import re
import logging
from datetime import datetime
from hikkatl.types import Message
from hikkatl import functions, types
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UltimateAntiSpam(loader.Module):
    """Мощный антиспам с интеллектуальными фильтрами"""

    strings = {
        "name": "UltimateAntiSpamPro",
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
        "user_not_found": "⚠️ Пользователь не найден",
        "spam_detected": "🚫 Обнаружен спам! Приняты меры."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ban_users", True, "Блокировать пользователей",
            "delete_messages", True, "Удалять сообщения",
            "delete_history", True, "Удалять историю",
            "report_to_chat", True, "Отправлять отчёты",
            "max_links", 2, "Максимум ссылок в сообщении",
            "check_adult", True, "Фильтровать NSFW контент",
            "check_malware", True, "Проверять вредоносное ПО"
        )
        self._ban_count = 0
        self._patterns = self._build_patterns()

    def _build_patterns(self):
        return {
            "Порнография": (
                r"(?i)\b(порно|porn|xxx|секс|🔞|onlyfans|nsfw|эротик[аи]?|"
                r"порнограф|интим|обнаж[её]нн?|гол[ыі]й|раздевайся|"
                r"соси|порнуха|порнушк|порняшк)\b"
                r"(?<!секс-|психо|история|методика|лекции|терапи|анализ)"
            ),
            "Реклама": (
                r"(?i)(\b(подпишись|канал|реклама|casino|казин[оа]|куплю|"
                r"продам|скидк[аи]|акци[яи]|промокод|раскрутк[аи]|"
                r"накрутк[аи]|заработок|биржа|инвестиции|крипта|"
                r"ставк[аи]|лотерея)\b"
                r"|[\U0001F4B0-\U0001F4B8💵💰📈💸🤑]"
                r"|(?:\bбесплатно\b.*\bвыгодно\b)"
                r"|(?:\bсрочно\b.*\bкуп[иь]\b))"
            ),
            "Вредоносное": (
                r"(?i)(?:bit\.ly|tinyurl|goo\.gl|скача[йи]|"
                r"\.exe|\bвирус\b|вредонос|взлом|кряк|фишинг|"
                r"malware|спам|ботнет|шифровальщик|руткит)"
                r"|(?:https?://[^\s]*?(casino|рулетк|скачать|virus))"
            ),
            "Подозрительные паттерны": (
                r"(?:https?://[^\s]*?){3,}|"
                r"([!?#$%^&]{4,})|"
                r"(\b\w+\b\s*?){3,}\1|"
                r"\b[a-z0-9]{20,}\b"
            )
        }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        try:
            self._log_chat = await self.client.get_entity("https://t.me/+ve_fxQ6dYj9hOTJi")
        except Exception as e:
            logger.error("Ошибка подключения чата: %s", e)
            self._log_chat = None

    async def is_user_blocked(self, user_id: int) -> bool:
        try:
            blocked = await self.client(functions.contacts.GetBlockedRequest(offset=0, limit=100))
            return any(
                user.peer.user_id == user_id if hasattr(user, 'peer') 
                else user.id == user_id 
                for user in getattr(blocked, 'blocked', [])
            )
        except Exception as e:
            logger.error("Ошибка проверки блокировки: %s", e)
            return False

    async def block_user_ultimate(self, user_id: int):
        try:
            if await self.is_user_blocked(user_id):
                return "already_banned"
            
            for _ in range(3):
                try:
                    user = await self.client.get_entity(types.PeerUser(user_id))
                    await self.client(functions.contacts.BlockRequest(
                        id=types.InputPeerUser(
                            user_id=user.id,
                            access_hash=user.access_hash
                        )
                    ))
                    return "success"
                except (ValueError, TypeError):
                    await self.client(functions.contacts.BlockRequest(
                        id=types.InputPeerUser(user_id=user_id, access_hash=0)
                    ))
                    return "success"
                except Exception as e:
                    logger.warning("Попытка блокировки %d: %s", user_id, e)
                    await asyncio.sleep(1)
            
            return "error"
        except Exception as e:
            logger.error("Фатальная ошибка блокировки: %s", e)
            return "error"

    async def delete_history_ultimate(self, user_id: int):
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
            return True
        except Exception as e:
            logger.error("Ошибка удаления истории: %s", e)
            return False

    async def _check_message(self, text: str) -> str:
        if len(re.findall(r"https?://", text)) > self.config["max_links"]:
            return "Подозрительные паттерны"
        
        for category, pattern in self._patterns.items():
            if not self.config[f"check_{category.split()[0].lower()}"]:
                continue
            if re.search(pattern, text, flags=re.IGNORECASE):
                return category
        
        if self.config["check_adult"] and any(
            kw in text.lower() for kw in {"🔞", "nsfw", "18+", "порно"}
        ):
            return "Порнография"
        
        return ""

    async def process_message(self, message: Message):
        if not message.is_private or message.out:
            return

        text = utils.get_raw_text(message)
        if not text:
            return

        reason = await self._check_message(text)
        if not reason:
            return

        user_id = message.sender_id
        response = []
        
        if self.config["ban_users"]:
            status = await self.block_user_ultimate(user_id)
            if status == "already_banned":
                response.append(self.strings["already_banned"])
            elif status == "error":
                response.append(self.strings["user_not_found"])
        
        if self.config["delete_messages"]:
            try:
                await message.delete()
            except Exception as e:
                logger.warning("Ошибка удаления: %s", e)
        
        if self.config["delete_history"]:
            if await self.delete_history_ultimate(user_id):
                response.append(self.strings["history_cleared"])
        
        if self.config["report_to_chat"] and self._log_chat:
            try:
                # Исправленная строка 205 с закрывающими скобками
                await self.client.send_message(
                    self._log_chat,
                    self.strings["log_msg"].format(
                        user_id=user_id,
                        time=datetime.now().strftime("%d.%m.%Y %H:%M"),
                        reason=reason,
                        msg=utils.escape_html(text[:500])
                    )  # Закрывающая скобка для format
                )  # Закрывающая скобка для send_message
            except Exception as e:
                logger.error("Ошибка отправки отчета: %s", e)
        
        final_response = "\n".join(filter(None, [
            self.strings["spam_detected"],
            *response,
            self.strings["banned"].format(reason=reason)
        ]))
        
        await utils.answer(message, final_response)
        self._ban_count += 1

    async def watcher(self, message: Message):
        await self.process_message(message)

    async def uastatcmd(self, message: Message):
        stats = (
            "📊 <b>UltimateAntiSpam Pro Stats</b>\n\n"
            f"• Всего блокировок: {self._ban_count}\n"
            f"• Активные фильтры:\n"
            f"  - NSFW: {'✅' if self.config['check_adult'] else '❌'}\n"
            f"  - Вредоносное: {'✅' if self.config['check_malware'] else '❌'}\n"
            f"  - Макс. ссылок: {self.config['max_links']}\n"
            f"• Последние действия:\n"
            f"  - Блокировка: {'✅' if self.config['ban_users'] else '❌'}\n"
            f"  - Очистка истории: {'✅' if self.config['delete_history'] else '❌'}"
        )
        await utils.answer(message, stats)
