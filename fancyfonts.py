from hikka import loader, utils
import random

@loader.tds
class FancyFonts(loader.Module):
    """Крутые шрифты для текста"""
    
    strings = {
        "name": "FancyFonts",
        "no_text": "❌ Укажи текст! Пример: <code>.font привет</code>",
        "available": "📝 <b>Доступные шрифты:</b>\n\n{fonts}\n\nИспользуй: <code>.font номер текст</code>",
    }
    
    def __init__(self):
        self.fonts = [
            {"name": "1. Полужирный", "func": self.bold},
            {"name": "2. Курсив", "func": self.italic},
            {"name": "3. Моноширинный", "func": self.mono},
            {"name": "4. Размашистый", "func": self.script},
            {"name": "5. Рандомный", "func": self.random_font},
        ]
    
    async def client_ready(self, client, db):
        self.client = client
    
    @loader.unrestricted
    async def fontcmd(self, message):
        """Изменить шрифт текста (.font номер текст)"""
        args = utils.get_args_raw(message)
        
        if not args:
            fonts_list = "\n".join(f["name"] for f in self.fonts)
            await utils.answer(
                message,
                self.strings["available"].format(fonts=fonts_list)
            )
            return
        
        if args.split()[0].isdigit():
            font_num = int(args.split()[0]) - 1
            text = " ".join(args.split()[1:])
        else:
            font_num = -1  # По умолчанию - рандом
            text = args
        
        if not text:
            await utils.answer(message, self.strings["no_text"])
            return
        
        if 0 <= font_num < len(self.fonts):
            styled = await self.fonts[font_num]["func"](text)
        else:
            styled = await self.random_font(text)
        
        await utils.answer(message, styled)
    
    async def bold(self, text):
        """Полужирный шрифт"""
        return "<b>" + text + "</b>"
    
    async def italic(self, text):
        """Курсив"""
        return "<i>" + text + "</i>"
    
    async def mono(self, text):
        """Моноширинный"""
        return "<code>" + text + "</code>"
    
    async def script(self, text):
        """Размашистый стиль"""
        fancy_map = {
            'a': '𝓪', 'b': '𝓫', 'c': '𝓬', 'd': '𝓭', 'e': '𝓮',
            'f': '𝓯', 'g': '𝓰', 'h': '𝓱', 'i': '𝓲', 'j': '𝓳',
            'k': '𝓴', 'l': '𝓵', 'm': '𝓶', 'n': '𝓷', 'o': '𝓸',
            'p': '𝓹', 'q': '𝓺', 'r': '𝓻', 's': '𝓼', 't': '𝓽',
            'u': '𝓾', 'v': '𝓿', 'w': '𝔀', 'x': '𝔁', 'y': '𝔂', 'z': '𝔃',
            'A': '𝓐', 'B': '𝓑', 'C': '𝓒', 'D': '𝓓', 'E': '𝓔',
            'F': '𝓕', 'G': '𝓖', 'H': '𝓗', 'I': '𝓘', 'J': '𝓙',
            'K': '𝓚', 'L': '𝓛', 'M': '𝓜', 'N': '𝓝', 'O': '𝓞',
            'P': '𝓟', 'Q': '𝓠', 'R': '𝓡', 'S': '𝓢', 'T': '𝓣',
            'U': '𝓤', 'V': '𝓥', 'W': '𝓦', 'X': '𝓧', 'Y': '𝓨', 'Z': '𝓩',
        }
        return "".join(fancy_map.get(c, c) for c in text)
    
    async def random_font(self, text):
        """Случайный стиль"""
        fonts = [self.bold, self.italic, self.mono, self.script]
        return await random.choice(fonts)(text)
