from hikka import loader, utils
from hikka.types import Config, ConfigField
from telethon.tl.types import UserStatusOnline, UserStatusOffline
from telethon import events
from datetime import datetime, timedelta
import asyncio
import csv
import io
import pandas as pd

@loader.tds
class UserTracker(loader.Module):
    """UserTracker — трекинг активности пользователей"""

    strings = {"name": "UserTracker"}

    def __init__(self):
        self.config = Config(
            ConfigField(
                "REPORT_CHAT",
                default="https://t.me/+ve_fxQ6dYj9hOTJi",
                doc="Chat ID/URL для отправки отчетов"
            ),
            ConfigField(
                "CHECK_INTERVAL",
                default=300,
                doc="Интервал проверки активности (в секундах)"
            )
        )
        self.tracked_users = {}
        self.activity_log = []
        self.scheduler = None

    async def client_ready(self, client, db):
        self.db = db
        self.tracked_users = self.db.get(__name__, "tracked_users", {})
        self.scheduler = asyncio.create_task(self._daily_report_loop())

    def save_state(self):
        self.db.set(__name__, "tracked_users", self.tracked_users)

    @loader.watcher(outgoing=False, incoming=True)
    async def user_watcher(self, message):
        sender = await message.get_sender()
        if not sender or not sender.id in self.tracked_users:
            return

        user_id = sender.id
        chat = await message.get_chat()
        chat_id = message.chat_id
        chat_title = getattr(chat, "title", "ЛС")

        now = datetime.now()

        entry = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "message" if not message.edit_date else "edit",
            "chat_id": chat_id,
            "chat_title": chat_title,
            "message": message.message[:100].replace("\n", " ") if message.message else "-"
        }

        self.activity_log.append(entry)

        user_data = self.tracked_users[user_id]
        user_data["last_online"] = now
        user_data.setdefault("messages_count", 0)
        user_data["messages_count"] += 1
        user_data.setdefault("chats_activity", {})
        user_data["chats_activity"].setdefault(chat_title, 0)
        user_data["chats_activity"][chat_title] += 1

        self.tracked_users[user_id] = user_data
        self.save_state()

    async def _daily_report_loop(self):
        while True:
            await asyncio.sleep(86400)  # 24 часа
            for user_id in self.tracked_users:
                await self._send_report(user_id)

    async def _send_report(self, user_id):
        user = await self._get_user(user_id)
        data = self.tracked_users[user_id]
        now = datetime.now()
        last_online = data.get("last_online", now)
        delta = now - last_online
        messages = data.get("messages_count", 0)
        chats = data.get("chats_activity", {})

        lines = [
            f"📊 Отчет за {now.date()}",
            f"👤 Пользователь: @{user.username or user.first_name}",
            f"🕒 Онлайн: {delta}",
            f"📨 Сообщений: {messages}",
            f"🌐 Чаты:"
        ]
        for chat, count in chats.items():
            lines.append(f" • {chat} (messages: {count})")
        lines.append(f"🕵️‍♂️ Последняя активность: {last_online}")

        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=["timestamp", "event_type", "chat_id", "chat_title", "message"])
        writer.writeheader()
        for row in self.activity_log:
            if int(user_id) == int(user_id):  # можно фильтровать по ID
                writer.writerow(row)

        csv_bytes = io.BytesIO(csv_buffer.getvalue().encode("utf-8"))
        csv_bytes.name = f"report_{user_id}_{now.date()}.csv"
        chat = self.config["REPORT_CHAT"]

        await self._send_report_to(chat, "\n".join(lines), csv_bytes)

    async def _send_report_to(self, chat, text, file=None):
        try:
            await self.client.send_file(chat, file=file, caption=text)
        except Exception as e:
            await self.client.send_message(chat, f"Ошибка при отправке отчета: {e}")

    async def _get_user(self, user):
        return await self.client.get_entity(user)

    @loader.command()
    async def addtrack(self, message):
        """Добавить пользователя в отслеживание: .addtrack @user"""
        args = utils.get_args(message)
        if not args:
            return await utils.answer(message, "Укажите пользователя.")
        try:
            user = await self._get_user(args[0])
            self.tracked_users[user.id] = {
                "last_online": datetime.now(),
                "messages_count": 0,
                "chats_activity": {}
            }
            self.save_state()
            await utils.answer(message, f"Добавлен {user.id} (@{user.username}) в трекинг.")
        except Exception as e:
            await utils.answer(message, f"Ошибка: {e}")

    @loader.command()
    async def deltrack(self, message):
        """Удалить пользователя из отслеживания: .deltrack @user"""
        args = utils.get_args(message)
        if not args:
            return await utils.answer(message, "Укажите пользователя.")
        try:
            user = await self._get_user(args[0])
            if user.id in self.tracked_users:
                self.tracked_users.pop(user.id)
                self.save_state()
                await utils.answer(message, f"Удалён {user.id} (@{user.username}) из трекинга.")
            else:
                await utils.answer(message, "Этот пользователь не отслеживается.")
        except Exception as e:
            await utils.answer(message, f"Ошибка: {e}")

    @loader.command()
    async def tracklist(self, message):
        """Список отслеживаемых пользователей"""
        if not self.tracked_users:
            return await utils.answer(message, "Никто не отслеживается.")
        text = "\n".join([f"- {uid}" for uid in self.tracked_users])
        await utils.answer(message, f"Отслеживаемые пользователи:\n{text}")

    @loader.command()
    async def report(self, message):
        """Ручной отчет: .report @user"""
        args = utils.get_args(message)
        if not args:
            return await utils.answer(message, "Укажите пользователя.")
        try:
            user = await self._get_user(args[0])
            if user.id in self.tracked_users:
                await self._send_report(user.id)
                await utils.answer(message, "Отчет отправлен.")
            else:
                await utils.answer(message, "Этот пользователь не отслеживается.")
        except Exception as e:
            await utils.answer(message, f"Ошибка: {e}")
