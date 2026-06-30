from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator, AliasPath, AliasChoices


class AnimeResponse(BaseModel):
    id:int
    title: str = Field(validation_alias=AliasChoices("name_anime","title"))
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


    @model_validator(mode='before')
    @classmethod
    def transform_data(cls,data:Any) -> Any:
        if not isinstance(data,dict):
            return data



        if "mal_id" in data and "id" not in data:
            data["id"] = data.pop("mal_id")


        if "images" in data:
            images = data.get("images", {})
            jpg = images.get("jpg", {})

            data["image_url"] = jpg.get("image_url")

        return data
    

class UserFavoriteResponse(BaseModel):
    status: str
    anime_id: int
    title: str = Field(validation_alias=AliasPath("anime", "name_anime"))

    model_config = {"from_attributes":True}