from .. import loader, utils
from telethon.tl.types import Message

@loader.tds
class FontStyleMod(loader.Module):
    """✍️ Постоянный стиль шрифта для всех сообщений"""
    strings = {
        "name": "FontStyle",
        "on": "🟢 <b>Стиль шрифта включен:</b> {}",
        "off": "🔴 <b>Стиль шрифта отключен</b>",
        "current": "✏️ <b>Текущий стиль:</b> {}",
        "help": (
            "🛠 <b>Доступные команды:</b>\n"
            "<code>.font bold</code> - жирный\n"
            "<code>.font italic</code> - курсив\n"
            "<code>.font mono</code> - моноширинный\n"
            "<code>.font off</code> - отключить стиль\n"
            "<code>.font</code> - текущий статус"
        ),
        "error": "❌ Неверный стиль! Доступно: bold/italic/mono"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "active_style",
                None,
                "Активный стиль шрифта",
                validator=loader.validators.Choice(["bold", "italic", "mono", None])
            )
        )

    async def client_ready(self, client, db):
        self._client = client

    async def fontcmd(self, message: Message):
        """Управление стилями шрифтов"""
        args = utils.get_args_raw(message)
        
        if not args:
            style = self.config["active_style"]
            status = style if style else "отключен"
            await utils.answer(message, self.strings["current"].format(status))
            return
        
        if args.lower() == "off":
            self.config["active_style"] = None
            await utils.answer(message, self.strings["off"])
            return
        
        if args.lower() not in ["bold", "italic", "mono"]:
            await utils.answer(message, self.strings["error"])
            return
        
        self.config["active_style"] = args.lower()
        await utils.answer(message, self.strings["on"].format(args.lower()))

    async def watcher(self, message: Message):
        """Автоматически применяет стиль ко всем сообщениям"""
        if not isinstance(message, Message) or message.out is False:
            return
        
        if not self.config["active_style"]:
            return
        
        style = self.config["active_style"]
        original_text = message.raw_text
        
        if not original_text:
            return
        
        styled_text = self._apply_style(original_text, style)
        await message.edit(styled_text)

    def _apply_style(self, text: str, style: str) -> str:
        """Применяет выбранный стиль к тексту"""
        styles = {
            "bold": lambda t: f"<b>{t}</b>",
            "italic": lambda t: f"<i>{t}</i>",
            "mono": lambda t: f"<code>{t}</code>"
        }
        return styles[style](text)
