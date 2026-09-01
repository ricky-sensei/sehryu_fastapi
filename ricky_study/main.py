from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator




app = FastAPI()

class Position(str, Enum):
    UPPER = "upper"
    MIDDLE = "middle"
    LOWER = "lower" 

class PartCreate(BaseModel):
    text: str = Field(min_length=1, max_length=20)
    position: Position
    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: str):
        if not isinstance(value, str):
            return value
        else:
            if "\n" in value or "\r" in value:
                raise ValueError("改行は使用できません")
            return value.strip()

part_list: list[PartCreate] = []


@app.get("/")
def get_root():
    return {"message": "川柳APIへようこそ"}

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/v1/parts")
def get_part():
    return part_list

@app.post("/v1/parts")
def post_part(part:PartCreate):
    part_list.append(part)
    return part
