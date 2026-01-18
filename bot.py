import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

BOT_TOKEN = "7713278203:AAGqLZQMDZ0he8_hZ4fq_4BpYDBmXGXWN38"
BASE_URL = "https://backendkokin-production.up.railway.app/"

ADMINS = {
    5016415554,
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Доступ запрещён")
        return
    await message.answer(
        "⚙️ Админ-панель \n\n"
        "Команды:\n"
        "/add <tg_id> <amount> - начислить баланс\n"
        "/balance <tg_id> - посмотреть баланс\n"
        "/set <tg_id> <amount> - установить баланс"
        "/users - список пользователей"
    )

@dp.message(Command("add"))
async def add_balance(message: Message):
    if message.from_user.id not in ADMINS:
        return
    
    try:
        tg_id, amount = message.text.split()[1:]
        amount = int(amount)
    except:
        await message.answer("Использование:\n/add <tg_id> <amount>")
        return
    
    r = requests.post(
        f"{BASE_URL}/admin/add_balance",
        json={
            "admin_id": message.from_user.id,
            "tg_id": tg_id,
            "amount": amount
        }
    )

    if r.status_code == 200:
        data = r.json()
        await message.answer(
            f"✅ Баланс начислен\n"
            f"ID: {tg_id}\n"
            f"Баланс: {data['balance']}"
        )
    else:
        await message.answer('❌ Ошибка сервера')

@dp.message(Command("balance"))
async def get_balance(message: Message):
    if message.from_user.id not in ADMINS:
        return
    
    try:
        tg_id = message.text.split()[1]
    except:
        await message.answer("Использование:\n/balance <tg_id>")
        return
    
    r = requests.post(
        f"{BASE_URL}/login",
        json={"tg_id": tg_id}
    )

    if r.status_code == 200:
        data = r.json()
        await message.answer(
            f"💰 Баланс пользователя\n"
            f"ID: {tg_id}\n"
            f"Баланс: {data['balance']}"
        )
    else:
        await message.answer("❌ Ошибка сервера")

@dp.message(Command("users"))
async def get_users(message: Message):
    if message.from_user.id not in ADMINS:
        return
    
    r = requests.post(
        f"{BASE_URL}/admin/users",
        json={
            "admin_id": message.from_user.id
        }
    )

    if r.status_code == 200:
        data = r.json()
        await message(
            f"📃 Список пользователей\n"
            f"{data}"
        )
    else:
        await message.answer("❌ Ошибка сервера")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())