"""Tests for the public graph exploration API."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_article_list():
    """The list returns bounded graph results."""
    with TestClient(app) as client, patch("app.main.read", return_value=[{"id": "a1", "title": "Story"}]):
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/articles?limit=1").json()["data"][0]["id"] == "a1"
        assert client.get("/api/articles?limit=101").status_code == 422


def test_missing_article_returns_404():
    """An unknown article is distinct from one with no evidence."""
    with TestClient(app) as client, patch("app.main.read", return_value=[]):
        assert client.get("/api/articles/missing/evidence").status_code == 404
        assert client.get("/api/articles/missing/related").status_code == 404


def test_evidence_and_related_are_distinct():
    """Related-topic paths do not appear as explicit references."""
    with TestClient(app) as client, patch("app.main.read") as read:
        read.return_value = [{"id": "a1", "papers": []}]
        assert client.get("/api/articles/a1/evidence").json()["data"][0]["papers"] == []
        read.side_effect = [[{"id": "a1"}], [{"id": "a2", "connection": "shared_topic"}]]
        assert client.get("/api/articles/a1/related").json()["data"][0]["connection"] == "shared_topic"


def test_unknown_paper_and_topic():
    """Unknown entities have meaningful HTTP status codes."""
    with TestClient(app) as client, patch("app.main.read", return_value=[]):
        assert client.get("/api/papers/missing/coverage").status_code == 404
        assert client.get("/api/topics/missing/connections").status_code == 404


def test_ask_success_and_rejected_query():
    """Model output passes the actual validator before any graph query runs."""
    import io
    import json

    def response(template, search):
        return io.BytesIO(json.dumps({"response": json.dumps({"template": template, "search": search})}).encode())

    with TestClient(app) as client, patch("app.main.read", return_value=[]) as read:
        with patch("urllib.request.urlopen", return_value=response("articles_by_topic", "AI")):
            assert client.post("/api/ask", json={"question": "AI papers"}).status_code == 200
            assert read.call_count == 1
        with patch("urllib.request.urlopen", return_value=response("MATCH (n) DELETE n", "AI")):
            assert client.post("/api/ask", json={"question": "Delete everything"}).status_code == 422
            assert read.call_count == 1
