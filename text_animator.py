from .. import loader, utils
import asyncio
from random import choice

@loader.tds
class TextAnimatorMod(loader.Module):
    """Анимация текста без удаления сообщений"""
    strings = {
        "name": "TextAnimator",
        "help": (
            "🎭 <b>Аниматор текста</b>\n\n"
            "<code>.anim волна Привет</code> - эффект волны\n"
            "<code>.anim радуга Текст</code> - разноцветный текст\n"
            "<code>.anim печать Сообщение</code> - эффект печати\n\n"
            "✨ <b>Эффекты:</b> волна, радуга, печать, матрица, дрожь"
        )
    }

    async def animcmd(self, message):
        """Анимация текста - .anim <эффект> <текст>"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["help"])
            return

        if " " not in args:
            effect = "радуга"
            text = args
        else:
            effect, text = args.split(" ", 1)

        effect = effect.lower()
        animated = await self.animate(text, effect)
        
        # Отправляем новое сообщение (без удаления исходного)
        await message.reply(animated)

    async def animate(self, text: str, effect: str) -> str:
        """Генерация анимированного текста"""
        effects = {
            "волна": self._wave,
            "радуга": self._rainbow,
            "печать": self._typing,
            "матрица": self._matrix,
            "дрожь": self._shake
        }

        if effect not in effects:
            return "❌ Неизвестный эффект. Доступно: " + ", ".join(effects.keys())

        return await effects[effect](text)

    async def _wave(self, text: str) -> str:
        """Эффект волны"""
        wave_chars = ['~', '≋', '≈']
        return " ".join([f"{choice(wave_chars)}{char}{choice(wave_chars)}" for char in text])

    async def _rainbow(self, text: str) -> str:
        """Радужный эффект"""
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
        colored = []
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            colored.append(f"<span color='{color}'>{char}</span>")
        return "".join(colored)

    async def _typing(self, text: str) -> str:
        """Эффект печати"""
        result = []
        for i in range(1, len(text)+1):
            part = text[:i]
            result.append(f"<code>{part}</code>")
        return result[-1]  # Возвращаем финальный вариант

    async def _matrix(self, text: str) -> str:
        """Матричный эффект"""
        chars = "░▒▓█║"
        return "".join([f"<span color='#00FF00'>{choice(chars)}</span>" if char != " " else " " for char in text])

    async def _shake(self, text: str) -> str:
        """Дрожащий текст"""
        directions = ["→", "←", "↑", "↓"]
        return "".join([f"{choice(directions)}{char}{choice(directions)}" for char in text])
