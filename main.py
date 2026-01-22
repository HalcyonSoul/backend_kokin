import asyncio
import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

import uvicorn
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

users = {}
ADMINS = {5016415554}


@app.post("/admin/add_balance")
def add_balance(data: dict):
    admin_id = int(data.get("admin_id"))
    tg_id = str(data.get("tg_id"))
    amount = int(data.get("amount"))

    if admin_id not in ADMINS:
        raise HTTPException(status_code=403, detail="Not admin")

    if tg_id not in users:
        users[tg_id] = {"balance": 1000}

    users[tg_id]["balance"] += amount

    return {"tg_id": tg_id, "balance": users[tg_id]["balance"]}


@app.post("/admin/users")
def get_users(data: dict):
    admin_id = int(data.get("admin_id"))

    if admin_id not in ADMINS:
        raise HTTPException(status_code=403, detail="Not admin")

    return {"users": users}


@app.post("/login")
def login(data: dict):
    tg_id = str(data["tg_id"])
    tg_name = str(data.get("tg_name", ""))
    tg_username = str(data.get("tg_username", ""))

    if tg_id not in users:
        users[tg_id] = {
            "balance": 1000,
            "name": tg_name,
            "username": tg_username,
        }

    return users[tg_id]


@app.post("/spin")
def spin(data: dict):
    tg_id = str(data["tg_id"])
    user = users[tg_id]

    bet = 50
    user["balance"] -= bet

    prize = [0, 2, 3, 10, "COCK IN"]
    a = random.choices(prize, weights=(10000, 3000, 1000, 100, 1))[0]
    angle = random.randint(360 * 5, 360 * 10)

    if a == "COCK IN":
        user["balance"] += bet * 1000
        win = True
    elif a == 0:
        win = False
    else:
        user["balance"] += bet * a
        win = True

    return {
        "roll": a,
        "angle": angle,
        "win": win,
        "balance": user["balance"],
    }



BOT_TOKEN = "7713278203:AAGqLZQMDZ0he8_hZ4fq_4BpYDBmXGXWN38"
BASE_URL = "https://backendkokin-production.up.railway.app"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer(
        "⚙️ Админ-панель\n"
        "/add <tg_id> <amount>\n"
        "/balance <tg_id>\n"
        "/users"
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
            "amount": amount,
        },
    )

    if r.status_code == 200:
        await message.answer("✅ Баланс обновлён")
    else:
        await message.answer(f"❌ Ошибка {r.status_code}")

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
        await message.answer(f"❌ Ошибка {r.status_code}")

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
        await message.answer(f"❌ Ошибка {r.status_code}")

async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot():
    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        start_fastapi(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())