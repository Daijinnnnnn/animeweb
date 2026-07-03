from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, FastAPI,Depends, HTTPException
from authx import AuthX, AuthXConfig
from database import get_db
from models import User
from schemas import UserRegisterSchema
from sqlalchemy import select
from security import hash_password


app = APIRouter(prefix ="/auth", tags=["Auth"])

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)


@app.post("/register")
async def register(creds:UserRegisterSchema, db: AsyncSession = Depends(get_db)):

    query = select(User).where(User.email_address == creds.email_address)

    result = await db.execute(query)
    if result != None:
        raise HTTPException(
            status_code=409,
            detail="Данный пользователь уже зарегистрирован"
            )    
    new_user = User(
        email_address = creds.email_address,
        hashed_password = hash_password(creds.password)
        )
    db.add(new_user)
    await db.commit()
            


@app.get("/login")
def protected():
    pass