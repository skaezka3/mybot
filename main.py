import asyncio
import random
import sqlite3
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiohttp import web

BOT_TOKEN = "8929388531:AAE3CZi50iDXhtX30t9hTMDN4fN_j5Z6OqY"
ADMIN_ID = 6713276258

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("giveaway.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, username TEXT, name TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS hack (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

user_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🎉 Участвовать в розыгрыше!")]], resize_keyboard=True)
admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎲 Запустить рандомайзер")],
    [KeyboardButton(text="✍️ Сделать подкрутку (выбрать победителя)")],
    [KeyboardButton(text="❌ Сбросить подкрутку")]
], resize_keyboard=True)

@dp.message(Command("start"))
async def start_command(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Здорово, создатель! Твоя секретная панель управления готова:", reply_markup=admin_kb)
    else:
        await message.answer(f"Привет, {message.from_user.first_name}! 👋\nНажми кнопку ниже, чтобы зарегистрироваться в розыгрыше!", reply_markup=user_kb)

@dp.message(F.text == "🎉 Участвовать в розыгрыше!")
async def join_giveaway(message: Message):
    username = message.from_user.username if message.from_user.username else "Без_ника"
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (message.from_user.id, username, message.from_user.first_name))
        conn.commit()
        await message.answer("✅ Отлично! Ты успешно записан. Жди объявления результатов!")
    except sqlite3.IntegrityError:
        await message.answer("ℹ️ Ты уже участвуешь в розыгрыше, не переживай!")

@dp.message(F.text == "🎲 Запустить рандомайзер", F.from_user.id == ADMIN_ID)
async def run_randomizer(message: Message):
    cursor.execute("SELECT value FROM hack WHERE key = 'fake_winner'")
    fake = cursor.fetchone()
    if fake:
        fake_username = fake[0]
        await message.answer(f"🎲 Розыгрыш завершен!\n\n🤖 Алгоритм случайных чисел выбрал победителя:\nПоздравляем @{fake_username}! 🎉")
        return
    cursor.execute("SELECT username FROM users")
    all_users = cursor.fetchall()
    if not all_users:
        await message.answer("❌ В базе еще нет ни одного участника.")
        return
    winner = random.choice(all_users)[0]
    await message.answer(f"🎲 Розыгрыш завершен!\n\n🤖 Алгоритм случайных чисел выбрал победителя:\nПоздравляем @{winner}! 🎉")

@dp.message(F.text == "✍️ Сделать подкрутку (выбрать победителя)", F.from_user.id == ADMIN_ID)
async def setup_hack(message: Message):
    await message.answer("Введи Telegram-никнейм человека БЕЗ знака @ (например, ivan_petrov):", reply_markup=ReplyKeyboardRemove())
    cursor.execute("INSERT OR REPLACE INTO hack VALUES ('status', 'waiting')")
    conn.commit()

@dp.message(F.text == "❌ Сбросить подкрутку", F.from_user.id == ADMIN_ID)
async def clear_hack(message: Message):
    cursor.execute("DELETE FROM hack WHERE key = 'fake_winner'")
    conn.commit()
    await message.answer("🔄 Подкрутка удалена! Следующий запуск будет честным.", reply_markup=admin_kb)

@dp.message(F.from_user.id == ADMIN_ID)
async def save_hack_winner(message: Message):
    cursor.execute("SELECT value FROM hack WHERE key = 'status'")
    status = cursor.fetchone()
    if status and status[0] == 'waiting':
        target_nick = message.text.replace("@", "").strip()
        cursor.execute("INSERT OR REPLACE INTO hack VALUES ('fake_winner', ?)", (target_nick,))
        cursor.execute("DELETE FROM hack WHERE key = 'status'")
        conn.commit()
        await message.answer(f"😈 Секретный режим активирован для @{target_nick}.", reply_markup=admin_kb)

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()
    
    asyncio.create_task(dp.start_polling(bot))
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())