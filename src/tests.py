from fastapi.testclient import TestClient
from typing import Any
from src.main import app
from http import HTTPStatus

client = TestClient(app)


def test_homepage():
    response: Any = client.get("/")

    assert "request" in response.context
    assert response.status_code == HTTPStatus.OK
    assert response.template.name == "index.html"


def test_process_statement():
    files_payload = {"statement": ("IBKR_ANNUAL_STATEMENT.pdf", b"content", "application/pdf")}

    response = client.post("/statements", files=files_payload)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"filename": "IBKR_ANUAL_STATEMENT.pdf"}
