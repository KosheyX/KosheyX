import json
import os
import random
import re
import asyncio
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from hikkatl.types import Message
from hikkatl.tl.functions.messages import SendMessageRequest
from .. import loader, utils
import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

@loader.tds
class SelfLearningBotMod(loader.Module):
    """Бот, который учится на ваших сообщениях и генерирует ответы сам"""

    strings = {
        "name": "SelfLearningBot",
        "cfg_bot_token": "Токен бота от @BotFather",
        "cfg_memory_limit": "Лимит памяти (сообщений на пользователя)",
        "born": "👶 *Я только что родился!* Говорите со мной — я буду учиться!",
        "ready": "🧠 *Я научился отвечать!* Задавайте вопросы или просто общайтесь!",
        "searching": "🔍 *Ищу информацию в интернете...*",
        "no_results": "❌ Не нашёл ответ. Попробуйте спросить иначе.",
        "thinking": "🤔 *Думаю над ответом...*",
        "memory_cleared": "🧹 *Память очищена!* Начинаю учиться заново.",
        "stats": "📊 *Статистика бота:*\nПользователей: {users}\nСлов в базе: {words}",
        "no_memory": "❌ У меня нет памяти о нашем диалоге.",
        "invalid_bot_token": "❌ Неверный токен бота!",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "BOT_TOKEN",
                None,
                lambda: self.strings["cfg_bot_token"],
                validator=loader.validators.Token()
            ),
            loader.ConfigValue(
                "MEMORY_LIMIT",
                100,
                lambda: self.strings["cfg_memory_limit"],
                validator=loader.validators.Integer(minimum=10, maximum=1000)
            ),
        )
        self.memory_file = os.path.join(loader.MODULES_DIR, "self_bot_memory.json")
        self.ngrams_file = os.path.join(loader.MODULES_DIR, "self_bot_ngrams.json")
        self.ngrams = defaultdict(list)
        self.dialog_context = defaultdict(list)
        self.load_data()
        self.bot_running = False
        self._bot_task = None

    async def client_ready(self, client, db):
        self._client = client
        if self.config["BOT_TOKEN"]:
            await self.start_bot()
        asyncio.create_task(self.autostart_messages())

    def load_data(self):
        """Загружает N-граммы и память из файлов с обработкой ошибок"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dialog_context = defaultdict(list, {
                        int(k): v[-self.config["MEMORY_LIMIT"]:] 
                        for k, v in data.items()
                    })
            
            if os.path.exists(self.ngrams_file):
                with open(self.ngrams_file, "r", encoding="utf-8") as f:
                    self.ngrams = defaultdict(list, json.load(f))
                    
            logger.info("Данные успешно загружены")
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")

    def save_data(self):
        """Сохраняет N-граммы и память в файлы с обработкой ошибок"""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v for k, v in self.dialog_context.items() if v}, 
                    f,
                    ensure_ascii=False,
                    indent=2
                )
                
            with open(self.ngrams_file, "w", encoding="utf-8") as f:
                json.dump(
                    dict(self.ngrams), 
                    f,
                    ensure_ascii=False,
                    indent=2
                )
                
            logger.info("Данные успешно сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")

    def update_ngrams(self, text: str):
        """Обновляет N-граммы из текста (разбивает на пары слов)"""
        words = re.findall(r"\w+", text.lower())
        for i in range(len(words) - 1):
            if words[i+1] not in self.ngrams[words[i]]:
                self.ngrams[words[i]].append(words[i + 1])

    async def generate_response(self, user_id: int, user_text: str) -> str:
        """Генерирует ответ на основе N-грамм и контекста"""
        # Добавляем сообщение в контекст
        self.dialog_context[user_id].append({
            "text": user_text,
            "time": datetime.now().isoformat()
        })
        
        # Ограничиваем размер памяти
        if len(self.dialog_context[user_id]) > self.config["MEMORY_LIMIT"]:
            self.dialog_context[user_id] = self.dialog_context[user_id][-self.config["MEMORY_LIMIT"]:]
        
        # Обновляем N-граммы
        self.update_ngrams(user_text)
        
        # Если вопрос - пробуем искать в интернете
        if any(q_word in user_text.lower() for q_word in ["что", "как", "почему", "кто", "где"]):
            web_result = await self.scrape_web(user_text)
            if web_result:
                return f"{self.strings['searching']}\n\n{web_result[:300]}{'...' if len(web_result) > 300 else ''}"
        
        # Генерация ответа на основе N-грамм
        words = re.findall(r"\w+", user_text.lower())
        last_word = words[-1] if words and words[-1] in self.ngrams else random.choice(
            [k for k in self.ngrams.keys() if len(self.ngrams[k]) > 3] or list(self.ngrams.keys())
        )
        
        response_words = []
        current_word = last_word
        
        for _ in range(random.randint(5, 15)):
            if current_word in self.ngrams and self.ngrams[current_word]:
                next_word = random.choice(self.ngrams[current_word])
                response_words.append(next_word)
                current_word = next_word
            else:
                break
        
        if response_words:
            response = " ".join(response_words).capitalize()
            response = response + random.choice([".", "!", "?"])
        else:
            response = random.choice([
                "Интересный вопрос...",
                "Я ещё учусь, спросите позже!",
                "Мне нужно больше данных для ответа.",
                "Не совсем понимаю, о чём вы...",
                "Можете объяснить по-другому?",
            ])
        
        return response

    async def scrape_web(self, query: str) -> Optional[str]:
        """Парсит интернет (через DuckDuckGo)"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://html.duckduckgo.com/html/?q={aiohttp.helpers.quote_plus(query)}"
                async with session.get(url, headers=headers, timeout=5) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    result = soup.find("div", class_="result__snippet")
                    return result.get_text().strip() if result else None
        except Exception as e:
            logger.error(f"Ошибка поиска в интернете: {e}")
            return None

    async def start_bot(self):
        """Запуск автономного бота"""
        if self.bot_running:
            return
            
        from hikkatl import TelegramClient, events
        from hikkatl.errors import ApiIdInvalidError, AccessTokenInvalidError
        
        try:
            self.bot = TelegramClient(
                "self_learning_bot", 
                self._client.api_id, 
                self._client.api_hash
            )
            
            await self.bot.start(bot_token=self.config["BOT_TOKEN"])
            self.bot.add_event_handler(
                self.bot_message_handler, 
                events.NewMessage(incoming=True)
            )
            
            self.bot_running = True
            self._bot_task = asyncio.create_task(self.bot.run_until_disconnected())
            logger.info("Бот успешно запущен")
            
        except AccessTokenInvalidError:
            logger.error("Неверный токен бота")
            await self._client.send_message(
                "me",
                self.strings["invalid_bot_token"]
            )
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")

    async def bot_message_handler(self, event):
        """Обработчик сообщений для автономного бота"""
        if not event.text or event.sender_id == (await event.client.get_me()).id:
            return
            
        user_id = event.sender_id
        try:
            async with event.client.action(event.chat_id, "typing"):
                response = await self.generate_response(user_id, event.text)
                await event.reply(response)
                self.save_data()
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения бота: {e}")

    async def on_message(self, message: Message):
        """Обработка сообщений в юзерботе"""
        if message.out or not message.text or not message.sender_id:
            return
            
        user_id = message.sender_id
        try:
            async with self._client.action(message.peer_id, "typing"):
                response = await self.generate_response(user_id, message.text)
                await utils.answer(message, response)
                self.save_data()
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")

    async def autostart_messages(self):
        """Авто-сообщения если пользователь молчит"""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Каждые 6 часов
                
                if not self.dialog_context:
                    continue
                    
                for user_id, messages in list(self.dialog_context.items()):
                    if not messages:
                        continue
                        
                    last_msg_time = datetime.fromisoformat(messages[-1]["time"])
                    if (datetime.now() - last_msg_time).total_seconds() > 3600 * 12:
                        try:
                            await self._client(SendMessageRequest(
                                peer=user_id,
                                message="🤖 Давно не общались! Как ваши дела?",
                                no_webpage=True
                            ))
                        except Exception as e:
                            logger.error(f"Ошибка отправки автосообщения: {e}")
                            if "USER_IS_BLOCKED" in str(e):
                                del self.dialog_context[user_id]
            except Exception as e:
                logger.error(f"Ошибка в autostart_messages: {e}")
                await asyncio.sleep(60)

    @loader.command()
    async def slbotclear(self, message: Message):
        """Очистить память бота"""
        self.ngrams.clear()
        self.dialog_context.clear()
        self.save_data()
        await utils.answer(message, self.strings["memory_cleared"])

    @loader.command()
    async def slbotstats(self, message: Message):
        """Показать статистику бота"""
        stats = {
            "users": len(self.dialog_context),
            "words": len(self.ngrams)
        }
        await utils.answer(message, self.strings["stats"].format(**stats))

 @loader.command()
