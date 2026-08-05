from pydantic import BaseModel, Field


class MinecraftLinkRequest(BaseModel):
    ign: str = Field(min_length=3, max_length=16)


class MinecraftProfile(BaseModel):
    ign: str
    uuid: str
    head_url: str
    avatar_url: str
