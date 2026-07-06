from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, FastAPI ,Depends, HTTPException, Request, Response
from authx import AuthX, AuthXConfig
from database import get_db
from models import User
from schemas import UserRegisterSchema,UserLoginSchema
from sqlalchemy import select
from auth.security import hash_password, verify_password


router = APIRouter(prefix ="/auth", tags=["Auth"])

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]


security = AuthX(config=config)


@router.post("/register")
async def register(creds:UserRegisterSchema, db: AsyncSession = Depends(get_db)):

    query = select(User).where(User.email_address == creds.email_address)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is not None:
        raise HTTPException(
            status_code=409,
            detail="Данный пользователь уже зарегистрирован"
            )    
    
    new_user = User(
        email_address = creds.email_address,
        hashed_password = hash_password(creds.password),
        name = creds.email_address.split("@")[0],  
        login = creds.email_address.split("@")[0]
        )
    
    db.add(new_user)
    await db.commit()
            


@router.post("/login")
async def protected(creds:UserLoginSchema, response: Response, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email_address == creds.email_address)
    email_result = await db.execute(query)
    user = email_result.scalar_one_or_none()

    if user == None: 
        raise HTTPException(
            status_code=404,
            detail="Юзер с такой почтой не зарегистрирован"
            )
    
    if not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code= 401,
            detail= "Неверный пароль"
            )
    
    token = security.create_access_token(uid= str(user.id))
    response.set_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=3600,
        expires=3600,
        samesite="lax")
    return{"access token":token}



async def get_current_user_id(request: Request, response: Response) -> int:
    try:

        token_data = await security.get_token_from_request(request, response, type="access")
        return int(token_data.sub)
    except:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )