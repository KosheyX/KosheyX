from .. import loader, utils
from telethon.tl.types import Message
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName
import io
import random

@loader.tds
class StickerMasterMod(loader.Module):
    """Управление стикерами прямо в чате"""
    strings = {
        "name": "StickerMaster",
        "sticker_saved": "🆔 <b>Стикер сохранен в коллекцию!</b>",
        "no_reply": "❌ <b>Ответьте на стикер!</b>",
        "pack_not_found": "❌ <b>Стикерпак не найден!</b>",
        "sticker_info": (
            "📌 <b>Информация о стикере:</b>\n\n"
            "• <b>ID:</b> <code>{sticker_id}</code>\n"
            "• <b>Эмодзи:</b> {emoji}\n"
            "• <b>Набор:</b> {set_name}\n"
            "• <b>Автор:</b> {author}\n"
            "• <b>Размер:</b> {width}x{height}"
        ),
        "help": (
            "🛠 <b>Команды StickerMaster:</b>\n\n"
            "<code>.stickersave</code> - сохранить стикер в коллекцию\n"
            "<code>.stickerinfo</code> - информация о стикере\n"
            "<code>.stickersend</code> - отправить случайный стикер\n"
            "<code>.stickerfind котов</code> - найти стикеры по тегу\n"
            "<code>.stickermake</code> - создать стикер из изображения (ответьте на фото)"
        )
    }

    def __init__(self):
        self.sticker_collection = {}

    async def client_ready(self, client, db):
        self._client = client

    async def stickersavecmd(self, message: Message):
        """Сохранить стикер в коллекцию"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings["no_reply"])
            return

        sticker = reply.sticker
        if not hasattr(self, 'sticker_collection'):
            self.sticker_collection = {}

        self.sticker_collection[sticker.id] = sticker
        await utils.answer(message, self.strings["sticker_saved"])

    async def stickerinfocmd(self, message: Message):
        """Информация о стикере"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings["no_reply"])
            return

        try:
            sticker_set = await self._client(GetStickerSetRequest(
                InputStickerSetShortName(reply.sticker.set.short_name)
            )
            author = sticker_set.set.owner_id or "Неизвестно"
            
            info = self.strings["sticker_info"].format(
                sticker_id=reply.sticker.id,
                emoji=reply.sticker.emoji or "❌",
                set_name=reply.sticker.set.short_name,
                author=author,
                width=reply.sticker.width,
                height=reply.sticker.height
            )
            await utils.answer(message, info)
        except:
            await utils.answer(message, self.strings["pack_not_found"])

    async def stickersendcmd(self, message: Message):
        """Отправить случайный стикер из коллекции"""
        if not self.sticker_collection:
            await utils.answer(message, "❌ Коллекция стикеров пуста!")
            return

        random_sticker = random.choice(list(self.sticker_collection.values()))
        await message.delete()
        await message.client.send_file(
            message.to_id,
            random_sticker,
            reply_to=message.reply_to_msg_id
        )

    async def stickermakecmd(self, message: Message):
        """Создать стикер из изображения (ответьте на фото)"""
        reply = await message.get_reply_message()
        if not reply or not reply.photo:
            await utils.answer(message, "❌ Ответьте на фото!")
            return

        await utils.answer(message, "🔄 Создаю стикер...")
        photo = await reply.download_media(bytes)
        
        # Конвертация в стикер (упрощенная версия)
        sticker = io.BytesIO(photo)
        sticker.name = "sticker.webp"
        
        await message.client.send_file(
            message.to_id,
            sticker,
            force_document=False,
            allow_cache=False,
            reply_to=message.reply_to_msg_id
        )
        await message.delete()

    async def stickerfindcmd(self, message: Message):
        """Поиск стикеров по тегу"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите тег для поиска!")
            return

        # Здесь должна быть логика поиска по тегам
        # В демо-версии просто возвращаем заглушку
        await utils.answer(message, f"🔍 Результаты по тегу «{args}»:\n\n(В реальной версии здесь будут найденные стикеры)")

    async def on_message(self, message: Message):
        """Авто-ответ на ключевые слова стикерами"""
        if not message.text:
            return

        triggers = {
            "привет": "👋",
            "пока": "👋",
            "люблю": "❤️",
            "смех": "😂"
        }

        for word, emoji in triggers.items():
            if word in message.text.lower():
                await message.reply(emoji)
                break
