from .. import loader, utils
from telethon.tl.types import Message, User
import time
import random

@loader.tds
class StyledAutoResponderMod(loader.Module):
    """Автоответчик с оформлением текста"""
    strings = {
        "name": "StyledAutoResponder",
        "config_text": "Текст ответа (можно использовать HTML-разметку)",
        "config_delay": "Задержка между ответами (минуты)",
        "config_font": "Стиль шрифта (normal/bold/italic/cursive)",
        "config_color": "Цвет текста (hex-код или название)",
        "status": "✍️ <b>Текущие настройки:</b>\n"
                 "• Состояние: {status}\n"
                 "• Задержка: {delay} мин\n"
                 "• Стиль: {font}\n"
                 "• Цвет: {color}\n"
                 "• Текст: {text}"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "text",
                "<i>Я сейчас занят</i>, <b>отвечу позже</b> ✨",
                lambda: self.strings["config_text"],
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "delay",
                30,
                lambda: self.strings["config_delay"],
                validator=loader.validators.Integer(minimum=1)
            ),
            loader.ConfigValue(
                "font",
                "normal",
                lambda: self.strings["config_font"],
                validator=loader.validators.Choice(["normal", "bold", "italic", "cursive"])
            ),
            loader.ConfigValue(
                "color",
                "default",
                lambda: self.strings["config_color"],
                validator=loader.validators.String()
            ),
        )
        self.active = False
        self.last_reply = {}

    async def client_ready(self, client, db):
        self._client = client

    async def arcmd(self, message: Message):
        """Управление автоответчиком"""
        args = utils.get_args_raw(message)
        
        if not args:
            status = "✅ <b>включен</b>" if self.active else "❌ <b>выключен</b>"
            await utils.answer(
                message,
                self.strings["status"].format(
                    status=status,
                    delay=self.config["delay"],
                    font=self.config["font"],
                    color=self.config["color"],
                    text=self.config["text"]
                )
            )
            return

        if args.lower() in ["on", "вкл"]:
            self.active = True
            await utils.answer(message, "🟢 <b>Автоответчик активирован</b>")
        elif args.lower() in ["off", "выкл"]:
            self.active = False
            await utils.answer(message, "🔴 <b>Автоответчик деактивирован</b>")
        elif args.isdigit():
            self.config["delay"] = int(args)
            await utils.answer(message, f"⏱ <b>Задержка изменена на</b> <code>{args}</code> <b>минут</b>")
        else:
            self.config["text"] = args
            await utils.answer(message, "✏️ <b>Текст ответа обновлен:</b>\n" + args)

    def _apply_style(self, text):
        """Применяет стили к тексту"""
        styles = {
            "bold": lambda t: f"<b>{t}</b>",
            "italic": lambda t: f"<i>{t}</i>",
            "cursive": lambda t: f"<i>{t}</i>",  # Для телеграма cursive = italic
        }
        
        if self.config["font"] != "normal":
            text = styles[self.config["font"]](text)
        
        if self.config["color"] != "default":
            text = f'<span color="{self.config["color"]}">{text}</span>'
        
        return text

    async def watcher(self, message: Message):
        if not self.active or not isinstance(message, Message):
            return

        try:
            user = await message.get_sender()
            if not isinstance(user, User) or user.bot or user.is_self:
                return
        except:
            return

        now = time.time()
        if now - self.last_reply.get(user.id, 0) < self.config["delay"] * 60:
            return

        styled_text = self._apply_style(self.config["text"])
        await message.reply(styled_text, parse_mode="HTML")
        self.last_reply[user.id] = now
