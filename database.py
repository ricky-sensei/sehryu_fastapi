from datetime import datetime
from pathlib import Path

from peewee import AutoField, CharField, DateTimeField, Model, SqliteDatabase


BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "data" / "senryu.db"

# テスト時に別のSQLiteファイルへ切り替えられるよう、
# DB名はあとから設定する。
database = SqliteDatabase(None)


class PhrasePart(Model):
    id = AutoField()
    text = CharField(max_length=20)
    position = CharField(max_length=6)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = database
        table_name = "phrase_parts"
        indexes = (
            # 同じ位置に同じ文章を重複登録できないようにする。
            (("position", "text"), True),
        )


def configure_database(path: Path = DATABASE_PATH):
    """使用するSQLiteファイルを設定する。"""
    if not database.is_closed():
        database.close()

    path.parent.mkdir(parents=True, exist_ok=True)
    database.init(
        str(path),
        pragmas={"foreign_keys": 1},
        check_same_thread=False,
    )


def initialize_database():
    """DBへ接続し、初回ならテーブルを作成する。"""
    database.connect(reuse_if_open=True)
    database.create_tables([PhrasePart])


def close_database():
    """開いているDB接続を閉じる。"""
    if not database.is_closed():
        database.close()


configure_database()
