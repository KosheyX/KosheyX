from hikkatl.types import Message, User, UserStatusOnline, UserStatusOffline
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
            "🟢 Последний онлайн: {}\n"
            "🔴 Последний оффлайн: {}\n"
            "⏱ Всего времени в сети: {}\n"
            "📈 Активность за последние 24 часа: {}"
        ),
        "not_tracking": "❌ Отслеживание не запущено",
        "invalid_user": "❌ Пользователь не найден",
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
        )
        self.tracked_user = None
        self.tracking = False
        self.user_data = {}
        self._task = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    async def on_unload(self):
        await self.stop_tracking()

    async def stop_tracking(self):
        if self._task:
            self._task.cancel()
            self._task = None
        self.tracking = False

    async def start_tracking(self):
        if self._task:
            self._task.cancel()

        self.tracking = True
        self.user_data = {
            "first_seen": datetime.now(),
            "last_online": None,
            "last_offline": None,
            "total_online": timedelta(),
            "current_session_start": None,
        }
        
        self._task = asyncio.create_task(self._track_loop())

    async def _track_loop(self):
        while self.tracking:
            try:
                await self._check_status()
                await self._send_report()
            except Exception as e:
                print(f"[UserTracker] Ошибка: {e}")
            
            await asyncio.sleep(self.config["check_interval"])

    async def _check_status(self):
        try:
            user = await self._client.get_entity(self.tracked_user)
            if not isinstance(user, User):
                return

            now = datetime.now()
            
            if hasattr(user, 'status'):
                if isinstance(user.status, UserStatusOnline):
                    if not self.user_data["current_session_start"]:
                        self.user_data["current_session_start"] = now
                        self.user_data["last_online"] = now
                elif isinstance(user.status, UserStatusOffline):
                    if self.user_data["current_session_start"]:
                        session_duration = now - self.user_data["current_session_start"]
                        self.user_data["total_online"] += session_duration
                        self.user_data["last_offline"] = now
                        self.user_data["current_session_start"] = None
        except Exception as e:
            print(f"[UserTracker] Ошибка при проверке статуса: {e}")

    async def _send_report(self):
        if not self.tracking or not self.tracked_user:
            return
        
        try:
            user = await self._client.get_entity(self.tracked_user)
            if not isinstance(user, User):
                return

            now = datetime.now()
            last_24h_online = timedelta()
            
            if self.user_data["current_session_start"]:
                session_duration = now - self.user_data["current_session_start"]
                last_24h_online = min(session_duration, timedelta(hours=24))
            
            report = self.strings["report"].format(
                utils.get_display_name(user),
                self.user_data["last_online"].strftime("%d.%m.%Y %H:%M") if self.user_data["last_online"] else "неизвестно",
                self.user_data["last_offline"].strftime("%d.%m.%Y %H:%M") if self.user_data["last_offline"] else "неизвестно",
                str(self.user_data["total_online"]).split('.')[0],
                str(last_24h_online).split('.')[0],
            )
            
            await self._client.send_message(self.config["report_chat"], report)
        except Exception as e:
            print(f"[UserTracker] Ошибка при отправке отчета: {e}")

    @loader.command()
    async def track(self, message: Message):
        """Начать отслеживание пользователя. Использование: .track <id/юзернейм>"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_user"])
            return
        
        try:
            user = await self._client.get_entity(args)
            if not isinstance(user, User):
                await utils.answer(message, self.strings["invalid_user"])
                return
                
            await self.stop_tracking()
            self.tracked_user = user.id
            await self.start_tracking()
            await utils.answer(message, self.strings["tracking_started"].format(utils.get_display_name(user)))
        except Exception as e:
            await utils.answer(message, f"Ошибка: {str(e)}")

    @loader.command()
    async def untrack(self, message: Message):
        """Остановить отслеживание"""
        if not self.tracking:
            await utils.answer(message, self.strings["not_tracking"])
            return
            
        await self.stop_tracking()
        await utils.answer(message, self.strings["tracking_stopped"].format(self.tracked_user))
        self.tracked_user = None

    @loader.command()
    async def trackreport(self, message: Message):
        """Получить текущий отчет"""
        if not self.tracking or not self.tracked_user:
            await utils.answer(message, self.strings["not_tracking"])
            return
            
        try:
            await self._send_report()
            await utils.answer(message, "Отчет отправлен в указанный чат")
        except Exception as e:
            await utils.answer(message, f"Ошибка при отправке отчета: {str(e)}")
