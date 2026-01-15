from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

users = {}

@app.post("/login")
def login(data: dict):
    print("Received login data:", data)
    tg_id = str(data["tg_id"])


    if tg_id not in users:
        users[tg_id] = {"balance": 1000}

    return users[tg_id]


@app.post("/spin")
def spin(data: dict):
    tg_id = str(data["tg_id"])
    user = users[tg_id]

    bet = 50
    user["balance"] -= bet
    prize = [0, 2, 3, 10, 'COCK IN']
    weights = [60, 25, 10, 4, 1]
    a = random.choice(prize, weights=weights)
    angle = 3600 * 3

    if a == 'COCK IN':
        user["balance"] = 67148867
        win = True
    elif a == 0:
        angle += random.randint(40, 50)
        win = False
    user["balance"] += bet * a

    return {
        "roll": a,
        "angle": angle,
        "win": win,
        "balance": user["balance"]
    }

# uvicorn main:app --reload
