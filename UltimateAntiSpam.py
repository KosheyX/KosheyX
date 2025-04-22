import re
import logging
import time
from datetime import datetime
from typing import List, Union, Optional

from hikkatl.types import Message, Document
from hikkatl.tl.types import (
    MessageEntityUrl,
    MessageEntityTextUrl,
    DocumentAttributeFilename,
)
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UltimateAntiSpamMod(loader.Module):
    """🔒 Ultimate защита от спама, рекламы и порно в ЛС + отчеты в канал."""

    strings = {
        "name": "UltimateAntiSpam",
        "banned": "🚨 <b>{user} забанен в ЛС!</b>\n<b>Причина:</b> {reason}",
        "deleted": "🗑 <i>Сообщение удалено.</i>",
        "log_header": "📢 <b>Лог блокировок</b>\n\n",
        "stats_header": "📊 <b>Статистика банов</b>\n\n",
        "report_msg": (
            "🚨 <b>Новая блокировка!</b>\n\n"
            "👤 <b>Пользователь:</b> {user}\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "📅 <b>Дата:</b> {date}\n"
            "🔍 <b>Причина:</b> {reason}\n"
            "✉️ <b>Сообщение:</b> <code>{message_preview}</code>\n"
        ),
    }

    def __init__(self):
        self._ban_count = 0
        self._last_ban_time = None
        self.config = loader.ModuleConfig(
            "ban_users", True, "Автоматически банить нарушителей",
            "delete_messages", True, "Удалять вредоносные сообщения",
            "log_to_channel", True, "Отправлять отчеты в канал",
            "log_chat_id", None, "ID чата для логов (например, @antispam_logs)",
            "antiporn", True, "Блокировать порнографию",
            "antispam", True, "Блокировать рекламу",
            "antilinks", True, "Блокировать вредоносные ссылки",
            "antifiles", True, "Блокировать опасные файлы",
            "flood_control", 5, "Макс. сообщений в минуту для флуда",
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self._flood_control = {}  # {user_id: [message_timestamps]}

    async def is_dm(self, message: Message) -> bool:
        """Проверяет, что сообщение пришло в ЛС."""
        return message.is_private and not message.out

    async def check_content(self, message: Message) -> Optional[str]:
        """Анализирует сообщение на нарушения."""
        text = (message.text or message.raw_text or "").lower()

        # 🔞 Порнография
        if self.config["antiporn"]:
            porn_triggers = [
                r"порно|porn|xxx|onlyfans|секс|сиськи|голые|nude|🔞|🍑|💋|🍒",
                r"секс|порно|обнаж|голая|порн|интим|fuck|dick|pussy",
            ]
            for trigger in porn_triggers:
                if re.search(trigger, text, re.IGNORECASE):
                    return "Порнография"

        # 📢 Реклама
        if self.config["antispam"]:
            spam_triggers = [
                r"подпишись|подписаться|канал|группа|чат|купить|продам|бесплатно",
                r"реклама|@[a-z0-9_]{5,}|t\.me/|telegram\.me/|оплата|заказать",
            ]
            for trigger in spam_triggers:
                if re.search(trigger, text, re.IGNORECASE):
                    return "Реклама"

        # ⚠️ Вредоносные ссылки
        if self.config["antilinks"]:
            malicious_domains = [
                r"bit\.ly|tinyurl\.com|shorte\.st|скачать\-бесплатно",
                r"steamcommunity\.com/login|discord\.gift|free-minecraft\.ru",
            ]
            urls = await self.extract_urls(message)
            for url in urls:
                for domain in malicious_domains:
                    if re.search(domain, url, re.IGNORECASE):
                        return "Вредоносная ссылка"

        # 📁 Опасные файлы
        if self.config["antifiles"] and message.file:
            bad_extensions = [r"\.exe", r"\.bat", r"\.js", r"\.scr", r"\.vbs"]
            for ext in bad_extensions:
                if re.search(ext, message.file.name or "", re.IGNORECASE):
                    return "Опасный файл"

        # 💬 Флуд
        if self.config["flood_control"] > 0:
            user_id = message.sender_id
            now = time.time()
            if user_id not in self._flood_control:
                self._flood_control[user_id] = []
            self._flood_control[user_id].append(now)
            # Удаляем старые сообщения (старше 60 сек)
            self._flood_control[user_id] = [
                t for t in self._flood_control[user_id] if now - t < 60
            ]
            if len(self._flood_control[user_id]) > self.config["flood_control"]:
                return "Флуд"

        return None

    async def extract_urls(self, message: Message) -> List[str]:
        """Извлекает URL из сообщения."""
        urls = []
        text = message.text or message.raw_text or ""
        if message.entities:
            for entity in message.entities:
                if isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
                    urls.append(text[entity.offset:entity.offset + entity.length])
        else:
            urls.extend(re.findall(r"https?://[^\s]+", text))
        return urls

    async def ban_user(self, message: Message, reason: str):
        """Банит пользователя и отправляет отчет."""
        user = await message.get_sender()
        self._ban_count += 1
        self._last_ban_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        try:
            # Блокировка
            if self.config["ban_users"]:
                await self.client.edit_permissions(
                    user.id,
                    view_messages=False,
                )
            # Удаление сообщения
            if self.config["delete_messages"]:
                await message.delete()

            # Отчет в канал
            if self.config["https://t.me/+IuzxM1GfO1k2MmNi"] and self.config["https://t.me/+ve_fxQ6dYj9hOTJi"]:
                report = self.strings("report_msg").format(
                    user=utils.escape_html(user.first_name),
                    user_id=user.id,
                    date=self._last_ban_time,
                    reason=reason,
                    message_preview=utils.escape_html((message.text or "")[:100]),
                )
                await self.client.send_message(
                    self.config["log_chat_id"],
                    report,
                )

            # Уведомление в ЛС
            await utils.answer(
                message,
                self.strings("banned").format(
                    user=utils.escape_html(user.first_name),
                    reason=reason,
                ),
            )
        except Exception as e:
            logger.error(f"Ошибка: {e}")

    async def show_stats(self, message: Message):
        """Показывает статистику банов."""
        stats = (
            f"📊 <b>Статистика блокировок</b>\n\n"
            f"🔢 <b>Всего забанено:</b> <code>{self._ban_count}</code>\n"
            f"⏰ <b>Последний бан:</b> <code>{self._last_ban_time or 'Нет данных'}</code>\n"
        )
        await utils.answer(message, stats)

    async def watcher(self, message: Message):
        """Обрабатывает все входящие ЛС."""
        if not await self.is_dm(message):
            return

        reason = await self.check_content(message)
        if reason:
            await self.ban_user(message, reason)

    async def ultaspamcmd(self, message: Message):
        """Показать статистику банов | .ultaspam"""
        await self.show_stats(message)
