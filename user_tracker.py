import asyncio
import csv
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, List, Union

from telethon.tl.types import (
    Message, MessageEdited, UpdateUserStatus, User, UserStatusEmpty,
    UserStatusLastMonth, UserStatusLastWeek, UserStatusOffline,
    UserStatusOnline, UserStatusRecently, ChatAction
)
from telethon.utils import get_display_name

from hikka import loader, utils


@loader.tds
class UserTrackerMod(loader.Module):
    """Track user activity and generate reports"""
    strings = {
        "name": "UserTracker",
        "user_added": "👤 User <code>{}</code> added to tracking",
        "user_not_found": "❌ User not found",
        "user_removed": "👤 User <code>{}</code> removed from tracking",
        "user_not_tracked": "❌ User <code>{}</code> is not being tracked",
        "tracklist": "📊 Tracked users:\n{}",
        "no_tracked": "❌ No users are being tracked",
        "report_header": "📊 Report for {}\n👤 User: {}\n",
        "online_status": "🕒 Online status: {}\n",
        "activity_stats": "📨 Messages: {} ({} edits)\n🌐 Chats:\n{}",
        "chat_entry": "  • {} (messages: {})",
        "last_activity": "🕵️‍♂️ Last activity: {} ({})",
        "report_generated": "📊 Report generated for user {}",
        "config_report_chat": "Chat ID/URL for reports",
        "config_check_interval": "Activity check interval (seconds)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "REPORT_CHAT",
                "https://t.me/+ve_fxQ6dYj9hOTJi",
                lambda: self.strings["config_report_chat"],
                validator=loader.validators.Link()
            ),
            loader.ConfigValue(
                "CHECK_INTERVAL",
                300,
                lambda: self.strings["config_check_interval"],
                validator=loader.validators.Integer(minimum=60)
            )
        )

        self.tracked_users: Dict[int, Dict] = {}
        self._scheduler_task = None

    async def client_ready(self, client, db):
        self._db = db
        self.tracked_users = self._db.get("UserTracker", "tracked_users", {})
        self._scheduler_task = asyncio.create_task(self._daily_report_scheduler())

    async def on_unload(self):
        if self._scheduler_task:
            self._scheduler_task.cancel()

    def _save_data(self):
        self._db.set("UserTracker", "tracked_users", self.tracked_users)

    async def _get_user(self, user_id: Union[int, str]) -> Union[User, None]:
        try:
            return await self.client.get_entity(user_id)
        except Exception:
            return None

    def _format_timedelta(self, td: timedelta) -> str:
        hours, remainder = divmod(td.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    async def _daily_report_scheduler(self):
        while True:
            now = datetime.now()
            next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            wait_seconds = (next_day - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            await self._generate_daily_reports()

    async def _generate_daily_reports(self):
        for user_id in list(self.tracked_users.keys()):
            await self._generate_report(user_id)

    async def _generate_report(self, user_id: int):
        if user_id not in self.tracked_users:
            return

        user_data = self.tracked_users[user_id]
        user = await self._get_user(user_id)
        if not user:
            return

        username = get_display_name(user)
        report_date = datetime.now().strftime("%Y-%m-%d")

        report_text = self.strings["report_header"].format(report_date, username)

        # Online status calculation
        online_status = "offline"
        last_activity_time = "never"
        last_online = user_data.get("last_online")
        last_offline = user_data.get("last_offline")

        if last_online:
            if isinstance(last_online, str):
                last_online = datetime.fromisoformat(last_online)
            
            if last_offline and isinstance(last_offline, str):
                last_offline = datetime.fromisoformat(last_offline)
            
            if last_offline and last_offline > last_online:
                online_status = "offline"
            else:
                if last_offline:
                    online_duration = last_offline - last_online
                    online_status = f"online for {self._format_timedelta(online_duration)}"
                else:
                    online_status = "currently online"
            
            last_activity_time = last_online.strftime("%Y-%m-%d %H:%M")
        else:
            online_status = "never online"

        report_text += self.strings["online_status"].format(online_status)

        # Activity stats
        messages_count = user_data.get("messages_count", 0)
        edits_count = user_data.get("edits_count", 0)
        chats_activity = user_data.get("chats_activity", {})

        chats_info = []
        for chat_id, count in chats_activity.items():
            try:
                chat = await self.client.get_entity(chat_id)
                chat_title = get_display_name(chat)
                chats_info.append(self.strings["chat_entry"].format(chat_title, count))
            except Exception:
                continue

        report_text += self.strings["activity_stats"].format(
            messages_count,
            edits_count,
            "\n".join(chats_info) if chats_info else "No activity"
        )

        report_text += "\n" + self.strings["last_activity"].format(
            last_activity_time,
            "online" if online_status != "offline" else "offline"
        )

        # Prepare CSV report
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)
        csv_writer.writerow(["timestamp", "event_type", "chat_id", "chat_title", "message"])

        if "activity_log" in user_data:
            for entry in user_data["activity_log"]:
                csv_writer.writerow([
                    entry.get("timestamp", ""),
                    entry.get("event_type", ""),
                    entry.get("chat_id", ""),
                    entry.get("chat_title", ""),
                    (entry.get("message", "") or "")[:100]
                ])

        csv_data.seek(0)
        csv_content = csv_data.getvalue()

        # Send report
        report_chat = self.config["REPORT_CHAT"]
        if report_chat:
            try:
                await self.client.send_message(
                    report_chat,
                    report_text,
                    file=(f"report_{user_id}_{report_date}.csv", csv_content),
                )
            except Exception as e:
                self.logger.error(f"Failed to send report: {e}")

    async def _log_activity(self, user_id: int, event_type: str, message: Message = None):
        if user_id not in self.tracked_users:
            return

        if "activity_log" not in self.tracked_users[user_id]:
            self.tracked_users[user_id]["activity_log"] = []

        chat_id = message.chat_id if message else 0
        chat_title = ""
        try:
            chat = await self.client.get_entity(chat_id)
            chat_title = get_display_name(chat)
        except Exception:
            pass

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "chat_id": chat_id,
            "chat_title": chat_title,
            "message": message.text if message and message.text else "",
        }

        self.tracked_users[user_id]["activity_log"].append(log_entry)
        self._save_data()

    @loader.watcher()
    async def on_user_status(self, update: UpdateUserStatus):
        if update.user_id not in self.tracked_users:
            return

        user_data = self.tracked_users[update.user_id]
        now = datetime.now().isoformat()

        if isinstance(update.status, UserStatusOnline):
            user_data["last_online"] = now
            await self._log_activity(update.user_id, "online")
        elif isinstance(update.status, (UserStatusOffline, UserStatusRecently,
                                      UserStatusLastWeek, UserStatusLastMonth,
                                      UserStatusEmpty)):
            user_data["last_offline"] = now
            await self._log_activity(update.user_id, "offline")

        self._save_data()

    @loader.watcher()
    async def on_message(self, message: Message):
        if not message.sender_id or message.sender_id not in self.tracked_users:
            return

        user_id = message.sender_id
        user_data = self.tracked_users[user_id]

        user_data["messages_count"] = user_data.get("messages_count", 0) + 1

        chat_id = message.chat_id
        if "chats_activity" not in user_data:
            user_data["chats_activity"] = {}
        user_data["chats_activity"][chat_id] = user_data["chats_activity"].get(chat_id, 0) + 1

        await self._log_activity(user_id, "message", message)
        self._save_data()

    @loader.watcher()
    async def on_message_edit(self, message: MessageEdited):
        if not message.sender_id or message.sender_id not in self.tracked_users:
            return

        user_id = message.sender_id
        user_data = self.tracked_users[user_id]

        user_data["edits_count"] = user_data.get("edits_count", 0) + 1

        await self._log_activity(user_id, "edit", message)
        self._save_data()

    @loader.command()
    async def addtrack(self, message: Message):
        """Add user to tracking"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Please specify user")
            return

        try:
            user = await self.client.get_entity(args)
        except Exception:
            await utils.answer(message, self.strings["user_not_found"])
            return

        if user.id not in self.tracked_users:
            self.tracked_users[user.id] = {
                "added": datetime.now().isoformat(),
                "messages_count": 0,
                "edits_count": 0,
                "chats_activity": {},
                "activity_log": [],
                "last_online": None,
                "last_offline": None,
            }
            self._save_data()

        await utils.answer(
            message,
            self.strings["user_added"].format(user.id)
        )

    @loader.command()
    async def deltrack(self, message: Message):
        """Remove user from tracking"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Please specify user")
            return

        try:
            user = await self.client.get_entity(args)
        except Exception:
            await utils.answer(message, self.strings["user_not_found"])
            return

        if user.id in self.tracked_users:
            del self.tracked_users[user.id]
            self._save_data()
            await utils.answer(
                message,
                self.strings["user_removed"].format(user.id)
            )
        else:
            await utils.answer(
                message,
                self.strings["user_not_tracked"].format(user.id)
            )

    @loader.command()
    async def tracklist(self, message: Message):
        """List tracked users"""
        if not self.tracked_users:
            await utils.answer(message, self.strings["no_tracked"])
            return

        users_list = []
        for user_id in self.tracked_users:
            try:
                user = await self.client.get_entity(user_id)
                users_list.append(f"• {get_display_name(user)} (<code>{user_id}</code>)")
            except Exception:
                continue

        await utils.answer(
            message,
            self.strings["tracklist"].format("\n".join(users_list))
        )

    @loader.command()
    async def report(self, message: Message):
        """Generate report for user"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Please specify user")
            return

        try:
            user = await self.client.get_entity(args)
        except Exception:
            await utils.answer(message, self.strings["user_not_found"])
            return

        if user.id not in self.tracked_users:
            await utils.answer(
                message,
                self.strings["user_not_tracked"].format(user.id)
            )
            return

        await self._generate_report(user.id)
        await utils.answer(
            message,
            self.strings["report_generated"].format(get_display_name(user))
            )
