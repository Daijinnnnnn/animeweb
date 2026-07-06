from fastapi import APIRouter, HTTPException, Request
import httpx
from typing import List
from fastapi import Depends
from schemas import AnimeResponse, UserFavoriteResponse
from api.main import state, JIKAN_URL
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from sqlalchemy import select
from models import Anime, UserAnimeList, User
from sqlalchemy.orm import selectinload, joinedload


app = APIRouter(prefix="/anime", tags=["Anime"])


@app.get("/popular", response_model=List[AnimeResponse], response_model_by_alias=False)
async def get_popular_anime():
    client: httpx.AsyncClient = state["http_client"]

    try:
        response = await client.get(JIKAN_URL + "top/anime", params={"limit": 10})
        response.raise_for_status()
        full_response = response.json()
        anime_list = full_response.get("data", [])
        return anime_list

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Jikan API вернул ошибку: {exc.response.text}",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Сервис MyAnimeList (Jikan) временно недоступен"
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
            return cached_anime

        response = await client.get(JIKAN_URL + "anime", params={"q": query, "limit": 10})
        response.raise_for_status()
        full_response = response.json()
        anime_list = full_response.get("data", [])

        for item in anime_list:
            anime_id = item.get("mal_id")
            anime_exists = await db.get(Anime, anime_id)

            if not anime_exists:
                new_anime = Anime(id=anime_id, name_anime=item.get("title"))
                db.add(new_anime)

        await db.commit()

        return anime_list

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Jikan API вернул ошибку: {exc.response.text}",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Сервис MyAnimeList (Jikan) временно недоступен"
        )


@app.post("/favorite")
async def add_favorite(
    user_id: int, anime_id: int, status: str, db: AsyncSession = Depends(get_db)
):

    try:
        anime_exists = await db.get(Anime, anime_id)
        if anime_exists == None:
            raise HTTPException(status_code=404, detail="Аниме не закэшировано")

        new_favorite = UserAnimeList(user_id=user_id, anime_id=anime_id, status=status)

        db.add(new_favorite)
        await db.commit()
        return "успешно добавлено в списки"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ошибка при добавлении в избранное {str(e)}")


@app.get("/user/{user_id}/favorite", response_model=List[UserFavoriteResponse])
async def favorite_list(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stms = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.anime_associations).joinedload(UserAnimeList.anime))
        )
        result = await db.execute(stms)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="Юзер в базе не найден")

        return user.anime_associations

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении избранного {str(e)}")


@app.delete("/user/{user_id}/favorite/{anime_id}")
async def delete_favorite(user_id: int, anime_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stms = select(UserAnimeList).where(
            UserAnimeList.user_id == user_id, UserAnimeList.anime_id == anime_id
        )
        result = await db.execute(stms)
        favorite = result.scalar_one_or_none()

        if favorite is None:
            raise HTTPException(
                status_code=404, detail="Данное аниме не найдено в списке этого пользователя"
            )

        await db.delete(favorite)
        await db.commit()

        return f"{anime_id} успешно удален из избранного"

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении из избранного {str(e)}")
