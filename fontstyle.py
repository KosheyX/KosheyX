from .. import loader, utils
from telethon.tl.types import Message
from telethon import events

@loader.tds
class StealthFontMod(loader.Module):
    """✍️ Стиль шрифта без пометки 'изменено'"""
    strings = {
        "name": "StealthFont",
        "on": "🟢 <b>Стиль включен:</b> {} (без пометки редактирования)",
        "off": "🔴 <b>Стиль отключен</b>",
        "current": "✏️ <b>Текущий стиль:</b> {}",
        "help": (
            "🛠 <b>Команды:</b>\n"
            "<code>.sfont bold</code> - жирный\n"
            "<code>.sfont italic</code> - курсив\n"
            "<code>.sfont underline</code> - подчёркнутый\n"
            "<code>.sfont strike</code> - зачёркнутый\n"
            "<code>.sfont off</code> - выключить\n"
            "<code>.sfont</code> - статус"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "active_style",
                None,
                "Активный стиль",
                validator=loader.validators.Choice(["bold", "italic", "underline", "strike", None])
            )
        )
        self._client = None
        self._me = None

    async def client_ready(self, client, db):
        self._client = client
        self._me = await client.get_me()
        client.add_event_handler(self._handle_outgoing, events.NewMessage(outgoing=True))

    async def _handle_outgoing(self, event):
        """Перехватывает отправку сообщения"""
        if not self.config["active_style"] or not event.message.text:
            return
            
        style = self.config["active_style"]
        styled_text = self._apply_style(event.message.text, style)
        
        # Отменяем оригинальное сообщение и отправляем стилизованное
        await event.delete()
        await self._client.send_message(
            entity=event.chat_id,
            message=styled_text,
            parse_mode='HTML'
        )

    async def sfontcmd(self, message: Message):
        """Управление стилями"""
        args = utils.get_args_raw(message)
        
        if not args:
            style = self.config["active_style"] or "отключен"
            await utils.answer(message, self.strings["current"].format(style))
            return
            
        if args.lower() == "off":
            self.config["active_style"] = None
            await utils.answer(message, self.strings["off"])
            return
            
        if args.lower() not in ["bold", "italic", "underline", "strike"]:
            await utils.answer(message, self.strings["help"])
            return
            
        self.config["active_style"] = args.lower()
        await utils.answer(message, self.strings["on"].format(args.lower()))

    def _apply_style(self, text: str, style: str) -> str:
        """Применяет стиль через HTML-разметку"""
        styles = {
            "bold": f"<b>{text}</b>",
            "italic": f"<i>{text}</i>",
            "underline": f"<u>{text}</u>",
            "strike": f"<s>{text}</s>"
        }
        return styles[style]
