from .. import loader, utils
from asyncio import sleep
from hikkatl.errors import FloodWaitError
import random
from typing import List, Optional

@loader.tds
class MagicAnimationsMod(loader.Module):
    """Коллекция анимированных эффектов с настройками"""
    
    strings = {
        "name": "MagicAnim",
        "cfg_speed": "Скорость анимации в секундах",
        "cfg_cycles": "Количество циклов анимации",
        "cfg_nsfw": "Разрешить NSFW анимации",
        "cfg_matrix_size": "Размер Matrix-анимации (строки, столбцы)",
        "wait_flood": "⏳ Ожидайте {seconds} секунд...",
        "error": "❌ Ошибка: {error}",
        "nsfw_disabled": "⚠️ Эта анимация отключена в настройках",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "anim_speed",
                0.3,
                lambda: self.strings("cfg_speed"),
                validator=loader.validators.Float(minimum=0.1, maximum=2.0)
            ),
            loader.ConfigValue(
                "anim_cycles",
                10,
                lambda: self.strings("cfg_cycles"),
                validator=loader.validators.Integer(minimum=1, maximum=50)
            ),
            loader.ConfigValue(
                "allow_nsfw",
                False,
                lambda: self.strings("cfg_nsfw"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "matrix_size",
                (20, 8),
                lambda: self.strings("cfg_matrix_size"),
                validator=loader.validators.Tuple(
                    loader.validators.Integer(minimum=5, maximum=50),
                    loader.validators.Integer(minimum=5, maximum=30)
                )
            )
        )
        self._matrix_cache: Optional[List[str]] = None

    async def _animate(self, message, frames, clear_cache: bool = False):
        """Улучшенный метод анимации с кэшированием"""
        if clear_cache and hasattr(self, '_matrix_cache'):
            self._matrix_cache = None
            
        try:
            for _ in range(self.config["anim_cycles"]):
                for frame in frames:
                    await message.edit(frame)
                    await sleep(self.config["anim_speed"])
        except FloodWaitError as e:
            await message.edit(self.strings("wait_flood").format(seconds=e.seconds))
        except Exception as e:
            await message.edit(self.strings("error").format(error=str(e)))

    def _generate_matrix_frames(self, count: int = 5) -> List[str]:
        """Генератор кадров для Matrix с кэшированием"""
        if self._matrix_cache:
            return self._matrix_cache
            
        rows, cols = self.config["matrix_size"]
        chars = ["0", "1", "░", "▓", "█", "▄", "▀", "■", "⣿", "⎅"]
        frames = [
            "\n".join(
                "".join(random.choice(chars) for _ in range(cols))
                for _ in range(rows)
            )
            for _ in range(count)
        ]
        self._matrix_cache = frames
        return frames

    @loader.owner
    async def heartscmd(self, message):
        """Анимация разноцветных сердец"""
        hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]
        await self._animate(message, hearts)

    @loader.owner
    async def weathercmd(self, message):
        """Анимация погодных явлений"""
        weather_frames = [
            "🌤️", "⛅", "🌥️", "☁️", "🌦️", "🌧️", "⛈️", 
            "🌨️", "❄️", "🌪️", "🌫️", "🌈", "☀️"
        ]
        await self._animate(message, weather_frames)

    @loader.owner
    async def treecmd(self, message):
        """Анимированная новогодняя ёлка"""
        tree_frames = [
            """
🎄✨
░░░░░★░░░
░░░░★✩★░░
░░★✩❄✩★░
★✩❄🎁❄✩★
░░░░| |░░
            """,
            """
🎄❄️
░░░░░☆░░░
░░░░☆★☆░░
░░☆★❅★☆░
☆★❅🎀❅★☆
░░░░| |░░
            """
        ]
        await self._animate(message, tree_frames)

    @loader.owner
    async def wavecmd(self, message):
        """Анимация морской волны"""
        wave_frames = [
            """
🌊🌊🌊🌊
░░░░░░░░
🐚🏖️🦀🌴
            """,
            """
░░🌊🌊🌊
🌊░░░░░░
🦀🏖️🐚🌴
            """
        ]
        await self._animate(message, wave_frames)

    @loader.owner
    async def clockcmd(self, message):
        """Плавное движение часовой стрелки"""
        clocks = ["🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", 
                "🕓", "🕟", "🕔", "🕠", "🕕", "🕡", "🕖", "🕢",
                "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦"]
        await self._animate(message, clocks)

    @loader.owner
    async def nyanccmd(self, message):
        """Анимация летящего Nyan Cat"""
        nyan_frames = [
            """
░░░░▄▀▀▀▄
▄███▀░◐░░░▌
░░░░▌░░░░░▐
░░░░▐░░░░░▐
░░░░▌░░░░░▐
░░░░▌░░░░░▐
░░░░▌░░░░░▐
▓▓▓▓▓▓▓▓▓▓
🌈🌈🌈🌈🌈🌈
            """,
            """
░░░░▄▀▀▀▄
▄███▀░◐░░░▌
░░░░▌░░░░░▐
░░░░▐░░░░░▐
░░░░▌░░░░░▐
░░░░▌░░░░░▐
░░░░▌░░░░░▐
▓▓▓▓▓▓▓▓▓▓
🌈🌈🌈🌈🌈🌈
            """
        ]
        await self._animate(message, nyan_frames)

    @loader.owner
    async def specialcmd(self, message):
        """Специальные анимации (требуют настройки)"""
        if not self.config["allow_nsfw"]:
            return await message.edit(self.strings("nsfw_disabled"))
        
        boom_frames = [
            "💥", "🔥", "🌪️", "💫", "✨", 
            """
░░░░▄▄▄▄▄
░░▄▀░░░░▀▄
▄▀░░░░░░░░▀▄
█░░░███░░░░█
█░░▄████▄░░█
▀▄░▀▀▀▀▀▀░▄▀
░░▀▀▀▀▀▀▀▀
            """
        ]
        await self._animate(message, boom_frames)

    @loader.owner
    async def matrixcmd(self, message):
        """Эффект падающих символов Matrix (настройки в .config)"""
        frames = self._generate_matrix_frames()
        await self._animate(message, frames)

    @loader.owner
    async def clearcachecmd(self, message):
        """Очистить кэш анимаций"""
        self._matrix_cache = None
        await message.edit("✅ Кэш анимаций очищен")

    @loader.owner
    async def helpcmd(self, message):
        """Список всех доступных анимаций"""
        help_text = [
            "<b>🎭 Доступные анимации:</b>",
            ".hearts - Разноцветные сердца",
            ".weather - Погодные явления",
            ".tree - Новогодняя ёлка",
            ".wave - Морская волна",
            ".clock - Часовые циферблаты",
            ".nyanc - Nyan Cat",
            ".matrix - Эффект Matrix (настраивается)",
            ".special - Спецэффекты (вкл. в настройках)",
            ".clearcache - Очистить кэш анимаций"
        ]
        await utils.answer(message, "\n".join(help_text))
