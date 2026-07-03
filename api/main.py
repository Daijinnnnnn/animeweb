from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx 


state = {}

JIKAN_URL = "https://api.jikan.moe/v4/"


@asynccontextmanager
async def lifespan(app:FastAPI):
    timeout_config = httpx.Timeout(connect=2.0, read=10.0, write=None, pool=None)


    async with httpx.AsyncClient(timeout = timeout_config) as client:
        state["http_client"] = client
        yield


    state.clear()


app = FastAPI(lifespan=lifespan)

from api.v1.api import app as anime_router

app.include_router(anime_router)