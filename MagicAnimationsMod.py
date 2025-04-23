from .. import loader, utils
from asyncio import sleep
from hikkatl.errors import FloodWaitError

@loader.tds
class MagicAnimationsMod(loader.Module):
    """Коллекция анимированных эффектов с настройками"""
    
    strings = {
        "name": "MagicAnim",
        "cfg_speed": "Скорость анимации в секундах",
        "cfg_cycles": "Количество циклов анимации",
        "cfg_nsfw": "Разрешить NSFW анимации",
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
            )
        )

    async def _animate(self, message, frames):
        try:
            for _ in range(self.config["anim_cycles"]):
                for frame in frames:
                    await message.edit(frame)
                    await sleep(self.config["anim_speed"])
        except FloodWaitError as e:
            await message.edit(f"<b>⏳ Ожидайте {e.seconds} секунд...</b>")
        except Exception as e:
            await message.edit(f"<b>❌ Ошибка: {str(e)}</b>")

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
            return await message.edit("<b>⚠️ Эта анимация отключена в настройках</b>")
        
        # Анимация с эффектом "взрыва"
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
        """Эффект падающих символов Matrix"""
        matrix_chars = ["0", "1", "░", "▓", "█", "▄", "▀", "■", "⣿", "⎅"]
        matrix_frames = [
            "\n".join("".join(random.choice(matrix_chars) for _ in range(8)) 
            for _ in range(20)
        ]
        await self._animate(message, matrix_frames)

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
            ".matrix - Эффект Matrix",
            ".special - Спецэффекты (вкл. в настройках)"
        ]
        await utils.answer(message, "\n".join(help_text))
