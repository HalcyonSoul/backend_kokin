import asyncio
import random
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway ENV
ADMINS = {5016415554}

PORT = int(os.getenv("PORT", 8000))

# BODY

users = {}

def get_user(tg_id: str, name="", username=""):
    if tg_id not in users:
        users[tg_id] = {
            "balance": 1000,
            "name": name,
            "username": username,
        }
    return users[tg_id]


def add_balance_logic(admin_id: int, tg_id: str, amount: int):
    if admin_id not in ADMINS:
        raise PermissionError

    user = get_user(tg_id)
    user["balance"] += amount
    return user


def spin_logic(tg_id: str):
    user = users[tg_id]
    bet = 50

    if user["balance"] < bet:
        return {"error": "no_money"}

    user["balance"] -= bet

    prize = [0, 2, 3, 10, "COCK IN"]
    roll = random.choices(prize, weights=(10000, 3000, 1000, 100, 1))[0]
    angle = random.randint(360 * 5, 360 * 10)

    win = False
    if roll == "COCK IN":
        user["balance"] += bet * 1000
        win = True
    elif roll != 0:
        user["balance"] += bet * roll
        win = True

    return {
        "roll": roll,
        "angle": angle,
        "win": win,
        "balance": user["balance"],
    }

# FastAPI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
def login(data: dict):
    return get_user(
        str(data["tg_id"]),
        data.get("tg_name", ""),
        data.get("tg_username", ""),
    )


@app.post("/spin")
def spin(data: dict):
    tg_id = str(data["tg_id"])
    if tg_id not in users:
        raise HTTPException(404)
    return spin_logic(tg_id)


@app.post("/admin/users")
def admin_users(data: dict):
    if int(data["admin_id"]) not in ADMINS:
        raise HTTPException(403)
    return users

# TG BOT
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    get_user(
        str(message.from_user.id),
        message.from_user.full_name,
        message.from_user.username or "",
    )
    await message.answer("🎰 Добро пожаловать!")


@dp.message(Command("add"))
async def add_cmd(message: Message):
    if message.from_user.id not in ADMINS:
        return

    try:
        tg_id, amount = message.text.split()[1:]
        amount = int(amount)
        user = add_balance_logic(message.from_user.id, tg_id, amount)
        await message.answer(f"✅ Баланс: {user['balance']}")
    except:
        await message.answer("❌ Ошибка")


@dp.message(Command("users"))
async def users_cmd(message: Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer(f"👥 Пользователи:\n{users}")

# START

async def start_api():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot():
    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        start_api(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())