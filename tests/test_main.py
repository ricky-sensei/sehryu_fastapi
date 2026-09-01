import pytest
from fastapi.testclient import TestClient

from database import configure_database
from main import app


@pytest.fixture
def client(tmp_path):
    configure_database(tmp_path / "test.db")

    with TestClient(app) as test_client:
        yield test_client


def register_part(client, text, position):
    return client.post(
        "/v1/parts",
        json={"text": text, "position": position},
    )


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_parts(client):
    created = register_part(client, "  古池や  ", "upper")

    assert created.status_code == 201
    assert created.json()["text"] == "古池や"
    assert created.json()["position"] == "upper"

    listed = client.get("/v1/parts", params={"position": "upper"})

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["text"] == "古池や"


def test_duplicate_in_same_position_is_rejected(client):
    first = register_part(client, "古池や", "upper")
    duplicate = register_part(client, "古池や", "upper")

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_same_text_in_different_positions_is_allowed(client):
    upper = register_part(client, "春の風", "upper")
    lower = register_part(client, "春の風", "lower")

    assert upper.status_code == 201
    assert lower.status_code == 201


@pytest.mark.parametrize(
    "text",
    ["", "   ", "上五\n下五", "あ" * 21],
)
def test_invalid_text_is_rejected(client, text):
    response = register_part(client, text, "upper")

    assert response.status_code == 422


def test_invalid_position_is_rejected(client):
    response = register_part(client, "古池や", "first")

    assert response.status_code == 422


def test_random_senryu_requires_all_positions(client):
    register_part(client, "古池や", "upper")

    response = client.get("/v1/senryu/random")

    assert response.status_code == 409
    assert "中七" in response.json()["detail"]
    assert "下五" in response.json()["detail"]


def test_random_senryu_is_created(client):
    register_part(client, "古池や", "upper")
    register_part(client, "蛙飛びこむ", "middle")
    register_part(client, "水の音", "lower")

    response = client.get("/v1/senryu/random")

    assert response.status_code == 200
    assert response.json() == {
        "upper": "古池や",
        "middle": "蛙飛びこむ",
        "lower": "水の音",
        "senryu": "古池や\n蛙飛びこむ\n水の音",
    }


def test_parts_remain_after_server_restart(tmp_path):
    database_path = tmp_path / "persistent.db"
    configure_database(database_path)

    with TestClient(app) as first_client:
        created = register_part(first_client, "五月雨を", "upper")
        assert created.status_code == 201

    configure_database(database_path)

    with TestClient(app) as restarted_client:
        listed = restarted_client.get(
            "/v1/parts",
            params={"position": "upper"},
        )

    assert listed.status_code == 200
    assert [part["text"] for part in listed.json()] == ["五月雨を"]
