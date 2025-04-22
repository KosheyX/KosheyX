from .. import loader, utils
import io
import requests
from gtts import gTTS  # Google Text-to-Speech
import os

@loader.tds
class VoiceSpeakerMod(loader.Module):
    """Озвучка текста в голосовое сообщение"""
    strings = {
        "name": "VoiceSpeaker",
        "ready": "🔊 Готово!",
        "no_text": "❌ Укажите текст для озвучки",
        "error": "⚠️ Ошибка генерации голоса",
        "lang_set": "🌍 Язык изменен на: {}",
        "speed_set": "⚡ Скорость речи: {}",
        "help": (
            "🛠 <b>Справка:</b>\n"
            "<code>.voice текст</code> - озвучить текст\n"
            "<code>.voice lang ru</code> - сменить язык (ru/en/es/...)\n"
            "<code>.voice speed 1.2</code> - скорость (0.5-2.0)\n\n"
            "🗣 <b>Доступные голоса:</b>\n"
            "• <code>male</code> - мужской\n"
            "• <code>female</code> - женский\n"
            "• <code>google</code> - стандартный (gTTS)"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "lang",
                "ru",
                "Язык озвучки (ru/en/es...)",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "speed",
                1.0,
                "Скорость речи",
                validator=loader.validators.Float(minimum=0.5, maximum=2.0)
            ),
            loader.ConfigValue(
                "voice_type",
                "google",
                "Тип голоса (google/male/female)",
                validator=loader.validators.Choice(["google", "male", "female"])
            ),
        )

    async def client_ready(self, client, db):
        self._client = client

    async def voicecmd(self, message):
        """Озвучить текст"""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings["help"])
            return

        # Смена языка
        if args.startswith("lang "):
            lang = args.split(" ", 1)[1]
            self.config["lang"] = lang
            await utils.answer(message, self.strings["lang_set"].format(lang))
            return

        # Смена скорости
        if args.startswith("speed "):
            try:
                speed = float(args.split(" ", 1)[1])
                self.config["speed"] = speed
                await utils.answer(message, self.strings["speed_set"].format(speed))
            except:
                await utils.answer(message, "❌ Некорректная скорость")
            return

        # Генерация голоса
        try:
            text = args
            
            # Используем gTTS (Google Text-to-Speech)
            tts = gTTS(
                text=text,
                lang=self.config["lang"],
                slow=False if self.config["speed"] >= 1.0 else True
            )
            
            # Сохраняем во временный файл
            voice_file = io.BytesIO()
            tts.write_to_fp(voice_file)
            voice_file.seek(0)
            
            # Отправляем как голосовое
            await message.client.send_file(
                message.chat_id,
                voice_file,
                voice_note=True,
                reply_to=message.id
            )
            await utils.answer(message, self.strings["ready"])
            
        except Exception as e:
            await utils.answer(message, f"{self.strings['error']}: {str(e)}")

    async def watcher(self, message):
        """Авто-озвучка по реплаю"""
        if message.is_reply:
            replied = await message.get_reply_message()
            if replied.sender_id == (await message.client.get_me()).id:
                if "озвучь" in message.text.lower():
                    await self.voicecmd(message)
