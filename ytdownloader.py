import os
import asyncio
from hikkatl.types import Message
from .. import loader, utils

@loader.tds
class SimpleVideoDownloaderMod(loader.Module):
    """Скачать видео по ссылке (YouTube, VK, TikTok и др.)"""
    strings = {"name": "SimpleVideoDownloader"}

    async def client_ready(self, client, db):
        self._client = client

    @loader.unrestricted
    async def vdlcmd(self, message: Message):
        """<ссылка> - Скачать видео по URL"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Нужна ссылка на видео!")
            return

        await utils.answer(message, "⏳ Качаю видео...")

        try:
            # Скачиваем в mp4 (максимальное качество)
            os.system(f"yt-dlp -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' -o 'video.mp4' {args}")
            
            if not os.path.exists("video.mp4"):
                await utils.answer(message, "❌ Не удалось скачать видео. Проверь ссылку!")
                return

            # Отправляем в чат
            await message.client.send_file(
                message.chat_id,
                "video.mp4",
                caption=f"📹 Видео по ссылке: {args}",
                reply_to=message.id,
            )
            await message.delete()
            
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка: {str(e)}")
        finally:
            if os.path.exists("video.mp4"):
                os.remove("video.mp4")  # Чистим за собой
