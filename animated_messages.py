import asyncio
import hikari
from hikari import Message
from typing import Dict, Optional, List

class AdvancedAnimator:
    def __init__(self):
        self.active_animations: Dict[int, asyncio.Task] = {}
        self.animation_states: Dict[int, dict] = {}
        self.animations = {
            'spin': self.spin_animation,
            'wave': self.wave_animation,
            'pulse': self.pulse_animation,
            'progress': self.progress_animation,
            'bounce': self.bounce_animation,
            'emoji': self.emoji_animation
        }
        self.animation_descriptions = {
            'spin': 'Вращающийся круг',
            'wave': 'Бегущая волна',
            'pulse': 'Пульсирующая линия',
            'progress': 'Прогресс бар',
            'bounce': 'Прыгающий шарик',
            'emoji': 'Смена эмодзи'
        }

    async def spin_animation(self, message: Message):
        frames = ['◴', '◷', '◶', '◵']
        while True:
            for frame in frames:
                try:
                    await message.edit(frame)
                    await asyncio.sleep(0.3)
                except hikari.NotFoundError:
                    return

    async def wave_animation(self, message: Message):
        text = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"
        while True:
            for i in range(len(text)):
                try:
                    await message.edit(text[i:i+8])
                    await asyncio.sleep(0.1)
                except hikari.NotFoundError:
                    return

    async def pulse_animation(self, message: Message):
        sizes = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        while True:
            for size in sizes + sizes[::-1]:
                try:
                    await message.edit(size)
                    await asyncio.sleep(0.1)
                except hikari.NotFoundError:
                    return

    async def progress_animation(self, message: Message):
        bar = "[----------]"
        while True:
            for i in range(1, 10):
                try:
                    await message.edit(bar.replace('-', '=', i).replace('=', '-', 10-i))
                    await asyncio.sleep(0.3)
                except hikari.NotFoundError:
                    return

    async def bounce_animation(self, message: Message):
        frames = [
            "|o        |",
            "|  o      |",
            "|    o    |",
            "|      o  |",
            "|        o|",
            "|      o  |",
            "|    o    |",
            "|  o      |"
        ]
        while True:
            for frame in frames + frames[::-1]:
                try:
                    await message.edit(frame)
                    await asyncio.sleep(0.2)
                except hikari.NotFoundError:
                    return

    async def emoji_animation(self, message: Message):
        emojis = ["🚀", "⭐", "🌙", "🌈", "🎈", "🎉", "✨", "💫"]
        while True:
            for emoji in emojis:
                try:
                    await message.edit(emoji)
                    await asyncio.sleep(0.4)
                except hikari.NotFoundError:
                    return

    async def start_animation(self, event: hikari.MessageCreateEvent, anim_type: str = 'spin'):
        if event.channel_id in self.active_animations:
            return await event.message.respond("🚫 Анимация уже запущена в этом канале!")

        initial_message = await event.message.respond("⏳ Загрузка анимации...")
        task = asyncio.create_task(self.animations[anim_type](initial_message))
        self.active_animations[event.channel_id] = task
        self.animation_states[event.channel_id] = {
            'type': anim_type,
            'message_id': initial_message.id
        }

    async def stop_animation(self, event: hikari.MessageCreateEvent):
        task = self.active_animations.get(event.channel_id)
        if task:
            task.cancel()
            del self.active_animations[event.channel_id]
            del self.animation_states[event.channel_id]
            await event.message.respond("✅ Анимация остановлена!")
        else:
            await event.message.respond("⚠️ Нет активных анимаций!")

    async def list_animations(self, event: hikari.MessageCreateEvent):
        anim_list = "\n".join([f"▸ **{name}** - {desc}" for name, desc in self.animation_descriptions.items()])
        await event.message.respond(
            "📜 **Доступные анимации:**\n" + anim_list + 
            "\n\nℹ️ Используйте `/animate_set <название>` для выбора"
        )

    async def set_animation(self, event: hikari.MessageCreateEvent, anim_type: str):
        if anim_type not in self.animations:
            return await event.message.respond(f"❌ Неизвестная анимация: `{anim_type}`")

        if event.channel_id in self.animation_states:
            await self.stop_animation(event)
            await asyncio.sleep(1)
            await self.start_animation(event, anim_type)
            await event.message.respond(f"🔄 Анимация изменена на: `{anim_type}`")
        else:
            await event.message.respond("ℹ️ Сначала запустите анимацию!")

def load_module(bot):
    animator = AdvancedAnimator()

    @bot.command
    @hikari.options.option(
        name="type",
        description="Тип анимации",
        required=False,
        choices=list(animator.animation_descriptions.keys())
    )
    async def animate_start(ctx: hikari.CommandContext, type: Optional[str] = 'spin'):
        await animator.start_animation(ctx, type)

    @bot.command
    async def animate_stop(ctx: hikari.CommandContext):
        await animator.stop_animation(ctx)

    @bot.command
    async def animate_list(ctx: hikari.CommandContext):
        await animator.list_animations(ctx)

    @bot.command
    @hikari.options.option(
        name="type",
        description="Тип анимации",
        required=True,
        choices=list(animator.animation_descriptions.keys())
    )
    async def animate_set(ctx: hikari.CommandContext, type: str):
        await animator.set_animation(ctx, type)

    print("✅ Модуль анимаций v2.0 успешно загружен!")
    print(f"Доступно анимаций: {len(animator.animations)}")
