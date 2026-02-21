import asyncio
import random
import os
import aiosqlite

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

import uvicorn

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = {5016415554}
PORT = int(os.getenv("PORT", 8000))
SECTORS = ["COCK IN", 0, 67, 2, 0, 2, 3, 0, 3, 10, 0, 2]

DB_PATH = "users.db"
MIGRATE = True   # ⚠️ После первого запуска поставить False

# ===== ТВОИ ТЕКУЩИЕ ПОЛЬЗОВАТЕЛИ =====
CURRENT_USERS = {
    "5016415554": 69697819,
    "6468077314": 4950,
    "5339394161": 7200,
    "1270483917": 750,
    "5656419405": 1450,
    "1905506395": 1306600,
    "1770352982": 1000,
    "6875164962": 27800,
    "1340113507": 3500,
    "6319651706": 750,
    "1880762709": 950,
    "2063105118": 2950,
    "5232547174": 100,
    "1634930784": 1800,
    "5613230972": 2500,
    "1265794344": 1450,
    "1308095038": 1000,
    "6092107420": 1150,
    "5180883849": 3250,
    "8287810262": 3000,
    "6047817744": 1700,
    "1940366587": 1350,
    "5829441288": 50550,
    "6519317012": 439650,
    "8417800338": 650,
    "7443810617": 900,
    "7938186442": 1050,
    "7851899240": 3600,
    "7045389115": 850,
    "6161031657": 5750,
    "6750007016": 1000,
    "8404293603": 1000,
    "1890318195": 46150,
    "2058474108": 1150,
    "2139262875": 103050,
    "5075315394": 3550,
    "6295267209": 1450,
    "5318333325": 1000,
    "6692731813": 1900,
    "1689797785": 50850,
    "1364492068": 61050,
    "1291987159": 1300,
    "7755184925": 400,
    "2054815140": 3500,
    "8460463604": 1100,
    "8364951625": 1000,
    "6016151639": 750,
    "8000195855": 1300,
    "8561850926": 493850,
    "5869752751": 650,
    "1974897071": 2350,
    "5948153417": 1550,
    "5948671582": 2300,
    "5603873811": 750,
    "2083474849": 1000,
    "2053436700": 49800,
    "6092697587": 1400,
    "6707723856": 1000,
    "7086366485": 4850,
    "6579360246": 2850,
    "8246698535": 5500,
    "6127109783": 1200,
    "7311020517": 800,
    "8285561198": 1000,
    "5574617794": 300,
    "1599819939": 1100,
    "7026554775": 1550,
    "5135122330": 600,
    "6239917097": 1050,
    "7618667708": 1300,
    "1321359184": 1000,
    "7486118469": 51450,
    "6261604663": 1450,
    "6802205034": 1000,
    "1651623796": 1000,
    "1527351466": 1000,
    "1876963523": 1050,
}

# ===== DATABASE =====

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id TEXT PRIMARY KEY,
                balance INTEGER NOT NULL,
                name TEXT,
                username TEXT
            )
        """)
        await db.commit()


async def migrate_users():
    async with aiosqlite.connect(DB_PATH) as db:
        for tg_id, balance in CURRENT_USERS.items():
            await db.execute("""
                INSERT OR REPLACE INTO users (tg_id, balance, name, username)
                VALUES (?, ?, '', '')
            """, (tg_id, balance))
        await db.commit()


async def get_user(tg_id: str, name="", username=""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, balance, name, username FROM users WHERE tg_id = ?",
            (tg_id,)
        )
        user = await cursor.fetchone()

        if user:
            # Обновляем имя и username если изменились
            if name != user[2] or username != user[3]:
                await db.execute(
                    "UPDATE users SET name = ?, username = ? WHERE tg_id = ?",
                    (name, username, tg_id)
                )
                await db.commit()

            return {
                "tg_id": user[0],
                "balance": user[1],
                "name": name,
                "username": username,
            }

        # Если пользователя нет — создаём
        await db.execute(
            "INSERT INTO users (tg_id, balance, name, username) VALUES (?, ?, ?, ?)",
            (tg_id, 1000, name, username),
        )
        await db.commit()

        return {
            "tg_id": tg_id,
            "balance": 1000,
            "name": name,
            "username": username,
        }


async def update_balance(tg_id: str, new_balance: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (new_balance, tg_id))
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, balance, name, username FROM users")
        rows = await cursor.fetchall()

        result = {}
        for row in rows:
            result[row[0]] = {
                "balance": row[1],
                "name": row[2],
                "username": row[3],
            }
        return result
    
async def get_top_users(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT tg_id, balance, name, username
            FROM users
            ORDER BY balance DESC
            LIMIT ?
        """, (limit,))
        return await cursor.fetchall()

