from hikka import loader, utils
import random

@loader.tds
class CoolFonts(loader.Module):
    """Крутые шрифты для русского/английского текста"""
    
    strings = {
        "name": "CoolFonts",
        "no_text": "🚫 <b>Укажи текст!</b> Пример: <code>.f Привет</code>",
        "fonts_list": "🌈 <b>Доступные шрифты:</b>\n\n{fonts}\n\nИспользуй: <code>.f номер текст</code>",
    }
    
    def __init__(self):
        self.font_styles = [
            {"name": "1. Полужирный", "func": self.bold},
            {"name": "2. Курсив", "func": self.italic},
            {"name": "3. Моноширинный", "func": self.mono},
            {"name": "4. Готический", "func": self.gothic},
            {"name": "5. Кружевной", "func": self.script},
            {"name": "6. Перевёрнутый", "func": self.upside_down},
            {"name": "7. Квадратный", "func": self.square},
            {"name": "8. Пузыри", "func": self.bubbles},
            {"name": "9. Магия", "func": self.magic},
            {"name": "10. Зачёркнутый", "func": self.strikethrough},
            {"name": "11. Надстрочный", "func": self.superscript},
            {"name": "12. Подстрочный", "func": self.subscript},
        ]
    
    async def client_ready(self, client, db):
        self.client = client
    
    @loader.unrestricted
    async def fcmd(self, message):
        """Изменить шрифт текста (.f номер текст)"""
        args = utils.get_args_raw(message)
        
        if not args:
            fonts = "\n".join(f["name"] for f in self.font_styles)
            await utils.answer(
                message,
                self.strings["fonts_list"].format(fonts=fonts)
            )
            return
        
        if args.split()[0].isdigit():
            font_num = int(args.split()[0]) - 1
            text = " ".join(args.split()[1:])
        else:
            font_num = -1  # Рандомный стиль
            text = args
        
        if not text:
            await utils.answer(message, self.strings["no_text"])
            return
        
        if 0 <= font_num < len(self.font_styles):
            styled = await self.font_styles[font_num]["func"](text)
        else:
            styled = await random.choice(self.font_styles)["func"](text)
        
        await utils.answer(message, styled)

    # Стили
    async def bold(self, text):
        return f"<b>{text}</b>"
    
    async def italic(self, text):
        return f"<i>{text}</i>"
    
    async def mono(self, text):
        return f"<code>{text}</code>"
    
    async def gothic(self, text):
        mapping = {
            'а': '𝔞', 'б': '𝔟', 'в': '𝔳', 'г': '𝔤', 'д': '𝔡', 'е': '𝔢',
            'ё': '𝔢̈', 'ж': '𝔷', 'з': '𝔷', 'и': '𝔦', 'й': '𝔧', 'к': '𝔨',
            'л': '𝔩', 'м': '𝔪', 'н': '𝔫', 'о': '𝔬', 'п': '𝔭', 'р': '𝔯',
            'с': '𝔰', 'т': '𝔱', 'у': '𝔲', 'ф': '𝔣', 'х': '𝔵', 'ц': '𝔠',
            'ч': '𝔥', 'ш': '𝔰𝔥', 'щ': '𝔰𝔠𝔥', 'ъ': '𝔟', 'ы': '𝔶', 'ь': '𝔟',
            'э': '𝔢', 'ю': '𝔧𝔲', 'я': '𝔧𝔞',
            'А': '𝔄', 'Б': '𝔅', 'В': '𝔙', 'Г': '𝔊', 'Д': '𝔇', 'Е': '𝔈',
            'Ё': '𝔈̈', 'Ж': '𝔚', 'З': '𝔜', 'И': '𝔉', 'Й': '𝔍', 'К': '𝔎',
            'Л': '𝔏', 'М': '𝔐', 'Н': '𝔑', 'О': '𝔒', 'П': '𝔓', 'Р': '𝔓',
            'С': '𝔖', 'Т': '𝔗', 'У': '𝔘', 'Ф': '𝔉', 'Х': '𝔛', 'Ц': '𝔜',
            'Ч': '𝔔', 'Ш': '𝔖𝔥', 'Щ': '𝔖𝔠𝔥', 'Ъ': '𝔅', 'Ы': '𝔜', 'Ь': '𝔅',
            'Э': '𝔈', 'Ю': '𝔍𝔲', 'Я': '𝔍𝔞',
        }
        return "".join(mapping.get(c, c) for c in text)
    
    async def script(self, text):
        mapping = {
            'а': '𝒶', 'б': '𝒷', 'в': '𝓋', 'г': '𝑔', 'д': '𝒹', 'е': '𝑒',
            'ё': '𝑒̈', 'ж': '𝓏', 'з': '𝓏', 'и': '𝒾', 'й': '𝒿', 'к': '𝓀',
            'л': '𝓁', 'м': '𝓂', 'н': '𝓃', 'о': '𝑜', 'п': '𝓅', 'р': '𝓇',
            'с': '𝓈', 'т': '𝓉', 'у': '𝓊', 'ф': '𝒻', 'х': '𝓍', 'ц': '𝒸',
            'ч': '𝒽', 'ш': '𝓈𝒽', 'щ': '𝓈𝒸𝒽', 'ъ': '𝒷', 'ы': '𝓎', 'ь': '𝒷',
            'э': '𝑒', 'ю': '𝒿𝓊', 'я': '𝒿𝒶',
            'А': '𝒜', 'Б': '𝐵', 'В': '𝒱', 'Г': '𝒢', 'Д': '𝒟', 'Е': '𝐸',
            'Ё': '𝐸̈', 'Ж': '𝒵', 'З': '𝒵', 'И': '𝐼', 'Й': '𝒥', 'К': '𝒦',
            'Л': '𝐿', 'М': '𝑀', 'Н': '𝒩', 'О': '𝒪', 'П': '𝒫', 'Р': '𝒫',
            'С': '𝒮', 'Т': '𝒯', 'У': '𝒰', 'Ф': '𝐹', 'Х': '𝒳', 'Ц': '𝒴',
            'Ч': '𝒬', 'Ш': '𝒮𝒽', 'Щ': '𝒮𝒸𝒽', 'Ъ': '𝐵', 'Ы': '𝒴', 'Ь': '𝐵',
            'Э': '𝐸', 'Ю': '𝒥𝓊', 'Я': '𝒥𝒶',
        }
        return "".join(mapping.get(c, c) for c in text)
    
    async def upside_down(self, text):
        normal = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        flipped = "ɐʚвǝɓёжεи̶йʞлмнопᴚsтꟼфхцчшщъыьэюя∀ꓭƋꓷƎЁӜƧͶꓘ⅂ꟽᴎOꓒꓤSꓕꓵФXϼҺШЩЪЫЬƐꓵ⅄Aɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz∀ꓭƆꓷƎℲ⅁HIſꓘ⅂WNOꓒꓤSꓕ∩ΛMX⅄Z"
        trans = str.maketrans(normal, flipped)
        return text.translate(trans)[::-1]
    
    async def square(self, text):
        mapping = {
            'а': '🄰', 'б': '🄱', 'в': '🅅', 'г': '🄶', 'д': '🄳', 'е': '🄴',
            'ё': '🄴̈', 'ж': '🅉', 'з': '🅉', 'и': '🄸', 'й': '🄹', 'к': '🄺',
            'л': '🄻', 'м': '🄼', 'н': '🄽', 'о': '🄾', 'п': '🄿', 'р': '🄿',
            'с': '🅂', 'т': '🅃', 'у': '🅄', 'ф': '🄵', 'х': '🅇', 'ц': '🅈',
            'ч': '🅀', 'ш': '🅂🄷', 'щ': '🅂🄲🄷', 'ъ': '🄱', 'ы': '🅈', 'ь': '🄱',
            'э': '🄴', 'ю': '🄹🅄', 'я': '🄹🄰',
        }
        return "".join(mapping.get(c, c) for c in text)
    
    async def bubbles(self, text):
        mapping = {
            'а': 'ⓐ', 'б': 'ⓑ', 'в': 'ⓥ', 'г': 'ⓖ', 'д': 'ⓓ', 'е': 'ⓔ',
            'ё': 'ⓔ̈', 'ж': 'ⓩ', 'з': 'ⓩ', 'и': 'ⓘ', 'й': 'ⓙ', 'к': 'ⓚ',
            'л': 'ⓛ', 'м': 'ⓜ', 'н': 'ⓝ', 'о': 'ⓞ', 'п': 'ⓟ', 'р': 'ⓟ',
            'с': 'ⓢ', 'т': 'ⓣ', 'у': 'ⓤ', 'ф': 'ⓕ', 'х': 'ⓧ', 'ц': 'ⓨ',
            'ч': 'ⓠ', 'ш': 'ⓢⓗ', 'щ': 'ⓢⓒⓗ', 'ъ': 'ⓑ', 'ы': 'ⓨ', 'ь': 'ⓑ',
            'э': 'ⓔ', 'ю': 'ⓙⓤ', 'я': 'ⓙⓐ',
        }
        return "".join(mapping.get(c, c) for c in text)
    
    async def magic(self, text):
        symbols = "✨♕☯☄☽♫☘⚡"
        return " ".join(f"{random.choice(symbols)}{c}{random.choice(symbols)}" for c in text)
    
    async def strikethrough(self, text):
        return f"<s>{text}</s>"
    
    async def superscript(self, text):
        mapping = str.maketrans("0123456789абвгдеёжзийклмнопрстуфхцчшщъыьэюя", "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᵛᵍᵈᵉᵉ̈ʲᶻⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᶠʰᶜᶜʰˢʰˢᶜʰᵇʸᵇᵉʲᵘʲᵃ")
        return text.translate(mapping)
    
    async def subscript(self, text):
        mapping = str.maketrans("0123456789абвгдеёжзийклмнопрстуфхцчшщъыьэюя", "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓᵪᵧᵩᵪ")
        return text.translate(mapping)
