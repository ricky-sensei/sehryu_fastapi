from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status
from peewee import IntegrityError, fn

from database import PhrasePart, close_database, initialize_database
from schemas import HealthResponse, PartCreate, PartResponse, Position, SenryuResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリの起動時にDBを準備し、終了時に接続を閉じる。"""
    initialize_database()
    try:
        yield
    finally:
        close_database()


app = FastAPI(
    title="みんなの川柳API",
    description=(
        "上五・中七・下五を登録し、ランダムな一句を作るAPIです。"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["案内"])
def root():
    return {
        "message": "みんなの川柳API",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["案内"])
def health_check():
    return HealthResponse(status="ok")


@app.post(
    "/v1/parts",
    response_model=PartResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["句の部品"],
)
def create_part(part: PartCreate):
    """上五・中七・下五のいずれかを1件登録する。"""
    try:
        saved_part = PhrasePart.create(
            text=part.text,
            position=part.position.value,
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="同じ位置に同じ句がすでに登録されています。",
        ) from error

    return saved_part


@app.get(
    "/v1/parts",
    response_model=list[PartResponse],
    tags=["句の部品"],
)
def get_parts(
    position: Position | None = Query(
        default=None,
        description="upper、middle、lowerのいずれかで絞り込みます。",
    ),
):
    """登録済みの句を、登録順に返す。"""
    query = PhrasePart.select()

    if position is not None:
        query = query.where(PhrasePart.position == position.value)

    return list(query.order_by(PhrasePart.id))


@app.get(
    "/v1/senryu/random",
    response_model=SenryuResponse,
    tags=["川柳"],
)
def create_random_senryu():
    """各位置から1件ずつ選び、ランダムな一句を返す。"""
    selected_parts: dict[Position, PhrasePart | None] = {
        position: (
            PhrasePart.select()
            .where(PhrasePart.position == position.value)
            .order_by(fn.Random())
            .first()
        )
        for position in Position
    }

    missing_positions = [
        position.japanese_name
        for position, part in selected_parts.items()
        if part is None
    ]

    if missing_positions:
        missing_text = "・".join(missing_positions)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{missing_text}がまだ登録されていません。",
        )

    upper = selected_parts[Position.UPPER]
    middle = selected_parts[Position.MIDDLE]
    lower = selected_parts[Position.LOWER]

    # 直前の不足チェックにより、ここでは3件とも必ず存在する。
    assert upper is not None
    assert middle is not None
    assert lower is not None

    return SenryuResponse(
        upper=upper.text,
        middle=middle.text,
        lower=lower.text,
        senryu=f"{upper.text}\n{middle.text}\n{lower.text}",
    )
