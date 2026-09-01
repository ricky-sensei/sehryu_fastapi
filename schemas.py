from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Position(str, Enum):
    UPPER = "upper"
    MIDDLE = "middle"
    LOWER = "lower"

    @property
    def japanese_name(self):
        names = {
            Position.UPPER: "上五",
            Position.MIDDLE: "中七",
            Position.LOWER: "下五",
        }
        return names[self]


class PartCreate(BaseModel):
    text: str = Field(min_length=1, max_length=20, examples=["古池や"])
    position: Position

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            if "\n" in value or "\r" in value:
                raise ValueError("句は改行せず1行で入力してください。")
            return value.strip()
        return value


class PartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: Position
    created_at: datetime


class SenryuResponse(BaseModel):
    upper: str
    middle: str
    lower: str
    senryu: str


class HealthResponse(BaseModel):
    status: str
