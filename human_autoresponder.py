from .. import loader, utils
from telethon.tl.types import Message, User
import time

@loader.tds
class StyledAutoResponderMod(loader.Module):
    """✨ Стильный автоответчик для ЛС и упоминаний"""
    strings = {
        "name": "StyledAutoResponder",
        "config_text": "Текст ответа (HTML-разметка доступна)",
        "config_delay": "Задержка между ответами (в минутах)",
        "status": (
            "⚙️ <b>Текущие настройки:</b>\n"
            "• Статус: {status}\n"
            "• Задержка: {delay} мин\n"
            "• Текст: {text}"
        ),
        "activated": "🟢 Автоответчик активирован",
        "deactivated": "🔴 Автоответчик деактивирован"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "text",
                "🤖 Я сейчас занят, отвечу позже ✨",
                lambda: self.strings["config_text"],
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "delay",
                30,
                lambda: self.strings["config_delay"],
                validator=loader.validators.Integer(minimum=1)
            ),
        )
        self.active = False
        self.last_reply = {}
        self._me = None  # Будет установлено в client_ready

    async def client_ready(self, client, db):
        self._client = client
        self._me = await client.get_me()  # Сохраняем информацию о себе

    async def arcmd(self, message: Message):
        """Управление автоответчиком"""
        args = utils.get_args_raw(message)
        
        if not args:
            status = self.strings["activated"] if self.active else self.strings["deactivated"]
            await utils.answer(
                message,
                self.strings["status"].format(
                    status=status,
                    delay=self.config["delay"],
                    text=self.config["text"]
                )
            )
            return

        if args.lower() in ["on", "вкл"]:
            self.active = True
            await utils.answer(message, self.strings["activated"])
        elif args.lower() in ["off", "выкл"]:
            self.active = False
            await utils.answer(message, self.strings["deactivated"])
        elif args.isdigit():
            self.config["delay"] = int(args)
            await utils.answer(message, f"⏱ Задержка изменена на {args} минут")
        else:
            self.config["text"] = args
            await utils.answer(message, f"✏️ Текст ответа обновлён: {args}")

    async def watcher(self, message: Message):
        if not self.active or not isinstance(message, Message):
            return

        try:
            user = await message.get_sender()
            if not isinstance(user, User) or user.bot or user.is_self:
                return
        except:
            return

        # Проверяем что сообщение адресовано нам
        is_private = message.is_private
        mentions_me = (self._me.username and 
                      f"@{self._me.username}" in (message.text or ""))
        
        if not is_private and not mentions_me:
            return

        now = time.time()
        if now - self.last_reply.get(user.id, 0) < self.config["delay"] * 60:
            return

        await message.reply(self.config["text"], parse_mode="HTML")
        self.last_reply[user.id] = now
