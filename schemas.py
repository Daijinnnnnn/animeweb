from typing import Any

from pydantic import BaseModel, Field, model_validator


class AnimeResponse(BaseModel):
    id:int
    title: str = Field(validation_alias="name_anime")
    image_url: str | None = None

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