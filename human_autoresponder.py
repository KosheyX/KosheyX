from .. import loader, utils
from telethon.tl.types import Message, User
import time
import random

@loader.tds
class StyledAutoResponderMod(loader.Module):
    """✨ Стильный автоответчик для ЛС и упоминаний"""
    strings = {
        "name": "💬 StyledAutoResponder",
        "config_text": "📝 Текст ответа (HTML-разметка доступна)",
        "config_delay": "⏳ Задержка между ответами (в минутах)",
        "config_font": "🔤 Стиль шрифта",
        "config_color": "🎨 Цвет текста",
        "status": (
            "⚙️ <b><u>Текущие настройки автоответчика</u></b>\n\n"
            "▫️ <b>Состояние:</b> {status}\n"
            "▫️ <b>Задержка:</b> {delay} мин\n"
            "▫️ <b>Стиль шрифта:</b> {font}\n"
            "▫️ <b>Цвет текста:</b> {color}\n\n"
            "📌 <b>Текст ответа:</b>\n{text}\n\n"
            "💡 <i>Используй .ar help для справки по командам</i>"
        ),
        "help": (
            "🛠 <b><u>Справка по командам</u></b>\n\n"
            "<code>.ar</code> - показать текущие настройки\n"
            "<code>.ar on/off</code> - включить/выключить\n"
            "<code>.ar текст</code> - изменить текст ответа\n"
            "<code>.ar 10</code> - установить задержку (10 мин)\n"
            "<code>.ar font bold</code> - изменить шрифт\n"
            "<code>.ar color #FF0000</code> - изменить цвет\n\n"
            "🎨 <b>Доступные цвета:</b>\n"
            "- HEX-код (<code>#FF0000</code> - красный)\n"
            "- Название (<code>red</code>, <code>blue</code>)\n"
            "- <code>default</code> - стандартный\n\n"
            "🔤 <b>Доступные шрифты:</b>\n"
            "- <code>normal</code> - обычный\n"
            "- <code>bold</code> - жирный\n"
            "- <code>italic</code> - курсив\n"
            "- <code>cursive</code> - рукописный"
        ),
        "font_set": "✏️ Шрифт изменён на: <b>{font}</b>",
        "color_set": "🎨 Цвет изменён на: <code>{color}</code>",
        "examples": (
            "🖌 <b><u>Примеры оформления</u></b>\n\n"
            "<b>Жирный</b>: <code>.ar font bold</code>\n"
            "<i>Курсив</i>: <code>.ar font italic</code>\n"
            "<span color='#FF0000'>Красный</span>: <code>.ar color #FF0000</code>\n"
            "<span color='#00FF00'>Зелёный</span>: <code>.ar color green</code>\n"
            "<b><i>Жирный курсив</i></b>: комбинируйте стили"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "text",
                "🤖 <i>Я сейчас занят</i>, <b>отвечу позже</b> ✨",
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
        """Управление автоответчиком - используй .ar help"""
        args = utils.get_args_raw(message)
        
        if not args:
            status = "🟢 <b>включен</b>" if self.active else "🔴 <b>выключен</b>"
            color_display = (
                f"<span color='{self.config['color']}'>{self.config['color']}</span>" 
                if self.config["color"] != "default" 
                else "стандартный"
            )
            await utils.answer(
                message,
                self.strings["status"].format(
                    status=status,
                    delay=self.config["delay"],
                    font=self.config["font"],
                    color=color_display,
                    text=self.config["text"]
                )
            )
            return

        args_lower = args.lower()
        
        if args_lower == "help":
            await utils.answer(message, self.strings["help"])
        elif args_lower == "examples":
            await utils.answer(message, self.strings["examples"])
        elif args_lower in ["on", "вкл"]:
            self.active = True
            await utils.answer(message, "🟢 <b>Автоответчик активирован!</b>")
        elif args_lower in ["off", "выкл"]:
            self.active = False
            await utils.answer(message, "🔴 <b>Автоответчик деактивирован!</b>")
        elif args_lower.startswith("font "):
            font = args[5:].lower()
            if font in ["normal", "bold", "italic", "cursive"]:
                self.config["font"] = font
                await utils.answer(message, self.strings["font_set"].format(font=font))
            else:
                await utils.answer(message, "❌ Неверный шрифт! Используй <code>.ar help</code> для списка")
        elif args_lower.startswith("color "):
            color = args[6:]
            self.config["color"] = color
            await utils.answer(message, self.strings["color_set"].format(color=color))
        elif args.isdigit():
            self.config["delay"] = int(args)
            await utils.answer(message, f"⏱ <b>Задержка изменена на</b> <code>{args}</code> <b>минут</b>")
        else:
            self.config["text"] = args
            await utils.answer(message, "✏️ <b>Текст ответа обновлён:</b>\n" + args)

    def _apply_style(self, text):
        """Применяет стили к тексту"""
        styles = {
            "bold": lambda t: f"<b>{t}</b>",
            "italic": lambda t: f"<i>{t}</i>",
            "cursive": lambda t: f"<i>{t}</i>",
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

        is_private = message.is_private
        mentions_me = f"@{self._client.me.username}" in message.text if self._client.me.username else False
        
        if not is_private and not mentions_me:
            return

        now = time.time()
        if now - self.last_reply.get(user.id, 0) < self.config["delay"] * 60:
            return

        styled_text = self._apply_style(self.config["text"])
        await message.reply(styled_text, parse_mode="HTML")
        self.last_reply[user.id] = now