def format_top_users(rows):
    if not rows:
        return "🏆 Пользователей пока нет"

    text = "🏆 <b>ТОП 10 игроков</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (tg_id, balance, name, username) in enumerate(rows, start=1):
        medal = medals[i-1] if i <= 3 else f"{i}."

        display_name = name if name else tg_id
        if username:
            display_name += f" (@{username})"

        text += f"{medal} https://t.me/@id{tg_id} — 💰 <b>{balance}</b>\n"

    return text

async def auto_report():
    await asyncio.sleep(10)

    while True:
        try:
            users = await get_all_users()
            text = format_users(users)

            for admin_id in ADMINS:
                await bot.send_message(admin_id, text, parse_mode="HTML")

        except Exception as e:
            print("Ошибка автоотчета:", e)

        await asyncio.sleep(600)


# ===== GAME LOGIC =====

async def spin_logic(tg_id: str):
    user = await get_user(tg_id)
    bet = 50

    if user["balance"] < bet:
        return {"error": "no_money"}

    new_balance = user["balance"] - bet

    prize = [0, 2, 3, 10, "COCK IN"]
    roll = random.choices(prize, weights=(1000, 400, 200, 50, 1))[0]
    roll_index = random.choice([i for i, v in enumerate(SECTORS) if v == roll])

    win = False

    if roll == "COCK IN":
        new_balance += bet * 1000
        win = True
    elif roll != 0:
        new_balance += bet * roll
        win = True

    await update_balance(tg_id, new_balance)

    return {
        "roll": roll,
        "index": roll_index,
        "win": win,
        "balance": new_balance,
    }


async def add_balance_logic(admin_id: int, tg_id: str, amount: int):
    if admin_id not in ADMINS:
        raise PermissionError

    user = await get_user(tg_id)
    new_balance = user["balance"] + amount

    await update_balance(tg_id, new_balance)
    return {"balance": new_balance}


def format_users(users: dict) -> str:
    if not users:
        return "👥 Пользователей пока нет"

    text = "👥 <b>Список пользователей</b>\n\n"

    for i, (tg_id, user) in enumerate(users.items(), start=1):
        text += (
            f"<b>{i}.</b> ID: <code>{tg_id}</code>\n"
            f"💰 Баланс: <b>{user['balance']}</b>\n"
        )

        if user.get("name"):
            text += f"👤 Имя: {user['name']}\n"
        if user.get("username"):
            text += f"🔗 @{user['username']}\n"

        text += "\n"

    return text


# ===== FASTAPI =====

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.post("/login")
async def login(data: dict):
    return await get_user(
        str(data["tg_id"]),
        data.get("tg_name", ""),
        data.get("tg_username", "")
    )

@app.post("/spin")
async def spin(data: dict):
    return await spin_logic(str(data["tg_id"]))

@app.post("/admin/users")
async def admin_users(data: dict):
    if int(data["admin_id"]) not in ADMINS:
        raise HTTPException(403)
    return await get_all_users()


# ===== TELEGRAM BOT =====

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await get_user(str(message.from_user.id),
                   message.from_user.full_name,
                   message.from_user.username or "")
    await message.answer("🎰 Добро пожаловать!")

@dp.message(Command("top"))
async def top_cmd(message: Message):
    rows = await get_top_users(10)
    text = format_top_users(rows)
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("add"))
async def add_cmd(message: Message):
    if message.from_user.id not in ADMINS:
        return
    try:
        tg_id, amount = message.text.split()[1:]
        amount = int(amount)
        result = await add_balance_logic(message.from_user.id, tg_id, amount)
        await message.answer(f"✅ Баланс: {result['balance']}")
    except:
        await message.answer("❌ Ошибка")

@dp.message(Command("users"))
async def users_cmd(message: Message):
    if message.from_user.id not in ADMINS:
        return
    users = await get_all_users()
    await message.answer(format_users(users), parse_mode="HTML")


# ===== RUN BOTH =====

async def start_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()

async def start_bot():
    await dp.start_polling(bot)

async def main():
    await init_db()

    if MIGRATE:
        await migrate_users()

    api_task = asyncio.create_task(start_api())
    bot_task = asyncio.create_task(start_bot())
    report_task = asyncio.create_task(auto_report())
    await asyncio.gather(api_task, bot_task, report_task)

if __name__ == "__main__":
    asyncio.run(main())