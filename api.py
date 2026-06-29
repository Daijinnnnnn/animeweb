from fastapi import APIRouter, HTTPException, Request
import httpx 
from typing import List
from fastapi import Depends
from schemas import AnimeResponse
from main import state, JIKAN_URL
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from sqlalchemy import select
from models import Anime


app = APIRouter(prefix="/anime", tags= ["Anime"])


@app.get("/popular", response_model=List[AnimeResponse], response_model_by_alias=False)
async def get_popular_anime():
    client: httpx.AsyncClient = state["http_client"]


    try:

        response = await client.get(JIKAN_URL + "top/anime", params = {"limit": 10})
    

        response.raise_for_status()


        full_response = response.json()
        anime_list = full_response.get("data", [])

        return anime_list


    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code= exc.response.status_code,
            detail=f'Jikan API вернул ошибку: {exc.response.text}'
        )
    
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Сервис MyAnimeList (Jikan) временно недоступен"
        )


@app.get("/search", response_model=List[AnimeResponse], response_model_by_alias=False)
async def search_anime(query: str, request: Request, db: AsyncSession = Depends(get_db)):
    client: httpx.AsyncClient = state["http_client"]

    try:

        stmt = select(Anime).where(Anime.name_anime.ilike(f"%{query}%")).limit(10)
        result = await db.execute(stmt)
        cached_anime = result.scalars().all()
        if cached_anime:
            print("Данные взяты из кэша")
            return (cached_anime)


        response = await client.get(JIKAN_URL + "anime", params = {"q": query, "limit": 10})

        response.raise_for_status()

        full_response = response.json()

        anime_list = full_response.get("data", [])

        for item in anime_list:
            anime_id = item.get("mal_id")
            anime_exists = await db.get(Anime, anime_id)

            if not anime_exists:
                new_anime = Anime(
                    id=anime_id,
                    name_anime=item.get('title')
                    )
                db.add(new_anime)
        
        await db.commit()

        return anime_list
    
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code= exc.response.status_code,
            detail=f'Jikan API вернул ошибку: {exc.response.text}'
        )
    
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Сервис MyAnimeList (Jikan) временно недоступен"
        )