async def slbotmemory(self, message: Message):
    """Показать, что бот запомнил"""
    user_id = message.sender_id
    if user_id not in self.dialog_context or not self.dialog_context[user_id]:
        await utils.answer(message, self.strings["no_memory"])
        return
        
    last_messages = "\n".join(
        f"{i+1}. {msg['text']}" 
        for i, msg in enumerate(self.dialog_context[user_id][-5:])
    )  # <- Закрывающая скобка была добавлена здесь
    
    await utils.answer(
        message,
        f"📝 <b>Последние сообщения в нашем диалоге:</b>\n\n{last_messages}"
    )

    @loader.command()
    async def slbotstart(self, message: Message):
        """Запустить автономного бота"""
        if not self.config["BOT_TOKEN"]:
            await utils.answer(
                message,
                "❌ Токен бота не установлен! Используйте .config для настройки"
            )
            return
            
        if self.bot_running:
            await utils.answer(message, "ℹ️ Бот уже запущен!")
            return
            
        await self.start_bot()
        await utils.answer(message, "🤖 Бот запущен!")

    @loader.command()
    async def slbotstop(self, message: Message):
        """Остановить автономного бота"""
        if not self.bot_running:
            await utils.answer(message, "ℹ️ Бот не запущен!")
            return
            
        try:
            self._bot_task.cancel()
            await self.bot.disconnect()
            self.bot_running = False
            await utils.answer(message, "🛑 Бот остановлен!")
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка остановки бота: {e}")
