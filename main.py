from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

users = {}
ADMINS = {
    5016415554,
}

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

    return {
        "tg_id": tg_id,
        "balance": users[tg_id]['balance']
    }

@app.post("/admin/users")
def get_users(data: dict):
    admin_id = int(data.get("admin_id"))

    if admin_id not in ADMINS:
        raise HTTPException(status_code=403, detail="Not admin")
    
    return {
        "users": users,
    }

@app.post("/login")
def login(data: dict):
    print("Received login data:", data)
    tg_id = str(data["tg_id"])
    tg_name = str(data["tg_name"])
    tg_username = str(data["tg_useranme"])


    if tg_id not in users:
        users[tg_id] = {"balance": 1000, "name": tg_name, "username": tg_username}


    return users[tg_id]


@app.post("/spin")
def spin(data: dict):
    tg_id = str(data["tg_id"])
    user = users[tg_id]

    bet = 50
    user["balance"] -= bet

    prize = [0, 2, 3, 10, 'COCK IN']
    a = random.choices(prize, weights=(10000, 3000, 1000, 100, 1))[0]

    angle = random.randint(360 * 5, 360 * 10)

    if a == 'COCK IN':
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
        "balance": user["balance"]
    }

# uvicorn main:app --reload
