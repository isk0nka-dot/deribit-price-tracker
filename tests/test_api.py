import pytest
from fastapi.testclient import TestClient

from app.db.session import Database
from tests.factories import make_price

ENDPOINTS = ["/prices", "/prices/latest", "/prices/by-date"]


@pytest.fixture
def seeded_client(database: Database, client: TestClient) -> TestClient:
    with database.session() as session:
        session.add_all(
            [
                make_price("btc_usd", "1.5", 100),
                make_price("btc_usd", "2.5", 200),
                make_price("btc_usd", "3.5", 300),
                make_price("eth_usd", "9.5", 200),
            ]
        )
    return client


def test_get_all_prices_returns_records_of_ticker(seeded_client: TestClient) -> None:
    response = seeded_client.get("/prices", params={"ticker": "btc_usd"})

    assert response.status_code == 200
    assert response.json() == [
        {"ticker": "btc_usd", "price": 1.5, "timestamp": 100},
        {"ticker": "btc_usd", "price": 2.5, "timestamp": 200},
        {"ticker": "btc_usd", "price": 3.5, "timestamp": 300},
    ]


@pytest.mark.parametrize("path", ENDPOINTS)
def test_ticker_is_required(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 422


@pytest.mark.parametrize("path", ENDPOINTS)
def test_unknown_ticker_is_rejected(client: TestClient, path: str) -> None:
    assert client.get(path, params={"ticker": "doge_usd"}).status_code == 422


def test_get_latest_price_returns_most_recent_record(seeded_client: TestClient) -> None:
    response = seeded_client.get("/prices/latest", params={"ticker": "eth_usd"})

    assert response.status_code == 200
    assert response.json() == {"ticker": "eth_usd", "price": 9.5, "timestamp": 200}


def test_get_latest_price_returns_404_without_data(client: TestClient) -> None:
    response = client.get("/prices/latest", params={"ticker": "btc_usd"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No prices stored for btc_usd"}


def test_get_prices_by_date_filters_by_period(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/prices/by-date",
        params={"ticker": "btc_usd", "date_from": 150, "date_to": 300},
    )

    assert response.status_code == 200
    assert [item["timestamp"] for item in response.json()] == [200, 300]


def test_get_prices_by_date_without_period_returns_everything(
    seeded_client: TestClient,
) -> None:
    response = seeded_client.get("/prices/by-date", params={"ticker": "btc_usd"})

    assert [item["timestamp"] for item in response.json()] == [100, 200, 300]


def test_get_prices_by_date_rejects_reversed_period(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/prices/by-date",
        params={"ticker": "btc_usd", "date_from": 300, "date_to": 100},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Period start must not be later than period end"}


def test_get_prices_by_date_rejects_negative_timestamp(client: TestClient) -> None:
    response = client.get(
        "/prices/by-date", params={"ticker": "btc_usd", "date_from": -1}
    )

    assert response.status_code == 422