from .. import loader, utils
import asyncio
from random import choice, randint

@loader.tds
class TextAnimatorMod(loader.Module):
    """Аниматор текста с крутыми эффектами"""
    strings = {
        "name": "TextAnimator",
        "effects": (
            "🌀 <b>Доступные эффекты:</b>\n\n"
            "<code>wave</code> - Волна\n"
            "<code>rainbow</code> - Радуга\n"
            "<code>typing</code> - Эффект печати\n"
            "<code>matrix</code> - Матрица\n"
            "<code>shake</code> - Дрожание\n"
            "<code>rotate</code> - Вращение\n"
            "<code>expand</code> - Расширение\n"
            "<code>invert</code> - Инверсия\n"
            "<code>random</code> - Случайный\n"
            "<code>emoji</code> - Эмодзи-спам\n\n"
            "✨ <b>Пример:</b> <code>.anim wave Привет</code>"
        ),
        "processing": "<i>Анимирую текст...</i>"
    }

    async def animcmd(self, message):
        """Анимация текста - .anim <эффект> <текст>"""
        args = utils.get_args_raw(message)
        if not args or " " not in args:
            await utils.answer(message, self.strings["effects"])
            return

        effect, text = args.split(" ", 1)
        effect = effect.lower()

        await utils.answer(message, self.strings["processing"])
        result = await self.animate_text(text, effect)
        
        # Удаляем сообщение "Анимирую текст..." перед отправкой результата
        await message.delete()
        await utils.answer(message, result)

    async def animate_text(self, text: str, effect: str) -> str:
        """Генерирует анимированный текст"""
        effects = {
            "wave": self.wave_effect,
            "rainbow": self.rainbow_effect,
            "typing": self.typing_effect,
            "matrix": self.matrix_effect,
            "shake": self.shake_effect,
            "rotate": self.rotate_effect,
            "expand": self.expand_effect,
            "invert": self.invert_effect,
            "random": self.random_effect,
            "emoji": self.emoji_effect
        }

        if effect not in effects:
            return "❌ Неизвестный эффект. Используйте <code>.anim</code> для списка"

        return await effects[effect](text)

    async def wave_effect(self, text: str) -> str:
        """Эффект волны"""
        wave_chars = ['~', '≋', '≈', '∿']
        result = []
        for i, char in enumerate(text):
            wave = choice(wave_chars)
            result.append(f"{wave}{char}{wave}")
        return " ".join(result)

    async def rainbow_effect(self, text: str) -> str:
        """Радужный эффект"""
        colors = [
            'red', 'orange', 'yellow', 
            'green', 'blue', 'purple'
        ]
        result = []
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            result.append(f"<span color='{color}'>{char}</span>")
        return "".join(result)

    async def typing_effect(self, text: str) -> str:
        """Эффект печатания"""
        result = []
        for i in range(1, len(text)+1):
            part = text[:i]
            remaining = "_" * (len(text) - i)
            result.append(f"<code>{part}{remaining}</code>")
            if len(result) > 10:  # Ограничиваем количество шагов
                result.pop(0)
        return result[-1]

    async def matrix_effect(self, text: str) -> str:
        """Матричный эффект"""
        matrix_chars = "░▒▓█║╗╝╔╚"
        result = []
        for char in text:
            if char == " ":
                result.append(" ")
                continue
            matrix_char = choice(matrix_chars)
            result.append(f"<span color='#00FF00'>{matrix_char}</span>")
        return "".join(result)

    async def shake_effect(self, text: str) -> str:
        """Дрожащий текст"""
        directions = ["→", "←", "↑", "↓"]
        return "".join([
            f"{choice(directions)}{char}{choice(directions)}" 
            for char in text
        ])

    async def rotate_effect(self, text: str) -> str:
        """Вращающийся текст"""
        rotated = []
        for char in text:
            rotated.append(f"<b>{char}</b>")
        return " ".join(rotated)

    async def expand_effect(self, text: str) -> str:
        """Расширяющийся текст"""
        sizes = ["small", "medium", "large"]
        return "".join([
            f"<span size='{choice(sizes)}'>{char}</span>" 
            for char in text
        ])

    async def invert_effect(self, text: str) -> str:
        """Инвертированный текст"""
        return text[::-1]

    async def random_effect(self, text: str) -> str:
        """Случайный эффект"""
        effects = [
            self.wave_effect,
            self.rainbow_effect,
            self.matrix_effect,
            self.shake_effect
        ]
        return await choice(effects)(text)

    async def emoji_effect(self, text: str) -> str:
        """Эмодзи-спам"""
        emojis = ["✨", "⚡", "🎯", "🔥", "💫", "🌟", "🌀"]
        return " ".join([
            f"{char}{choice(emojis)}" 
            for char in text
        ])
