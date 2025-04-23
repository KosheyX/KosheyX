from hikkatl.types import Message, UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from hikkatl.tl.types import PeerUser, PeerChat, PeerChannel
from datetime import datetime, timedelta
import asyncio
from .. import loader, utils

@loader.tds
class UserTrackerMod(loader.Module):
    """Модуль для отслеживания активности пользователя"""
    strings = {
        "name": "UserTracker",
        "tracking_started": "🚀 Начато отслеживание пользователя {}",
        "tracking_stopped": "🛑 Остановлено отслеживание пользователя {}",
        "no_user": "❌ Укажите ID или юзернейм пользователя для отслеживания",
        "report": (
            "📊 Отчет по пользователю {}\n\n"
            "🟢 Был онлайн: {}\n"
            "🔴 Был оффлайн: {}\n"
            "⏱ Всего времени в сети: {}\n"
            "💬 Чаты активности:\n{}\n"
            "📈 Статистика за последние 24 часа:\n{}"
        ),
        "chat_entry": "  - {} ({} сообщений, время: {})",
        "status_online": "🟢 В сети",
        "status_offline": "🔴 Не в сети",
        "status_recently": "🟡 Был недавно",
        "status_last_week": "🟠 Был на этой неделе",
        "status_last_month": "🔵 Был в этом месяце",
        "status_long_ago": "⚫ Давно не был в сети",
        "not_tracking": "❌ Отслеживание не запущено",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "report_chat",
                "https://t.me/+ve_fxQ6dYj9hOTJi",
                "Чат для отправки отчетов",
                validator=loader.validators.Link()
            ),
            loader.ConfigValue(
                "check_interval",
                300,
                "Интервал проверки (в секундах)",
                validator=loader.validators.Integer(minimum=60)
            ),
            loader.ConfigValue(
                "track_messages",
                True,
                "Отслеживать сообщения пользователя",
                validator=loader.validators.Boolean()
            ),
        )
        self.tracked_user = None
        self.tracking = False
        self.user_data = {}
        self.last_check = None
        self.online_times = {}
        self.message_counts = {}
        self._task = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    async def on_unload(self):
        if self._task:
            self._task.cancel()

    async def start_tracking(self):
        if not self.tracked_user:
            return
        
        self.tracking = True
        self.user_data = {
            "first_seen": datetime.now(),
            "last_online": None,
            "last_offline": None,
            "total_online": timedelta(),
            "sessions": [],
            "current_session_start": None,
            "chats": {},
        }
        
        self._task = asyncio.create_task(self._track_loop())

    async def _track_loop(self):
        while self.tracking:
            try:
                await self.check_user_status()
                if self.config["track_messages"]:
                    await self.check_user_chats()
                await self.send_report()
            except Exception as e:
                print(f"[UserTracker] Ошибка: {e}")
            
            await asyncio.sleep(self.config["check_interval"])

    async def check_user_status(self):
        try:
            user = await self._client.get_entity(self.tracked_user)
            now = datetime.now()
            
            if hasattr(user, 'status'):
                if isinstance(user.status, UserStatusOnline):
                    if not self.user_data["current_session_start"]:
                        self.user_data["current_session_start"] = now
                        self.user_data["last_online"] = now
                        if now.date() not in self.online_times:
                            self.online_times[now.date()] = timedelta()
                elif isinstance(user.status, UserStatusOffline):
                    if self.user_data["current_session_start"]:
                        session_duration = now - self.user_data["current_session_start"]
                        self.user_data["total_online"] += session_duration
                        if now.date() in self.online_times:
                            self.online_times[now.date()] += session_duration
                        else:
                            self.online_times[now.date()] = session_duration
                        self.user_data["sessions"].append({
                            "start": self.user_data["current_session_start"],
                            "end": now,
                            "duration": session_duration
                        })
                        self.user_data["current_session_start"] = None
                        self.user_data["last_offline"] = now
        except Exception as e:
            print(f"[UserTracker] Ошибка при проверке статуса: {e}")

    async def check_user_chats(self):
        try:
            user = await self._client.get_entity(self.tracked_user)
            dialogs = await self._client.get_dialogs()
            
            for dialog in dialogs:
                if dialog.is_user or dialog.is_group or dialog.is_channel:
                    try:
                        chat_id = dialog.id
                        messages = await self._client.get_messages(
                            dialog.entity,
                            from_user=user.id,
                            limit=100,
                            wait_time=2
                        )
                        
                        if chat_id not in self.user_data["chats"]:
                            self.user_data["chats"][chat_id] = {
                                "name": dialog.name,
                                "message_count": 0,
                                "last_message": None,
                                "time_spent": timedelta()
                            }
                        
                        prev_count = self.user_data["chats"][chat_id]["message_count"]
                        self.user_data["chats"][chat_id]["message_count"] = len(messages)
                        
                        if messages:
                            self.user_data["chats"][chat_id]["last_message"] = messages[0].date
                            
                            if len(messages) > prev_count:
                                if chat_id in self.message_counts:
                                    time_diff = messages[0].date - self.message_counts[chat_id]["last_time"]
                                    self.user_data["chats"][chat_id]["time_spent"] += time_diff
                                self.message_counts[chat_id] = {
                                    "count": len(messages),
                                    "last_time": messages[0].date
                                }
                    except Exception as e:
                        print(f"[UserTracker] Ошибка при проверке чата {dialog.name}: {e}")
                        continue
        except Exception as e:
            print(f"[UserTracker] Ошибка при проверке чатов: {e}")

    async def send_report(self):
        if not self.tracked_user or not self.user_data:
            return
        
        try:
            user = await self._client.get_entity(self.tracked_user)
            chat_list = "\n".join(
                self.strings("chat_entry").format(
                    chat["name"],
                    chat["message_count"],
                    str(chat["time_spent"]).split(".")[0]
                )
                for chat in self.user_data["chats"].values()
            )
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            today_time = self.online_times.get(today, timedelta())
            yesterday_time = self.online_times.get(yesterday, timedelta())
            
            stats_24h = (
                f"Сегодня: {str(today_time).split('.')[0]}\n"
                f"Вчера: {str(yesterday_time).split('.')[0]}\n"
                f"Всего сессий: {len(self.user_data['sessions'])}"
            )
            
            report = self.strings("report").format(
                utils.get_display_name(user),
                self.user_data["last_online"].strftime("%Y-%m-%d %H:%M:%S") if self.user_data["last_online"] else "N/A",
                self.user_data["last_offline"].strftime("%Y-%m-%d %H:%M:%S") if self.user_data["last_offline"] else "N/A",
                str(self.user_data["total_online"]).split(".")[0],
                chat_list if chat_list else "Нет данных о чатах",
                stats_24h
            )
            
            await self._client.send_message(self.config["report_chat"], report)
        except Exception as e:
            print(f"[UserTracker] Ошибка при отправке отчета: {e}")

    @loader.command()
    async def track(self, message: Message):
        """Начать отслеживание пользователя. Использование: .track <id/юзернейм>"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_user"))
            return
        
        if self.tracking:
            await utils.answer(message, "Уже отслеживается пользователь. Сначала остановите текущее отслеживание.")
            return
            
        try:
            self.tracked_user = args
            await self.start_tracking()
            await utils.answer(message, self.strings("tracking_started").format(args))
        except Exception as e:
            await utils.answer(message, f"Ошибка: {str(e)}")

    @loader.command()
    async def untrack(self, message: Message):
        """Остановить отслеживание"""
        if not self.tracking:
            await utils.answer(message, self.strings("not_tracking"))
            return
            
        self.tracking = False
        if self._task:
            self._task.cancel()
            self._task = None
            
        await utils.answer(message, self.strings("tracking_stopped").format(self.tracked_user))
        self.tracked_user = None

    @loader.command()
    async def trackreport(self, message: Message):
        """Получить текущий отчет"""
        if not self.tracking or not self.tracked_user:
            await utils.answer(message, self.strings("not_tracking"))
            return
            
        try:
            await self.send_report()
            await utils.answer(message, "Отчет отправлен в указанный чат")
        except Exception as e:
            await utils.answer(message, f"Ошибка при отправке отчета: {str(e)}")
