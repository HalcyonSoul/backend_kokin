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
SECTORS = ["COCK IN", 0, 67, 2, 0, 3, 2, 0, 10, 3, 0, 2];

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
    roll = random.choices(prize, weights=(1000, 400, 200, 50, 1))[0]
    roll_index = random.choice([i for i, v in enumerate(SECTORS) if v == roll])

    win = False
    if roll == "COCK IN":
        user["balance"] += bet * 1000
        win = True
    elif roll != 0:
        user["balance"] += bet * roll
        win = True

    return {
        "roll": roll,
        "index": roll_index,
        "win": win,
        "balance": user["balance"],
    }

def format_users(users: dict) -> str:
    if not users:
        return "👥 Пользователей пока нет"

    text = "👥 <b>Список пользователей</b>\n\n"

    for i, (tg_id, user) in enumerate(users.items(), start=1):
        text += (
            f"<b>{i}.</b> "
            f"ID: <code>{tg_id}</code>\n"
            f"💰 Баланс: <b>{user['balance']}</b>\n"
        )

        if user.get("name"):
            text += f"👤 Имя: {user['name']}\n"
        if user.get("username"):
            text += f"🔗 @{user['username']}\n"

        text += "\n"

    return text

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

    text = format_users(users)

    await message.answer(
        text,
        parse_mode="HTML"
    )

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